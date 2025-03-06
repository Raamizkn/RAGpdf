import os
import sys
import requests
import json
import time
from typing import List, Dict, Any
import streamlit as st
import pandas as pd

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

# API endpoint
API_URL = f"http://localhost:{config.API_PORT}"

# Page configuration
st.set_page_config(
    page_title="PDF Research Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .citation {
        background-color: #f0f2f6;
        border-radius: 5px;
        padding: 10px;
        margin-bottom: 10px;
    }
    .source-text {
        font-size: 0.9rem;
        border-left: 3px solid #4CAF50;
        padding-left: 10px;
        margin-top: 5px;
    }
    .answer-box {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        border: 1px solid #e0e0e0;
    }
    .upload-section {
        background-color: #f0f7ff;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Session state initialization
if "document_count" not in st.session_state:
    st.session_state.document_count = 0
if "processing" not in st.session_state:
    st.session_state.processing = False
if "question_history" not in st.session_state:
    st.session_state.question_history = []

# Helper functions
def check_api_status():
    """Check if the API is running and get document count"""
    try:
        response = requests.get(f"{API_URL}/status")
        if response.status_code == 200:
            data = response.json()
            st.session_state.document_count = data["document_count"]
            return True
        return False
    except:
        return False

def upload_pdfs(files, use_pdfplumber):
    """Upload PDFs to the API"""
    if not files:
        return
    
    try:
        # Create form data
        form_data = {"use_pdfplumber": str(use_pdfplumber).lower()}
        files_data = [("files", (file.name, file.getvalue(), "application/pdf")) for file in files]
        
        # Upload files
        response = requests.post(
            f"{API_URL}/upload-pdfs",
            data=form_data,
            files=files_data
        )
        
        if response.status_code == 200:
            data = response.json()
            st.session_state.processing = True
            return data
        else:
            st.error(f"Error uploading files: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

def ask_question(question, top_k=None):
    """Ask a question to the API"""
    try:
        payload = {"question": question}
        if top_k:
            payload["top_k"] = top_k
        
        response = requests.post(
            f"{API_URL}/ask",
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Add to question history
            st.session_state.question_history.append({
                "question": question,
                "answer": result["answer"],
                "citations": result["citations"],
                "retrieved_docs": result["retrieved_docs"]
            })
            
            return result
        else:
            st.error(f"Error: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

# Main app
def main():
    # Header
    st.title("📚 PDF Research Assistant")
    st.markdown("Upload PDFs and ask questions about their content using AI.")
    
    # Check API status
    api_running = check_api_status()
    if not api_running:
        st.error("⚠️ API server is not running. Please start the backend server.")
        st.code("cd backend && uvicorn main:app --reload", language="bash")
        return
    
    # Sidebar
    with st.sidebar:
        st.header("Settings")
        
        # Document status
        st.subheader("Document Status")
        st.metric("Documents Loaded", st.session_state.document_count)
        
        # Upload section
        st.subheader("Upload PDFs")
        uploaded_files = st.file_uploader(
            "Upload PDF files",
            type=["pdf"],
            accept_multiple_files=True
        )
        
        use_pdfplumber = st.checkbox(
            "Use PDFPlumber (better for complex layouts)",
            value=False
        )
        
        if st.button("Process PDFs"):
            if uploaded_files:
                with st.spinner("Uploading files..."):
                    result = upload_pdfs(uploaded_files, use_pdfplumber)
                    if result:
                        st.success(f"Processing {len(uploaded_files)} PDFs in the background")
            else:
                st.warning("Please upload PDF files first")
        
        # Search settings
        st.subheader("Search Settings")
        top_k = st.slider(
            "Number of documents to retrieve",
            min_value=1,
            max_value=10,
            value=config.MAX_DOCS_TO_RETRIEVE
        )
        
        # History
        st.subheader("Question History")
        if st.session_state.question_history:
            for i, item in enumerate(st.session_state.question_history):
                if st.button(f"Q: {item['question'][:30]}...", key=f"hist_{i}"):
                    st.session_state.selected_history = i
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Question input
        st.subheader("Ask a Question")
        question = st.text_area("Enter your question about the documents", height=100)
        
        if st.button("Ask"):
            if question:
                with st.spinner("Generating answer..."):
                    result = ask_question(question, top_k)
                    if result:
                        st.session_state.current_result = result
            else:
                st.warning("Please enter a question")
        
        # Display answer
        if "current_result" in st.session_state:
            result = st.session_state.current_result
            
            st.subheader("Answer")
            st.markdown(f"<div class='answer-box'>{result['answer']}</div>", unsafe_allow_html=True)
            
            # Display citations
            if result["citations"]:
                st.subheader("Sources")
                for citation in result["citations"]:
                    st.markdown(
                        f"<div class='citation'>"
                        f"<strong>Document:</strong> {citation['title']} | "
                        f"<strong>Page:</strong> {citation['page']} | "
                        f"<strong>Relevance:</strong> {citation['score']:.2f}"
                        f"</div>",
                        unsafe_allow_html=True
                    )
    
    with col2:
        # Display retrieved documents
        if "current_result" in st.session_state and st.session_state.current_result["retrieved_docs"]:
            st.subheader("Retrieved Passages")
            docs = st.session_state.current_result["retrieved_docs"]
            
            for i, doc in enumerate(docs):
                with st.expander(f"Passage {i+1} - {doc['metadata']['filename']} (Page {doc['metadata']['page']})"):
                    st.markdown(f"<div class='source-text'>{doc['text']}</div>", unsafe_allow_html=True)
                    st.caption(f"Relevance Score: {doc['score']:.2f}")

# Run the app
if __name__ == "__main__":
    main() 