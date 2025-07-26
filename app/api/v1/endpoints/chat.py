from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any

from app.models.chat import ChatRequest, ChatResponse
from app.models.tenant import TenantInDB
from app.api.deps import get_current_tenant
from app.utils.rag import generate_answer

router = APIRouter()

@router.post("/", response_model=ChatResponse)
def chat_with_documents(
    chat_request: ChatRequest,
    current_tenant: TenantInDB = Depends(get_current_tenant)
):
    """Chat with documents using RAG."""
    try:
        result = generate_answer(
            query=chat_request.query,
            tenant_id=current_tenant.id,
            chat_history=chat_request.chat_history,
            metadata_filter=chat_request.metadata_filter,
            max_documents=chat_request.max_documents or 5
        )
        
        return ChatResponse(
            answer=result["answer"],
            sources=result["sources"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating response: {str(e)}"
        )