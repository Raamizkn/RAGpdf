import os
import fitz  # PyMuPDF
import pdfplumber
from typing import List, Dict, Tuple, Optional
import hashlib
from langchain.text_splitter import RecursiveCharacterTextSplitter
from tqdm import tqdm
import config

class PDFProcessor:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def extract_text_pymupdf(self, pdf_path: str) -> Tuple[str, Dict]:
        """Extract text from PDF using PyMuPDF (faster but less accurate with complex layouts)"""
        doc = fitz.open(pdf_path)
        metadata = {
            "title": doc.metadata.get("title", ""),
            "author": doc.metadata.get("author", ""),
            "subject": doc.metadata.get("subject", ""),
            "creator": doc.metadata.get("creator", ""),
            "producer": doc.metadata.get("producer", ""),
            "pages": len(doc),
            "filename": os.path.basename(pdf_path)
        }
        
        full_text = ""
        for page_num, page in enumerate(doc):
            text = page.get_text()
            if text.strip():  # Only add non-empty pages
                full_text += f"\n\n--- Page {page_num + 1} ---\n\n{text}"
        
        doc.close()
        return full_text, metadata
    
    def extract_text_pdfplumber(self, pdf_path: str) -> Tuple[str, Dict]:
        """Extract text from PDF using pdfplumber (better for complex layouts)"""
        with pdfplumber.open(pdf_path) as pdf:
            metadata = {
                "pages": len(pdf.pages),
                "filename": os.path.basename(pdf_path)
            }
            
            full_text = ""
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                if text.strip():  # Only add non-empty pages
                    full_text += f"\n\n--- Page {page_num + 1} ---\n\n{text}"
        
        return full_text, metadata
    
    def extract_text(self, pdf_path: str, use_pdfplumber: bool = False) -> Tuple[str, Dict]:
        """Extract text from PDF using the specified method"""
        if use_pdfplumber:
            return self.extract_text_pdfplumber(pdf_path)
        else:
            return self.extract_text_pymupdf(pdf_path)
    
    def chunk_text(self, text: str, metadata: Dict) -> List[Dict]:
        """Split text into chunks using LangChain's RecursiveCharacterTextSplitter"""
        chunks = self.text_splitter.split_text(text)
        
        # Create document chunks with metadata and page info
        doc_chunks = []
        for i, chunk in enumerate(chunks):
            # Extract page number from chunk if available
            page_match = None
            for line in chunk.split('\n'):
                if line.startswith("--- Page ") and line.endswith(" ---"):
                    try:
                        page_match = int(line.replace("--- Page ", "").replace(" ---", ""))
                        break
                    except:
                        pass
            
            # Create a unique ID for the chunk
            chunk_id = hashlib.md5(f"{metadata['filename']}_{i}_{chunk[:100]}".encode()).hexdigest()
            
            doc_chunks.append({
                "id": chunk_id,
                "text": chunk,
                "metadata": {
                    **metadata,
                    "chunk_id": i,
                    "page": page_match if page_match else "unknown"
                }
            })
        
        return doc_chunks
    
    def process_pdf(self, pdf_path: str, use_pdfplumber: bool = False) -> List[Dict]:
        """Process a PDF file: extract text and split into chunks with metadata"""
        text, metadata = self.extract_text(pdf_path, use_pdfplumber)
        chunks = self.chunk_text(text, metadata)
        return chunks
    
    def process_multiple_pdfs(self, pdf_paths: List[str], use_pdfplumber: bool = False) -> List[Dict]:
        """Process multiple PDF files and return all chunks"""
        all_chunks = []
        
        for pdf_path in tqdm(pdf_paths, desc="Processing PDFs"):
            try:
                chunks = self.process_pdf(pdf_path, use_pdfplumber)
                all_chunks.extend(chunks)
                print(f"Processed {pdf_path}: {len(chunks)} chunks extracted")
            except Exception as e:
                print(f"Error processing {pdf_path}: {str(e)}")
        
        return all_chunks


# For testing
if __name__ == "__main__":
    processor = PDFProcessor()
    
    # Test with a sample PDF
    sample_pdf = os.path.join(config.DATA_DIR, "sample.pdf")
    if os.path.exists(sample_pdf):
        chunks = processor.process_pdf(sample_pdf)
        print(f"Extracted {len(chunks)} chunks from {sample_pdf}")
        print(f"First chunk: {chunks[0]['text'][:200]}...")
    else:
        print(f"Sample PDF not found at {sample_pdf}") 