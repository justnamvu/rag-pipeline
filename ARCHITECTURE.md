# RAG Architecture

## Overview
- RAG (Retrieval-Augmented Generation) is a system that enables users to upload documents and query them through a conversational AI interface. Rather than relying on an LLM’s pre-trained knowledge, the system grounds every response strictly in the content of the uploaded documents.
- Incoming documents are parsed, cleaned, and split into chunks by the Ingestion Service, which then converts them into vector embeddings and stores them alongside their metadata in a Vector Store. At query time, the user’s question is similarly vectorised and used to retrieve the most semantically relevant chunks via cosine similarity search. Those chunks are injected into a structured prompt and passed to an LLM, which produces a response grounded entirely in the retrieved context.
- All client interactions flow through a single FastAPI-based API Gateway, which handles routing and validation across both the upload and query pipelines.

## Components
1. **API Gateway:**
    - The single entry point for all client requests, whether that’s a document upload or a user query
    - Handle routing, authentication, and request validation before forwarding traffic to the appropriate internal service
    - Nothing reaches the backend without passing through it first
2. **Ingestion Service:**
    - Receive raw docs, parse them into plain text, and split that text into overlapping chunks suitable for embedding
    - Handle all the messy pre-processing work: clean special characters, normalise whitespace, and produce a clean array of text chunks as output
    - Downstream services never touch raw files and only receive what the ingestion service has prepared
3. **Vector Store:**
    - The database layer that persists vector embeddings alongside their metadata (filename, chunk index, etc.)
    - Expose similarity search capabilities so that at query time, the system can efficiently retrieve the top-K chunks most semantically relevant to a user’s question
    - Everything ingested lives here until explicitly deleted
4. **LLM Service:**
    - Wrap the language model 
    - Take a user query + the retrieved context chunks and produce a grounded natural-language answer
    - Enforce the strict prompting rules that prevent hallucination: if the answer isn’t in the provided context, it says no
    - The only component that generates text, whereas every other component moves or transforms data

## Data Flow Diagram
![Architecture Diagram](./docs/architecture_diagram.png)

## Ingestion Pipeline
The upload endpoint runs the following sequence on every file:

1. **Validation:** file type (MIME) and size check against config values
2. **Parsing:** file bytes dispatched to the correct parser via 'PARSER_MAP' :
    - PDF → 'docling' (exports to markdown, preserving structure)
    - DOCX → 'python-docx' (extracts paragraphs, filters blank lines)
    - TXT → 'bytes.decode()' with UTF-8 / Latin-1 fallback
3. **Cleaning:** soft hyphens, non-breaking spaces, special characters, excess whitespace removed via 'clean_text()'
4. **Chunking:** sliding window split with 'chunk_size=500', 'overlap=50'. Each chunk carries 'doc_id', 'file_name', 'chunk_index', and 'char_count' as metadata.

Output: A list of chunk dictionaries ready to be passed to the Embeddings API

## Embeddings & Retrieval

### Embedding Model
- Provider: OpenAI
- Model: 'text-embedding-3-small'
- Dimension: 1536

### OpenSearch Index
- Index name: 'rag_vectors'
- Algorithm: HNSW (Hierachival Navigable Small World)
- Similarity metric: cosine similarity
- Engine: faiss

### Storage
Each chunk is stored as a seperate OpenSearch document with:
- `embedding` - the 1536-dim vector
- `doc_id`, `filename`, `chunk_index` - for tracing back to source
- `chunk_text`, `char_count` - the actual content and its size

Document ID format: `{doc_id}_{chunk_index}` - re-uploading a document overwrites its previous chunks rather than duplicating them.

### Similarity Search
`POST /api/v1/query` accepts `{"query": "...", "top_k": 5}`, embeds the query using the same model as ingestion, and runs a knn search against the index. Returns the top-K chunks ranked by cosine similarity score.

### Baseline Chunk counts (fixture files)
| File | Chunks stored |
| :-: | :-: |
| sample.txt | 7 |
| sample.pdf | 7 |
| sample.docx | 7 |

## Retrieval Evaluation (precision@3)

Evaluated against `sample.txt` with 5 hand-crafted question/chunk pairs.

| Question | Expected Chunk Index | Top Index Returned | Score | Hit |
| :-: | :-: | :-: | :-: | :-: |
| What is SpaceX's ticker symbol on Nasdaq... | 0 | 0 | 0.7620 | Yes |
| When could SpaceX’s revenue hit $1 trill... | 1 | 1 | 0.7463 | Yes |
| Which professor has collected data on U.... | 2 | 2 | 0.6546 | Yes |
| What has been the average one-year retur... | 3 | 3 | 0.8407 | Yes |
| Do tech companies generally fare better ... | 4 | 4 | 0.6981 | Yes |

Precision@3: X/5 = X%

Chunk parameters: `chunk_size=500`, `overlap=50`

## LLM Service

### Model
- Provider: OpenAI
- Model: 'gpt-5.4-nano'
- Temperature: 0 (fully deterministic, no creative drift)
- Max completion tokens: 500

### System Prompt Design
The system prompt enforces strict grounding with five rules:
1. Answer only from provided context passages
2. Return "I don't have enough information..." if context is insufficient
3. Never infer or use outside knowledge
4. Keep answers concise and factual

### Hallucination provention test results
| Scenario | Expected Behavior | Result |
| :-: | :-: | :-: |
| Answerable from context | Direct answer with citation | Pass |
| Partially answerable | No fabricated information | Pass |
| Out of context | "I don't know" response | Pass |
| Empty chunks | Fallback without API call | Pass |
| Empty query | 400 error raised | Pass |

## Current API Contracts

### POST /api/v1/upload
Request: `multipart/form-data` with a `file` field.
Response:
```json
{
    "doc_id": "uuid",
    "filename": "report.pdf",
    "content_type": "application/pdf",
    "file_size_bytes": 84231,
    "char_count": 7420,
    "chunk_count": 14,
    "message": "Pipeline complete. 14 chunks stored in OpenSearch."
}
```

### POST /api/v1/query
Request:
```json
{
    "query": "What is SpaceX's ticker symbol on Nasdaq?",
    "top_k": 5
}
```
Response:
```json
{
    "query": "What is SpaceX's ticker symbol on Nasdaq?",
    "answer": "According to passage [1], SpaceX's ticker symbol on Nasdaq is SPCX",
    "sources": [
        {
            "doc_id": "uuid",
            "filename": "sample.txt",
            "chunk_index": 0,
            "chunk_text": "Space Exploration Technologies (NASDAQ: SPCX), better known as SpaceX, had a successful IPO...",
            "char_count": 487,
            "score": 0.8124,
        }
    ],
    "source_count": 3
}
```

## Key Design Decisions
- Schema between FastAPI and Vector DB finalised before coding begins
- Metadata stored alongside vector to enable filtered retrieval
- LLM Service never receives raw documents - only pre-retrieved context
- Query and chunk embeddings must come from the identical odel (text-embedding-3-small) - comparing vectors from different models would be meaningless
- `temperature=0` is non-negotiable for a RAG system: any temperature > 0 introduces randomness that can cause the model to drift from the provided context

## Frontend

### Stack
- Framework: React (Vite)
- Styling: Tailwind CSS v4
- Markdown rendering: react-markdown + @tailwindcss/typography

### Structure
frontend/src/
- App.jsx - Two-pane shell, sidebar toggle, doc state
- components/UploadPanel.jsx - Drag-and-drop upload, skelon, doc list
- components/ChatInterface.jsx - Message list, input bar, sources, retry

### Layout
Two-panel layout matching ChatGPT/Claude conventions:
- Left sidebar (w-72, collapsible) - document upload and list
- Right main panel (flex-1) - chat interface with fixed bottom input bar

### Key UI Decisions
- Neutral gray/white palette - one accent color (blue-500) reserved for the Send button and active states only
- User messages right-aligned (blue bubble), LLM messsages left-aligned (gray bubble)
- Sources collapsible beneath each LLM message - filename, chunk index, similarity score, and 3-line text preview
- Thinking dots during query loading, spinner on send button, skeleton shimmer during upload
- Error bubbles include a Retry button that resends the original query
- Sidebar slides closed via hamburger toggle for narrow viewports

### CORS
`CORSMiddleware` added to FastAPI allowing `http://localhost:5173`

## Deployment

### Container
- Base image: `python:3.11-slim`
- Build: three-stage Dockerfile (frontend-builder, backend-builder, runtime)
- Frontend served via FastAPI `StaticFiles` at `/`
- API routes mounted before static files to avoid interception

### Kubernetes manifests (`k8s/`)
| File | Purpose |
| :-: | :-: |
| `configmap.yaml` | Non-sensitive environment variables |
| `secret.yaml` | API keys (gitignored, use secret.example.yaml as template) |
| `opensearch-deployment.yaml` | OpenSearch pod + internal Service |
| `deployment.yaml` | RAG pod with probes and resource limits |
| `service.yaml` | Internal cluster endpoint for RAG |
| `route.yaml` | Public HTTPS URL via OpenShift edge TLS termination |

### Resource Limits
| Container | CPU Request | CPU Limit | Memory Request | Memory Limit |
| :-: | :-: | :-: | :-: | :-: |
| rag | 250m | 500m | 512Mi | 1Gi |
| opensearch | 500m | 1000m | 1Gi | 2Gi |

### Probes
Both liveness and readiness probes call `GET /health`
- Liveness: 30s initial delay, 15s period, restarts after 3 failures
- Readiness: 30s initial delay, 10s period, removes from traffic after 5 failures