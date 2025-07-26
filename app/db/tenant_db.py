import json
import os
from typing import List, Optional
from uuid import UUID
from datetime import datetime
import pathlib

from app.models.tenant import TenantInDB, TenantCreate, TenantUpdate
from app.core.security import get_password_hash, generate_api_key

# Simple file-based storage for tenants
TENANTS_FILE = pathlib.Path("./data/tenants.json")
TENANTS_FILE.parent.mkdir(parents=True, exist_ok=True)

if not TENANTS_FILE.exists():
    with open(TENANTS_FILE, "w") as f:
        json.dump([], f)

def get_tenants() -> List[TenantInDB]:
    """Get all tenants."""
    with open(TENANTS_FILE, "r") as f:
        tenants_data = json.load(f)
    
    return [TenantInDB(**{**tenant, 
                          "id": UUID(tenant["id"]), 
                          "created_at": datetime.fromisoformat(tenant["created_at"]),
                          "updated_at": datetime.fromisoformat(tenant["updated_at"])}) 
            for tenant in tenants_data]

def get_tenant_by_id(tenant_id: UUID) -> Optional[TenantInDB]:
    """Get a tenant by ID."""
    tenants = get_tenants()
    for tenant in tenants:
        if tenant.id == tenant_id:
            return tenant
    return None

def get_tenant_by_api_key(api_key_hash: str) -> Optional[TenantInDB]:
    """Get a tenant by API key hash."""
    tenants = get_tenants()
    for tenant in tenants:
        if tenant.api_key_hash == api_key_hash:
            return tenant
    return None

def create_tenant(tenant: TenantCreate) -> TenantInDB:
    """Create a new tenant."""
    api_key = generate_api_key()
    api_key_hash = get_password_hash(api_key)
    
    tenant_data = TenantInDB(
        **tenant.model_dump(),
        api_key=api_key,
        api_key_hash=api_key_hash
    )
    
    tenants = get_tenants()
    
    # Convert UUID to string for JSON serialization
    tenant_dict = tenant_data.model_dump()
    tenant_dict["id"] = str(tenant_dict["id"])
    tenant_dict["created_at"] = tenant_dict["created_at"].isoformat()
    tenant_dict["updated_at"] = tenant_dict["updated_at"].isoformat()
    
    tenants_dict = [t.model_dump() for t in tenants]
    for t in tenants_dict:
        t["id"] = str(t["id"])
        t["created_at"] = t["created_at"].isoformat()
        t["updated_at"] = t["updated_at"].isoformat()
    
    tenants_dict.append(tenant_dict)
    
    with open(TENANTS_FILE, "w") as f:
        json.dump(tenants_dict, f, indent=2)
    
    return tenant_data

def update_tenant(tenant_id: UUID, tenant_update: TenantUpdate) -> Optional[TenantInDB]:
    """Update a tenant."""
    tenants = get_tenants()
    updated_tenant = None
    
    for i, tenant in enumerate(tenants):
        if tenant.id == tenant_id:
            update_data = tenant_update.model_dump(exclude_unset=True)
            updated_tenant = TenantInDB(**{**tenant.model_dump(), **update_data, "updated_at": datetime.utcnow()})
            tenants[i] = updated_tenant
            break
    
    if updated_tenant:
        tenants_dict = [t.model_dump() for t in tenants]
        for t in tenants_dict:
            t["id"] = str(t["id"])
            t["created_at"] = t["created_at"].isoformat()
            t["updated_at"] = t["updated_at"].isoformat()
        
        with open(TENANTS_FILE, "w") as f:
            json.dump(tenants_dict, f, indent=2)
    
    return updated_tenant

def delete_tenant(tenant_id: UUID) -> bool:
    """Delete a tenant."""
    tenants = get_tenants()
    tenant_found = False
    
    tenants_filtered = []
    for tenant in tenants:
        if tenant.id != tenant_id:
            tenants_filtered.append(tenant)
        else:
            tenant_found = True
    
    if tenant_found:
        tenants_dict = [t.model_dump() for t in tenants_filtered]
        for t in tenants_dict:
            t["id"] = str(t["id"])
            t["created_at"] = t["created_at"].isoformat()
            t["updated_at"] = t["updated_at"].isoformat()
        
        with open(TENANTS_FILE, "w") as f:
            json.dump(tenants_dict, f, indent=2)
    
    return tenant_found