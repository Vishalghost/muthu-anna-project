from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import API_V1_STR, PROJECT_NAME
from app.api.deps import get_current_tenant

app = FastAPI(
    title=PROJECT_NAME,
    description="Multi-tenant RAG API with FastAPI, ChromaDB, and Sentence Transformers",
    version="0.1.0",
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=API_V1_STR)

@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "Welcome to the Multi-Tenant RAG API",
        "docs_url": "/docs",
        "api_version": "v1"
    }

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.get("/auth-check")
def auth_check(current_tenant=Depends(get_current_tenant)):
    """Authentication check endpoint."""
    return {
        "authenticated": True,
        "tenant_id": str(current_tenant.id),
        "tenant_name": current_tenant.name
    }