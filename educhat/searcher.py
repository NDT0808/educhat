import os
import time
from typing import List, Optional
from loguru import logger
try:
    from serpapi import GoogleSearch
except ImportError:
    GoogleSearch = None
    
try:
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None

class SearchManager:
    """
    Manages search operations with fallback logic.
    Primary: SerpAPI (Google)
    Fallback: DuckDuckGo
    """

    def __init__(self, serpapi_key: Optional[str] = None):
        self.serpapi_key = serpapi_key or os.getenv("SERPAPI_KEY")
        self.ddgs = DDGS() if DDGS else None

    def search(self, query: str, num_results: int = 5) -> List[str]:
        """
        Executes a search query and returns a list of URLs.
        
        Args:
            query (str): The search keyword.
            num_results (int): Number of results to return.
            
        Returns:
            List[str]: A list of URLs found.
        """
        urls = []
        
        # Try SerpAPI first
        if self.serpapi_key and GoogleSearch:
            try:
                logger.info(f"Searching with SerpAPI for: '{query}'")
                params = {
                    "q": query,
                    "api_key": self.serpapi_key,
                    "num": num_results,
                    "engine": "google"
                }
                search = GoogleSearch(params)
                results = search.get_dict()
                
                if "organic_results" in results:
                    for result in results["organic_results"]:
                        link = result.get("link")
                        if link:
                            urls.append(link)
                    logger.success(f"SerpAPI returned {len(urls)} results.")
                    return urls[:num_results]
                else:
                    logger.warning("SerpAPI returned no organic results.")
            except Exception as e:
                logger.error(f"SerpAPI failed: {e}. Switching to fallback...")
        else:
            if not self.serpapi_key:
                logger.warning("SERPAPI_KEY not found.")
            if not GoogleSearch:
                logger.warning("google-search-results library not installed.")

        # Fallback to DuckDuckGo
        if self.ddgs:
            try:
                logger.info(f"Fallback: Searching with DuckDuckGo for: '{query}'")
                results = self.ddgs.text(query, max_results=num_results)
                if results:
                    for res in results:
                        link = res.get("href")
                        if link:
                            urls.append(link)
                    logger.success(f"DuckDuckGo returned {len(urls)} results.")
                    return urls[:num_results]
                else:
                    logger.warning("DuckDuckGo returned no results.")
            except Exception as e:
                logger.error(f"DuckDuckGo search failed: {e}")
        else:
            logger.error("duckduckgo-search library not installed or failed to initialize.")

        return urls

if __name__ == "__main__":
    # Simple test
    from dotenv import load_dotenv
    load_dotenv()
    
    manager = SearchManager()
    links = manager.search("artificial intelligence trends 2024", num_results=3)
    print("Found links:")
    for l in links:
        print(f"- {l}")
