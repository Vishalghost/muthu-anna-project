from fastapi import Depends, HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader
from typing import Optional

from app.core.security import verify_password
from app.db.tenant_db import get_tenant_by_api_key
from app.models.tenant import TenantInDB

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_current_tenant(api_key: str = Security(API_KEY_HEADER)) -> TenantInDB:
    """Dependency to get the current tenant from API key."""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is missing",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # Find tenant by API key
    tenant = None
    tenants = get_tenant_by_api_key(api_key)
    
    # If tenant is found directly by API key hash
    if tenants:
        return tenants
    
    # Otherwise, check all tenants for a matching API key
    from app.db.tenant_db import get_tenants
    all_tenants = get_tenants()
    
    for t in all_tenants:
        if verify_password(api_key, t.api_key_hash):
            tenant = t
            break
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    return tenant