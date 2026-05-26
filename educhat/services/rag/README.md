# RAG Service

Retrieval-Augmented Generation service for document ingestion and semantic search using Qdrant and SentenceTransformers.

## Overview

The RAG service handles document ingestion, chunking, embedding, and retrieval. It uses Qdrant as the vector database and SentenceTransformers for generating embeddings.

## Features

- Document ingestion with automatic chunking
- Vector embeddings using `all-MiniLM-L6-v2`
- Semantic search with similarity scoring
- Metadata support for filtering

## API Endpoints

### Health Check
```bash
GET /v1/health
```

### Ingest Documents
```bash
POST /v1/ingest
```

**Request Body:**
```json
{
  "source": "university_website",
  "documents": [
    "The admissions deadline is March 15th.",
    "Tuition for undergraduate programs is $50,000 per year."
  ],
  "metadatas": [
    {"source": "admissions", "doc_id": "001"},
    {"source": "finance", "doc_id": "002"}
  ]
}
```

**Response:**
```json
{
  "message": "Ingestion complete",
  "chunks_indexed": 2
}
```

### Retrieve Documents
```bash
GET /v1/retrieve?query=admissions+deadline&top_k=5
```

**Response:**
```json
[
  {
    "text": "The admissions deadline is March 15th.",
    "score": 0.85,
    "metadata": {"source": "admissions", "doc_id": "001"}
  }
]
```

## Running Locally

```bash
cd services/rag
pip install -r requirements.txt
uvicorn src.rag.main:app --host 0.0.0.0 --port 8000
```

**Note:** Requires Qdrant running on `localhost:6333`

## Docker

```bash
docker compose -f infra/docker-compose.yml up qdrant rag
```

## Environment Variables

- `PORT` - Server port (default: 8000)
- `QDRANT_HOST` - Qdrant host (default: localhost)
- `QDRANT_PORT` - Qdrant port (default: 6333)

## Architecture

1. **Ingestion Pipeline:**
   - Receive documents → Chunk text (500 chars, 50 overlap) → Generate embeddings → Store in Qdrant

2. **Retrieval Pipeline:**
   - Query → Generate query embedding → Search Qdrant → Return top-k results with scores

## Dependencies

- FastAPI
- Qdrant client (>=1.7.3)
- Sentence-Transformers
- Common library (shared schemas and logging)

## Collection

- **Name:** `documents`
- **Vector Size:** 384 (MiniLM dimensions)
- **Distance:** Cosine similarity
