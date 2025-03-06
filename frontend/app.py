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
try:
    from backend import config
    API_PORT = 8002
    CHUNK_SIZE = config.CHUNK_SIZE
    CHUNK_OVERLAP = config.CHUNK_OVERLAP
    MAX_DOCS_TO_RETRIEVE = config.MAX_DOCS_TO_RETRIEVE
except (ImportError, AttributeError):
    # Fallback to hardcoded values if import fails
    API_PORT = 8002
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    MAX_DOCS_TO_RETRIEVE = 5

# API endpoint
API_URL = f"http://localhost:{API_PORT}"

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
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
        border-left: 4px solid #4CAF50;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .source-text {
        font-size: 0.9rem;
        border-left: 3px solid #4CAF50;
        padding-left: 15px;
        margin-top: 10px;
        background-color: #f9f9f9;
        padding: 10px;
        border-radius: 5px;
    }
    .answer-box {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 25px;
        margin-bottom: 25px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .upload-section {
        background-color: #f0f7ff;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        border: 1px solid #d0e1f9;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 5px;
        border: none;
        padding: 10px 24px;
        font-weight: bold;
        white-space: nowrap;
        min-width: 80px;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    h1, h2, h3, h4, h5, h6 {
        color: white !important;
    }
    .feature-box {
        background-color: #e8f4fd;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
        border-left: 4px solid #3498db;
    }
    .summary-box {
        background-color: #fff8e1;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
        border-left: 4px solid #ffc107;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #f0f2f6;
        border-radius: 4px 4px 0 0;
        padding: 10px 20px;
        border: none;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4CAF50 !important;
        color: white !important;
    }
    .header-container {
        display: flex;
        align-items: center;
        margin-bottom: 1rem;
    }
    .header-logo {
        font-size: 2.5rem;
        margin-right: 0.5rem;
    }
    .header-title {
        font-size: 2rem;
        font-weight: bold;
        margin: 0;
    }
    .header-subtitle {
        font-size: 1rem;
        color: #666;
        margin-top: 0.5rem;
    }
    /* Fix for sidebar headers */
    .sidebar .block-container h1, 
    .sidebar .block-container h2, 
    .sidebar .block-container h3, 
    .sidebar .block-container h4 {
        color: white !important;
    }
    /* Fix for question text area */
    .stTextArea textarea {
        color: #666 !important;
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
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Ask"
if "summaries" not in st.session_state:
    st.session_state.summaries = {}
if "documents" not in st.session_state:
    st.session_state.documents = []
if "chunk_size" not in st.session_state:
    st.session_state.chunk_size = CHUNK_SIZE
if "chunk_overlap" not in st.session_state:
    st.session_state.chunk_overlap = CHUNK_OVERLAP

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

def get_documents():
    """Get list of documents from the API"""
    try:
        response = requests.get(f"{API_URL}/documents")
        if response.status_code == 200:
            data = response.json()
            st.session_state.documents = data["documents"]
            return data["documents"]
        return []
    except Exception as e:
        st.error(f"Error getting documents: {str(e)}")
        return []

def delete_document(filename):
    """Delete a document from the API"""
    try:
        response = requests.delete(f"{API_URL}/documents/{filename}")
        if response.status_code == 200:
            # Refresh document list
            get_documents()
            return True
        return False
    except Exception as e:
        st.error(f"Error deleting document: {str(e)}")
        return False

def upload_pdfs(files, use_pdfplumber, chunk_size=None, chunk_overlap=None):
    """Upload PDFs to the API"""
    if not files:
        return
    
    try:
        # Create form data
        form_data = {"use_pdfplumber": str(use_pdfplumber).lower()}
        
        # Add chunking parameters if provided
        if chunk_size:
            form_data["chunk_size"] = str(chunk_size)
        if chunk_overlap:
            form_data["chunk_overlap"] = str(chunk_overlap)
        
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

def generate_document_summary(filename):
    """Generate a summary for a document"""
    try:
        # Check if we already have a summary for this document
        if filename in st.session_state.summaries:
            return st.session_state.summaries[filename]
        
        # Request summary from API
        payload = {"filename": filename}
        response = requests.post(
            f"{API_URL}/summarize",
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            # Cache the summary
            st.session_state.summaries[filename] = result
            return result
        else:
            st.error(f"Error generating summary: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

def update_chunking_config(chunk_size, chunk_overlap):
    """Update chunking configuration"""
    try:
        payload = {
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap
        }
        
        response = requests.post(
            f"{API_URL}/chunking-config",
            json=payload
        )
        
        if response.status_code == 200:
            st.session_state.chunk_size = chunk_size
            st.session_state.chunk_overlap = chunk_overlap
            return True
        else:
            st.error(f"Error updating chunking config: {response.text}")
            return False
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return False

# Main app
def main():
    # Header with logo
    st.markdown("""
    <div class="header-container">
        <div class="header-logo">📚</div>
        <div>
            <h1 class="header-title">PDF Research Assistant</h1>
            <p class="header-subtitle">Powered by RAG (Retrieval-Augmented Generation)</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Check API status
    api_running = check_api_status()
    if not api_running:
        st.error("⚠️ API server is not running. Please start the backend server.")
        st.code("cd backend && uvicorn main:app --reload", language="bash")
        return
    
    # Get document list
    if st.session_state.document_count > 0 and not st.session_state.documents:
        get_documents()
    
    # Sidebar
    with st.sidebar:
        st.header("📊 Dashboard")
        
        # Document status
        st.subheader("Document Status")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Documents Loaded", st.session_state.document_count)
        with col2:
            if st.session_state.processing:
                st.success("Processing...")
            else:
                st.info("Ready")
        
        # Upload section
        st.markdown("---")
        st.subheader("📤 Upload Documents")
        
        uploaded_files = st.file_uploader(
            "Upload PDF files",
            type=["pdf"],
            accept_multiple_files=True
        )
        
        use_pdfplumber = st.checkbox(
            "Use PDFPlumber (better for complex layouts)",
            value=False
        )
        
        # Advanced chunking options - moved outside of any expander
        st.subheader("Advanced Chunking Options")
        chunk_size = st.slider(
            "Chunk Size",
            min_value=100,
            max_value=2000,
            value=st.session_state.chunk_size,
            step=100
        )
        
        chunk_overlap = st.slider(
            "Chunk Overlap",
            min_value=0,
            max_value=500,
            value=st.session_state.chunk_overlap,
            step=50
        )
        
        if st.button("Process Documents", key="process_btn"):
            if uploaded_files:
                with st.spinner("Uploading files..."):
                    result = upload_pdfs(
                        uploaded_files, 
                        use_pdfplumber,
                        chunk_size,
                        chunk_overlap
                    )
                    if result:
                        st.success(f"Processing {len(uploaded_files)} PDFs in the background")
            else:
                st.warning("Please upload PDF files first")
        
        # Search settings
        st.markdown("---")
        st.subheader("🔍 Search Settings")
        
        top_k = st.slider(
            "Number of documents to retrieve",
            min_value=1,
            max_value=10,
            value=MAX_DOCS_TO_RETRIEVE
        )
        
        # History
        st.markdown("---")
        st.subheader("📝 Question History")
        
        if st.session_state.question_history:
            for i, item in enumerate(st.session_state.question_history):
                if st.button(f"Q: {item['question'][:30]}...", key=f"hist_{i}"):
                    st.session_state.selected_history = i
                    st.session_state.active_tab = "Ask"
    
    # Main content - Tabs
    tabs = st.tabs(["📝 Ask Questions", "📊 Document Management", "📋 Summaries", "⚙️ Settings"])
    
    # Tab 1: Ask Questions
    with tabs[0]:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Question input
            st.subheader("Ask a Question")
            question = st.text_area("Enter your question about the documents", height=100, 
                                    placeholder="e.g., What are the main types of machine learning?")
            
            col_btn1, col_btn2 = st.columns([1, 5])
            with col_btn1:
                if st.button("Ask", key="ask_btn", use_container_width=True):
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
                
                st.markdown("### 💡 Answer")
                st.markdown(f"<div class='answer-box'>{result['answer']}</div>", unsafe_allow_html=True)
                
                # Display citations
                if result["citations"]:
                    st.markdown("### 📚 Sources")
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
                st.markdown("### 📄 Retrieved Passages")
                docs = st.session_state.current_result["retrieved_docs"]
                
                for i, doc in enumerate(docs):
                    with st.expander(f"Passage {i+1} - {doc['metadata']['filename']} (Page {doc['metadata']['page']})"):
                        st.markdown(f"<div class='source-text'>{doc['text']}</div>", unsafe_allow_html=True)
                        st.caption(f"Relevance Score: {doc['score']:.2f}")
    
    # Tab 2: Document Management
    with tabs[1]:
        st.markdown("### 📚 Document Management")
        
        # Document list
        if st.session_state.documents:
            st.markdown("<div class='feature-box'>", unsafe_allow_html=True)
            st.markdown("#### 📁 Your Documents")
            
            # Create a dataframe from the document list
            doc_df = pd.DataFrame(st.session_state.documents)
            
            # Add a selection column
            if not doc_df.empty:
                # Display as a table
                st.dataframe(doc_df, use_container_width=True)
                
                # Document actions
                selected_doc = st.selectbox("Select a document for actions:", 
                                           [doc["filename"] for doc in st.session_state.documents])
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("Delete Document", key="delete_btn"):
                        with st.spinner("Deleting document..."):
                            if delete_document(selected_doc):
                                st.success(f"Document {selected_doc} deleted successfully")
                                # Refresh document count
                                check_api_status()
                with col2:
                    st.button("Download", key="download_btn", disabled=True)
                with col3:
                    if st.button("Generate Summary", key="summary_btn"):
                        with st.spinner("Generating summary..."):
                            summary = generate_document_summary(selected_doc)
                            if summary:
                                st.session_state.current_summary = summary
                                st.session_state.active_tab = "Summaries"
            
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("No documents uploaded yet. Please upload documents in the sidebar.")
    
    # Tab 3: Summaries
    with tabs[2]:
        st.markdown("### 📋 Document Summaries")
        
        if st.session_state.documents:
            # Document selection for summary
            selected_doc = st.selectbox("Select a document to summarize:", 
                                       [doc["filename"] for doc in st.session_state.documents],
                                       key="summary_select")
            
            if st.button("Generate Summary", key="gen_summary_btn"):
                with st.spinner("Generating summary..."):
                    summary = generate_document_summary(selected_doc)
                    if summary:
                        st.session_state.current_summary = summary
            
            # Display summary if available
            if "current_summary" in st.session_state:
                summary = st.session_state.current_summary
                
                st.markdown("<div class='summary-box'>", unsafe_allow_html=True)
                st.markdown(f"#### 📄 {summary['title']}")
                st.markdown(summary["summary"])
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("No documents uploaded yet. Please upload documents to generate summaries.")
    
    # Tab 4: Settings
    with tabs[3]:
        st.markdown("### ⚙️ Settings")
        
        # LLM Settings
        st.markdown("<div class='feature-box'>", unsafe_allow_html=True)
        st.markdown("#### 🤖 LLM Settings")
        
        llm_option = st.radio(
            "Select LLM Provider",
            ["Local (Ollama)", "OpenAI API"],
            index=0
        )
        
        if llm_option == "Local (Ollama)":
            st.selectbox(
                "Select Model",
                ["mistral", "llama2", "llama2-uncensored", "vicuna"],
                index=0
            )
        else:
            st.selectbox(
                "Select Model",
                ["gpt-4", "gpt-3.5-turbo"],
                index=0
            )
            st.text_input("API Key", type="password")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Chunking Settings
        st.markdown("<div class='feature-box'>", unsafe_allow_html=True)
        st.markdown("#### 📄 Chunking Settings")
        
        chunk_size = st.slider(
            "Chunk Size",
            min_value=100,
            max_value=2000,
            value=st.session_state.chunk_size,
            step=100,
            key="settings_chunk_size"
        )
        
        chunk_overlap = st.slider(
            "Chunk Overlap",
            min_value=0,
            max_value=500,
            value=st.session_state.chunk_overlap,
            step=50,
            key="settings_chunk_overlap"
        )
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Search Settings
        st.markdown("<div class='feature-box'>", unsafe_allow_html=True)
        st.markdown("#### 🔍 Search Settings")
        
        use_hybrid = st.checkbox("Use Hybrid Search (Vector + BM25)", value=True)
        
        if use_hybrid:
            vector_weight = st.slider(
                "Vector Search Weight",
                min_value=0.0,
                max_value=1.0,
                value=0.7,
                step=0.1
            )
            
            bm25_weight = st.slider(
                "BM25 Weight",
                min_value=0.0,
                max_value=1.0,
                value=0.3,
                step=0.1
            )
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Save button
        if st.button("Save Settings", key="save_settings"):
            # Update chunking config
            if update_chunking_config(chunk_size, chunk_overlap):
                st.success("Settings saved successfully")

# Run the app
if __name__ == "__main__":
    main() 