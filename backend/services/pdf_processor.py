import PyPDF2
from typing import List, Dict
import re
import io

class PDFProcessor:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def process_pdf(self, file_path: str) -> List[Dict[str, any]]:
        """Extract text from PDF and split into chunks"""
        try:
            text = self._extract_text_from_pdf(file_path)
            chunks = self._split_text_into_chunks(text, file_path)
            return chunks
        except Exception as e:
            raise Exception(f"Error processing PDF: {str(e)}")

    def process_pdf_content(self, file_content: bytes, document_id: str, filename: str) -> List[Dict[str, any]]:
        """Extract text from PDF content (bytes) and split into chunks"""
        try:
            text = self._extract_text_from_pdf_content(file_content)
            chunks = self._split_text_into_chunks(text, filename)
            # Add document_id to chunks
            for chunk in chunks:
                chunk['document_id'] = document_id
            return chunks
        except Exception as e:
            raise Exception(f"Error processing PDF content: {str(e)}")
    
    def _extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        # Add page marker
                        text += f"\n[Page {page_num + 1}]\n{page_text}"
            return text
        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {str(e)}")

    def _extract_text_from_pdf_content(self, file_content: bytes) -> str:
        """Extract text from PDF content (bytes)"""
        text = ""
        try:
            # Create a file-like object from bytes
            pdf_file = io.BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                if page_text:
                    # Add page marker
                    text += f"\n[Page {page_num + 1}]\n{page_text}"
            return text
        except Exception as e:
            raise Exception(f"Error extracting text from PDF content: {str(e)}")
    
    def _split_text_into_chunks(self, text: str, source_file: str) -> List[Dict[str, any]]:
        """Split text into overlapping chunks"""
        # Clean the text
        text = self._clean_text(text)
        
        chunks = []
        start = 0
        chunk_id = 0
        
        while start < len(text):
            # Calculate end position
            end = start + self.chunk_size
            
            # If this is not the last chunk, try to end at a sentence boundary
            if end < len(text):
                # Look for sentence endings near the end position
                sentence_end = self._find_sentence_boundary(text, end)
                if sentence_end > start:
                    end = sentence_end
            
            chunk_text = text[start:end].strip()
            
            if chunk_text:
                # Extract page number from chunk
                page_match = re.search(r'\[Page (\d+)\]', chunk_text)
                page_num = int(page_match.group(1)) if page_match else None
                
                # Remove page markers from chunk text
                clean_chunk = re.sub(r'\[Page \d+\]\s*', '', chunk_text)
                
                chunks.append({
                    "text": clean_chunk,
                    "source": source_file,
                    "chunk_id": chunk_id,
                    "page": page_num
                })
                chunk_id += 1
            
            # Move start position with overlap
            start = end - self.chunk_overlap if end < len(text) else len(text)
        
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters that might interfere with processing
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)\[\]]', ' ', text)
        return text.strip()
    
    def _find_sentence_boundary(self, text: str, position: int) -> int:
        """Find the nearest sentence boundary near the given position"""
        # Look for sentence endings within a reasonable range
        search_range = min(100, len(text) - position)
        
        for i in range(search_range):
            if position + i < len(text) and text[position + i] in '.!?':
                # Make sure it's not an abbreviation
                if position + i + 1 < len(text) and text[position + i + 1].isspace():
                    return position + i + 1
        
        # If no sentence boundary found, return original position
        return position 