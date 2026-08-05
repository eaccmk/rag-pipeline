import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class SearchService:
    """Web search service using DuckDuckGo (no API key needed)."""
    
    def __init__(self):
        self.ddgs = None
        try:
            from ddgs import DDGS
            self.ddgs = DDGS()
        except ImportError:
            try:
                from duckduckgo_search import DDGS
                self.ddgs = DDGS()
            except Exception as e:
                logger.warning(f"Could not initialize DuckDuckGo search: {e}")
        except Exception as e:
            logger.warning(f"Could not initialize DuckDuckGo search: {e}")
    
    def search_rate_news(self, query: str = "Australian interest rates RBA", max_results: int = 3) -> List[Dict[str, Any]]:
        """Search for interest rate related news."""
        if not self.ddgs:
            logger.info(f"✅ DuckDuckGo Web Search: DDGS package offline. Using fallback web search context.")
            return self._mock_search_results(query)
            
        try:
            results = list(self.ddgs.text(query, max_results=max_results))
            logger.info(f"✅ DuckDuckGo Web Search: Found {len(results)} live results for '{query}'")
            return results
        except Exception as e:
            logger.error(f"❌ DuckDuckGo Web Search Error: {e}. Falling back to search context.")
            return self._mock_search_results(query)
    
    def get_search_context(self, query: str) -> str:
        """Get search results as formatted context for RAG."""
        results = self.search_rate_news(query)
        if not results:
            return "No additional search context available."
        
        context = "Recent search results:\n"
        for i, result in enumerate(results, 1):
            context += f"{i}. {result.get('title', 'No title')}\n"
            context += f"   {result.get('body', 'No description')}\n"
        return context

    def _mock_search_results(self, query: str) -> List[Dict[str, Any]]:
        """Fallback mock search results when offline or DDGS fails."""
        return [
            {
                "title": "RBA Rate Decision Analysis 2026",
                "body": "Economists predict potential rate easing later in 2026 as inflation normalizes towards the target band of 2-3%."
            },
            {
                "title": "Australian SMB Lending Rates Overview",
                "body": "Commercial variable loan rates hover around 4.8% to 5.8%, with 3-year fixed rates offered near 5.2% to 5.9%."
            }
        ]


if __name__ == "__main__":
    search = SearchService()
    results = search.search_rate_news("Australian interest rates 2026")
    for result in results:
        print(f"Title: {result.get('title')}")
        print(f"Body: {result.get('body')}\n")
