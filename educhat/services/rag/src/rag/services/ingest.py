from sentence_transformers import SentenceTransformer
from fastembed import SparseTextEmbedding
import hashlib
import uuid
from typing import List, Dict, Any
import numpy as np
from common.schemas import ChunkMetadata
from ..storage.qdrant import upsert_vectors, ensure_collection
from qdrant_client.http import models

# Load models
# Use AITeamVN/Vietnamese_Embedding (fine-tuned BGE-M3, 1024 dimensions)
DENSE_MODEL_NAME = "AITeamVN/Vietnamese_Embedding"
SPARSE_MODEL_NAME = "Qdrant/bm25"

print(f"Loading dense model: {DENSE_MODEL_NAME}...")
dense_model = SentenceTransformer(DENSE_MODEL_NAME)
print(f"Embedding dimension: {dense_model.get_sentence_embedding_dimension()}")

print(f"Loading sparse model: {SPARSE_MODEL_NAME}...")
sparse_model = SparseTextEmbedding(model_name=SPARSE_MODEL_NAME)

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    # Simple character based chunking for now
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks

def ingest_documents(documents: List[str], metadatas: List[Dict[str, Any]]):
    ensure_collection(dense_size=dense_model.get_sentence_embedding_dimension())
    
    points = []
    for doc, meta in zip(documents, metadatas):
        # Enable chunking with reasonable size for Vietnamese text
        chunks = chunk_text(doc, chunk_size=1000, overlap=200)
        
        # Batch embedding
        dense_embeddings = dense_model.encode(chunks)
        sparse_embeddings = list(sparse_model.embed(chunks))
        
        for i, (chunk, dense_emb, sparse_emb) in enumerate(zip(chunks, dense_embeddings, sparse_embeddings)):
            # Generate deterministic ID based on content
            content_hash = hashlib.md5(chunk.encode("utf-8")).hexdigest()
            chunk_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, content_hash))  # Use a namespace for uniqueness
            
            payload = meta.copy()
            payload["content"] = chunk
            payload["chunk_id"] = chunk_id
            payload["chunk_index"] = i
            
            # Prepare sparse vector
            sparse_vec = models.SparseVector(
                indices=sparse_emb.indices.tolist(),
                values=sparse_emb.values.tolist()
            )
            
            points.append(models.PointStruct(
                id=chunk_id,
                vector={
                    "dense": dense_emb.tolist(),
                    "sparse": sparse_vec
                },
                payload=payload
            ))
            
    if points:
        upsert_vectors(points)
    return len(points)
