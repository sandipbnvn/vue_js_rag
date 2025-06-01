from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import os
from datetime import datetime
import uuid
import logging

from .models.models import (
    ChatQuery, ChatResponse, WebSearchPermissionRequest, WebSearchPermission,
    UploadResponse, Source, ConversationHistory
)
from .services.pdf_processor import PDFProcessor
from .services.vector_store import VectorStore
from .services.llm_service import LLMService
from .services.database import DatabaseService
from .services.web_search import WebSearchService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="RAG Chatbot API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
pdf_processor = PDFProcessor()
vector_store = VectorStore()
llm_service = LLMService()
database_service = DatabaseService()
web_search_service = WebSearchService()

@app.post("/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """Upload and process a PDF file"""
    try:
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Read file content
        content = await file.read()
        
        # Process PDF
        document_id = str(uuid.uuid4())
        chunks = pdf_processor.process_pdf_content(content, document_id, file.filename)
        
        if not chunks:
            raise HTTPException(status_code=400, detail="Could not extract text from PDF")
        
        # Store in vector database
        vector_store.add_documents(chunks, document_id, file.filename)
        
        # Store in database
        await database_service.store_document(document_id, file.filename, len(chunks))
        
        logger.info(f"Successfully processed PDF: {file.filename} with {len(chunks)} chunks")
        
        return UploadResponse(
            message=f"Successfully processed {file.filename}",
            document_id=document_id,
            chunks_count=len(chunks)
        )
        
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query", response_model=ChatResponse)
async def query_documents(request: ChatQuery):
    """Query documents and get AI response"""
    try:
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        # Check if LLM service is available
        if not llm_service.is_available():
            return ChatResponse(
                response="❌ LLM service is not available. Please configure OPENAI_API_KEY environment variable.",
                sources=[],
                conversation_id=conversation_id,
                needs_web_search=False
            )
        
        # Get conversation history
        conversation_history = await database_service.get_conversation_history(conversation_id)
        
        # Search relevant documents
        context = ""
        sources = []
        
        if vector_store.index is not None:
            search_results = vector_store.search(request.query, top_k=request.top_k)
            
            if search_results:
                context_parts = []
                for result in search_results:
                    context_parts.append(result['text'])
                    sources.append(Source(
                        text=result['text'],
                        source=result['source'],
                        page=result.get('page'),
                        score=result['score']
                    ))
                context = "\n\n".join(context_parts)
        
        # Get LLM response
        response, needs_web_search, search_query = await llm_service.generate_response(
            request.query, 
            context, 
            conversation_history
        )
        
        # Store the conversation
        await database_service.store_conversation(
            conversation_id, request.query, response, sources
        )
        
        return ChatResponse(
            response=response,
            sources=sources,
            conversation_id=conversation_id,
            needs_web_search=needs_web_search,
            search_query=search_query
        )
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/web-search", response_model=ChatResponse)
async def perform_web_search(request: WebSearchPermission):
    """Perform web search after user permission"""
    try:
        if not request.approved:
            return ChatResponse(
                response="Web search was not approved. I can only answer based on your uploaded documents.",
                sources=[],
                conversation_id=request.conversation_id
            )
        
        # Check if services are available
        if not llm_service.is_available():
            return ChatResponse(
                response="❌ LLM service is not available. Please configure OPENAI_API_KEY environment variable.",
                sources=[],
                conversation_id=request.conversation_id
            )
        
        if not web_search_service.is_available():
            return ChatResponse(
                response="❌ Web search is not available. Please configure TAVILY_API_KEY environment variable.",
                sources=[],
                conversation_id=request.conversation_id
            )
        
        # Get the latest conversation to find the search query
        conversation_history = await database_service.get_conversation_history(request.conversation_id)
        if not conversation_history:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Get the last message to find the search query
        last_message = conversation_history[-1]
        original_query = last_message['query']
        
        # Extract search query from the last response
        last_response = last_message['response']
        search_query = None
        if "WEB_SEARCH_NEEDED:" in last_response:
            search_query = last_response.split("WEB_SEARCH_NEEDED:")[1].strip().strip("[]\"'")
        
        if not search_query:
            search_query = original_query  # Fallback to original query
        
        # Perform web search
        web_results = await web_search_service.search(search_query, max_results=5)
        
        # Get document context again
        context = ""
        doc_sources = []
        
        if vector_store.index is not None:
            search_results = vector_store.search(original_query, top_k=5)
            
            if search_results:
                context_parts = []
                for result in search_results:
                    context_parts.append(result['text'])
                    doc_sources.append(Source(
                        text=result['text'],
                        source=result['source'],
                        page=result.get('page'),
                        score=result['score']
                    ))
                context = "\n\n".join(context_parts)
        
        # Generate response with web search results
        response = await llm_service.generate_response_with_web_search(
            original_query, 
            context, 
            web_results,
            conversation_history
        )
        
        # Combine sources
        all_sources = doc_sources.copy()
        for web_result in web_results:
            all_sources.append(Source(
                text=web_result['content'][:500] + "..." if len(web_result['content']) > 500 else web_result['content'],
                source=web_result['url'],
                score=web_result['score']
            ))
        
        # Update the last conversation entry with the new response
        await database_service.update_conversation_response(
            request.conversation_id, response, all_sources
        )
        
        return ChatResponse(
            response=response,
            sources=all_sources,
            conversation_id=request.conversation_id,
            web_search_results=web_results
        )
        
    except Exception as e:
        logger.error(f"Error performing web search: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/conversations/{conversation_id}", response_model=ConversationHistory)
async def get_conversation(conversation_id: str):
    """Get conversation history"""
    try:
        messages = await database_service.get_conversation_messages(conversation_id)
        if not messages:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return ConversationHistory(
            conversation_id=conversation_id,
            messages=messages,
            created_at=messages[0].timestamp,
            updated_at=messages[-1].timestamp
        )
    except Exception as e:
        logger.error(f"Error getting conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/conversations")
async def list_conversations():
    """List all conversations"""
    try:
        conversations = await database_service.list_conversations()
        return {"conversations": conversations}
    except Exception as e:
        logger.error(f"Error listing conversations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "vector_store_ready": vector_store.index is not None,
        "web_search_available": web_search_service.is_available(),
        "llm_service_available": llm_service.is_available(),
        "openai_api_configured": llm_service.is_available(),
        "tavily_api_configured": web_search_service.is_available(),
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 