# RAG Pipeline

A Retrieval-Augmented Generation system that lets users upload documents and ask questions answered strictly from their content. Documents are parsed, chunked, embedded, and stored in OpenSearch; queries retrieve the most relevant chunks and pass them to an LLM that answers only from the provided context.

Deployed on IBM OpenShift.

## Features

- Upload PDF, DOCX, and TXT documents through a web UI
- Semantic search over document content via vector embeddings
- Grounded answers that refuse to hallucinate when the context is sufficient
- Source citations shown beneath every answer
- Single-container deployment (React frontend served by FastAPI)

## Architecture

```
Upload  →  Parse  →  Clean  →  Chunk  →  Embed  →  Store (OpenSearch)
Query   →  Embed  →  Search (OpenSearch)  →  Generate (LLM)  →  Answer
```

See [ARCHITECTURE.md](./ARCHITECTURE.md) for the full design, component, breakdown, data-flow diagram, and evaluation results.

## Tech Stack

- **Backend:** FastAPI, Python 3.14
- **Vector store:** OpenSearch 3.x (HNSW, cosine similarity, faiss engine)
- **Embeddings:** OpenAI `text-embedding-3-small` (1536 dims)
- **LLM:** OpenAI `gpt-5.4-nano` (temperature 0)
- **Parsing:** docling (PDF and DOCX), UTF-8/Latin-1 decode (TXT)
- **Frontend:** React, Vite, Tailwind CSS v4
- **Infrastructure:** Docker, GitHub Actions, Kubernetes / OpenShift

## Repository Structure

```
rag-pipeline/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app, routes, static file serving
│   │   ├── api/routes/        # upload and query endpoints
│   │   ├── core/config.py     # settings from environment
│   │   ├── models/schemas.py  # request/response models
│   │   └── services/          # parser, cleaner, chunker, embedder,
│   │                          #   vector_store, llm, opensearch_client
│   ├── tests/                 # pytest suite (unit + integration)
│   └── requirements.txt
├── frontend/                  # React + Vite + Tailwind
├── k8s/                       # Kubernetes / OpenShift manifests
├── scripts/                   # profiling and debug utilities
├── docker-compose.yml         # local dev stack
├── Dockerfile                 # multi-stage production build
├── Makefile                   # common commands
└── ARCHITECTURE.md
```

## Prerequisites

- Docker Desktop
- Node.js 26+ (for frontend development)
- Python 3.14+ (for running tests locally)
- An OpenAI API key

## Local Development Setup

### 1. Environment variables

Copy the example and fill in your OpenAI key:

```bash
cp .env.example .env
```

Required variables:

| Variable | Description | Example |
| - | - | - |
| `OPENSEARCH_URL` | OpenSearch endpoint | `http://opensearch:9200` |
| `OPENSEARCH_INDEX_NAME` | Vector index name | `rag_vectors` |
| `EMBEDDINGS_API_KEY` | OpenAI key for embeddings | `sk-...` |
| `EMBEDDINGS_MODEL` | Embedding model | `text-embedding-3-small` |
| `LLM_API_KEY` | OpenAI key for generation | `sk-...` |
| `LLM_MODEL_NAME` | Chat model | `gpt-5.4-nano` |

### 2. Hostname alias (one-time)

`OPENSEARCH_URL` uses the host name `opensearch`, which resolves inside Docker automatically. To let local test scripts reach the same container, add an alias:

```bash
sudo sh -c 'echo "127.0.0.1 opensearch" >> /etc/hosts'
```

This is machine-local; each developer runs it once.

### 3. Run the full stack

```bash
make up
```

This starts OpenSearch, OpenSearch Dashboards, and the API. The UI is served at `http://localhost:8000`. OpenSearch Dashboards is at `http://localhost:5601`.

### 4. Frontend development (optional)

For hot-reloading frontend work, run Vite separately against the running backend:

```bash
cd frontend
npm install
npm run dev
```

The dev server runs at `http://localhost:5173` and proxies API calls to the backend via the Vite proxy (no CORS configuration needed).

## Running Tests

```bash
make test        # full suite (needs the stack up + a valid OpenAI key)
make test-unit   # pure-function tests only (no network, no API cost)
```

Unit tests cover the parser, cleaner, and chunker. Integration tests (marked with `@pytest.mark.integration`) exercise the embedder, vector store, search LL, and full pipeline against a live OpenSearch and the OpenAI API.

## Production Build

Build and run the single-container production image locally:

```bash
make build-prod   # builds rag:prod
make prod         # runs it against the compose OpenSearch
```

The production image is a three-stage build: the React frontend is compiled, Python dependencies are installed, and only the compiled assets plus runtime dependencies reach the final image.

## Deployment

Deployed on IBM OpenShift as a single container. Manifests live in `k8s/`:
 
| File | Purpose |
| - | - |
| `configmap.yaml` | Non-sensitive configuration |
| `secret.yaml` | API keys (gitignored) |
| `opensearch-deployment.yaml` | OpenSearch pod and service |
| `deployment.yaml` | App pod with liveness/readiness probes |
| `service.yaml` | Internal cluster endpoint |
| `route.yaml` | Public HTTPS URL |

Deploy with:
 
```bash
oc apply -f k8s/
```

CI/CD (GitHub Actions) runs lint, unit tests, integration tests, and frontend build on every push, then builds and pushes the Docker image to Docker Hub on merges to `main`.

## Common Commands

| Command | Description |
| - | - |
| `make up` | Start the full local stack |
| `make down` | Stop the stack |
| `make test` | Run the full test suite |
| `make test-unit` | Run unit tests only |
| `make build-prod` | Build the production image |
| `make prod` | Run the production image locally |
| `make check` | Format (black) and lint (flake8) |
