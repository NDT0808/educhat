# 🎓 EduChat: Personalized AI Virtual Assistant for Students

![Python](https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python)
![RAG](https://img.shields.io/badge/RAG-Retrieval_Augmented_Generation-orange?style=for-the-badge)
![Qdrant](https://img.shields.io/badge/Qdrant-Vector_DB-red?style=for-the-badge)
![Docker](https://img.shields.io/badge/Docker-Containerized-blue?style=for-the-badge&logo=docker)

EduChat is a state-funded university research project designed to bridge the gap between academic curriculum data and personalized student assistance. By leveraging **Retrieval-Augmented Generation (RAG)** and **Natural Language Processing (NLP)**, EduChat provides context-aware, 24/7 academic support for students.

<img width="1916" height="907" alt="Educhat_img" src="https://github.com/user-attachments/assets/36efea3c-d66f-4b6f-a153-6b91a9258dc9" />

## 🌟 Key Features

* **Context-Aware RAG:** Integrates a custom vector database (Qdrant) to retrieve and synthesize information from complex university curriculum PDFs and academic documents.
* **Emotion Analysis:** Utilizes fine-tuned **PhoBERT** models to detect student sentiment, allowing the assistant to provide empathetic and tailored academic support.
* **Intelligent OCR Pipeline:** Automated document parsing to ingest and structure unstructured curriculum data from physical scans and PDFs.
* **Smart Optimizer:** Built-in tools for schedule optimization and registration parsing using advanced Prompt Engineering and LLM orchestration.

## 🛠️ Technology Stack

* **AI/NLP:** PhoBERT, RAG (Retrieval-Augmented Generation), LLM Orchestration
* **Databases:** Qdrant (Vector DB), SQLite (SGU Schedules)
* **OCR:** Custom pipeline for academic curriculum parsing
* **Frontend:** React, TypeScript, Tailwind CSS
* **Infrastructure:** Docker, Python (FastAPI/Flask integration)

## 📁 Project Structure

```text
educhat/
├── services/
│   ├── advisor/      # Student advisor & scheduler logic
│   ├── llm/          # LLM routers (OCR, Emotion, Intent)
│   └── rag/          # Qdrant Vector store & Ingestion pipeline
├── ui/               # React-based Frontend
├── scripts/          # Ingestion & verification tools
└── OCR/              # Academic curriculum parsing pipeline
```

## 🚀 Research & Development
Principal Investigator: Nguyen Duc Trong (Project Code: SVC2025-162)

Funding: University-funded research grant (5,000,000 VND).

Focus: Commercializing AI solutions for the education sector through sentiment-aware assistants.

## ⚙️ Installation & Setup
1. Clone the repository

```text

git clone [https://github.com/NDT0808/educhat.git](https://github.com/NDT0808/educhat.git)
cd educhat

2. Start Services (Docker)

cd infra
docker-compose up -d


3. Ingest Academic Data

Bash
python ingest_data.py --source ./data/curriculum.pdf

```
## 🧠 System Architecture Highlights
EduChat employs a microservices architecture where the LLM router acts as an orchestrator, dispatching tasks between the RAG service (for knowledge retrieval) and the Emotion service (for student sentiment analysis), ensuring a seamless and human-like interaction experience.

Created by NDT0808. Focused on AI Engineering and Intelligent Education Systems.


