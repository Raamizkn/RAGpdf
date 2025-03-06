import os
import json
import requests
from typing import List, Dict, Any, Optional, Tuple
import ollama
from langchain.prompts import PromptTemplate
import config
from embed_store import EmbeddingStore

class QueryHandler:
    def __init__(self, embedding_store: EmbeddingStore):
        self.embedding_store = embedding_store
        
        # Configure Ollama client for Docker
        if hasattr(config, 'OLLAMA_URL'):
            ollama.host = config.OLLAMA_URL
        
        # Define the RAG prompt template
        self.rag_template = PromptTemplate(
            input_variables=["context", "question"],
            template="""You are a helpful research assistant. Use the following context to answer the question. 
If you don't know the answer based on the context, just say that you don't know, don't try to make up an answer.
Always include citations to the source documents in your answer, using the format [Document: Title, Page: X].

Context:
{context}

Question: {question}

Answer:"""
        )
        
        # Define the summarization prompt template
        self.summary_template = PromptTemplate(
            input_variables=["document_content"],
            template="""You are a helpful research assistant. Please provide a concise summary of the following document. 
Focus on the main topics, key findings, and important concepts. The summary should be informative and highlight the most 
important aspects of the document.

Document:
{document_content}

Summary:"""
        )
    
    def format_context(self, retrieved_docs: List[Dict]) -> Tuple[str, List[Dict]]:
        """Format retrieved documents into context string and citation info"""
        context_parts = []
        citations = []
        
        for i, doc in enumerate(retrieved_docs):
            # Extract metadata
            metadata = doc["metadata"]
            title = metadata.get("title", metadata.get("filename", "Unknown"))
            page = metadata.get("page", "unknown")
            
            # Format document text with citation marker
            doc_text = f"[Document {i+1}: {title}, Page: {page}]\n{doc['text']}\n"
            context_parts.append(doc_text)
            
            # Add to citations
            citations.append({
                "document_id": doc["id"],
                "title": title,
                "page": page,
                "score": doc["score"]
            })
        
        return "\n\n".join(context_parts), citations
    
    def query_local_llm(self, prompt: str, model: str = None) -> str:
        """Query a local LLM using Ollama"""
        if model is None:
            model = config.DEFAULT_LLM_MODEL
        
        try:
            response = ollama.generate(
                model=model,
                prompt=prompt,
                options={
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 1024
                }
            )
            return response["response"]
        except Exception as e:
            print(f"Error querying local LLM: {str(e)}")
            return f"Error: Could not generate response from local LLM. {str(e)}"
    
    def query_openai(self, prompt: str) -> str:
        """Query OpenAI API for LLM response"""
        if not config.OPENAI_API_KEY:
            return "Error: OpenAI API key not configured."
        
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {config.OPENAI_API_KEY}"
            }
            
            data = {
                "model": "gpt-4",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 1024
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                data=json.dumps(data)
            )
            
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                return f"Error: OpenAI API returned status code {response.status_code}. {response.text}"
        except Exception as e:
            print(f"Error querying OpenAI: {str(e)}")
            return f"Error: Could not generate response from OpenAI. {str(e)}"
    
    def answer_question(self, question: str, top_k: int = None) -> Dict[str, Any]:
        """Answer a question using RAG approach"""
        if top_k is None:
            top_k = config.MAX_DOCS_TO_RETRIEVE
        
        # Retrieve relevant documents
        retrieved_docs = self.embedding_store.search(question, top_k=top_k)
        
        if not retrieved_docs:
            return {
                "answer": "I don't have enough information to answer this question. Please upload relevant documents first.",
                "citations": [],
                "retrieved_docs": []
            }
        
        # Format context and get citations
        context, citations = self.format_context(retrieved_docs)
        
        # Generate prompt
        prompt = self.rag_template.format(context=context, question=question)
        
        # Get LLM response
        if config.USE_LOCAL_LLM:
            answer = self.query_local_llm(prompt)
        else:
            answer = self.query_openai(prompt)
        
        return {
            "answer": answer,
            "citations": citations,
            "retrieved_docs": retrieved_docs if config.SHOW_CITATIONS else []
        }
    
    def summarize_document(self, document_id: str = None, filename: str = None) -> Dict[str, Any]:
        """Generate a summary for a document"""
        # Get all chunks for the document
        if document_id:
            # In a real implementation, we would query the database for all chunks with this document_id
            # For now, we'll use a mock approach
            document_chunks = self.embedding_store.get_document_chunks(document_id)
        elif filename:
            # Get chunks by filename
            document_chunks = self.embedding_store.get_document_chunks_by_filename(filename)
        else:
            return {
                "summary": "Error: No document ID or filename provided.",
                "document_id": None,
                "title": None
            }
        
        if not document_chunks:
            return {
                "summary": "No document found with the provided ID or filename.",
                "document_id": document_id,
                "title": filename
            }
        
        # Concatenate all chunks
        document_content = "\n\n".join([chunk["text"] for chunk in document_chunks])
        
        # Get metadata from the first chunk
        metadata = document_chunks[0]["metadata"]
        title = metadata.get("title", metadata.get("filename", "Unknown"))
        
        # Generate prompt
        prompt = self.summary_template.format(document_content=document_content)
        
        # Get LLM response
        if config.USE_LOCAL_LLM:
            summary = self.query_local_llm(prompt)
        else:
            summary = self.query_openai(prompt)
        
        return {
            "summary": summary,
            "document_id": document_id or document_chunks[0]["id"],
            "title": title
        }


# For testing
if __name__ == "__main__":
    from embed_store import EmbeddingStore
    
    # Initialize embedding store
    store = EmbeddingStore()
    
    # Initialize query handler
    handler = QueryHandler(store)
    
    # Test with a sample question
    if store.get_document_count() > 0:
        result = handler.answer_question("What is machine learning?")
        print(f"Answer: {result['answer']}")
        print(f"Citations: {len(result['citations'])}")
    else:
        print("No documents in the database. Please add documents first.") 