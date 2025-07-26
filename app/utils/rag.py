import os
from typing import List, Dict, Any, Optional
from uuid import UUID
import openai
import re

from app.core.config import OPENAI_API_KEY, LLM_PROVIDER
from app.db.vector_db import query_documents, add_documents
from app.models.chat import ChatMessage

# Set OpenAI API key
if LLM_PROVIDER == "openai" and OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

# Simple text splitter
def simple_text_splitter(text, chunk_size=1000, chunk_overlap=200):
    """Split text into chunks."""
    if not text:
        return []
    
    # Split by paragraphs first
    paragraphs = re.split(r'\n\s*\n', text)
    
    chunks = []
    current_chunk = ""
    
    for paragraph in paragraphs:
        # If adding this paragraph would exceed chunk size, save current chunk and start a new one
        if len(current_chunk) + len(paragraph) > chunk_size and current_chunk:
            chunks.append(current_chunk)
            # Keep some overlap
            current_chunk = current_chunk[-chunk_overlap:] if chunk_overlap > 0 else ""
        
        # Add paragraph to current chunk
        if current_chunk:
            current_chunk += "\n\n" + paragraph
        else:
            current_chunk = paragraph
    
    # Add the last chunk if it's not empty
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks

# RAG prompt template
RAG_PROMPT_TEMPLATE = """
You are a helpful AI assistant. Use the following pieces of context to answer the question at the end.
If you don't know the answer, just say that you don't know, don't try to make up an answer.

Context:
{context}

Chat History:
{chat_history}

Question: {question}

Answer:
"""

def format_prompt(context, chat_history, question):
    """Format the prompt with context, chat history, and question."""
    chat_history_text = format_chat_history(chat_history)
    return RAG_PROMPT_TEMPLATE.format(
        context=context,
        chat_history=chat_history_text,
        question=question
    )

def process_document(content: str, metadata: Dict[str, Any], document_id: str, tenant_id: UUID):
    """Process a document by splitting it into chunks and adding to vector store."""
    # Split text into chunks
    chunks = simple_text_splitter(content)
    
    # Prepare metadata for each chunk
    metadatas = []
    ids = []
    
    for i, chunk in enumerate(chunks):
        chunk_metadata = metadata.copy()
        chunk_metadata["chunk_id"] = i
        chunk_metadata["document_id"] = document_id
        
        metadatas.append(chunk_metadata)
        ids.append(f"{document_id}_chunk_{i}")
    
    # Add chunks to vector store
    add_documents(tenant_id, chunks, metadatas, ids)
    
    return len(chunks)

def format_chat_history(chat_history: List[ChatMessage]) -> str:
    """Format chat history for the prompt."""
    if not chat_history:
        return ""
    
    formatted_history = ""
    for message in chat_history:
        formatted_history += f"{message.role.capitalize()}: {message.content}\n"
    
    return formatted_history

def generate_answer_with_openai(prompt_text: str) -> str:
    """Generate an answer using OpenAI API."""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers questions based on the provided context."},
                {"role": "user", "content": prompt_text}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating response with OpenAI: {str(e)}"

def generate_answer_without_llm(query: str, context: str) -> str:
    """Generate a simple answer without using an LLM."""
    if not context:
        return "I don't have enough information to answer that question."
    
    # Extract the most relevant paragraph from context
    paragraphs = context.split("\n\n")
    most_relevant = paragraphs[0] if paragraphs else context
    
    return f"Based on the available information: {most_relevant[:300]}... (Showing partial context as no LLM is available)"

def generate_answer(query: str, tenant_id: UUID, chat_history: List[ChatMessage] = None, 
                   metadata_filter: Optional[Dict[str, Any]] = None, max_documents: int = 5):
    """Generate an answer using RAG."""
    if chat_history is None:
        chat_history = []
    
    # Query relevant documents
    results = query_documents(tenant_id, query, max_documents, metadata_filter)
    
    # Extract documents and their metadata
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    
    if not documents:
        return {
            "answer": "I don't have enough information to answer that question.",
            "sources": []
        }
    
    # Format context from retrieved documents
    context = "\n\n".join([f"Document {i+1}:\n{doc}" for i, doc in enumerate(documents)])
    
    # Generate prompt
    filled_prompt = format_prompt(
        context=context,
        chat_history=chat_history,
        question=query
    )
    
    # Generate response using selected provider
    if LLM_PROVIDER == "openai" and OPENAI_API_KEY:
        answer = generate_answer_with_openai(filled_prompt)
    else:
        # Fallback to simple context extraction
        answer = generate_answer_without_llm(query, context)
    
    # Format sources
    sources = []
    for i, metadata in enumerate(metadatas):
        source = {
            "document_id": metadata.get("document_id", ""),
            "title": metadata.get("title", "Unknown"),
            "chunk_id": metadata.get("chunk_id", i)
        }
        sources.append(source)
    
    return {
        "answer": answer,
        "sources": sources
    }