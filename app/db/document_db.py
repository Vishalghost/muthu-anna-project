import json
import os
from typing import List, Optional, Dict
from uuid import UUID
from datetime import datetime
import pathlib

from app.models.document import DocumentInDB, DocumentCreate, DocumentUpdate

# Simple file-based storage for documents
DOCUMENTS_FILE = pathlib.Path("./data/documents.json")
DOCUMENTS_FILE.parent.mkdir(parents=True, exist_ok=True)

if not DOCUMENTS_FILE.exists():
    with open(DOCUMENTS_FILE, "w") as f:
        json.dump([], f)

def get_documents(tenant_id: Optional[UUID] = None) -> List[DocumentInDB]:
    """Get all documents, optionally filtered by tenant_id."""
    with open(DOCUMENTS_FILE, "r") as f:
        documents_data = json.load(f)
    
    documents = []
    for doc in documents_data:
        doc_obj = DocumentInDB(**{
            **doc,
            "id": UUID(doc["id"]),
            "tenant_id": UUID(doc["tenant_id"]),
            "created_at": datetime.fromisoformat(doc["created_at"]),
            "updated_at": datetime.fromisoformat(doc["updated_at"])
        })
        
        if tenant_id is None or doc_obj.tenant_id == tenant_id:
            documents.append(doc_obj)
    
    return documents

def get_document_by_id(document_id: UUID, tenant_id: Optional[UUID] = None) -> Optional[DocumentInDB]:
    """Get a document by ID, optionally filtered by tenant_id."""
    documents = get_documents(tenant_id)
    for document in documents:
        if document.id == document_id:
            return document
    return None

def create_document(document: DocumentCreate, file_path: Optional[str] = None) -> DocumentInDB:
    """Create a new document."""
    document_data = DocumentInDB(
        **document.model_dump(),
        file_path=file_path
    )
    
    documents = get_documents()
    
    # Convert UUID to string for JSON serialization
    document_dict = document_data.model_dump()
    document_dict["id"] = str(document_dict["id"])
    document_dict["tenant_id"] = str(document_dict["tenant_id"])
    document_dict["created_at"] = document_dict["created_at"].isoformat()
    document_dict["updated_at"] = document_dict["updated_at"].isoformat()
    
    documents_dict = [d.model_dump() for d in documents]
    for d in documents_dict:
        d["id"] = str(d["id"])
        d["tenant_id"] = str(d["tenant_id"])
        d["created_at"] = d["created_at"].isoformat()
        d["updated_at"] = d["updated_at"].isoformat()
    
    documents_dict.append(document_dict)
    
    with open(DOCUMENTS_FILE, "w") as f:
        json.dump(documents_dict, f, indent=2)
    
    return document_data

def update_document(document_id: UUID, document_update: DocumentUpdate, tenant_id: UUID) -> Optional[DocumentInDB]:
    """Update a document."""
    documents = get_documents()
    updated_document = None
    
    for i, document in enumerate(documents):
        if document.id == document_id and document.tenant_id == tenant_id:
            update_data = document_update.model_dump(exclude_unset=True)
            updated_document = DocumentInDB(**{**document.model_dump(), **update_data, "updated_at": datetime.utcnow()})
            documents[i] = updated_document
            break
    
    if updated_document:
        documents_dict = [d.model_dump() for d in documents]
        for d in documents_dict:
            d["id"] = str(d["id"])
            d["tenant_id"] = str(d["tenant_id"])
            d["created_at"] = d["created_at"].isoformat()
            d["updated_at"] = d["updated_at"].isoformat()
        
        with open(DOCUMENTS_FILE, "w") as f:
            json.dump(documents_dict, f, indent=2)
    
    return updated_document

def delete_document(document_id: UUID, tenant_id: UUID) -> bool:
    """Delete a document."""
    documents = get_documents()
    document_found = False
    
    documents_filtered = []
    for document in documents:
        if document.id != document_id or document.tenant_id != tenant_id:
            documents_filtered.append(document)
        else:
            document_found = True
    
    if document_found:
        documents_dict = [d.model_dump() for d in documents_filtered]
        for d in documents_dict:
            d["id"] = str(d["id"])
            d["tenant_id"] = str(d["tenant_id"])
            d["created_at"] = d["created_at"].isoformat()
            d["updated_at"] = d["updated_at"].isoformat()
        
        with open(DOCUMENTS_FILE, "w") as f:
            json.dump(documents_dict, f, indent=2)
    
    return document_found