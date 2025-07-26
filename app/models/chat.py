from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4

class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str

class ChatRequest(BaseModel):
    query: str
    chat_history: Optional[List[ChatMessage]] = Field(default_factory=list)
    metadata_filter: Optional[Dict[str, Any]] = None
    max_documents: Optional[int] = 5

class ChatResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    
class ChatHistory(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    messages: List[ChatMessage] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)