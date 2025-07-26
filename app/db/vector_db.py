import os
import json
import pickle
from typing import List, Dict, Any, Optional
from uuid import UUID
from pathlib import Path
import re
from collections import Counter

# Simple in-memory vector store with basic text matching
class SimpleVectorStore:
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.documents = []
        self.metadatas = []
        self.ids = []
        self.storage_dir = Path(f"./data/vector_store/{tenant_id}")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.storage_path = self.storage_dir / "vector_store.pkl"
        self.load()
    
    def add(self, documents: List[str], metadatas: List[Dict[str, Any]], ids: List[str]):
        """Add documents to the vector store."""
        self.documents.extend(documents)
        self.metadatas.extend(metadatas)
        self.ids.extend(ids)
        self.save()
    
    def query(self, query_text: str, n_results: int = 5, 
              where: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Query the vector store using simple keyword matching."""
        if not self.documents:
            return {"documents": [[]], "metadatas": [[]], "ids": [[]], "distances": [[]]}
        
        # Preprocess query
        query_terms = self._preprocess_text(query_text)
        
        # Calculate simple relevance scores
        scores = []
        for doc in self.documents:
            doc_terms = self._preprocess_text(doc)
            score = self._calculate_similarity(query_terms, doc_terms)
            scores.append(score)
        
        # Filter by metadata if where clause is provided
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
                return {"documents": [[]], "metadatas": [[]], "ids": [[]], "distances": [[]]}
            
            # Filter results
            filtered_scores = [scores[i] for i in filtered_indices]
            filtered_documents = [self.documents[i] for i in filtered_indices]
            filtered_metadatas = [self.metadatas[i] for i in filtered_indices]
            filtered_ids = [self.ids[i] for i in filtered_indices]
            
            # Sort by score
            sorted_indices = sorted(range(len(filtered_scores)), key=lambda i: filtered_scores[i], reverse=True)[:n_results]
            
            documents = [[filtered_documents[i] for i in sorted_indices]]
            metadatas = [[filtered_metadatas[i] for i in sorted_indices]]
            ids = [[filtered_ids[i] for i in sorted_indices]]
            distances = [[1 - filtered_scores[i] for i in sorted_indices]]
        else:
            # Sort by score
            sorted_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:n_results]
            
            documents = [[self.documents[i] for i in sorted_indices]]
            metadatas = [[self.metadatas[i] for i in sorted_indices]]
            ids = [[self.ids[i] for i in sorted_indices]]
            distances = [[1 - scores[i] for i in sorted_indices]]
        
        return {
            "documents": documents,
            "metadatas": metadatas,
            "ids": ids,
            "distances": distances
        }
    
    def _preprocess_text(self, text: str) -> List[str]:
        """Simple text preprocessing."""
        # Convert to lowercase and split into words
        text = text.lower()
        # Remove punctuation and split into words
        words = re.findall(r'\w+', text)
        return words
    
    def _calculate_similarity(self, query_terms: List[str], doc_terms: List[str]) -> float:
        """Calculate simple similarity score based on term overlap."""
        if not query_terms or not doc_terms:
            return 0.0
        
        # Count term frequencies
        query_counter = Counter(query_terms)
        doc_counter = Counter(doc_terms)
        
        # Calculate overlap
        common_terms = set(query_counter.keys()) & set(doc_counter.keys())
        if not common_terms:
            return 0.0
        
        # Simple score based on term overlap
        overlap_score = sum(min(query_counter[term], doc_counter[term]) for term in common_terms)
        max_possible = sum(query_counter.values())
        
        return overlap_score / max_possible if max_possible > 0 else 0.0
    
    def delete(self, ids: List[str]):
        """Delete documents from the vector store."""
        indices_to_delete = [i for i, doc_id in enumerate(self.ids) if doc_id in ids]
        
        # Create new lists without the deleted items
        self.documents = [doc for i, doc in enumerate(self.documents) if i not in indices_to_delete]
        self.metadatas = [meta for i, meta in enumerate(self.metadatas) if i not in indices_to_delete]
        self.ids = [doc_id for i, doc_id in enumerate(self.ids) if i not in indices_to_delete]
        
        self.save()
    
    def save(self):
        """Save the vector store to disk."""
        data = {
            "documents": self.documents,
            "metadatas": self.metadatas,
            "ids": self.ids
        }
        with open(self.storage_path, "wb") as f:
            pickle.dump(data, f)
    
    def load(self):
        """Load the vector store from disk."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "rb") as f:
                    data = pickle.load(f)
                self.documents = data.get("documents", [])
                self.metadatas = data.get("metadatas", [])
                self.ids = data.get("ids", [])
            except Exception as e:
                print(f"Error loading vector store: {e}")

# Dictionary to store vector stores by tenant ID
vector_stores = {}

def get_tenant_collection(tenant_id: UUID):
    """Get or create a collection for a tenant."""
    tenant_id_str = str(tenant_id)
    if tenant_id_str not in vector_stores:
        vector_stores[tenant_id_str] = SimpleVectorStore(tenant_id_str)
    return vector_stores[tenant_id_str]

def add_documents(
    tenant_id: UUID,
    texts: List[str],
    metadatas: List[Dict[str, Any]],
    ids: List[str]
):
    """Add documents to a tenant's collection."""
    collection = get_tenant_collection(tenant_id)
    
    # Add documents to collection
    collection.add(
        documents=texts,
        metadatas=metadatas,
        ids=ids
    )
    
    return len(texts)

def query_documents(
    tenant_id: UUID,
    query_text: str,
    n_results: int = 5,
    metadata_filter: Optional[Dict[str, Any]] = None
):
    """Query documents from a tenant's collection."""
    collection = get_tenant_collection(tenant_id)
    
    # Query the collection
    results = collection.query(
        query_text=query_text,
        n_results=n_results,
        where=metadata_filter
    )
    
    return results

def delete_document(tenant_id: UUID, document_id: str):
    """Delete a document from a tenant's collection."""
    collection = get_tenant_collection(tenant_id)
    collection.delete(ids=[document_id])
    
def delete_tenant_collection(tenant_id: UUID):
    """Delete a tenant's entire collection."""
    tenant_id_str = str(tenant_id)
    if tenant_id_str in vector_stores:
        del vector_stores[tenant_id_str]
    
    # Delete the file
    storage_path = Path(f"./data/vector_store/{tenant_id_str}/vector_store.pkl")
    if storage_path.exists():
        storage_path.unlink()
    
    return True