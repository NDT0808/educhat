FROM python:3.11-slim

WORKDIR /app

# Install PyTorch CPU-only first (prevents sentence-transformers from pulling full PyTorch)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

COPY ./services/llm/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY ./libs /app/libs
RUN pip install -e /app/libs/common

COPY ./services/llm /app/services/llm
COPY ./services/advisor /app/services/advisor
ENV PYTHONPATH=/app

CMD ["uvicorn", "services.llm.src.llm.main:app", "--host", "0.0.0.0", "--port", "8000"]
