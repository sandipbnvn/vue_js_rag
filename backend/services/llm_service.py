import os
from typing import List, Dict, Any, Optional, Tuple
from openai import AsyncOpenAI
from .web_search import web_search_service
import logging

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not found. LLM functionality will be disabled.")
            self.client = None
            self.model = None
        else:
            self.client = AsyncOpenAI(api_key=self.api_key)
            self.model = "gpt-3.5-turbo"
    
    def is_available(self) -> bool:
        """Check if LLM service is available"""
        return self.client is not None
    
    async def generate_response(
        self, 
        query: str, 
        context: str = "", 
        conversation_history: List[Dict[str, str]] = None
    ) -> Tuple[str, bool, Optional[str]]:
        """
        Generate response from LLM
        
        Args:
            query: User's question
            context: Document context from vector search
            conversation_history: Previous conversation messages
        
        Returns:
            Tuple of (response, needs_web_search, search_query)
        """
        if not self.is_available():
            return "LLM service is not available. Please configure OPENAI_API_KEY.", False, None
        
        if conversation_history is None:
            conversation_history = []
        
        # Create messages for the conversation
        messages = [
            {
                "role": "system",
                "content": self._get_system_prompt()
            }
        ]
        
        # Add conversation history
        for msg in conversation_history[-10:]:  # Keep last 10 messages
            messages.append({"role": "user", "content": msg["query"]})
            messages.append({"role": "assistant", "content": msg["response"]})
        
        # Create the current query with context
        user_message = self._format_user_message(query, context)
        messages.append({"role": "user", "content": user_message})
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            answer = response.choices[0].message.content.strip()
            
            # Check if the LLM indicates it needs web search
            needs_web_search, search_query = self._parse_web_search_request(answer)
            
            return answer, needs_web_search, search_query
            
        except Exception as e:
            logger.error(f"Error generating LLM response: {str(e)}")
            raise Exception(f"Failed to generate response: {str(e)}")
    
    async def generate_response_with_web_search(
        self, 
        query: str, 
        context: str = "", 
        web_search_results: List[Dict[str, Any]] = None,
        conversation_history: List[Dict[str, str]] = None
    ) -> str:
        """
        Generate response using both document context and web search results
        
        Args:
            query: User's question
            context: Document context from vector search
            web_search_results: Results from web search
            conversation_history: Previous conversation messages
        
        Returns:
            LLM response
        """
        if not self.is_available():
            return "LLM service is not available. Please configure OPENAI_API_KEY."
        
        if conversation_history is None:
            conversation_history = []
        
        # Create messages for the conversation
        messages = [
            {
                "role": "system",
                "content": self._get_web_search_system_prompt()
            }
        ]
        
        # Add conversation history
        for msg in conversation_history[-10:]:  # Keep last 10 messages
            messages.append({"role": "user", "content": msg["query"]})
            messages.append({"role": "assistant", "content": msg["response"]})
        
        # Format context with both document and web search results
        combined_context = self._combine_contexts(context, web_search_results)
        user_message = self._format_user_message(query, combined_context)
        messages.append({"role": "user", "content": user_message})
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1500
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating LLM response with web search: {str(e)}")
            raise Exception(f"Failed to generate response: {str(e)}")
    
    def _get_system_prompt(self) -> str:
        return """You are a helpful AI assistant that answers questions based on provided document context. 

Instructions:
1. Answer questions using the provided document context when possible
2. If the document context doesn't contain enough information to answer the question, respond with: "WEB_SEARCH_NEEDED: [specific search query]"
3. Be accurate and cite your sources when using document information
4. If you can partially answer from documents but need additional information, still request web search
5. Keep your responses clear and concise
6. Always be honest about the limitations of the provided context

Remember: Only use WEB_SEARCH_NEEDED when the documents truly don't contain sufficient information."""
    
    def _get_web_search_system_prompt(self) -> str:
        return """You are a helpful AI assistant that answers questions using both document context and web search results.

Instructions:
1. Use both document context and web search results to provide comprehensive answers
2. Clearly distinguish between information from documents vs web sources
3. Cite your sources appropriately
4. If document and web information conflict, acknowledge both perspectives
5. Synthesize information from multiple sources when relevant
6. Be accurate and provide helpful, well-structured responses

Format your response to clearly indicate which information comes from which source type."""
    
    def _format_user_message(self, query: str, context: str) -> str:
        if context:
            return f"""Context information:
{context}

Question: {query}

Please answer the question based on the provided context. If the context doesn't contain sufficient information, indicate that web search is needed."""
        else:
            return f"""Question: {query}

No document context is available. Please indicate if web search is needed to answer this question."""
    
    def _parse_web_search_request(self, response: str) -> Tuple[bool, Optional[str]]:
        """
        Parse LLM response to check if web search is needed
        
        Returns:
            Tuple of (needs_search, search_query)
        """
        if "WEB_SEARCH_NEEDED:" in response:
            try:
                search_query = response.split("WEB_SEARCH_NEEDED:")[1].strip()
                # Remove any surrounding brackets or quotes
                search_query = search_query.strip("[]\"'")
                return True, search_query
            except:
                return True, None
        
        return False, None
    
    def _combine_contexts(self, doc_context: str, web_results: List[Dict[str, Any]]) -> str:
        """
        Combine document context and web search results
        """
        contexts = []
        
        if doc_context:
            contexts.append(f"=== DOCUMENT CONTEXT ===\n{doc_context}")
        
        if web_results:
            web_context = web_search_service.format_search_context(web_results)
            contexts.append(f"=== WEB SEARCH RESULTS ===\n{web_context}")
        
        return "\n\n".join(contexts)

# Global instance
llm_service = LLMService() 