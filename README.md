# 📚 PDF Research Assistant (RAG-Powered)

![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.10+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28.0-red)
![LangChain](https://img.shields.io/badge/LangChain-0.0.335-orange)
![Docker](https://img.shields.io/badge/Docker-Ready-blue)

A powerful AI-powered research assistant that analyzes multiple PDFs, extracts information, and answers queries using Retrieval-Augmented Generation (RAG). Unlike regular ChatPDF apps, this system supports multi-document knowledge retrieval, context-aware responses, and both local and API-based LLM execution.

## ✨ Features

- **📄 Multi-PDF Upload**: Process multiple research papers, legal documents, or books simultaneously
- **🧠 Advanced Chunking**: Uses NLP-based chunking with configurable parameters instead of naive fixed-length chunks
- **🔍 RAG-Powered Retrieval**: Retrieves the most relevant text and augments LLM responses for accurate answers
- **🤖 Flexible LLM Support**: Works with both local models (via Ollama) and API-based models (OpenAI)
- **🔎 Hybrid Search**: Combines vector embeddings and BM25 for superior retrieval accuracy
- **📝 Citation Tracking**: Shows source references for extracted answers with page numbers
- **📊 Document Management**: Organize, delete, and summarize your uploaded documents
- **📱 Modern UI**: User-friendly Streamlit-based frontend with tabs and responsive design
- **🚀 Scalability**: Efficiently processes hundreds of PDFs with optimized memory usage
- **🐳 Docker Support**: Easy deployment with Docker and Docker Compose

## 🛠️ Technology Stack

### Backend
- **FastAPI**: High-performance API framework for the backend server
- **LangChain**: Framework for building RAG pipelines and LLM interactions
- **PyMuPDF & PDFPlumber**: PDF parsing and text extraction
- **Sentence Transformers**: Text embedding generation for semantic search
- **ChromaDB & FAISS**: Vector database for efficient similarity search
- **BM25**: Statistical retrieval function for keyword-based search
- **Ollama**: Interface for running local LLMs (Mistral, Llama, etc.)
- **OpenAI API**: Optional integration for cloud-based LLMs

### Frontend
- **Streamlit**: Interactive web interface with minimal code
- **Pandas**: Data manipulation for document management
- **Custom CSS**: Enhanced styling for better user experience

### Deployment
- **Docker**: Containerization for easy deployment
- **Docker Compose**: Multi-container orchestration
- **Cloud Ready**: Deployable to AWS, GCP, Azure, and other cloud platforms

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- [Ollama](https://ollama.ai/) (for local LLM support)
- Docker and Docker Compose (for containerized deployment)

### Standard Installation

1. Clone this repository
   ```bash
   git clone https://github.com/yourusername/pdf-research-assistant.git
   cd pdf-research-assistant
   ```

2. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

3. For local LLM support, install Ollama and download a model
   ```bash
   # Install Ollama from https://ollama.ai/
   ollama pull mistral
   ```

### Docker Installation

1. Clone this repository
   ```bash
   git clone https://github.com/yourusername/pdf-research-assistant.git
   cd pdf-research-assistant
   ```

2. Build and start the containers
   ```bash
   docker-compose up -d
   ```

3. Access the application
   - Frontend: http://localhost:8501
   - Backend API: http://localhost:8002

For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

### Configuration

Edit the `.env` file to configure:
- LLM settings (local or API-based)
- Vector database path
- Hybrid search weights
- Other parameters

```
# API Keys
OPENAI_API_KEY=your_api_key_here  # Optional

# LLM Settings
USE_LOCAL_LLM=true
DEFAULT_LLM_MODEL=mistral

# Vector DB Settings
VECTOR_DB_PATH=./models/chroma_db

# Hybrid Search Settings
USE_HYBRID_SEARCH=true
BM25_WEIGHT=0.3
VECTOR_WEIGHT=0.7
```

### Running the Application

1. Start the application (backend and frontend)
   ```bash
   python run.py
   ```

2. Or start components separately
   ```bash
   # Terminal 1 - Backend
   cd backend
   uvicorn main:app --reload --port 8002

   # Terminal 2 - Frontend
   cd frontend
   streamlit run app.py
   ```

3. Open your browser and navigate to http://localhost:8501

## 📋 Usage Guide

### Uploading Documents
1. Use the sidebar to upload one or more PDF files
2. Configure advanced chunking options if needed
3. Click "Process Documents" to start extraction and indexing

### Asking Questions
1. Type your question in the text area
2. Click "Ask" to generate an answer
3. View the answer along with citations and source passages

### Managing Documents
1. Navigate to the "Document Management" tab
2. View, delete, or generate summaries of your documents

### Customizing Settings
1. Navigate to the "Settings" tab
2. Configure LLM options, chunking parameters, and search settings

## 🏗️ Project Structure

```
📂 pdf-research-assistant
├── 📁 backend
│   ├── main.py              # FastAPI server
│   ├── process_pdf.py       # PDF extraction & chunking
│   ├── embed_store.py       # Vector DB handling
│   ├── query_handler.py     # RAG retrieval & LLM response
│   ├── config.py            # Configuration settings
├── 📁 frontend
│   ├── app.py               # Streamlit UI
├── 📁 models                # Storage for embeddings and vector DB
├── 📁 data                  # Sample and uploaded PDFs
├── 📁 tools                 # Utility scripts
├── Dockerfile               # Docker container definition
├── docker-compose.yml       # Multi-container orchestration
├── requirements.txt         # Dependencies
├── .env                     # Environment variables
├── run.py                   # Combined runner script
└── README.md                # Documentation
```

## 🔧 Advanced Configuration

### Chunking Strategy
The system uses LangChain's RecursiveCharacterTextSplitter for intelligent document chunking. You can configure:
- Chunk size (default: 1000 characters)
- Chunk overlap (default: 200 characters)
- Custom separators for domain-specific documents

### Hybrid Search
The system combines vector similarity and BM25 keyword matching:
- Vector weight: Controls the importance of semantic similarity (default: 0.7)
- BM25 weight: Controls the importance of keyword matching (default: 0.3)

### LLM Selection
- Local models via Ollama: Mistral, Llama2, etc.
- API-based models: OpenAI's GPT models (requires API key)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgements

- [LangChain](https://github.com/langchain-ai/langchain) for the RAG framework
- [Sentence Transformers](https://github.com/UKPLab/sentence-transformers) for embeddings
- [ChromaDB](https://github.com/chroma-core/chroma) for vector storage
- [FastAPI](https://fastapi.tiangolo.com/) for the backend framework
- [Streamlit](https://streamlit.io/) for the frontend framework
- [Ollama](https://ollama.ai/) for local LLM support 