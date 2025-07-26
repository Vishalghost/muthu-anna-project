import os
import shutil
from typing import Dict, Any, Optional
from uuid import UUID
from pathlib import Path
import hashlib

from app.utils.rag import process_document
from app.models.document import DocumentCreate, DocumentInDB
from app.db.document_db import create_document

def save_document_file(file_content: bytes, tenant_id: UUID, filename: str) -> str:
    """Save a document file to disk."""
    # Create directory for tenant if it doesn't exist
    tenant_dir = Path(f"./data/documents/{tenant_id}")
    tenant_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate a unique filename to avoid collisions
    file_hash = hashlib.md5(file_content).hexdigest()
    file_ext = Path(filename).suffix
    unique_filename = f"{file_hash}{file_ext}"
    
    # Save the file
    file_path = tenant_dir / unique_filename
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    return str(file_path)

def extract_text_from_file(file_path: str) -> str:
    """Extract text content from a file."""
    # Simple implementation that works with text files
    # In a production system, you'd want to handle various file types (PDF, DOCX, etc.)
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return f"Error reading file: {str(e)}"

def process_uploaded_document(
    file_content: bytes,
    filename: str,
    tenant_id: UUID,
    title: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> DocumentInDB:
    """Process an uploaded document."""
    # Save the file
    file_path = save_document_file(file_content, tenant_id, filename)
    
    # Extract text from the file
    text_content = extract_text_from_file(file_path)
    
    # Create document metadata
    if title is None:
        title = Path(filename).stem
    
    if metadata is None:
        metadata = {}
    
    metadata.update({
        "filename": filename,
        "title": title
    })
    
    # Create document in database
    document_create = DocumentCreate(
        title=title,
        content=text_content,
        metadata=metadata,
        tenant_id=tenant_id
    )
    
    document = create_document(document_create, file_path)
    
    # Process document for RAG
    process_document(text_content, metadata, str(document.id), tenant_id)
    
    return document