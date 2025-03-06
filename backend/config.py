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
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
MAX_DOCS_TO_RETRIEVE = 5

# Vector DB settings
VECTOR_DB_PATH = os.path.join(MODELS_DIR, "chroma_db")
EMBEDDINGS_MODEL = "all-MiniLM-L6-v2"  # Default local model from sentence-transformers

# LLM settings
DEFAULT_LLM_MODEL = "mistral"  # Default Ollama model
USE_LOCAL_LLM = True  # Set to False to use OpenAI API

# API keys (load from environment variables)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# FastAPI settings
API_HOST = "0.0.0.0"
API_PORT = 8000

# Streamlit settings
STREAMLIT_PORT = 8501

# BM25 settings
USE_HYBRID_SEARCH = True  # Combine vector search with BM25
BM25_WEIGHT = 0.3  # Weight for BM25 scores in hybrid search (0-1)
VECTOR_WEIGHT = 0.7  # Weight for vector scores in hybrid search (0-1)

# Citation settings
SHOW_CITATIONS = True
MAX_CITATIONS = 3 