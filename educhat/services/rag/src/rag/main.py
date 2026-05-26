from fastapi import FastAPI, HTTPException
from common.schemas import IngestRequest, RetrieveRequest, RetrievalResult, ChunkMetadata
from common.logging import setup_logger
from common.middleware import RequestIDMiddleware
from common.auth import verify_internal_token
from fastapi import Depends
from .services.ingest import ingest_documents, dense_model, sparse_model
from .storage.qdrant import search_hybrid_vectors

logger = setup_logger("rag_service")

app = FastAPI(title="RAG Service")
app.add_middleware(RequestIDMiddleware)

# Prometheus Metrics
from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app)

from .services.job_manager import JobManager
from fastapi import BackgroundTasks

@app.post("/v1/ingest", dependencies=[Depends(verify_internal_token)])
async def ingest(request: IngestRequest, background_tasks: BackgroundTasks):
    logger.info(f"Received ingestion request for {len(request.documents)} documents")
    metadatas = request.metadatas or [{"source": request.source}] * len(request.documents)
    
    job_manager = JobManager()
    job_id = job_manager.submit_job(request.documents, metadatas)
    
    # Process in background
    background_tasks.add_task(job_manager.process_job, job_id)
    
    return {"message": "Ingestion job submitted", "job_id": job_id}

@app.get("/v1/jobs/{job_id}", dependencies=[Depends(verify_internal_token)])
async def get_job_status(job_id: str):
    job_manager = JobManager()
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "job_id": job.job_id,
        "status": job.status,
        "result": job.result,
        "error": job.error
    }

@app.post("/v1/index")
async def index():
    # No-op in this design as we index on ingest, but kept for API contract compatibility
    return {"message": "Indexing triggered (no-op)"}

@app.get("/v1/retrieve", dependencies=[Depends(verify_internal_token)])
async def retrieve(query: str, top_k: int = 5):
    try:
        # Dense embedding (bkai model doesn't need 'query: ' prefix)
        dense_vector = dense_model.encode(query, normalize_embeddings=True).tolist()
        
        # Sparse embedding
        sparse_gen = sparse_model.embed([query])
        sparse_vec_result = list(sparse_gen)[0]
        
        sparse_vector = {
            "indices": sparse_vec_result.indices.tolist(),
            "values": sparse_vec_result.values.tolist()
        }
        
        results = search_hybrid_vectors(dense_vector, sparse_vector, top_k=top_k)
        
        response = []
        for res in results:
            content = res.payload.get("content", "")
            # Append tables content if available, to ensure LLM sees it
            tables = res.payload.get("tables", "")
            if tables:
                content += f"\n\nTHÔNG TIN TUYỂN SINH CHI TIẾT:\n{tables}"
            
            # Return flexible dict structure instead of strict Pydantic validation
            response.append({
                "content": content,
                "metadata": res.payload,  # Return entire payload as metadata
                "score": res.score
            })
        return response
    except Exception as e:
        logger.error(f"Retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/health")
async def health():
    return {"status": "ok"}
