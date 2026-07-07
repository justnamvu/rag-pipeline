from opensearchpy import OpenSearch
from app.core.config import settings

_opensearch_client: OpenSearch | None = None


def get_opensearch_client() -> OpenSearch:
    global _opensearch_client
    if _opensearch_client is None:
        _opensearch_client = OpenSearch(
            hosts=[settings.opensearch_url],
            use_ssl=False,
            verify_certs=False,
        )
    return _opensearch_client
