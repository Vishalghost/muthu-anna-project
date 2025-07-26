import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

# API settings
API_V1_STR = "/api/v1"
PROJECT_NAME = "Multi-Tenant RAG API"

# JWT settings
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

# LLM Provider settings
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "huggingface").lower()

# OpenAI settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Hugging Face settings
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
HUGGINGFACE_MODEL = os.getenv("HUGGINGFACE_MODEL", "google/flan-t5-base")

# ChromaDB settings
CHROMA_PERSIST_DIRECTORY = os.getenv("CHROMA_PERSIST_DIRECTORY", "./data/chroma")

# Ensure data directories exist
Path(CHROMA_PERSIST_DIRECTORY).mkdir(parents=True, exist_ok=True)
Path("./data/documents").mkdir(parents=True, exist_ok=True)