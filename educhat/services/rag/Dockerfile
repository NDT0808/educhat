FROM python:3.11-slim

WORKDIR /app

# Install PyTorch CPU-only (much smaller than CUDA version)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

COPY ./services/rag/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY ./libs /app/libs
RUN pip install -e /app/libs/common

COPY ./services/rag /app/services/rag
ENV PYTHONPATH=/app

CMD ["uvicorn", "services.rag.src.rag.main:app", "--host", "0.0.0.0", "--port", "8000"]
