# Feature: Intelligent Schedule Optimization 📅

## 🚀 Overview
This MR introduces a comprehensive **Schedule Optimization System** designed to help students plan their semester. It moves beyond simple manual entry to an **NLP-powered, intent-driven** experience, backed by a robust scoring algorithm.

## ✨ Key Changes

### 1. Data Engineering & Backend 🗄️
- **New SQLite Database**: Created `generate_schedule_db.py` to parse the UMP Curriculum PDF and generate a structured `hmu_schedules.db` (Students, Courses, Offerings, Registrations).
- **Optimizer Service**: Implemented `ScheduleOptimizerService` with a new "Human-Centric" scoring algorithm:
    - **Gap Penalty**: Penalizes idle hours (gaps) between classes to favor compact schedules.
    - **Smart Constraints**: strict enforcement of "No Monday", "Morning Only" (Periods 1-6), etc.
- **NLP Integration**: Added `schedule_extraction` prompt to convert natural language (e.g., *"xếp lịch năm 2, nghỉ thứ 2"*) into structured JSON constraints.

### 2. Frontend UI/UX 🎨
- **Refactored `ScheduleOptimizerModal`**:
    - **Smart Search**: Replaced manual text input with a **Searchable Autocomplete** dropdown connected to the backend API.
    - **Result-Driven Flow**: UI automatically switches to "Results View" after optimization, hiding configuration clutter.
    - **Improved Visualization**: Results table now shows correct **Class Codes** (e.g., `YD101_01`) and clearly distinct time blocks.

### 3. System Stability & Fixes 🛠️
- **Image Optimization (Saved ~7.7GB)**: 
    - Switched to CPU-only PyTorch and slim base images for **RAG** (9GB -> 1.5GB) and **LLM** (2GB -> 1.4GB) services.
- **Persistent Model Caching**: Added named Docker volumes (`rag_hf_cache`, `llm_hf_cache`) to persist HuggingFace downloads across container restarts.
- **Fixed CUDA OOM**: Optimized `Orchestrator` to load `CrossEncoder` model **once** globally (lazy-loaded) instead of per-request.
- **Internal Dependencies**: Fixed `ModuleNotFoundError` by mounting `services/advisor` into the LLM container.
- **Vietnamese Enforcement**: Updated system prompts to strictly enforce Vietnamese responses.

### 4. Local LLM & Networking 🌐
- **Local vLLM Integration**: Configured system to use host-side vLLM (`Qwen/Qwen2.5-7B-Instruct`) on port 8800.
- **Host Connectivity**: Resolved Docker-to-Host communication by allowing port 8800 in UFW and using the bridge gateway IP (`172.18.0.1`).
- **Resilience**: Increased LLM client timeout to 120s to handle large model response times.

## 🧪 Verification
- **Unit Tests**: Added `test_algorithm.py` verifying that:
    - Compact schedules score higher than gapped ones.
    - Hard constraints (e.g., "No Monday") are strictly respected.
- **Manual QA**: verified end-to-end flow from Chat -> NLP Extraction -> Optimization -> UI Display.

## 📸 Screenshots
*(You can add screenshots of the new modal and result table here)*

## 🔗 Related Issues
- Closes [FEAT-SCHEDULE]

## 🛡️ RAG & Infrastructure Fixes (Hotfix)
### 1. Cloudflare Login Fix 🔐
- **Issue**: Frontend used internal IP `100.64.0.25`, inaccessible via Cloudflare Tunnel.
- **Fix**: Updated `ui/vite.config.ts` and `api.ts` to use relative paths, correctly proxying requests through the tunnel.

### 2. RAG Retrieval Quality 🧠
- **Issue**: Query "điều kiện xét tuyển vào đại học y dược tphcm" returned irrelevant results.
- **Root Cause**: Large documents (UMP) were not chunked, causing embedding truncation and loss of critical admission info.
- **Fix**:
    - **Enabled Semantic Chunking**: `ingest.py` now splits docs (1000 chars, 200 overlap).
    - **Hybrid Search**: `qdrant.py` now uses **Dense (0.7) + Sparse (0.3)** weighting to capture entity names better.
    - **Re-indexed Data**: Full re-ingestion of 253 universities.
