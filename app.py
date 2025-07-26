import os
import json
import uuid
import hashlib
import secrets
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import re
from collections import Counter

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DATA_DIR = Path("./data")
DATA_DIR.mkdir(exist_ok=True)

# Create necessary directories
DOCUMENTS_DIR = DATA_DIR / "documents"
DOCUMENTS_DIR.mkdir(exist_ok=True)
TENANTS_FILE = DATA_DIR / "tenants.json"
DOCUMENTS_FILE = DATA_DIR / "documents.json"

# Initialize data files if they don't exist
if not TENANTS_FILE.exists():
    with open(TENANTS_FILE, "w") as f:
        json.dump([], f)

if not DOCUMENTS_FILE.exists():
    with open(DOCUMENTS_FILE, "w") as f:
        json.dump([], f)

# Simple in-memory vector store
class SimpleVectorStore:
    def __init__(self, tenant_id):
        self.tenant_id = tenant_id
        self.documents = []
        self.metadatas = []
        self.ids = []
        self.storage_dir = DATA_DIR / "vector_store" / tenant_id
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.storage_path = self.storage_dir / "vector_store.json"
        self.load()
    
    def add(self, documents, metadatas, ids):
        self.documents.extend(documents)
        self.metadatas.extend(metadatas)
        self.ids.extend(ids)
        self.save()
    
    def query(self, query_text, n_results=5, where=None):
        if not self.documents:
            return {"documents": [[]], "metadatas": [[]], "ids": [[]]}
        
        # Simple keyword matching
        query_terms = self._preprocess_text(query_text)
        scores = []
        
        for doc in self.documents:
            doc_terms = self._preprocess_text(doc)
            score = self._calculate_similarity(query_terms, doc_terms)
            scores.append(score)
        
        # Filter by metadata if needed
        if where:
            filtered_indices = []
            for i, metadata in enumerate(self.metadatas):
                match = True
                for key, value in where.items():
                    if key not in metadata or metadata[key] != value:
                        match = False
                        break
                if match:
                    filtered_indices.append(i)
            
            if not filtered_indices:
                return {"documents": [[]], "metadatas": [[]], "ids": [[]]}
            
            filtered_scores = [scores[i] for i in filtered_indices]
            filtered_documents = [self.documents[i] for i in filtered_indices]
            filtered_metadatas = [self.metadatas[i] for i in filtered_indices]
            filtered_ids = [self.ids[i] for i in filtered_indices]
            
            sorted_indices = sorted(range(len(filtered_scores)), key=lambda i: filtered_scores[i], reverse=True)[:n_results]
            
            return {
                "documents": [[filtered_documents[i] for i in sorted_indices]],
                "metadatas": [[filtered_metadatas[i] for i in sorted_indices]],
                "ids": [[filtered_ids[i] for i in sorted_indices]]
            }
        else:
            sorted_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:n_results]
            
            return {
                "documents": [[self.documents[i] for i in sorted_indices]],
                "metadatas": [[self.metadatas[i] for i in sorted_indices]],
                "ids": [[self.ids[i] for i in sorted_indices]]
            }
    
    def _preprocess_text(self, text):
        text = text.lower()
        words = re.findall(r'\w+', text)
        return words
    
    def _calculate_similarity(self, query_terms, doc_terms):
        if not query_terms or not doc_terms:
            return 0.0
        
        query_counter = Counter(query_terms)
        doc_counter = Counter(doc_terms)
        
        common_terms = set(query_counter.keys()) & set(doc_counter.keys())
        if not common_terms:
            return 0.0
        
        overlap_score = sum(min(query_counter[term], doc_counter[term]) for term in common_terms)
        max_possible = sum(query_counter.values())
        
        return overlap_score / max_possible if max_possible > 0 else 0.0
    
    def delete(self, ids):
        indices_to_delete = [i for i, doc_id in enumerate(self.ids) if doc_id in ids]
        
        self.documents = [doc for i, doc in enumerate(self.documents) if i not in indices_to_delete]
        self.metadatas = [meta for i, meta in enumerate(self.metadatas) if i not in indices_to_delete]
        self.ids = [doc_id for i, doc_id in enumerate(self.ids) if i not in indices_to_delete]
        
        self.save()
    
    def save(self):
        data = {
            "documents": self.documents,
            "metadatas": self.metadatas,
            "ids": self.ids
        }
        with open(self.storage_path, "w") as f:
            json.dump(data, f)
    
    def load(self):
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r") as f:
                    data = json.load(f)
                self.documents = data.get("documents", [])
                self.metadatas = data.get("metadatas", [])
                self.ids = data.get("ids", [])
            except Exception as e:
                print(f"Error loading vector store: {e}")

# Vector store dictionary
vector_stores = {}

# Helper functions
def get_vector_store(tenant_id):
    if tenant_id not in vector_stores:
        vector_stores[tenant_id] = SimpleVectorStore(tenant_id)
    return vector_stores[tenant_id]

def generate_api_key():
    return secrets.token_hex(16)

def hash_api_key(api_key):
    return hashlib.sha256(api_key.encode()).hexdigest()

def verify_api_key(api_key, api_key_hash):
    return hashlib.sha256(api_key.encode()).hexdigest() == api_key_hash

def get_tenants():
    with open(TENANTS_FILE, "r") as f:
        return json.load(f)

def get_documents():
    with open(DOCUMENTS_FILE, "r") as f:
        return json.load(f)

def save_tenants(tenants):
    with open(TENANTS_FILE, "w") as f:
        json.dump(tenants, f, indent=2)

def save_documents(documents):
    with open(DOCUMENTS_FILE, "w") as f:
        json.dump(documents, f, indent=2)

def get_tenant_by_api_key(api_key):
    tenants = get_tenants()
    for tenant in tenants:
        if verify_api_key(api_key, tenant["api_key_hash"]):
            return tenant
    return None

def simple_text_splitter(text, chunk_size=1000, chunk_overlap=200):
    if not text:
        return []
    
    paragraphs = re.split(r'\n\s*\n', text)
    chunks = []
    current_chunk = ""
    
    for paragraph in paragraphs:
        if len(current_chunk) + len(paragraph) > chunk_size and current_chunk:
            chunks.append(current_chunk)
            current_chunk = current_chunk[-chunk_overlap:] if chunk_overlap > 0 else ""
        
        if current_chunk:
            current_chunk += "\n\n" + paragraph
        else:
            current_chunk = paragraph
    
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks

# Authentication middleware
def authenticate():
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        return None
    
    tenant = get_tenant_by_api_key(api_key)
    return tenant

# API Routes
@app.route("/")
def home():
    return jsonify({
        "message": "Welcome to the Multi-Tenant RAG API",
        "version": "1.0.0"
    })

@app.route("/api/v1/tenants", methods=["POST"])
def create_tenant():
    data = request.json
    if not data or "name" not in data:
        return jsonify({"error": "Name is required"}), 400
    
    tenant_id = str(uuid.uuid4())
    api_key = generate_api_key()
    api_key_hash = hash_api_key(api_key)
    
    tenant = {
        "id": tenant_id,
        "name": data["name"],
        "description": data.get("description", ""),
        "api_key_hash": api_key_hash,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    tenants = get_tenants()
    tenants.append(tenant)
    save_tenants(tenants)
    
    # Return tenant with API key (only time it's exposed)
    response_tenant = tenant.copy()
    response_tenant["api_key"] = api_key
    del response_tenant["api_key_hash"]
    
    return jsonify(response_tenant), 201

@app.route("/api/v1/tenants", methods=["GET"])
def list_tenants():
    tenants = get_tenants()
    # Don't expose API key hashes
    for tenant in tenants:
        if "api_key_hash" in tenant:
            del tenant["api_key_hash"]
    
    return jsonify(tenants)

@app.route("/api/v1/tenants/me", methods=["GET"])
def get_current_tenant():
    tenant = authenticate()
    if not tenant:
        return jsonify({"error": "Unauthorized"}), 401
    
    # Don't expose API key hash
    response_tenant = tenant.copy()
    if "api_key_hash" in response_tenant:
        del response_tenant["api_key_hash"]
    
    return jsonify(response_tenant)

@app.route("/api/v1/documents", methods=["POST"])
def upload_document():
    tenant = authenticate()
    if not tenant:
        return jsonify({"error": "Unauthorized"}), 401
    
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400
    
    title = request.form.get("title", file.filename)
    metadata_json = request.form.get("metadata_json", "{}")
    
    try:
        metadata = json.loads(metadata_json)
    except json.JSONDecodeError:
        metadata = {}
    
    # Save file
    tenant_dir = DOCUMENTS_DIR / tenant["id"]
    tenant_dir.mkdir(exist_ok=True)
    
    file_content = file.read()
    file_hash = hashlib.md5(file_content).hexdigest()
    file_ext = Path(file.filename).suffix
    unique_filename = f"{file_hash}{file_ext}"
    file_path = tenant_dir / unique_filename
    
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    # Extract text
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text_content = f.read()
    except Exception as e:
        text_content = f"Error reading file: {str(e)}"
    
    # Create document
    document_id = str(uuid.uuid4())
    document = {
        "id": document_id,
        "tenant_id": tenant["id"],
        "title": title,
        "file_path": str(file_path),
        "metadata": {**metadata, "filename": file.filename, "title": title},
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    documents = get_documents()
    documents.append(document)
    save_documents(documents)
    
    # Process for RAG
    chunks = simple_text_splitter(text_content)
    metadatas = []
    ids = []
    
    for i, chunk in enumerate(chunks):
        chunk_metadata = document["metadata"].copy()
        chunk_metadata["chunk_id"] = i
        chunk_metadata["document_id"] = document_id
        
        metadatas.append(chunk_metadata)
        ids.append(f"{document_id}_chunk_{i}")
    
    # Add to vector store
    vector_store = get_vector_store(tenant["id"])
    vector_store.add(chunks, metadatas, ids)
    
    return jsonify(document), 201

@app.route("/api/v1/documents", methods=["GET"])
def list_documents():
    tenant = authenticate()
    if not tenant:
        return jsonify({"error": "Unauthorized"}), 401
    
    documents = get_documents()
    tenant_documents = [doc for doc in documents if doc["tenant_id"] == tenant["id"]]
    
    return jsonify(tenant_documents)

@app.route("/api/v1/documents/<document_id>", methods=["GET"])
def get_document(document_id):
    tenant = authenticate()
    if not tenant:
        return jsonify({"error": "Unauthorized"}), 401
    
    documents = get_documents()
    document = next((doc for doc in documents if doc["id"] == document_id and doc["tenant_id"] == tenant["id"]), None)
    
    if not document:
        return jsonify({"error": "Document not found"}), 404
    
    return jsonify(document)

@app.route("/api/v1/documents/<document_id>", methods=["DELETE"])
def delete_document(document_id):
    tenant = authenticate()
    if not tenant:
        return jsonify({"error": "Unauthorized"}), 401
    
    documents = get_documents()
    document = next((doc for doc in documents if doc["id"] == document_id and doc["tenant_id"] == tenant["id"]), None)
    
    if not document:
        return jsonify({"error": "Document not found"}), 404
    
    # Remove from documents list
    documents = [doc for doc in documents if not (doc["id"] == document_id and doc["tenant_id"] == tenant["id"])]
    save_documents(documents)
    
    # Remove from vector store
    vector_store = get_vector_store(tenant["id"])
    vector_store.delete([document_id])
    
    return "", 204

@app.route("/api/v1/chat", methods=["POST"])
def chat():
    tenant = authenticate()
    if not tenant:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    if not data or "query" not in data:
        return jsonify({"error": "Query is required"}), 400
    
    query = data["query"]
    max_documents = data.get("max_documents", 5)
    metadata_filter = data.get("metadata_filter")
    
    # Query vector store
    vector_store = get_vector_store(tenant["id"])
    results = vector_store.query(query, max_documents, metadata_filter)
    
    documents = results["documents"][0] if results["documents"] and results["documents"][0] else []
    metadatas = results["metadatas"][0] if results["metadatas"] and results["metadatas"][0] else []
    
    if not documents:
        return jsonify({
            "answer": "I don't have enough information to answer that question.",
            "sources": []
        })
    
    # Format context
    context = "\n\n".join([f"Document {i+1}:\n{doc}" for i, doc in enumerate(documents)])
    
    # Generate answer
    if OPENAI_API_KEY:
        import openai
        openai.api_key = OPENAI_API_KEY
        
        try:
            prompt = f"""
            You are a helpful AI assistant. Use the following pieces of context to answer the question at the end.
            If you don't know the answer, just say that you don't know, don't try to make up an answer.

            Context:
            {context}

            Question: {query}

            Answer:
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that answers questions based on the provided context."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            answer = response.choices[0].message["content"]
        except Exception as e:
            answer = f"Error generating response: {str(e)}"
    else:
        # Simple fallback without OpenAI
        paragraphs = context.split("\n\n")
        most_relevant = paragraphs[0] if paragraphs else context
        answer = f"Based on the available information: {most_relevant[:300]}... (Showing partial context as no LLM is available)"
    
    # Format sources
    sources = []
    for i, metadata in enumerate(metadatas):
        source = {
            "document_id": metadata.get("document_id", ""),
            "title": metadata.get("title", "Unknown"),
            "chunk_id": metadata.get("chunk_id", i)
        }
        sources.append(source)
    
    return jsonify({
        "answer": answer,
        "sources": sources
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)