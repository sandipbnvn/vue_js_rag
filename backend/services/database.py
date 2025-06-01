from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from typing import List, Dict, Any, Optional
import json
import sqlite3
import logging

Base = declarative_base()

logger = logging.getLogger(__name__)

class ConversationHistoryDB(Base):
    __tablename__ = "conversation_history"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String, index=True)
    query = Column(Text)
    response = Column(Text)
    sources = Column(Text)  # JSON string of sources
    timestamp = Column(DateTime, default=datetime.utcnow)

class DatabaseService:
    def __init__(self, db_path: str = "ragbot.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Documents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                chunks_count INTEGER NOT NULL,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Conversations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                query TEXT NOT NULL,
                response TEXT NOT NULL,
                sources TEXT,  -- JSON string of sources
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_conversation_id 
            ON conversations(conversation_id)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON conversations(timestamp)
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    
    async def store_document(self, document_id: str, filename: str, chunks_count: int):
        """Store document metadata"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO documents (id, filename, chunks_count)
                VALUES (?, ?, ?)
            ''', (document_id, filename, chunks_count))
            
            conn.commit()
            logger.info(f"Document stored: {filename} ({chunks_count} chunks)")
            
        except sqlite3.Error as e:
            logger.error(f"Error storing document: {e}")
            raise
        finally:
            conn.close()
    
    async def store_conversation(
        self, 
        conversation_id: str, 
        query: str, 
        response: str, 
        sources: List[Any]
    ):
        """Store a conversation message"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Convert sources to JSON string
            sources_json = json.dumps([
                {
                    'text': source.text,
                    'source': source.source,
                    'page': source.page,
                    'score': source.score
                }
                for source in sources
            ])
            
            cursor.execute('''
                INSERT INTO conversations (conversation_id, query, response, sources)
                VALUES (?, ?, ?, ?)
            ''', (conversation_id, query, response, sources_json))
            
            conn.commit()
            logger.info(f"Conversation stored for ID: {conversation_id}")
            
        except sqlite3.Error as e:
            logger.error(f"Error storing conversation: {e}")
            raise
        finally:
            conn.close()
    
    async def update_conversation_response(
        self, 
        conversation_id: str, 
        new_response: str, 
        new_sources: List[Any]
    ):
        """Update the latest conversation response (for web search results)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Convert sources to JSON string
            sources_json = json.dumps([
                {
                    'text': source.text,
                    'source': source.source,
                    'page': getattr(source, 'page', None),
                    'score': source.score
                }
                for source in new_sources
            ])
            
            # Update the most recent conversation entry
            cursor.execute('''
                UPDATE conversations 
                SET response = ?, sources = ?
                WHERE conversation_id = ? 
                AND id = (
                    SELECT id FROM conversations 
                    WHERE conversation_id = ? 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                )
            ''', (new_response, sources_json, conversation_id, conversation_id))
            
            conn.commit()
            logger.info(f"Conversation response updated for ID: {conversation_id}")
            
        except sqlite3.Error as e:
            logger.error(f"Error updating conversation response: {e}")
            raise
        finally:
            conn.close()
    
    async def get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for a specific conversation"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT query, response, sources, timestamp
                FROM conversations
                WHERE conversation_id = ?
                ORDER BY timestamp ASC
            ''', (conversation_id,))
            
            results = cursor.fetchall()
            
            history = []
            for row in results:
                query, response, sources_json, timestamp = row
                sources = json.loads(sources_json) if sources_json else []
                
                history.append({
                    'query': query,
                    'response': response,
                    'sources': sources,
                    'timestamp': timestamp
                })
            
            return history
            
        except sqlite3.Error as e:
            logger.error(f"Error getting conversation history: {e}")
            raise
        finally:
            conn.close()
    
    async def get_conversation_messages(self, conversation_id: str) -> List[Any]:
        """Get conversation messages in the format expected by the API"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT id, query, response, sources, timestamp
                FROM conversations
                WHERE conversation_id = ?
                ORDER BY timestamp ASC
            ''', (conversation_id,))
            
            results = cursor.fetchall()
            
            from models.models import ConversationMessage, Source
            
            messages = []
            for row in results:
                msg_id, query, response, sources_json, timestamp = row
                sources = []
                
                if sources_json:
                    sources_data = json.loads(sources_json)
                    sources = [
                        Source(
                            text=s['text'],
                            source=s['source'],
                            page=s.get('page'),
                            score=s['score']
                        )
                        for s in sources_data
                    ]
                
                messages.append(ConversationMessage(
                    id=msg_id,
                    conversation_id=conversation_id,
                    query=query,
                    response=response,
                    sources=sources,
                    timestamp=datetime.fromisoformat(timestamp)
                ))
            
            return messages
            
        except sqlite3.Error as e:
            logger.error(f"Error getting conversation messages: {e}")
            raise
        finally:
            conn.close()
    
    async def list_conversations(self) -> List[Dict[str, Any]]:
        """List all unique conversations with metadata"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT 
                    conversation_id,
                    COUNT(*) as message_count,
                    MIN(timestamp) as created_at,
                    MAX(timestamp) as updated_at,
                    MIN(query) as first_query
                FROM conversations
                GROUP BY conversation_id
                ORDER BY MAX(timestamp) DESC
            ''')
            
            results = cursor.fetchall()
            
            conversations = []
            for row in results:
                conv_id, msg_count, created_at, updated_at, first_query = row
                conversations.append({
                    'conversation_id': conv_id,
                    'message_count': msg_count,
                    'created_at': created_at,
                    'updated_at': updated_at,
                    'first_query': first_query[:100] + "..." if len(first_query) > 100 else first_query
                })
            
            return conversations
            
        except sqlite3.Error as e:
            logger.error(f"Error listing conversations: {e}")
            raise
        finally:
            conn.close()
    
    async def delete_conversation(self, conversation_id: str):
        """Delete a conversation"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                DELETE FROM conversations WHERE conversation_id = ?
            ''', (conversation_id,))
            
            conn.commit()
            logger.info(f"Conversation deleted: {conversation_id}")
            
        except sqlite3.Error as e:
            logger.error(f"Error deleting conversation: {e}")
            raise
        finally:
            conn.close()

# Global instance
database_service = DatabaseService()

def get_db():
    """Dependency to get database service"""
    return database_service 