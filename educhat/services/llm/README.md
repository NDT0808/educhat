# LLM Service

Orchestration service that coordinates prompt rendering, RAG retrieval, and LLM inference for chat requests.

## Overview

The LLM service acts as the main orchestrator, combining:
1. **Prompt Service** - Template rendering
2. **RAG Service** - Context retrieval  
3. **vLLM** - Language model inference (external)

## Features

- Chat completion API compatible with OpenAI format
- RAG-enhanced responses with citations
- Configurable LLM backend (vLLM, OpenAI, etc.)
- Request logging and error handling

## API Endpoints

### Health Check
```bash
GET /v1/health
```

### Chat Completion
```bash
POST /v1/chat
```

**Request Body:**
```json
{
  "messages": [
    {"role": "user", "content": "What are the admission requirements?"}
  ]
}
```

**Response:**
```json
{
  "answer": "The admission requirements include...",
  "citations": [
    {
      "text": "Applicants must have a high school diploma...",
      "score": 0.92,
      "metadata": {"source": "admissions_policy"}
    }
  ]
}
```

## Running Locally

```bash
cd services/llm
pip install -r requirements.txt
uvicorn src.llm.main:app --host 0.0.0.0 --port 8000
```

**Prerequisites:**
- Prompt service running on port 8001
- RAG service running on port 8002
- vLLM or OpenAI-compatible endpoint available

## Docker

```bash
docker compose -f infra/docker-compose.yml up llm
```

## Environment Variables

### Required
- `PROMPT_SERVICE_URL` - Prompt service endpoint (default: `http://prompt:8000`)
- `RAG_SERVICE_URL` - RAG service endpoint (default: `http://rag:8000`)

### LLM Configuration
- `OPENAI_API_KEY` - API key (use "dummy" for vLLM)
- `OPENAI_BASE_URL` - LLM endpoint (default: `http://host.docker.internal:8800/v1`)
- `OPENAI_MODEL` - Model name (default: `Qwen/Qwen2.5-7B-Instruct`)

## Architecture Flow

```
User Request
    ↓
1. RAG: Retrieve relevant context
    ↓
2. Prompt: Render system prompt with context
    ↓
3. vLLM: Generate response
    ↓
4. Return answer + citations
```

## External LLM Setup

### vLLM (Recommended)
Currently using external vLLM on **host:8800** with Qwen2.5-7B-Instruct model.

### OpenAI API
```bash
export OPENAI_API_KEY="sk-..."
export OPENAI_BASE_URL="https://api.openai.com/v1"
export OPENAI_MODEL="gpt-4"
```

## Dependencies

- FastAPI
- OpenAI Python client
- Requests
- Common library (shared schemas and logging)

## Error Handling

- Returns 500 with error details if RAG/Prompt/LLM fails
- Logs all errors with request context
- Graceful degradation if citations unavailable
