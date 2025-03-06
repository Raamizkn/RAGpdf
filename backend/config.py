import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = os.path.join(BASE_DIR, "data")
MODELS_DIR = os.path.join(BASE_DIR, "models")

# Create directories if they don't exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

# PDF Processing
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
MAX_DOCS_TO_RETRIEVE = int(os.getenv("MAX_DOCS_TO_RETRIEVE", "5"))

# Vector DB settings
VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", os.path.join(MODELS_DIR, "chroma_db"))
EMBEDDINGS_MODEL = os.getenv("EMBEDDINGS_MODEL", "all-MiniLM-L6-v2")  # Default local model from sentence-transformers

# LLM settings
DEFAULT_LLM_MODEL = os.getenv("DEFAULT_LLM_MODEL", "mistral")  # Default Ollama model
USE_LOCAL_LLM = os.getenv("USE_LOCAL_LLM", "true").lower() == "true"  # Set to False to use OpenAI API

# API keys (load from environment variables)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# FastAPI settings
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8002"))

# Streamlit settings
STREAMLIT_PORT = int(os.getenv("STREAMLIT_PORT", "8501"))

# BM25 settings
USE_HYBRID_SEARCH = os.getenv("USE_HYBRID_SEARCH", "true").lower() == "true"  # Combine vector search with BM25
BM25_WEIGHT = float(os.getenv("BM25_WEIGHT", "0.3"))  # Weight for BM25 scores in hybrid search (0-1)
VECTOR_WEIGHT = float(os.getenv("VECTOR_WEIGHT", "0.7"))  # Weight for vector scores in hybrid search (0-1)

# Citation settings
SHOW_CITATIONS = os.getenv("SHOW_CITATIONS", "true").lower() == "true"
MAX_CITATIONS = int(os.getenv("MAX_CITATIONS", "3"))

# Ollama settings (for Docker)
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "localhost")
OLLAMA_PORT = int(os.getenv("OLLAMA_PORT", "11434"))
OLLAMA_URL = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}" 