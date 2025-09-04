# RagNet

A lightweight, horizontally-scalable RAG microservice. This is **Step 1 (Repo Setup)** of the implementation plan.

## Features (Step 1)
- FastAPI service with `/healthz`, `/ready`, `/ingest` (stub), `/query` (stub)
- Dockerized with `docker-compose.yml` (API + MySQL + Redis + Chroma)
- Config via `configs/config.yaml` (example provided)
- Basic tests

## Quickstart

### 1) Clone & configure
```bash
cp configs/config.yaml.example configs/config.yaml
cp .env.example .env
```

### 2) Run with Docker
```bash
docker compose up -d --build
# Check health
curl http://localhost:8000/healthz
curl http://localhost:8000/ready
```

### 3) Local dev (optional)
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn ragnet.api:app --reload --host 0.0.0.0 --port 8000
```

## Endpoints
- `GET /healthz` — liveness
- `GET /ready` — checks dependent services (MySQL, Redis, Chroma) are reachable
- `POST /ingest` — stub for folder-based ingestion (will be implemented in Step 4)
- `POST /query` — stub for query flow (will be implemented in Step 5)

## References
- FastAPI docs: https://fastapi.tiangolo.com/
- Uvicorn: https://www.uvicorn.org/
- Docker best practices: https://docs.docker.com/develop/develop-images/dockerfile_best-practices/
- Docker Compose: https://docs.docker.com/compose/
- Chroma: https://docs.trychroma.com/
- Redis: https://redis.io/docs/latest/
- MySQL: https://dev.mysql.com/doc/
