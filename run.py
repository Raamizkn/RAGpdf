import os
import sys
import subprocess
import time
import webbrowser
import signal
import atexit

def run_backend():
    """Run the FastAPI backend server"""
    print("Starting backend server...")
    backend_process = subprocess.Popen(
        ["uvicorn", "backend.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Register cleanup function
    atexit.register(lambda: backend_process.terminate())
    
    # Wait for backend to start
    time.sleep(2)
    print("Backend server running at http://localhost:8000")
    return backend_process

def run_frontend():
    """Run the Streamlit frontend"""
    print("Starting frontend server...")
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
    print("Frontend running at http://localhost:8501")
    return frontend_process

def open_browser():
    """Open the browser to the frontend URL"""
    webbrowser.open("http://localhost:8501")

def handle_exit(signum, frame):
    """Handle exit signal"""
    print("\nShutting down servers...")
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)
    
    # Run backend
    backend_process = run_backend()
    
    # Run frontend
    frontend_process = run_frontend()
    
    # Open browser
    open_browser()
    
    print("Press Ctrl+C to exit")
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down servers...")
        sys.exit(0) 