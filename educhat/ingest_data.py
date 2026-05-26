#!/usr/bin/env python3
"""
Script to ingest all_universities.json into Qdrant via RAG service.
Ingests in batches to avoid timeout.
"""
import json
import requests
import time

RAG_URL = "http://localhost:8002"
BATCH_SIZE = 10  # Ingest 10 universities at a time

def main():
    # Load data
    with open('all_universities.json', 'r') as f:
        universities = json.load(f)
    
    print(f"Loaded {len(universities)} universities")
    
    total_chunks = 0
    failed = []
    
    # Process in batches
    for i in range(0, len(universities), BATCH_SIZE):
        batch = universities[i:i+BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1
        total_batches = (len(universities) + BATCH_SIZE - 1) // BATCH_SIZE
        
        documents = []
        metadatas = []
        
        for uni in batch:
            content = uni.get('content', '')
            if not content.strip():
                continue
                
            documents.append(content)
            metadatas.append({
                'name': uni.get('name', ''),
                'url': uni.get('url', ''),
                'region': uni.get('region', ''),
                'tables': uni.get('tables', '')  # Include tables if available
            })
        
        if not documents:
            continue
            
        payload = {
            'source': 'universities',
            'documents': documents,
            'metadatas': metadatas
        }
        
        print(f"Batch {batch_num}/{total_batches}: Ingesting {len(documents)} docs...", end=" ")
        
        try:
            headers = {
                "X-Internal-Token": "internal_secret_key_change_me"
            }
            resp = requests.post(
                f'{RAG_URL}/v1/ingest',
                json=payload,
                headers=headers,
                timeout=120
            )
            
            if resp.status_code == 200:
                result = resp.json()
                job_id = result.get('job_id')
                print(f"Job {job_id} submitted...", end=" ", flush=True)
                
                # Poll for completion
                while True:
                    time.sleep(1)
                    job_resp = requests.get(
                        f'{RAG_URL}/v1/jobs/{job_id}',
                        headers=headers,
                        timeout=30
                    )
                    
                    if job_resp.status_code != 200:
                        print(f"✗ Job status error: {job_resp.status_code}")
                        failed.append(batch_num)
                        break
                        
                    job_data = job_resp.json()
                    status = job_data.get('status')
                    
                    if status == "completed":
                        chunks = job_data.get('result', {}).get('chunks_indexed', 0)
                        total_chunks += chunks
                        print(f"✓ {chunks} chunks")
                        break
                    elif status == "failed":
                        error = job_data.get('error')
                        print(f"✗ Failed: {error}")
                        failed.append(batch_num)
                        break
                    # If pending or running, continue polling
            else:
                print(f"✗ Error: {resp.status_code}")
                failed.append(batch_num)
                
        except requests.exceptions.Timeout:
            print("✗ Timeout")
            failed.append(batch_num)
        except Exception as e:
            print(f"✗ {e}")
            failed.append(batch_num)
        
        # Small delay between batches
        time.sleep(0.5)
    
    print(f"\n{'='*50}")
    print(f"Ingestion complete!")
    print(f"Total chunks indexed: {total_chunks}")
    if failed:
        print(f"Failed batches: {failed}")
    else:
        print("All batches succeeded!")

if __name__ == "__main__":
    main()
