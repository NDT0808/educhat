# Prompt Service

Template rendering service for chat prompts using Jinja2.

## Overview

The Prompt service manages prompt templates and renders them with dynamic variables. It provides a centralized way to manage and version control prompt templates used across the EduChat system.

## API Endpoints

### Health Check
```bash
GET /v1/health
```

### Get Prompt Template
```bash
GET /v1/prompts/{template_name}
```

**Example:**
```bash
curl http://localhost:8001/v1/prompts/chat_default
```

### Create Prompt Template
```bash
POST /v1/prompts
```

**Request Body:**
```json
{
  "name": "chat_default",
  "template": "You are a helpful assistant.\n\nContext:\n{{ context }}\n\nQuestion: {{ question }}"
}
```

### Render Prompt
```bash
POST /v1/render
```

**Request Body:**
```json
{
  "template_name": "chat_default",
  "variables": {
    "context": "Paris is the capital of France",
    "question": "What is the capital of France?"
  }
}
```

**Response:**
```json
{
  "rendered_prompt": "You are a helpful assistant....."
}
```

## Running Locally

```bash
cd services/prompt
pip install -r requirements.txt
uvicorn src.prompt.main:app --host 0.0.0.0 --port 8000
```

## Docker

```bash
docker compose -f infra/docker-compose.yml up prompt
```

## Environment Variables

- `PORT` - Server port (default: 8000)

## Dependencies

- FastAPI
- Uvicorn
- Jinja2
- Common library (shared schemas and logging)
