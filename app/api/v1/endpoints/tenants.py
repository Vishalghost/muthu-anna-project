from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID

from app.models.tenant import Tenant, TenantCreate, TenantUpdate, TenantWithKey
from app.db.tenant_db import (
    get_tenants, get_tenant_by_id, create_tenant, update_tenant, delete_tenant
)
from app.api.deps import get_current_tenant
from app.db.vector_db import delete_tenant_collection

router = APIRouter()

@router.get("/", response_model=List[Tenant])
def read_tenants():
    """Get all tenants."""
    return get_tenants()

@router.post("/", response_model=TenantWithKey, status_code=status.HTTP_201_CREATED)
def create_new_tenant(tenant: TenantCreate):
    """Create a new tenant."""
    tenant_data = create_tenant(tenant)
    return TenantWithKey(
        id=tenant_data.id,
        name=tenant_data.name,
        description=tenant_data.description,
        created_at=tenant_data.created_at,
        updated_at=tenant_data.updated_at,
        api_key=tenant_data.api_key
    )

@router.get("/me", response_model=Tenant)
def read_tenant_me(current_tenant: TenantWithKey = Depends(get_current_tenant)):
    """Get current tenant."""
    return current_tenant

@router.get("/{tenant_id}", response_model=Tenant)
def read_tenant(tenant_id: UUID):
    """Get a tenant by ID."""
    tenant = get_tenant_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant

@router.put("/{tenant_id}", response_model=Tenant)
def update_tenant_by_id(tenant_id: UUID, tenant_update: TenantUpdate):
    """Update a tenant."""
    tenant = update_tenant(tenant_id, tenant_update)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant

@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tenant_by_id(tenant_id: UUID):
    """Delete a tenant."""
    tenant_exists = delete_tenant(tenant_id)
    if not tenant_exists:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Delete tenant's vector collection
    delete_tenant_collection(tenant_id)
    
    return None