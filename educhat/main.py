import asyncio
import json
import os
from typing import List, Dict
from loguru import logger
from dotenv import load_dotenv

from searcher import SearchManager
from scraper import WebScraper
from reviser import DataNormalizer
from models import ContentNode

# Configure logger
logger.add("pipeline.log", rotation="10 MB", level="INFO")

class AutonomousPipeline:
    def __init__(self):
        self.searcher = SearchManager()
        self.scraper = WebScraper()
        # Initialize Normalizer; warn if key missing
        self.normalizer = DataNormalizer()
        self.seen_urls = set()
        self.load_seen_urls("rag_dataset.json")

    def load_seen_urls(self, filename: str):
        if os.path.exists(filename):
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for entry in data:
                        if "url" in entry:
                            self.seen_urls.add(entry["url"])
            except Exception:
                pass # Ignore errors

    async def run(self, query: str, num_urls: int = 5, output_file: str = "rag_dataset.json"):
        logger.info(f"Starting pipeline for query: '{query}'")
        
        # 1. Search
        all_urls = self.searcher.search(query, num_results=num_urls)
        if not all_urls:
            logger.error("No URLs found. Aborting.")
            return
            
        # Filter duplicates
        urls = [url for url in all_urls if url not in self.seen_urls]
        if not urls:
            logger.info("All found URLs have already been processed.")
            return

        logger.info(f"Found {len(all_urls)} URLs. Processing {len(urls)} new URLs...")
        
        # 2. Scrape (Concurrent with Depth)
        DEPTH = 2
        tasks = [self.scraper.scrape(url, depth=DEPTH) for url in urls]
        root_nodes = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 3. AI Normalization (Recursive)
        results = []
        logger.info("Scraping finished. Starting AI Normalization on Content Tree...")
        
        for node in root_nodes:
            if isinstance(node, Exception):
                logger.error(f"Scrape failed: {node}")
                continue
            
            if not node:
                continue

            # Process Tree recursively
            processed_data = self.process_node_tree(node)
            results.append(processed_data)
            self.seen_urls.add(processed_data.get('url'))

        # 4. Save
        self.save_results(results, output_file)
        logger.success(f"Pipeline finished. Saved {len(results)} records to {output_file}")

    def process_node_tree(self, node) -> Dict:
        """
        Recursively normalize content of the node and its children.
        """
        # Normalize current node
        if node.content and len(node.content) > 50:
             # Normalize content
             normalized = self.normalizer.normalize(node.content, node.url)
             node_data = node.model_dump()
             node_data['ai_knowledge'] = normalized
        else:
             node_data = node.model_dump()
             node_data['ai_knowledge'] = None
             
        # Process children
        new_children = []
        for child in node.children:
            new_children.append(self.process_node_tree(child))
            
        node_data['children'] = new_children
        return node_data

    def save_results(self, data: List[Dict], filename: str):
        try:
            existing_data = []
            if os.path.exists(filename):
                try:
                    with open(filename, "r", encoding="utf-8") as f:
                        existing_data = json.load(f)
                except json.JSONDecodeError:
                    pass # Start fresh if corrupt
            
            existing_data.extend(data)
            
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save results: {e}")

async def main():
    load_dotenv()
    
    # Check keys
    if not os.getenv("SERPAPI_KEY"):
        logger.warning("SERPAPI_KEY is missing. Search might be limited or fail if using SerpAPI.")
    if not os.getenv("OPENAI_API_KEY"):
        logger.warning("OPENAI_API_KEY is missing. AI normalization will fail.")

    # Get user input
    print("Welcome to Autonomous Data Pipeline.")
    keyword = input("Enter keyword OR path to .txt file (e.g. search_queries.txt): ")
    if not keyword:
        print("No input provided. Exiting.")
        return

    pipeline = AutonomousPipeline()

    if keyword.endswith(".txt") and os.path.exists(keyword):
        print(f"Detected batch mode from {keyword}")
        with open(keyword, "r", encoding="utf-8") as f:
            queries = [line.strip() for line in f if line.strip()]
        
        print(f"Found {len(queries)} queries. Starting batch process...")
        
        for i, q in enumerate(queries):
            logger.info(f"Batch processing {i+1}/{len(queries)}: {q}")
            await pipeline.run(q, num_urls=5)
            await asyncio.sleep(2) # rate limit politeness
            
    else:
        await pipeline.run(keyword, num_urls=5)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nPipeline stopped by user.")
