# Edu Agent - AI University Admissions Assistant

> 🎓 Hệ thống chatbot tư vấn tuyển sinh đại học sử dụng RAG và LLM

## 📋 Tổng Quan

Edu Agent là một hệ thống AI hỗ trợ tư vấn tuyển sinh đại học, được xây dựng theo kiến trúc microservices với các thành phần:

- **RAG (Retrieval-Augmented Generation)**: Tìm kiếm và trích xuất thông tin từ cơ sở dữ liệu
- **LLM (Large Language Model)**: Xử lý ngôn ngữ tự nhiên và tạo câu trả lời
- **Vector Database (Qdrant)**: Lưu trữ và tìm kiếm ngữ nghĩa

## 🏗️ Kiến Trúc Hệ Thống

```
┌─────────────────────────────────────────────────────────────┐
│                    External Services (Host)                 │
├─────────────────────────────────────────────────────────────┤
│  vLLM (8800)              │  Chandra OCR (8099)             │
│  Qwen2.5-32B-AWQ          │  datalab-to/chandra             │
└─────────────────────────────────────────────────────────────┘
                               ▲
                               │
┌──────────────────────────────┼──────────────────────────────┐
│               Docker Services (Backend)                     │
├─────────────────────────────────────────────────────────────┤
│  Qdrant (6333)   │  Prompt (8001)   │  RAG (8002)           │
│  Vector DB       │  Templates       │  Ingestion/Search     │
├─────────────────────────────────────────────────────────────┤
│                   LLM Service (8004)                        │
│                   Orchestrator chính                        │
└─────────────────────────────────────────────────────────────┘
                               ▲
                               │
                    UI (React/Vite - Port 3000)
```

## 📁 Cấu Trúc Dự Án

```
Edu Agent/
├── services/
│   ├── llm/             # LLM Orchestrator Service
│   ├── rag/             # RAG Service (ingestion, retrieval)
│   └── prompt/          # Prompt Template Service
├── libs/
│   └── common/          # Shared schemas và utilities
├── infra/
│   └── docker-compose.yml
├── ui/                  # Frontend React/Vite
└── .env.example         # Environment variables template
```

---

## 🚀 Hướng Dẫn Deploy

### Yêu Cầu Hệ Thống

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 4 cores | 8+ cores |
| RAM | 16GB | 32GB+ |
| GPU | 1x RTX 3090 | 2x RTX 4090 |
| Storage | 50GB SSD | 100GB NVMe |
| Docker | 20.10+ | Latest |

### Bước 1: Clone Repository

```bash
git clone <repository-url>
cd Edu Agent
```

### Bước 2: Cấu Hình Environment

```bash
# Copy file mẫu
cp .env.example .env

# Chỉnh sửa các biến môi trường
nano .env
```

**Nội dung `.env`:**
```bash
# HuggingFace Token (bắt buộc cho vLLM)
HF_TOKEN=hf_your_token_here

# LLM Configuration
OPENAI_BASE_URL=http://host.docker.internal:8800/v1
OPENAI_MODEL=Qwen/Qwen2.5-32B-Instruct-AWQ
OPENAI_API_KEY=dummy

# RAG Configuration
QDRANT_HOST=qdrant
QDRANT_PORT=6333
```

### Bước 3: Khởi Động External Services

#### 3.1 vLLM (LLM Engine)

```bash
docker run -d --name vllm-qwen \
  --gpus '"device=0,1"' \
  --ipc=host \
  -p 8800:8000 \
  -e HF_TOKEN=${HF_TOKEN} \
  vllm/vllm-openai:v0.11.0 \
  --model Qwen/Qwen2.5-32B-Instruct-AWQ \
  --tensor-parallel-size 2 \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.9
```

**Kiểm tra vLLM:**
```bash
curl http://localhost:8800/v1/models
```

#### 3.2 Chandra OCR (Optional)

```bash
docker run -d --name chandra-ocr \
  --gpus device=2 \
  --ipc=host \
  -p 8099:8000 \
  -e HF_TOKEN=${HF_TOKEN} \
  vllm/vllm-openai:v0.11.0 \
  --model datalab-to/chandra \
  --served-model-name chandra \
  --max-model-len 8192
```

### Bước 4: Khởi Động Backend Services

```bash
# Build và start tất cả services
cd infra
docker compose up -d --build

# Xem logs
docker compose logs -f
```

**Kiểm tra services:**
```bash
# Health check tất cả services
curl http://localhost:8001/v1/health  # Prompt
curl http://localhost:8002/v1/health  # RAG
curl http://localhost:8004/v1/health  # LLM
curl http://localhost:6333/health     # Qdrant
```

### Bước 5: Khởi Động Frontend

```bash
cd ui

# Cài đặt dependencies
pnpm install

# Development mode
pnpm dev

# Hoặc build production
pnpm build
pnpm preview
```

Frontend sẽ chạy tại: `http://localhost:3000`

---

## 💻 Development Setup (Miniconda3)

Hướng dẫn chạy các services locally cho development sử dụng Miniconda3.

### Cài Đặt Miniconda3

```bash
# Download và cài đặt Miniconda3
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh

# Khởi động lại terminal hoặc
source ~/.bashrc
```

### Tạo Môi Trường Conda

```bash
# Tạo môi trường mới với Python 3.11
conda create -n Edu Agent python=3.11 -y

# Kích hoạt môi trường
conda activate Edu Agent
```

### Cài Đặt Common Library

```bash
cd libs/common
pip install -e .
cd ../..
```

### Khởi Động Qdrant (Docker)

```bash
docker run -d --name qdrant \
  -p 6333:6333 \
  -v qdrant_data:/qdrant/storage \
  qdrant/qdrant:v1.7.4
```

### Chạy Các Services

Mở 3 terminal riêng biệt, mỗi terminal activate môi trường conda:

**Terminal 1 - Prompt Service (Port 8001):**
```bash
conda activate Edu Agent
cd services/prompt
pip install -r requirements.txt
uvicorn src.prompt.main:app --reload --port 8001
```

**Terminal 2 - RAG Service (Port 8002):**
```bash
conda activate Edu Agent
cd services/rag
pip install -r requirements.txt

# Set environment variables
export QDRANT_HOST=localhost
export QDRANT_PORT=6333

uvicorn src.rag.main:app --reload --port 8002
```

**Terminal 3 - LLM Service (Port 8004):**
```bash
conda activate Edu Agent
cd services/llm
pip install -r requirements.txt

# Set environment variables
export PROMPT_SERVICE_URL=http://localhost:8001
export RAG_SERVICE_URL=http://localhost:8002
export OPENAI_BASE_URL=http://localhost:8800/v1
export OPENAI_MODEL=Qwen/Qwen2.5-32B-Instruct-AWQ
export OPENAI_API_KEY=dummy

uvicorn src.llm.main:app --reload --port 8004
```

**Terminal 4 - Frontend (Port 3000):**
```bash
cd ui
pnpm install
pnpm dev
```

### Script Tiện Ích

Tạo file `dev-run.sh` để khởi động nhanh:

```bash
#!/bin/bash
# dev-run.sh - Chạy service cụ thể

SERVICE=$1
conda activate Edu Agent

case $SERVICE in
  prompt)
    cd services/prompt && uvicorn src.prompt.main:app --reload --port 8001
    ;;
  rag)
    export QDRANT_HOST=localhost QDRANT_PORT=6333
    cd services/rag && uvicorn src.rag.main:app --reload --port 8002
    ;;
  llm)
    export PROMPT_SERVICE_URL=http://localhost:8001
    export RAG_SERVICE_URL=http://localhost:8002
    export OPENAI_BASE_URL=http://localhost:8800/v1
    export OPENAI_MODEL=Qwen/Qwen2.5-32B-Instruct-AWQ
    export OPENAI_API_KEY=dummy
    cd services/llm && uvicorn src.llm.main:app --reload --port 8004
    ;;
  ui)
    cd ui && pnpm dev
    ;;
  *)
    echo "Usage: ./dev-run.sh [prompt|rag|llm|ui]"
    ;;
esac
```

```bash
chmod +x dev-run.sh
./dev-run.sh rag
```

### Cập Nhật Dependencies

```bash
conda activate Edu Agent

# Cập nhật tất cả services
pip install -r services/prompt/requirements.txt
pip install -r services/rag/requirements.txt
pip install -r services/llm/requirements.txt
```

---

## 🔧 Production Deployment

### Docker Compose Production

Tạo file `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  qdrant:
    image: qdrant/qdrant:v1.7.4
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage
    restart: always
    deploy:
      resources:
        limits:
          memory: 4G

  prompt:
    build:
      context: ..
      dockerfile: services/prompt/Dockerfile
    ports:
      - "8001:8000"
    restart: always
    environment:
      - PORT=8000

  rag:
    build:
      context: ..
      dockerfile: services/rag/Dockerfile
    ports:
      - "8002:8000"
    depends_on:
      - qdrant
    restart: always
    environment:
      - PORT=8000
      - QDRANT_HOST=qdrant
      - QDRANT_PORT=6333

  llm:
    build:
      context: ..
      dockerfile: services/llm/Dockerfile
    ports:
      - "8004:8000"
    depends_on:
      - prompt
      - rag
    restart: always
    environment:
      - PORT=8000
      - PROMPT_SERVICE_URL=http://prompt:8000
      - RAG_SERVICE_URL=http://rag:8000
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - OPENAI_BASE_URL=${OPENAI_BASE_URL}
      - OPENAI_MODEL=${OPENAI_MODEL}
    extra_hosts:
      - "host.docker.internal:host-gateway"

volumes:
  qdrant_data:
```

### Nginx Reverse Proxy

```nginx
# /etc/nginx/sites-available/Edu Agent
server {
    listen 80;
    server_name Edu Agent.yourdomain.com;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # API
    location /api/ {
        proxy_pass http://localhost:8004/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 300s;
    }
}
```

### SSL với Certbot

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d Edu Agent.yourdomain.com
```

---

## 📊 Data Ingestion

### Ingest University Data

```bash
# Chuẩn bị file all_universities.json
# Format: [{"name": "...", "content": "...", "metadata": {...}}, ...]

# Gọi API ingest
curl -X POST http://localhost:8002/v1/ingest \
  -H "Content-Type: application/json" \
  -d @all_universities.json
```

### Verify Data

```bash
# Kiểm tra số lượng documents
curl http://localhost:6333/collections/universities

# Test search
curl "http://localhost:8002/v1/retrieve?query=đại%20học%20bách%20khoa&top_k=5"
```

---

## 🧪 Testing

### API Testing

```bash
# Test chat API
curl -X POST http://localhost:8004/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Điểm chuẩn đại học Bách Khoa năm 2024?"}
    ]
  }'
```

### Health Check Script

```bash
#!/bin/bash
services=("8001:Prompt" "8002:RAG" "8004:LLM" "6333:Qdrant")

for svc in "${services[@]}"; do
  port=${svc%%:*}
  name=${svc##*:}
  if curl -s "http://localhost:$port/v1/health" > /dev/null 2>&1; then
    echo "✅ $name (port $port): OK"
  else
    echo "❌ $name (port $port): FAILED"
  fi
done
```

---

## 🔍 Monitoring & Logs

### Xem Logs

```bash
# Tất cả services
docker compose -f infra/docker-compose.yml logs -f

# Service cụ thể
docker compose -f infra/docker-compose.yml logs -f llm
docker compose -f infra/docker-compose.yml logs -f rag
```

### Service Status

```bash
docker compose -f infra/docker-compose.yml ps
```

---

## ❗ Troubleshooting

### Lỗi Thường Gặp

| Lỗi | Nguyên Nhân | Giải Pháp |
|-----|-------------|-----------|
| `Connection refused 8800` | vLLM chưa khởi động | Kiểm tra `docker logs vllm-qwen` |
| `Qdrant connection failed` | Qdrant chưa sẵn sàng | Đợi 10-15s sau khi start |
| `CUDA out of memory` | Không đủ VRAM | Giảm `--max-model-len` hoặc dùng model nhỏ hơn |
| `Port already in use` | Port bị chiếm | `lsof -i :PORT` và kill process |

### Reset Dữ Liệu

```bash
# Xóa Qdrant data
docker compose -f infra/docker-compose.yml down -v

# Rebuild tất cả
docker compose -f infra/docker-compose.yml up -d --build --force-recreate
```

---

## 📚 Tech Stack

- **Backend**: Python 3.11, FastAPI, Uvicorn
- **Vector Store**: Qdrant
- **Embeddings**: bkai-foundation-models/vietnamese-bi-encoder
- **LLM**: vLLM + Qwen2.5-32B-Instruct-AWQ
- **OCR**: datalab-to/chandra
- **Frontend**: React 18, Vite, TypeScript, TailwindCSS

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.
