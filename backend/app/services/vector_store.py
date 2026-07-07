import logging
from typing import List
from fastapi import HTTPException
from app.services.opensearch_client import get_opensearch_client
from app.services.embedder import embed_single
from app.core.config import settings

logger = logging.getLogger(__name__)


def store_chunks(chunks: List[dict]) -> int:
    if not chunks:
        return 0

    client = get_opensearch_client()
    index_name = settings.opensearch_index_name
    stored_count = 0

    logger.info(f"Storing {len(chunks)} chunks into '{index_name}'...")

    for chunk in chunks:
        doc_id = f"{chunk['doc_id']}_{chunk['chunk_index']}"

        body = {
            "embedding": chunk["embedding"],
            "doc_id": chunk["doc_id"],
            "filename": chunk["filename"],
            "chunk_index": chunk["chunk_index"],
            "chunk_text": chunk["chunk_text"],
            "char_count": chunk["char_count"],
        }

        try:
            client.index(
                index=index_name,
                id=doc_id,
                body=body,
            )
            stored_count += 1
            logger.info(f"Stored chunk {chunk['chunk_text']} (doc_id={doc_id})")

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to store chunk {chunk['chunk_index']} "
                f"(doc_id={chunk['doc_id']}): str{e}",
            )

    logger.info(f"Storage complete. {stored_count}/{len(chunks)} chunks stored.")
    return stored_count


def search_chunks(query: str, top_k: int = 5) -> List[dict]:
    if not query.strip():
        return []

    client = get_opensearch_client()
    index_name = settings.opensearch_index_name

    query_vector = embed_single(query)

    search_body = {
        "size": top_k,
        "query": {
            "knn": {
                "embedding": {
                    "vector": query_vector,
                    "k": top_k,
                }
            }
        },
        "_source": ["doc_id", "filename", "chunk_index", "chunk_text", "char_count"],
    }

    try:
        response = client.search(index=index_name, body=search_body)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

    results = []
    for hit in response["hits"]["hits"]:
        result = dict(hit["_source"])
        result["score"] = hit["_score"]
        results.append(result)

    logger.info(f"Search for '{query[:50]}...' returned {len(results)} results.")
    return results
