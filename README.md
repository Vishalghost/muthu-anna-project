# Multi-Tenant RAG API

A secure multi-tenant Retrieval-Augmented Generation (RAG) API built with Flask and Hugging Face Transformers.

## Features

- **Multi-tenancy**: Each tenant gets their own isolated vector database
- **Secure API Keys**: Authentication with API keys for each tenant
- **Document Management**: Upload, retrieve, and delete documents
- **RAG-powered Chat**: Ask questions about tenant-specific documents
- **Simple Search**: Keyword-based document retrieval
- **LLM Integration**: Hugging Face Transformers for generating responses

## Project Structure

```
.
├── app.py              # Main Flask application
├── data/               # Data storage directory
│   ├── documents/      # Uploaded documents
│   ├── vector_store/   # Vector storage per tenant
│   ├── tenants.json    # Tenant information
│   └── documents.json  # Document metadata
├── .env               # Environment variables (optional)
├── requirements.txt   # Python dependencies
├── .gitignore        # Git ignore file
└── README.md         # This file
```

## Setup

1. Clone the repository:
   ```
   git clone https://github.com/Vishalghost/muthu-anna-project.git
   cd muthu-anna-project
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python app.py
   ```

The API will be available at `http://localhost:8000`

## API Usage

### Create a Tenant

```bash
curl -X POST "http://localhost:8000/api/v1/tenants" \
  -H "Content-Type: application/json" \
  -d '{"name": "Example Tenant", "description": "An example tenant"}'
```

### Upload a Document

```bash
curl -X POST "http://localhost:8000/api/v1/documents" \
  -H "X-API-Key: your_api_key" \
  -F "file=@document.txt" \
  -F "title=Example Document" \
  -F 'metadata_json={"category": "example"}'
```

### Chat with Documents

```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What information is in my documents?",
    "max_documents": 5
  }'
```

## License

MIT