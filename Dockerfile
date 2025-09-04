FROM python:3.11-slim

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \    build-essential \    default-libmysqlclient-dev \    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
ENV PYTHONPATH=/app/src
COPY .env ./.env

EXPOSE 8000
CMD ["uvicorn", "ragnet.api:app", "--host", "0.0.0.0", "--port", "8000"]
