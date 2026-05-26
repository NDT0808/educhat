import base64
import re
import requests
import fitz  # pymupdf
import asyncio
import aiohttp
import yaml
from typing import List, Optional, Set, Dict
from pathlib import Path
from bs4 import BeautifulSoup
from loguru import logger
from markdownify import markdownify as md
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from openai import OpenAI
from PIL import Image
import os
from urllib.parse import urljoin, urlparse
from models import ContentNode, UniversityInfo, ImageContent

class WebScraper:
    """
    Universal scraper handling static web, dynamic web (Playwright), PDF, Images, and Deep Crawling.
    """

    def __init__(self, user_agent: str = None, chandra_ocr_url: str = None, chandra_api_key: str = None):
        self.headers = {
            "User-Agent": user_agent or "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) if os.getenv("OPENAI_API_KEY") else None
        self.chandra_ocr_url = chandra_ocr_url or os.getenv("CHANDRA_OCR_URL", "http://localhost:8009")
        self.chandra_api_key = chandra_api_key or os.getenv("CHANDRA_API_KEY", "EMPTY")
        self.image_cache_dir = Path("downloaded_images")
        self.image_cache_dir.mkdir(exist_ok=True)

    async def scrape(self, url: str, depth: int = 1, current_depth: int = 0) -> ContentNode:
        """
        Scrapes content from a URL recursively.
        """
        # Base node
        node = ContentNode(url=url, type="page", content="")
        logger.info(f"Scraping URL: {url} (Depth: {current_depth}/{depth})")
        
        try:
            # 1. Determine Type & Scrape Content
            content_type_valid = await self._is_valid_content_type(url)
            
            # Special handling for images
            if self._is_image(url):
                node.type = "image"
                node.content = await self._process_image(url)
                return node
                
            # Special handling for PDFs
            if url.lower().endswith(".pdf") or (content_type_valid and "pdf" in self._get_content_type(url)):
                 node.type = "pdf"
                 node.content = await self._scrape_pdf(url)
                 return node

            if not content_type_valid:
                node.content = "[Skipped: Invalid Content Type]"
                return node

            # Web Scraping (Static -> Dynamic fallback)
            content = await self._scrape_static(url)
            if not content or content == "JS_DETECTED": # Assuming _scrape_static returns None or specific flag
                 logger.info(f"Switching to Playwright for {url}")
                 content = await self._scrape_dynamic(url)
            
            node.content = content or ""
            
            # 2. Deep Crawling (Find children)
            if current_depth < depth:
                # Extract links from Markdown content
                links = self._extract_links_from_markdown(node.content, url)
                
                tasks = []
                for link in links[:5]: # Limit to 5 children to avoid explosion
                    if link not in [c.url for c in node.children]: # Simple dedup
                        tasks.append(self.scrape(link, depth, current_depth + 1))
                
                if tasks:
                    children_nodes = await asyncio.gather(*tasks)
                    node.children = list(children_nodes)

        except Exception as e:
            logger.error(f"Failed to scrape {url}: {e}")
            node.content = f"Error: {e}"

        return node

    def _is_image(self, url: str) -> bool:
        return any(url.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp'])

    def _get_content_type(self, url: str) -> str:
        try:
             # Basic sync/async check - for caching, might be expensive. 
             # We rely on previous HEAD check logic mostly.
             return "text/html" # placeholder
        except:
            return ""

    async def _process_image(self, url: str) -> str:
        """
        Uses GPT-4o Vision to describe image.
        """
        if not self.client:
            return "[OCR Skipped: No API Key]"
            
        logger.info(f"Processing Image OCR for {url}")
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Extract all text and describe this image in detail."},
                            {"type": "image_url", "image_url": {"url": url}}
                        ],
                    }
                ],
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OCR Failed: {e}")
            return f"[OCR Failed: {e}]"

    def _extract_links_from_markdown(self, text: str, base_url: str) -> List[str]:
        # Regex for [text](href)
        links = re.findall(r'\[.*?\]\((.*?)\)', text)
        # Filter relevant
        valid_links = []
        for link in links:
            # Resolve relative URLs (basic)
            if link.startswith('/'):
                from urllib.parse import urljoin
                link = urljoin(base_url, link)
            
            # Simple filter: PDF, Images, or sub-pages
            if link.startswith('http') and ('pdf' in link or 'jpg' in link or base_url in link):
                valid_links.append(link)
        return list(set(valid_links))

    # ... (Keep existing _scrape_static, _scrape_dynamic, _scrape_pdf, _is_valid_content_type)
    # Be careful to merge correctly.


    async def _is_valid_content_type(self, url: str) -> bool:
        """
        Checks if the URL points to valid text-based content.
        """
        try:
            response = await asyncio.to_thread(requests.head, url, headers=self.headers, timeout=5, allow_redirects=True)
            content_type = response.headers.get("Content-Type", "").lower()
            logger.info(f"Checking {url} - Content-Type: {content_type}")
            
            # Allow: html, pdf, plain text, xml, json
            if any(t in content_type for t in ["text/html", "application/pdf", "text/plain", "application/xml", "application/json"]):
                return True
            
            # Block: image, video, audio, zip, binary
            if any(t in content_type for t in ["image/", "video/", "audio/", "application/zip", "application/octet-stream"]):
                logger.info(f"Ignored content type: {content_type}")
                return False
                
            return True # Default allow if unsure
        except Exception as e:
            logger.warning(f"HEAD check failed for {url}: {e}")
            return True # If HEAD fails, try scraping anyway

    async def _scrape_static(self, url: str) -> str:
        """
        Attempt to scrape using requests + BeautifulSoup.
        Returns None if JS rendering suspected or request failed.
        """
        try:
            # Run blocking requests in thread
            response = await asyncio.to_thread(requests.get, url, headers=self.headers, timeout=10)
            
            if response.status_code == 403:
                logger.warning(f"403 Forbidden on static request for {url}")
                return None
            
            if "application/pdf" in response.headers.get("Content-Type", "").lower():
                return "PDF_DETECTED"
            
            # Simple check for JS rendering (empty body or specific indicators)
            # This is a heuristic.
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Remove scripts and styles
            for script in soup(["script", "style"]):
                script.decompose()

            # Convert to Markdown to preserve tables, links, images
            clean_text = md(str(soup), heading_style="ATX")
            
            if len(clean_text) < 200: # Heuristic: too short might mean JS required
                logger.debug(f"Content too short ({len(clean_text)} chars). Suspecting JS render.")
                return None
                
            return clean_text

        except Exception as e:
            logger.warning(f"Static scrape error: {e}")
            return None

    async def _scrape_dynamic(self, url: str) -> str:
        """
        Scrape using Playwright for dynamic content.
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                # Create a new context with user agent
                context = await browser.new_context(user_agent=self.headers["User-Agent"])
                page = await context.new_page()
                
                # Navigate
                try:
                    # networkidle: wait until there are no network connections for at least 500 ms.
                    await page.goto(url, timeout=45000, wait_until="networkidle")
                except PlaywrightTimeoutError:
                    logger.warning(f"Timeout waiting for networkidle on {url}, continuing with loaded content.")

                # Remove scripts/styles via evaluation
                await page.evaluate("""
                    () => {
                        const elements = document.querySelectorAll('script, style');
                        elements.forEach(el => el.remove());
                    }
                """)
                
                # Get content HTML and convert to Markdown
                content_html = await page.content()
                clean_text = md(content_html, heading_style="ATX")
                return clean_text
                
            except Exception as e:
                logger.error(f"Playwright error for {url}: {e}")
                return ""
            finally:
                await browser.close()

    async def _scrape_pdf(self, url: str) -> str:
        """
        Download and extract text from PDF.
        """
        try:
            response = await asyncio.to_thread(requests.get, url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            with fitz.open(stream=response.content, filetype="pdf") as doc:
                text = ""
                for page in doc:
                    text += page.get_text() + "\n"
            
            return text
        except Exception as e:
            logger.error(f"PDF scrape error: {e}")
            return ""

    # === New Methods for Enhanced Crawling ===
    
    async def _download_image(self, url: str) -> Optional[str]:
        """
        Download an image and save it locally.
        Returns the local file path.
        """
        try:
            # Create a safe filename from URL
            parsed = urlparse(url)
            filename = Path(parsed.path).name
            if not filename:
                filename = f"image_{hash(url)}.jpg"
            
            local_path = self.image_cache_dir / filename
            
            # Skip if already downloaded
            if local_path.exists():
                logger.info(f"Image already cached: {local_path}")
                return str(local_path)
            
            # Download image
            response = await asyncio.to_thread(requests.get, url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            # Save to disk
            with open(local_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Downloaded image: {url} -> {local_path}")
            return str(local_path)
            
        except Exception as e:
            logger.error(f"Failed to download image {url}: {e}")
            return None

    def _should_chunk_image(self, image_path: Path, height_threshold: int = 3000) -> bool:
        """
        Determine if image needs chunking based on height.
        
        Args:
            image_path: Path to image file
            height_threshold: Minimum height (px) to trigger chunking
            
        Returns:
            True if image should be chunked
        """
        try:
            from PIL import Image
            img = Image.open(image_path)
            should_chunk = img.height > height_threshold
            if should_chunk:
                logger.info(f"Image requires chunking: {image_path.name} ({img.width}x{img.height}px)")
            return should_chunk
        except Exception as e:
            logger.warning(f"Could not check image dimensions: {e}")
            return False

    def _chunk_image(self, image_path: Path, chunk_height: int = 2500, overlap: int = 500) -> List[str]:
        """
        Split tall image into overlapping vertical chunks.
        
        Args:
            image_path: Path to source image
            chunk_height: Height of each chunk in pixels
            overlap: Overlap between chunks to prevent text cut-off
            
        Returns:
            List of base64-encoded chunk strings
        """
        from PIL import Image
        from io import BytesIO
        
        img = Image.open(image_path)
        width, height = img.size
        
        # Return single image if small enough
        if height <= chunk_height:
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            return [image_data]
        
        chunks = []
        y_start = 0
        chunk_num = 0
        
        while y_start < height:
            y_end = min(y_start + chunk_height, height)
            
            # Crop chunk
            chunk_img = img.crop((0, y_start, width, y_end))
            
            # Encode to base64
            buffer = BytesIO()
            chunk_img.save(buffer, format='PNG')
            chunk_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            chunks.append(chunk_b64)
            
            chunk_num += 1
            logger.debug(f"Created chunk {chunk_num}: y={y_start}-{y_end} ({y_end-y_start}px)")
            
            # Safety limit
            if chunk_num >= 10:
                logger.warning(f"Reached max chunks limit (10) for {image_path}")
                break
            
            # Exit if we've reached the bottom
            if y_end >= height:
                break
            
            # Move to next position with overlap
            y_start = y_end - overlap
        
        logger.info(f"Split {image_path.name} into {len(chunks)} chunks")
        return chunks

    def _fuzzy_match(self, str1: str, str2: str, threshold: float = 0.75) -> bool:
        """
        Check if two strings are similar enough (for overlap detection).
        
        Args:
            str1, str2: Strings to compare
            threshold: Similarity ratio threshold (0-1)
            
        Returns:
            True if strings are similar enough
        """
        from difflib import SequenceMatcher
        # Normalize whitespace and compare
        s1 = ' '.join(str1.split()).lower()
        s2 = ' '.join(str2.split()).lower()
        ratio = SequenceMatcher(None, s1, s2).ratio()
        return ratio >= threshold

    def _merge_chunk_texts(self, texts: List[str], overlap_search: int = 200) -> str:
        """
        Merge overlapping chunk texts by detecting and removing duplicates.
        
        Args:
            texts: List of OCR text from chunks
            overlap_search: Number of chars to search for overlap
            
        Returns:
            Merged text without duplicates
        """
        if not texts:
            return ""
        
        if len(texts) == 1:
            return texts[0]
        
        merged = texts[0]
        
        for i, next_text in enumerate(texts[1:], 1):
            # Find overlap: last N chars of merged == first N chars of next_text
            best_overlap = 0
            
            # Try different overlap lengths
            for overlap_len in range(min(overlap_search, len(merged), len(next_text)), 20, -5):
                merged_suffix = merged[-overlap_len:].strip()
                next_prefix = next_text[:overlap_len].strip()
                
                # Check for fuzzy match
                if len(merged_suffix) > 20 and self._fuzzy_match(merged_suffix, next_prefix, threshold=0.7):
                    best_overlap = overlap_len
                    logger.debug(f"Chunk {i}: Found overlap of {overlap_len} chars")
                    break
            
            if best_overlap > 0:
                # Remove duplicate portion from next_text
                merged += next_text[best_overlap:]
            else:
                # No overlap found, append with separator
                merged += "\n\n" + next_text
                logger.debug(f"Chunk {i}: No overlap found, adding separator")
        
        return merged

    async def _process_image_with_chandra_ocr(self, image_url: str, local_path: Optional[str] = None) -> Dict:
        """
        Process image using chandra-ocr service (vllm OpenAI-compatible API).
        Automatically chunks tall images for complete extraction.
        Returns dict with 'text', 'confidence', and optionally 'chunks_processed' keys.
        """
        try:
            # Download image if not already done
            if not local_path:
                local_path = await self._download_image(image_url)
                if not local_path:
                    return {"text": "[Image Download Failed]", "confidence": 0.0}
            
            local_path_obj = Path(local_path)
            
            # Check if image needs chunking
            if self._should_chunk_image(local_path_obj):
                return await self._process_chunked_image(image_url, local_path_obj)
            
            # Standard single-image processing
            with open(local_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            # Prepare OpenAI-compatible request
            payload = {
                "model": "chandra",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Extract all text from this image, preserving any table structure in markdown format. Be precise and maintain formatting."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 4096,  # Increased from 2000
                "temperature": 0.1
            }
            
            # Call chandra-ocr API
            headers = {"Content-Type": "application/json"}
            if self.chandra_api_key:
                headers["Authorization"] = f"Bearer {self.chandra_api_key}"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.chandra_ocr_url}/v1/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Chandra OCR API error: {response.status} - {error_text}")
                        return {"text": f"[OCR API Error: {response.status}]", "confidence": 0.0}
                    
                    result = await response.json()
                    ocr_text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    
                    logger.info(f"OCR processed: {image_url[:50]}... -> {len(ocr_text)} chars")
                    return {"text": ocr_text, "confidence": 0.95}
                    
        except asyncio.TimeoutError:
            logger.error(f"Chandra OCR timeout for {image_url}")
            return {"text": "[OCR Timeout]", "confidence": 0.0}
        except Exception as e:
            logger.error(f"Chandra OCR error for {image_url}: {e}")
            return {"text": f"[OCR Error: {e}]", "confidence": 0.0}

    async def _process_chunked_image(self, image_url: str, local_path: Path) -> Dict:
        """
        Process tall image in chunks and merge results.
        
        Args:
            image_url: Original image URL (for logging)
            local_path: Path to downloaded image
            
        Returns:
            Dict with merged 'text', 'confidence', and 'chunks_processed'
        """
        chunks = self._chunk_image(local_path)
        logger.info(f"Processing {len(chunks)} chunks for {local_path.name}")
        
        all_texts = []
        confidences = []
        
        for i, chunk_b64 in enumerate(chunks):
            logger.debug(f"OCR chunk {i+1}/{len(chunks)}")
            
            payload = {
                "model": "chandra",
                "messages": [{
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Extract all text from this image section. Preserve formatting, tables, and structure. Output as clean text."
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{chunk_b64}"}
                        }
                    ]
                }],
                "max_tokens": 4096,
                "temperature": 0.1
            }
            
            headers = {"Content-Type": "application/json"}
            if self.chandra_api_key:
                headers["Authorization"] = f"Bearer {self.chandra_api_key}"
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.chandra_ocr_url}/v1/chat/completions",
                        json=payload,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=90)  # Longer timeout for chunks
                    ) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            logger.error(f"Chunk {i+1} OCR failed: {error_text}")
                            all_texts.append(f"[Chunk {i+1} OCR Error]")
                            confidences.append(0.0)
                            continue
                        
                        result = await response.json()
                        chunk_text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                        all_texts.append(chunk_text)
                        confidences.append(0.95)
                        
                        logger.info(f"Chunk {i+1}/{len(chunks)}: {len(chunk_text)} chars extracted")
                
                # Rate limit between chunks
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Chunk {i+1} processing error: {e}")
                all_texts.append(f"[Chunk {i+1} Error: {e}]")
                confidences.append(0.0)
        
        # Merge chunks with overlap deduplication
        merged_text = self._merge_chunk_texts(all_texts)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        logger.info(f"✓ Merged {len(chunks)} chunks -> {len(merged_text)} chars (conf: {avg_confidence:.2f})")
        
        return {
            "text": merged_text,
            "confidence": avg_confidence,
            "chunks_processed": len(chunks)
        }

    def _detect_content_format(self, soup: BeautifulSoup) -> str:
        """
        Detect if tabContent contains primarily HTML or images.
        Returns 'html' or 'image'.
        """
        # Look for images in the content area
        images = soup.find_all('img')
        text_length = len(soup.get_text(strip=True))
        
        # Heuristic: if there are images and little text, it's image-based
        if len(images) > 0 and text_length < 200:
            return 'image'
        return 'html'

    async def _extract_regional_links(self, main_url: str) -> List[Dict[str, str]]:
        """
        Extract regional category links from the main university list page.
        Returns list of dicts with 'name' and 'url'.
        """
        try:
            content = await self._scrape_static(main_url)
            if not content:
                content = await self._scrape_dynamic(main_url)
            
            # Parse with BeautifulSoup
            response = await asyncio.to_thread(requests.get, main_url, headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find boxtabcontent or similar container
            # Based on the chunk we saw, links are in the content
            regional_links = []
            
            # Find all links that match the pattern for regional pages
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                # Match patterns like "CÁC TRƯỜNG ĐẠI HỌC..."
                if 'truong' in href.lower() and 'khu-vuc' in href.lower():
                    full_url = urljoin(main_url, href)
                    regional_links.append({
                        'name': text,
                        'url': full_url
                    })
                    logger.info(f"Found regional link: {text} -> {full_url}")
            
            return regional_links
            
        except Exception as e:
            logger.error(f"Failed to extract regional links: {e}")
            return []

    async def _extract_school_links(self, regional_url: str, region_name: str) -> List[Dict[str, str]]:
        """
        Extract individual school links from a regional page.
        Returns list of dicts with 'name', 'url', 'region'.
        """
        try:
            response = await asyncio.to_thread(requests.get, regional_url, headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            school_links = []
            
            # Use the FIRST .boxtabcontent only (avoid "Tin cùng chuyên mục")
            main_content = soup.find('div', class_='boxtabcontent')
            
            if not main_content:
                logger.warning(f"No .boxtabcontent found on {regional_url}")
                return []
            
            # Extract all links from  this container
            for link in main_content.find_all('a', href=True):
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                # Skip empty links
                if not text or len(text) < 3:
                    continue
                
                # Skip common navigation links
                skip_patterns = [
                    'javascript', '#', 'facebook', 'twitter',
                    'Trang chủ', 'Bản tin', 'Cao đẳng', 'Trung cấp',
                    'Dự kiến', 'Công bố', 'Thông báo'
                ]
                
                if any(pattern in text for pattern in skip_patterns):
                    continue
                
                if any(pattern in href.lower() for pattern in ['javascript', '#']):
                    continue
                
                # Build full URL
                full_url = urljoin(regional_url, href)
                
                # Only include school detail pages from thongtintuyensinh.vn
                # Filter out regional/category pages
                if 'thongtintuyensinh.vn' in full_url and full_url != regional_url:
                    # Avoid category pages (they have _C in URL typically)
                    if '_C' in full_url and '_D' not in full_url:
                        continue
                    
                    school_links.append({
                        'name': text,
                        'url': full_url,
                        'region': region_name
                    })
            
            logger.info(f"Found {len(school_links)} schools in {region_name}")
            return school_links
            
        except Exception as e:
            logger.error(f"Failed to extract school links from {regional_url}: {e}")
            return []

    async def _scrape_school_detail(self, school_info: Dict[str, str]) -> UniversityInfo:
        """
        Scrape a school's detail page, handling both HTML and image content.
        """
        name = school_info['name']
        url = school_info['url']
        region = school_info['region']
        
        logger.info(f"Scraping school: {name}")
        
        try:
            response = await asyncio.to_thread(requests.get, url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the main content area - #tabContent
            main_content = soup.find('div', id='tabContent')
            
            if not main_content:
                # Fallback to other selectors
                main_content = soup.find('div', class_='content') or soup.find('article') or soup.body
            
            if not main_content:
                logger.warning(f"No content found for {name}")
                return UniversityInfo(
                    name=name,
                    url=url,
                    region=region,
                    content="[No content area found]",
                    metadata={'error': 'No content area'}
                )
            
            # Remove scripts and styles
            for element in main_content(['script', 'style']):
                element.decompose()
            
            # Detect content format
            content_format = self._detect_content_format(main_content)
            
            content_text = ""
            images = []
            tables = []
            
            # Metadata tracking
            ocr_stats = {
                'total_images': 0,
                'images_processed': 0,
                'avg_confidence': 0.0,
                'total_ocr_chars': 0
            }
            
            if content_format == 'image':
                logger.info(f"{name}: Image-based content detected")
                # Process images with OCR
                confidences = []
                for img in main_content.find_all('img'):
                    img_url = img.get('src', '')
                    if img_url:
                        img_url = urljoin(url, img_url)
                        local_path = await self._download_image(img_url)
                        
                        if local_path:
                            ocr_result = await self._process_image_with_chandra_ocr(img_url, local_path)
                            
                            images.append(ImageContent(
                                url=img_url,
                                local_path=local_path,
                                ocr_text=ocr_result['text'],
                                ocr_confidence=ocr_result['confidence']
                            ))
                            content_text += f"\n\n## Image Content from {Path(img_url).name}\n{ocr_result['text']}"
                            
                            # Track stats
                            confidences.append(ocr_result['confidence'])
                            ocr_stats['total_ocr_chars'] += len(ocr_result['text'])
                            ocr_stats['images_processed'] += 1
                            
                            # Track chunks if image was chunked
                            if 'chunks_processed' in ocr_result:
                                if 'total_chunks' not in ocr_stats:
                                    ocr_stats['total_chunks'] = 0
                                ocr_stats['total_chunks'] += ocr_result['chunks_processed']
                        
                        ocr_stats['total_images'] += 1
                
                # Calculate average confidence
                if confidences:
                    ocr_stats['avg_confidence'] = sum(confidences) / len(confidences)
            else:
                logger.info(f"{name}: HTML content detected")
                # Process as HTML
                # Extract tables first
                for table in main_content.find_all('table'):
                    table_md = md(str(table), heading_style="ATX")
                    tables.append(table_md)
                    content_text += f"\n\n{table_md}\n\n"
                
                # Extract general content
                content_md = md(str(main_content), heading_style="ATX")
                content_text += content_md
            
            # Build comprehensive metadata
            metadata = {
                'scraped_at': str(asyncio.get_event_loop().time()),
                'content_type': content_format,
                'content_length': len(content_text),
                'num_tables': len(tables),
                'num_images': len(images)
            }
            
            # Add OCR stats if applicable
            if content_format == 'image' and ocr_stats['images_processed'] > 0:
                metadata['ocr'] = ocr_stats
            
            return UniversityInfo(
                name=name,
                url=url,
                region=region,
                content=content_text,
                images=images,
                tables=tables,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Failed to scrape {name}: {e}")
            return UniversityInfo(
                name=name,
                url=url,
                region=region,
                content=f"Error: {e}",
                metadata={'error': str(e)}
            )

    async def scrape_thongtintuyensinh(
        self, 
        main_url: str = "https://thongtintuyensinh.vn/Cac-truong-Dai-hoc-va-Hoc-vien_C284_D10208.htm", 
        test_mode: bool = False,
        save_callback: callable = None
    ) -> List[UniversityInfo]:
        """
        Main entry point for crawling thongtintuyensinh.vn university data.
        
        Args:
            main_url: Starting URL to crawl
            test_mode: If True, limit to 2 regions and 3 schools per region
            save_callback: Optional callback function(uni: UniversityInfo) called after each school
        """
        logger.info(f"Starting university crawl from {main_url}")
        
        # Step 1: Extract regional links
        regional_links = await self._extract_regional_links(main_url)
        logger.info(f"Found {len(regional_links)} regional categories")
        
        # Limit for testing
        if test_mode:
            regional_links = regional_links[:2]
            logger.info(f"Test mode: limiting to {len(regional_links)} regions")
        
        all_universities = []
        
        # Step 2: For each region, extract schools
        for region_info in regional_links:
            school_links = await self._extract_school_links(region_info['url'], region_info['name'])
            
            # Step 3: Scrape each school (limit for testing)
            limit = 3 if test_mode else len(school_links)
            for school_info in school_links[:limit]:
                university_data = await self._scrape_school_detail(school_info)
                all_universities.append(university_data)
                
                # Call save callback if provided
                if save_callback:
                    save_callback(university_data)
                
                # Be respectful with rate limiting
                await asyncio.sleep(1)
        
        logger.info(f"Crawling complete. Collected {len(all_universities)} universities")
        return all_universities


if __name__ == "__main__":
    # Test
    async def main():
        scraper = WebScraper()
        # Test a static site or PDF
        url = "https://www.example.com" 
        print(f"Scraping {url}...")
        text = await scraper.scrape(url)
        print(f"Result (first 100 chars): {text[:100]}...")

    asyncio.run(main())
