import os
import time
from typing import Dict, Optional
from loguru import logger
from openai import OpenAI
from pydantic import BaseModel, Field

class CleanedData(BaseModel):
    title: str = Field(..., description="The title of the content")
    summary: str = Field(..., description="A 2-sentence summary of the content")
    content: str = Field(..., description="The cleaned and structured markdown content")
    published_date: Optional[str] = Field(None, description="Published date if available")

class DataNormalizer:
    """
    Uses OpenAI to clean and restructure raw text into knowledge.
    """

    def __init__(self, api_key: str = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not found. AI processing will fail.")
            self.client = None
        else:
            try:
                self.client = OpenAI(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                self.client = None

        self.model = model or os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")

    def normalize(self, raw_text: str, source_url: str) -> Dict:
        """
        Sends raw text to LLM for cleaning and formatting.
        """
        if not self.api_key or not self.client:
            return {"error": "Missing API Key or Client", "raw_content": raw_text[:500]}

        logger.info(f"Normalizing content from {source_url} (size: {len(raw_text)} chars)...")
        
        # Truncate if too long to save tokens/money (heuristic)
        # GPT-4o-mini has huge context, but let's be safe + efficient.
        max_chars = 100000 
        if len(raw_text) > max_chars:
            logger.warning(f"Text too long ({len(raw_text)}). Truncating to {max_chars}.")
            raw_text = raw_text[:max_chars]

        system_prompt = (
            "You are an expert Data Engineer and Editor. Your task is to process raw Markdown text scraped from the web "
            "and convert it into a clean, structured 'Knowledge' format suitable for RAG systems.\n"
            "Rules:\n"
            "1. Remove implementation details like navbars, footers, ads, cookie warnings, code boilerplates.\n"
            "2. Keep core information, definitions, statistics, and logic.\n"
            "3. **CRITICAL**: Preserve all TABLES, IMAGES, and LINKS to files (PDF/DOCX) or relevant sources.\n"
            "4. Format the output in standard Markdown (Use # for title, ## for sections).\n"
            "5. Extract a Title, a 2-sentence Summary, and a Published Date (if found).\n"
            "6. Return the result strictly as a valid JSON object matching the schema: "
            "{'title': str, 'summary': str, 'content': str, 'published_date': str|null}."
        )

        user_prompt = f"Source URL: {source_url}\n\nRaw Text:\n{raw_text}"

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            content = response.choices[0].message.content
            
            # Simple validation/parsing since we requested JSON mode
            import json
            data = json.loads(content)
            
            # Fallback validation with Pydantic
            validated = CleanedData(**data)
            
            return validated.model_dump()

        except Exception as e:
            logger.error(f"AI Normalization failed: {e}")
            return {
                "url": source_url,
                "error": str(e),
                "raw_preview": raw_text[:200]
            }

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    normalizer = DataNormalizer()
    sample_text = "Home | About Us | ... \n Artificial Intelligence is a field of CS. ... \n Copyright 2024"
    result = normalizer.normalize(sample_text, "http://test.com")
    print(result)
