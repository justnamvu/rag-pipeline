import logging
from typing import List

from openai import OpenAI
from fastapi import HTTPException

from app.core.config import settings

logger = logging.getLogger(__name__)

_openai_client: OpenAI | None = None


def get_openai_client() -> OpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(api_key=settings.embeddings_api_key)
    return _openai_client


def embed_single(text: str) -> List[float]:
    try:
        client = get_openai_client()
        response = client.embeddings.create(
            input=text,
            model=settings.embeddings_model,
        )
        return response.data[0].embedding
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate embedding: {str(e)}",
        )


def embed_chunks(chunks: List[dict]) -> List[dict]:
    if not chunks:
        return []

    logger.info(f"Embedding {len(chunks)} chunks in one batch...")

    client = get_openai_client()
    texts = [chunk["chunk_text"] for chunk in chunks]

    try:
        response = client.embeddings.create(
            input=texts,
            model=settings.embeddings_model,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to embed chunks: {str(e)}",
        )

    embedded = []
    for chunk, item in zip(chunks, response.data):
        embedded_chunk = dict(chunk)
        embedded_chunk["embedding"] = item.embedding
        embedded.append(embedded_chunk)

    logger.info(f"Embedding complete. {len(embedded)} chunks embedded.")
    return embedded
