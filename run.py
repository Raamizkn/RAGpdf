import os
import sys
import subprocess
import time
import webbrowser
import signal
import atexit
import argparse

def run_backend():
    """Run the FastAPI backend server"""
    print("🚀 Starting backend server...")
    backend_process = subprocess.Popen(
        ["uvicorn", "backend.main:app", "--reload", "--host", "0.0.0.0", "--port", "8002"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Register cleanup function
    atexit.register(lambda: backend_process.terminate())
    
    # Wait for backend to start
    time.sleep(2)
    print("✅ Backend server running at http://localhost:8002")
    return backend_process

def run_frontend():
    """Run the Streamlit frontend"""
    print("🚀 Starting frontend server...")
    frontend_process = subprocess.Popen(
        ["streamlit", "run", "frontend/app.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Register cleanup function
    atexit.register(lambda: frontend_process.terminate())
    
    # Wait for frontend to start
    time.sleep(5)
    print("✅ Frontend running at http://localhost:8501")
    return frontend_process

def open_browser():
    """Open the browser to the frontend URL"""
    print("🌐 Opening browser...")
    webbrowser.open("http://localhost:8501")

def handle_exit(signum, frame):
    """Handle exit signal"""
    print("\n🛑 Shutting down servers...")
    sys.exit(0)

def create_sample_pdf():
    """Create a sample PDF for testing"""
    print("📄 Creating sample PDF...")
    try:
        from tools.create_sample_pdf import create_sample_pdf as create_pdf
        create_pdf()
        print("✅ Sample PDF created successfully")
    except Exception as e:
        print(f"❌ Error creating sample PDF: {str(e)}")

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    try:
        import fastapi
        import uvicorn
        import streamlit
        import langchain
        import sentence_transformers
        import faiss
        import chromadb
        import pymupdf
        import pdfplumber
        import rank_bm25
        import ollama
        import dotenv
        import numpy
        import pandas
        import tqdm
        import fpdf
        print("✅ All dependencies installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {str(e)}")
        print("Please install all dependencies with: pip install -r requirements.txt")
        return False

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run the PDF Research Assistant")
    parser.add_argument("--no-browser", action="store_true", help="Don't open the browser automatically")
    parser.add_argument("--create-sample", action="store_true", help="Create a sample PDF for testing")
    args = parser.parse_args()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Create sample PDF if requested
    if args.create_sample:
        create_sample_pdf()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)
    
    # Print welcome message
    print("\n" + "=" * 60)
    print("📚 Welcome to the PDF Research Assistant!")
    print("=" * 60)
    
    # Run backend
    backend_process = run_backend()
    
    # Run frontend
    frontend_process = run_frontend()
    
    # Open browser
    if not args.no_browser:
        open_browser()
    
    print("\n" + "=" * 60)
    print("🎉 PDF Research Assistant is now running!")
    print("📝 Frontend: http://localhost:8501")
    print("🔌 Backend API: http://localhost:8002")
    print("=" * 60)
    print("\nPress Ctrl+C to exit")
    
    try:
        # Monitor processes and restart if needed
        while True:
            # Check if backend is still running
            if backend_process.poll() is not None:
                print("⚠️ Backend server stopped, restarting...")
                backend_process = run_backend()
            
            # Check if frontend is still running
            if frontend_process.poll() is not None:
                print("⚠️ Frontend server stopped, restarting...")
                frontend_process = run_frontend()
            
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down servers...")
        sys.exit(0) 