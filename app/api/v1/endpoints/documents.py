from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import List, Optional, Dict, Any
from uuid import UUID
import json

from app.models.document import Document, DocumentCreate, DocumentUpdate
from app.models.tenant import TenantInDB
from app.db.document_db import (
    get_documents, get_document_by_id, create_document, update_document, delete_document
)
from app.api.deps import get_current_tenant
from app.utils.document_processor import process_uploaded_document
from app.db.vector_db import delete_document as delete_vector_document

router = APIRouter()

@router.get("/", response_model=List[Document])
def read_documents(current_tenant: TenantInDB = Depends(get_current_tenant)):
    """Get all documents for the current tenant."""
    return get_documents(current_tenant.id)

@router.post("/", response_model=Document, status_code=status.HTTP_201_CREATED)
async def create_new_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    metadata_json: Optional[str] = Form(None),
    current_tenant: TenantInDB = Depends(get_current_tenant)
):
    """Upload and process a new document."""
    try:
        # Parse metadata if provided
        metadata = {}
        if metadata_json:
            metadata = json.loads(metadata_json)
        
        # Read file content
        file_content = await file.read()
        
        # Process the document
        document = process_uploaded_document(
            file_content=file_content,
            filename=file.filename,
            tenant_id=current_tenant.id,
            title=title,
            metadata=metadata
        )
        
        return document
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error processing document: {str(e)}"
        )

@router.get("/{document_id}", response_model=Document)
def read_document(
    document_id: UUID,
    current_tenant: TenantInDB = Depends(get_current_tenant)
):
    """Get a document by ID."""
    document = get_document_by_id(document_id, current_tenant.id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document

@router.put("/{document_id}", response_model=Document)
def update_document_by_id(
    document_id: UUID,
    document_update: DocumentUpdate,
    current_tenant: TenantInDB = Depends(get_current_tenant)
):
    """Update a document."""
    document = update_document(document_id, document_update, current_tenant.id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document_by_id(
    document_id: UUID,
    current_tenant: TenantInDB = Depends(get_current_tenant)
):
    """Delete a document."""
    document_exists = delete_document(document_id, current_tenant.id)
    if not document_exists:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete document from vector store
    delete_vector_document(current_tenant.id, str(document_id))
    
    return None