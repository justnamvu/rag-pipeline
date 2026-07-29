.PHONY: run format lint check build build-prod up down prod test test-unit

run:
	uvicorn app.main:app --reload

format:
	black backend/app/

lint:
	flake8 backend/app/ 

check: format lint

build:
	docker-compose build

up:
	docker-compose up

down:
	docker-compose down

build-prod:
	docker build -t rag-pipeline:prod .

prod:
	docker-compose up opensearch opensearch-dashboards -d
	@echo "Waiting for OpenSearch..."
	@until docker exec rag-pipeline-opensearch-1 curl -s http://localhost:9200 > /dev/null 2>&1; do \
		echo "  not ready yet, retrying in 5s..."; \
		sleep 5; \
	done
	@echo "OpenSearch is ready."
	docker run --rm \
		--network rag-pipeline_default \
		-p 8000:8000 \
		-e OPENSEARCH_URL=http://opensearch:9200 \
		-e EMBEDDINGS_API_KEY=$(shell grep EMBEDDINGS_API_KEY .env | cut -d '=' -f2) \
		-e EMBEDDINGS_MODEL=$(shell grep EMBEDDINGS_MODEL .env | cut -d '=' -f2) \
		-e LLM_API_KEY=$(shell grep LLM_API_KEY .env | cut -d '=' -f2) \
		-e LLM_MODEL_NAME=$(shell grep LLM_MODEL_NAME .env | cut -d '=' -f2) \
		-e OPENSEARCH_INDEX_NAME=$(shell grep OPENSEARCH_INDEX_NAME .env | cut -d '=' -f2) \
		rag-pipeline:prod

test:
	pytest

test-unit:
	pytest -m "not integration"