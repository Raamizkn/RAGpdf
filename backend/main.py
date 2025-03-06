import os
import tempfile
import shutil
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import config
from process_pdf import PDFProcessor
from embed_store import EmbeddingStore
from query_handler import QueryHandler

app = FastAPI(title="PDF Research Assistant API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
pdf_processor = PDFProcessor()
embedding_store = EmbeddingStore()
query_handler = QueryHandler(embedding_store)

# Try to load BM25 state if it exists
embedding_store.load_state()

# Pydantic models for API
class QuestionRequest(BaseModel):
    question: str
    top_k: Optional[int] = None

class QuestionResponse(BaseModel):
    answer: str
    citations: List[Dict[str, Any]]
    retrieved_docs: List[Dict[str, Any]]

class ProcessingStatus(BaseModel):
    status: str
    message: str
    document_count: int

# Background task for processing PDFs
def process_pdfs_task(file_paths: List[str], use_pdfplumber: bool = False):
    try:
        # Process PDFs
        chunks = pdf_processor.process_multiple_pdfs(file_paths, use_pdfplumber)
        
        # Add to vector store
        embedding_store.add_documents(chunks)
        
        # Save BM25 state
        embedding_store.save_state()
        
        # Clean up temporary files
        for file_path in file_paths:
            if os.path.exists(file_path):
                os.remove(file_path)
    except Exception as e:
        print(f"Error in background task: {str(e)}")

@app.post("/upload-pdfs", response_model=ProcessingStatus)
async def upload_pdfs(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    use_pdfplumber: bool = Form(False)
):
    """Upload and process multiple PDF files"""
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    # Save uploaded files to temporary location
    temp_file_paths = []
    for file in files:
        if not file.filename.lower().endswith(".pdf"):
            continue
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            # Copy uploaded file content to temporary file
            shutil.copyfileobj(file.file, temp_file)
            temp_file_paths.append(temp_file.name)
    
    if not temp_file_paths:
        raise HTTPException(status_code=400, detail="No valid PDF files provided")
    
    # Process PDFs in background
    background_tasks.add_task(process_pdfs_task, temp_file_paths, use_pdfplumber)
    
    return {
        "status": "processing",
        "message": f"Processing {len(temp_file_paths)} PDF files in the background",
        "document_count": embedding_store.get_document_count()
    }

@app.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """Ask a question about the uploaded PDFs"""
    if not request.question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    # Check if we have documents
    if embedding_store.get_document_count() == 0:
        return {
            "answer": "No documents have been uploaded yet. Please upload PDF documents first.",
            "citations": [],
            "retrieved_docs": []
        }
    
    # Answer the question
    result = query_handler.answer_question(request.question, request.top_k)
    return result

@app.get("/status", response_model=ProcessingStatus)
async def get_status():
    """Get the current status of the system"""
    document_count = embedding_store.get_document_count()
    return {
        "status": "ready",
        "message": f"System is ready with {document_count} document chunks",
        "document_count": document_count
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=True
    ) 