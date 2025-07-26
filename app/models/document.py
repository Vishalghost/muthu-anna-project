from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID, uuid4

class DocumentBase(BaseModel):
    title: str
    content: Optional[str] = None
    metadata: Optional[dict] = Field(default_factory=dict)

class DocumentCreate(DocumentBase):
    tenant_id: UUID

class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    metadata: Optional[dict] = None

class DocumentInDB(DocumentBase):
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    file_path: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Document(DocumentBase):
    id: UUID
    tenant_id: UUID
    file_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime