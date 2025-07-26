from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID, uuid4

class TenantBase(BaseModel):
    name: str
    description: Optional[str] = None

class TenantCreate(TenantBase):
    pass

class TenantUpdate(TenantBase):
    name: Optional[str] = None

class TenantInDB(TenantBase):
    id: UUID = Field(default_factory=uuid4)
    api_key: str
    api_key_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Tenant(TenantBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

class TenantWithKey(Tenant):
    api_key: str