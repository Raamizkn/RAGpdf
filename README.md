# Personal Research Assistant for PDFs (RAG-Powered)

A powerful AI-powered research assistant that can analyze multiple PDFs, extract information, and answer queries using Retrieval-Augmented Generation (RAG).

## Features

- **Multi-PDF Upload**: Upload multiple research papers, legal documents, or books
- **Advanced Chunking**: Uses NLP-based chunking instead of naive fixed-length chunks
- **RAG-Powered Retrieval**: Retrieves the most relevant text and augments LLM responses
- **Local & API-Based LLMs**: Works with both local models (Llama 2, Mistral 7B) and API-based models
- **Hybrid Search**: Combines embeddings and BM25 for improved retrieval accuracy
- **Citation Tracking**: Shows source references for extracted answers
- **Scalability**: Can process hundreds of PDFs efficiently
- **Simple Web UI**: User-friendly Streamlit-based frontend

## Setup and Installation

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. For local LLM support, install [Ollama](https://ollama.ai/) and download a model:
   ```
   ollama pull mistral
   ```

## Usage

1. Start the backend server:
   ```
   cd backend
   uvicorn main:app --reload
   ```

2. Start the Streamlit frontend:
   ```
   cd frontend
   streamlit run app.py
   ```

3. Open your browser and navigate to http://localhost:8501

## Project Structure

```
📂 research-assistant
├── 📁 backend
│   ├── main.py  # FastAPI server
│   ├── process_pdf.py  # PDF extraction & chunking
│   ├── embed_store.py  # Vector DB handling (ChromaDB/FAISS)
│   ├── query_handler.py  # RAG retrieval & LLM response
│   ├── config.py  # Configuration settings
├── 📁 frontend
│   ├── app.py  # Streamlit UI
├── 📁 models
│   ├── embeddings.pkl  # Precomputed embeddings
├── 📁 data
│   ├── sample_papers.pdf
├── requirements.txt  # Dependencies
├── README.md  # Project documentation
```

## License

MIT 