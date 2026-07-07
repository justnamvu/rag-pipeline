import logging
from app.services.opensearch_client import get_opensearch_client
from app.core.config import settings

logger = logging.getLogger(__name__)

INDEX_MAPPING = {
    "settings": {
        "index": {
            "knn": True,
            "knn.algo_param.ef_search": 100,
        }
    },
    "mappings": {
        "properties": {
            "embedding": {
                "type": "knn_vector",
                "dimension": 1536,
                "method": {
                    "name": "hnsw",
                    "space_type": "cosinesimil",
                    "engine": "faiss",
                },
            },
            "doc_id": {"type": "keyword"},
            "filename": {"type": "keyword"},
            "chunk_index": {"type": "integer"},
            "chunk_text": {"type": "text"},
            "char_count": {"type": "integer"},
        }
    },
}


def create_index() -> None:
    client = get_opensearch_client()
    index_name = settings.opensearch_index_name

    if client.indices.exists(index=index_name):
        logger.info(f"Index '{index_name}' already exists - skipping creation.")
        return

    client.indices.create(index=index_name, body=INDEX_MAPPING)
    logger.info(f"Index '{index_name}' created successfully.")
