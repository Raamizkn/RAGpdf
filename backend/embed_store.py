import os
import pickle
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from tqdm import tqdm
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    print("Warning: sentence_transformers not available. Using numpy random embeddings as fallback.")
    SENTENCE_TRANSFORMERS_AVAILABLE = False
import chromadb
from chromadb.config import Settings
from rank_bm25 import BM25Okapi
import config

class EmbeddingStore:
    def __init__(self):
        # Initialize the embedding model
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.embedding_model = SentenceTransformer(config.EMBEDDINGS_MODEL)
            except Exception as e:
                print(f"Error loading SentenceTransformer: {str(e)}")
                print("Using numpy random embeddings as fallback.")
                self.embedding_model = None
        else:
            self.embedding_model = None
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=config.VECTOR_DB_PATH,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Create or get the collection
        self.collection = self.chroma_client.get_or_create_collection(
            name="pdf_chunks",
            metadata={"hnsw:space": "cosine"}
        )
        
        # BM25 index
        self.bm25_index = None
        self.bm25_corpus = []
        self.chunk_lookup = {}  # Maps chunk IDs to their original data
        
        # Document metadata
        self.document_metadata = {}  # Maps document filenames to metadata
    
    def embed_text(self, text: str) -> np.ndarray:
        """Generate embeddings for a single text"""
        if self.embedding_model is not None:
            return self.embedding_model.encode(text)
        else:
            # Fallback to random embeddings
            return np.random.rand(384)  # Common embedding size
    
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for multiple texts"""
        if self.embedding_model is not None:
            return self.embedding_model.encode(texts)
        else:
            # Fallback to random embeddings
            return np.array([np.random.rand(384) for _ in texts])
    
    def add_documents(self, chunks: List[Dict]) -> None:
        """Add document chunks to the vector store and BM25 index"""
        if not chunks:
            return
        
        # Prepare data for ChromaDB
        ids = [chunk["id"] for chunk in chunks]
        texts = [chunk["text"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]
        
        # Generate embeddings
        print("Generating embeddings...")
        embeddings = self.embed_texts(texts)
        
        # Add to ChromaDB
        print("Adding to vector database...")
        self.collection.add(
            ids=ids,
            embeddings=embeddings.tolist(),
            documents=texts,
            metadatas=metadatas
        )
        
        # Update BM25 index
        if config.USE_HYBRID_SEARCH:
            print("Updating BM25 index...")
            # Tokenize texts for BM25
            tokenized_corpus = [text.lower().split() for text in texts]
            
            # If BM25 index already exists, extend it
            if self.bm25_index is not None:
                self.bm25_corpus.extend(tokenized_corpus)
                self.bm25_index = BM25Okapi(self.bm25_corpus)
            else:
                self.bm25_corpus = tokenized_corpus
                self.bm25_index = BM25Okapi(tokenized_corpus)
        
        # Update chunk lookup
        for chunk in chunks:
            self.chunk_lookup[chunk["id"]] = chunk
            
            # Update document metadata
            filename = chunk["metadata"].get("filename", "")
            if filename and filename not in self.document_metadata:
                self.document_metadata[filename] = {
                    "title": chunk["metadata"].get("title", filename),
                    "pages": chunk["metadata"].get("pages", 0),
                    "date_added": chunk["metadata"].get("date_added", ""),
                    "chunk_count": 0
                }
            if filename:
                self.document_metadata[filename]["chunk_count"] += 1
        
        print(f"Added {len(chunks)} chunks to the database")
    
    def hybrid_search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Perform hybrid search using both vector similarity and BM25"""
        # Vector search
        vector_results = self.collection.query(
            query_texts=[query],
            n_results=top_k * 2  # Get more results to combine with BM25
        )
        
        if not vector_results["ids"][0]:
            return []
        
        # BM25 search if enabled
        if config.USE_HYBRID_SEARCH and self.bm25_index is not None:
            # Tokenize query
            tokenized_query = query.lower().split()
            
            # Get BM25 scores for all documents
            bm25_scores = self.bm25_index.get_scores(tokenized_query)
            
            # Normalize BM25 scores to 0-1 range
            if bm25_scores.max() > 0:
                bm25_scores = bm25_scores / bm25_scores.max()
            
            # Get vector search scores
            vector_ids = vector_results["ids"][0]
            vector_scores = np.array(vector_results["distances"][0])
            
            # Normalize vector scores (assuming they're already in 0-1 range for cosine)
            
            # Combine scores for the vector search results
            combined_results = []
            for i, doc_id in enumerate(vector_ids):
                # Find the index of this document in the BM25 corpus
                try:
                    bm25_idx = list(self.chunk_lookup.keys()).index(doc_id)
                    bm25_score = bm25_scores[bm25_idx]
                except (ValueError, IndexError):
                    bm25_score = 0
                
                vector_score = vector_scores[i]
                
                # Weighted combination
                combined_score = (config.VECTOR_WEIGHT * vector_score) + (config.BM25_WEIGHT * bm25_score)
                
                combined_results.append({
                    "id": doc_id,
                    "score": combined_score,
                    "text": vector_results["documents"][0][i],
                    "metadata": vector_results["metadatas"][0][i]
                })
            
            # Sort by combined score
            combined_results.sort(key=lambda x: x["score"], reverse=True)
            
            # Return top_k results
            return combined_results[:top_k]
        else:
            # Return vector search results only
            return [
                {
                    "id": vector_results["ids"][0][i],
                    "score": vector_results["distances"][0][i],
                    "text": vector_results["documents"][0][i],
                    "metadata": vector_results["metadatas"][0][i]
                }
                for i in range(min(top_k, len(vector_results["ids"][0])))
            ]
    
    def vector_search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Perform vector search only"""
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )
        
        if not results["ids"][0]:
            return []
        
        return [
            {
                "id": results["ids"][0][i],
                "score": results["distances"][0][i],
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i]
            }
            for i in range(len(results["ids"][0]))
        ]
    
    def search(self, query: str, top_k: int = 5, use_hybrid: Optional[bool] = None) -> List[Dict]:
        """Search for relevant chunks using the specified method"""
        if use_hybrid is None:
            use_hybrid = config.USE_HYBRID_SEARCH
        
        if use_hybrid:
            return self.hybrid_search(query, top_k)
        else:
            return self.vector_search(query, top_k)
    
    def get_document_count(self) -> int:
        """Get the number of documents in the collection"""
        return self.collection.count()
    
    def get_document_list(self) -> List[Dict]:
        """Get a list of all documents with metadata"""
        return [
            {
                "filename": filename,
                "title": metadata.get("title", filename),
                "pages": metadata.get("pages", 0),
                "chunks": metadata.get("chunk_count", 0),
                "date_added": metadata.get("date_added", "")
            }
            for filename, metadata in self.document_metadata.items()
        ]
    
    def get_document_chunks(self, document_id: str) -> List[Dict]:
        """Get all chunks for a document by document ID"""
        # In a real implementation, we would query the database
        # For now, we'll use a mock approach
        if document_id in self.chunk_lookup:
            chunk = self.chunk_lookup[document_id]
            filename = chunk["metadata"].get("filename", "")
            return self.get_document_chunks_by_filename(filename)
        return []
    
    def get_document_chunks_by_filename(self, filename: str) -> List[Dict]:
        """Get all chunks for a document by filename"""
        # Query ChromaDB for all chunks with this filename
        try:
            results = self.collection.get(
                where={"filename": filename}
            )
            
            if not results["ids"]:
                # Fallback to searching in chunk_lookup
                chunks = []
                for chunk_id, chunk in self.chunk_lookup.items():
                    if chunk["metadata"].get("filename") == filename:
                        chunks.append(chunk)
                return chunks
            
            # Format results
            return [
                {
                    "id": results["ids"][i],
                    "text": results["documents"][i],
                    "metadata": results["metadatas"][i]
                }
                for i in range(len(results["ids"]))
            ]
        except Exception as e:
            print(f"Error getting document chunks: {str(e)}")
            
            # Fallback to searching in chunk_lookup
            chunks = []
            for chunk_id, chunk in self.chunk_lookup.items():
                if chunk["metadata"].get("filename") == filename:
                    chunks.append(chunk)
            return chunks
    
    def delete_document(self, filename: str) -> bool:
        """Delete a document and all its chunks"""
        try:
            # Get all chunks for this document
            chunks = self.get_document_chunks_by_filename(filename)
            
            if not chunks:
                return False
            
            # Delete from ChromaDB
            chunk_ids = [chunk["id"] for chunk in chunks]
            self.collection.delete(ids=chunk_ids)
            
            # Remove from chunk_lookup
            for chunk_id in chunk_ids:
                if chunk_id in self.chunk_lookup:
                    del self.chunk_lookup[chunk_id]
            
            # Remove from document_metadata
            if filename in self.document_metadata:
                del self.document_metadata[filename]
            
            # Rebuild BM25 index
            if config.USE_HYBRID_SEARCH and self.bm25_index is not None:
                # This is inefficient but simple - in a real implementation we would
                # have a more efficient way to update the BM25 index
                self.bm25_corpus = []
                for chunk in self.chunk_lookup.values():
                    self.bm25_corpus.append(chunk["text"].lower().split())
                
                if self.bm25_corpus:
                    self.bm25_index = BM25Okapi(self.bm25_corpus)
                else:
                    self.bm25_index = None
            
            return True
        except Exception as e:
            print(f"Error deleting document: {str(e)}")
            return False
    
    def save_state(self) -> None:
        """Save the BM25 index and chunk lookup to disk"""
        if self.bm25_index is not None:
            state = {
                "bm25_corpus": self.bm25_corpus,
                "chunk_lookup": self.chunk_lookup,
                "document_metadata": self.document_metadata
            }
            
            with open(os.path.join(config.MODELS_DIR, "bm25_state.pkl"), "wb") as f:
                pickle.dump(state, f)
    
    def load_state(self) -> bool:
        """Load the BM25 index and chunk lookup from disk"""
        state_path = os.path.join(config.MODELS_DIR, "bm25_state.pkl")
        if os.path.exists(state_path):
            try:
                with open(state_path, "rb") as f:
                    state = pickle.load(f)
                
                self.bm25_corpus = state["bm25_corpus"]
                self.chunk_lookup = state["chunk_lookup"]
                
                if "document_metadata" in state:
                    self.document_metadata = state["document_metadata"]
                
                if self.bm25_corpus:
                    self.bm25_index = BM25Okapi(self.bm25_corpus)
                
                return True
            except Exception as e:
                print(f"Error loading state: {str(e)}")
                return False
        return False


# For testing
if __name__ == "__main__":
    store = EmbeddingStore()
    
    # Test embedding
    test_text = "This is a test document for embedding."
    embedding = store.embed_text(test_text)
    print(f"Embedding shape: {embedding.shape}")
    
    # Test document count
    count = store.get_document_count()
    print(f"Document count: {count}")
    
    # Test search if documents exist
    if count > 0:
        results = store.search("test query", top_k=3)
        print(f"Search results: {len(results)}")
        if results:
            print(f"Top result: {results[0]['text'][:100]}...") 