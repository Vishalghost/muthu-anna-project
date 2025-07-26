# Multi-Tenant RAG API

A secure multi-tenant Retrieval-Augmented Generation (RAG) API built with FastAPI, ChromaDB, and Sentence Transformers.

## Features

- **Multi-tenancy**: Each tenant gets their own isolated vector database
- **Secure API Keys**: Authentication with API keys for each tenant
- **Document Management**: Upload, retrieve, and delete documents
- **RAG-powered Chat**: Ask questions about tenant-specific documents
- **Vector Search**: Semantic search using Sentence Transformers embeddings
- **LLM Integration**: OpenAI or LLaMA for generating responses

## Project Structure

```
.
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── chat.py
│   │   │   │   ├── documents.py
│   │   │   │   └── tenants.py
│   │   │   └── api.py
│   │   └── deps.py
│   ├── core/
│   │   ├── config.py
│   │   └── security.py
│   ├── db/
│   │   ├── document_db.py
│   │   ├── tenant_db.py
│   │   └── vector_db.py
│   ├── models/
│   │   ├── chat.py
│   │   ├── document.py
│   │   └── tenant.py
│   ├── utils/
│   │   ├── document_processor.py
│   │   └── rag.py
│   └── main.py
├── data/
│   ├── chroma/
│   └── documents/
├── .env
├── requirements.txt
├── run.py
└── README.md
```

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv venv
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # Linux/Mac
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Configure environment variables in `.env`:
   ```
   OPENAI_API_KEY=your_openai_api_key
   JWT_SECRET_KEY=your_jwt_secret_key
   JWT_ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   CHROMA_PERSIST_DIRECTORY=./data/chroma
   ```
5. Run the application:
   ```
   python run.py
   ```

## API Usage

### Create a Tenant

```bash
curl -X POST "http://localhost:8000/api/v1/tenants/" \
  -H "Content-Type: application/json" \
  -d '{"name": "Example Tenant", "description": "An example tenant"}'
```

### Upload a Document

```bash
curl -X POST "http://localhost:8000/api/v1/documents/" \
  -H "X-API-Key: your_api_key" \
  -F "file=@document.txt" \
  -F "title=Example Document" \
  -F 'metadata_json={"category": "example"}'
```

### Chat with Documents

```bash
curl -X POST "http://localhost:8000/api/v1/chat/" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What information is in my documents?",
    "max_documents": 5
  }'
```

## License

MIT