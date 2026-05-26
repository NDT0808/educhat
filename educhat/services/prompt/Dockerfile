FROM python:3.11-slim

WORKDIR /app

COPY ./services/prompt/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY ./libs /app/libs
RUN pip install -e /app/libs/common

COPY ./services/prompt /app/services/prompt
ENV PYTHONPATH=/app

CMD ["uvicorn", "services.prompt.src.prompt.main:app", "--host", "0.0.0.0", "--port", "8000"]
