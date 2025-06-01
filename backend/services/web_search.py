import os
from typing import List, Dict, Any, Optional
from tavily import TavilyClient
import logging

logger = logging.getLogger(__name__)

class WebSearchService:
    def __init__(self):
        self.api_key = os.getenv("TAVILY_API_KEY")
        if not self.api_key:
            logger.warning("TAVILY_API_KEY not found. Web search will be disabled.")
            self.client = None
        else:
            self.client = TavilyClient(api_key=self.api_key)
    
    def is_available(self) -> bool:
        """Check if web search is available"""
        return self.client is not None
    
    async def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search the web for information related to the query
        
        Args:
            query: The search query
            max_results: Maximum number of results to return
            
        Returns:
            List of search results with title, content, and URL
        """
        if not self.client:
            raise Exception("Web search is not available. Please set TAVILY_API_KEY.")
        
        try:
            # Perform the search
            response = self.client.search(
                query=query,
                search_depth="basic",
                max_results=max_results,
                include_answer=False,
                include_raw_content=False
            )
            
            # Format the results
            formatted_results = []
            for result in response.get('results', []):
                formatted_results.append({
                    'title': result.get('title', ''),
                    'content': result.get('content', ''),
                    'url': result.get('url', ''),
                    'score': result.get('score', 0.0),
                    'source': 'web_search'
                })
            
            logger.info(f"Web search for '{query}' returned {len(formatted_results)} results")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error during web search: {str(e)}")
            raise Exception(f"Web search failed: {str(e)}")
    
    def format_search_context(self, results: List[Dict[str, Any]]) -> str:
        """
        Format search results into a context string for the LLM
        
        Args:
            results: List of search results
            
        Returns:
            Formatted context string
        """
        if not results:
            return ""
        
        context_parts = ["Based on web search results:\n"]
        
        for i, result in enumerate(results, 1):
            title = result.get('title', 'Untitled')
            content = result.get('content', '')
            url = result.get('url', '')
            
            context_parts.append(f"{i}. {title}")
            if content:
                # Limit content length
                content = content[:500] + "..." if len(content) > 500 else content
                context_parts.append(f"   Content: {content}")
            if url:
                context_parts.append(f"   Source: {url}")
            context_parts.append("")  # Empty line for separation
        
        return "\n".join(context_parts)

# Global instance
web_search_service = WebSearchService() 