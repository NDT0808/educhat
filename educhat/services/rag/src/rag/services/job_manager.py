import asyncio
import uuid
import logging
from enum import Enum
from typing import Dict, Optional, List, Any
from .ingest import ingest_documents

logger = logging.getLogger("rag_service")

class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class IngestionJob:
    def __init__(self, documents: List[str], metadatas: List[Dict[str, Any]]):
        self.job_id = str(uuid.uuid4())
        self.status = JobStatus.PENDING
        self.documents = documents
        self.metadatas = metadatas
        self.result = None
        self.error = None

class JobManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(JobManager, cls).__new__(cls)
            cls._instance.jobs: Dict[str, IngestionJob] = {}
            cls._instance.lock = asyncio.Lock()
        return cls._instance

    def submit_job(self, documents: List[str], metadatas: List[Dict[str, Any]]) -> str:
        job = IngestionJob(documents, metadatas)
        self.jobs[job.job_id] = job
        return job.job_id

    def get_job(self, job_id: str) -> Optional[IngestionJob]:
        return self.jobs.get(job_id)

    async def process_job(self, job_id: str):
        job = self.jobs.get(job_id)
        if not job:
            return

        # Acquire lock to ensure only one ingestion job runs at a time
        if self.lock.locked():
            logger.info(f"Job {job_id} waiting for lock...")
        
        async with self.lock:
            try:
                logger.info(f"Starting job {job_id}")
                job.status = JobStatus.RUNNING
                
                # Run sync ingestion in thread pool to not block event loop
                loop = asyncio.get_running_loop()
                num_chunks = await loop.run_in_executor(
                    None, 
                    ingest_documents, 
                    job.documents, 
                    job.metadatas
                )
                
                job.result = {"chunks_indexed": num_chunks}
                job.status = JobStatus.COMPLETED
                logger.info(f"Job {job_id} completed successfully")
            except Exception as e:
                logger.error(f"Job {job_id} failed: {e}")
                job.error = str(e)
                job.status = JobStatus.FAILED
