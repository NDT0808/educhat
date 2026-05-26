import os
from qdrant_client import QdrantClient
from qdrant_client.http import models
from common.logging import setup_logger

logger = setup_logger("qdrant_storage")

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
COLLECTION_NAME = "universities_hybrid"

# Disable version check for compatibility
client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

class ResultObj:
    def __init__(self, payload, score):
        self.payload = payload
        self.score = score

def ensure_collection(dense_size: int = 768):
    try:
        client.get_collection(COLLECTION_NAME)
        logger.info(f"Collection {COLLECTION_NAME} exists.")
    except Exception:
        logger.info(f"Creating collection {COLLECTION_NAME}.")
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config={
                "dense": models.VectorParams(
                    size=dense_size,
                    distance=models.Distance.COSINE,
                )
            },
            sparse_vectors_config={
                "sparse": models.SparseVectorParams(
                    index=models.SparseIndexParams(),
                )
            },
        )

def upsert_vectors(points):
    try:
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )
    except Exception as e:
        logger.error(f"Failed to upsert vectors: {e}")
        raise

def search_vectors(vector, top_k=5, filters=None):
    """Legacy pure dense search - mapped to 'dense' vector"""
    try:
        results = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=("dense", vector),
            limit=top_k,
            query_filter=filters,
            with_payload=True,
        )
        return results
    except Exception as e:
        logger.error(f"Failed to search vectors: {e}")
        return []

def search_hybrid_vectors(dense_vector, sparse_vector, top_k=5, dense_weight=0.7, sparse_weight=0.3, filters=None):
    """Hybrid search using both dense and sparse vectors"""
    try:
        # We'll use manual fusion if RRF is not supported or for more control
        # But let's try the modern query_points with Prefetch for RRF if available
        try:
            search_result = client.query_points(
                collection_name=COLLECTION_NAME,
                prefetch=[
                    models.Prefetch(query=dense_vector, using="dense", limit=top_k * 2),
                    models.Prefetch(
                        query=models.SparseVector(
                            indices=sparse_vector["indices"],
                            values=sparse_vector["values"]
                        ), 
                        using="sparse", 
                        limit=top_k * 2
                    ),
                ],
                query=models.FusionQuery(fusion=models.Fusion.RRF),
                limit=top_k,
                query_filter=filters,
                with_payload=True,
            )
            return [ResultObj(res.payload, res.score) for res in search_result.points]
        except Exception as e:
            logger.warning(f"RRF search failed, falling back to dense-only: {e}")
            # Fallback to dense only
            search_result = client.query_points(
                collection_name=COLLECTION_NAME,
                query=dense_vector,
                using="dense",
                limit=top_k,
                query_filter=filters,
                with_payload=True,
            )
            return [ResultObj(res.payload, res.score) for res in search_result.points]
            
    except Exception as e:
        logger.error(f"Failed to search hybrid vectors: {e}")
        return []
