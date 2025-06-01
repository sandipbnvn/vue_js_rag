import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Tuple
import pickle
import os

class VectorStore:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        self.index = faiss.IndexFlatIP(self.dimension)  # Inner Product for cosine similarity
        self.documents = []  # Store document metadata
        self.index_file = "vector_index.faiss"
        self.docs_file = "documents.pkl"
        
        # Load existing index if available
        self._load_index()
    
    def add_documents(self, chunks: List[Dict], document_id: str, filename: str):
        """Add documents to the vector store"""
        try:
            texts = [chunk["text"] for chunk in chunks]
            embeddings = self.model.encode(texts, convert_to_tensor=False)
            
            # Normalize embeddings for cosine similarity
            embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
            
            # Add to FAISS index
            self.index.add(embeddings.astype('float32'))
            
            # Store document metadata
            for i, chunk in enumerate(chunks):
                self.documents.append({
                    "text": chunk["text"],
                    "source": filename,
                    "document_id": document_id,
                    "chunk_id": chunk.get("chunk_id", i),
                    "page": chunk.get("page"),
                    "index_id": len(self.documents)
                })
            
            # Save index and metadata
            self._save_index()
            
        except Exception as e:
            raise Exception(f"Error adding documents to vector store: {str(e)}")
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search for similar documents"""
        try:
            if self.index.ntotal == 0:
                return []
            
            # Create query embedding
            query_embedding = self.model.encode([query], convert_to_tensor=False)
            query_embedding = query_embedding / np.linalg.norm(query_embedding, axis=1, keepdims=True)
            
            # Search in FAISS index
            scores, indices = self.index.search(query_embedding.astype('float32'), top_k)
            
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < len(self.documents):
                    doc = self.documents[idx].copy()
                    doc["score"] = float(score)
                    results.append(doc)
            
            return results
            
        except Exception as e:
            raise Exception(f"Error searching vector store: {str(e)}")
    
    def _save_index(self):
        """Save FAISS index and document metadata to disk"""
        try:
            faiss.write_index(self.index, self.index_file)
            with open(self.docs_file, 'wb') as f:
                pickle.dump(self.documents, f)
        except Exception as e:
            print(f"Warning: Could not save index: {str(e)}")
    
    def _load_index(self):
        """Load FAISS index and document metadata from disk"""
        try:
            if os.path.exists(self.index_file) and os.path.exists(self.docs_file):
                self.index = faiss.read_index(self.index_file)
                with open(self.docs_file, 'rb') as f:
                    self.documents = pickle.load(f)
                print(f"Loaded existing index with {len(self.documents)} documents")
        except Exception as e:
            print(f"Could not load existing index: {str(e)}")
            # Initialize empty index if loading fails
            self.index = faiss.IndexFlatIP(self.dimension)
            self.documents = []
    
    def get_stats(self) -> Dict:
        """Get vector store statistics"""
        return {
            "total_documents": len(self.documents),
            "index_size": self.index.ntotal,
            "dimension": self.dimension
        }
    
    def clear_index(self):
        """Clear all documents from the index"""
        self.index = faiss.IndexFlatIP(self.dimension)
        self.documents = []
        # Remove saved files
        for file in [self.index_file, self.docs_file]:
            if os.path.exists(file):
                os.remove(file) 