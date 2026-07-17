import pytest

from app.services.embedder import embed_chunks
from app.services.vector_store import store_chunks

pytestmark = pytest.mark.integration

DOC_ID = "test-vector-store-001"

MOCK_CHUNKS = [
    {
        "chunk_index": 0,
        "doc_id": DOC_ID,
        "filename": "sample.txt",
        "chunk_text": "Professor Jay Ritter has collected data on U.S. IPOs since 1960.",
        "char_count": 64,
    },
    {
        "chunk_index": 1,
        "doc_id": DOC_ID,
        "filename": "sample.txt",
        "chunk_text": "CEO Elon Musk even suggested SpaceX's revenue could hit $1 trillion by 2030",
        "char_count": 75,
    },
]


@pytest.fixture
def stored(cleanup_doc, opensearch_client, index_name):
    cleanup_doc(DOC_ID)
    count = store_chunks(embed_chunks(MOCK_CHUNKS))
    opensearch_client.indices.refresh(index=index_name)
    return count


def test_stores_all_chunks(stored):
    assert stored == len(MOCK_CHUNKS)


def test_stored_document_is_retrievable(stored, opensearch_client, index_name):
    result = opensearch_client.get(index=index_name, id=f"{DOC_ID}_0")
    source = result["_source"]

    assert source["doc_id"] == DOC_ID
    assert source["filename"] == "sample.txt"
    assert source["chunk_index"] == 0
    assert source["char_count"] == MOCK_CHUNKS[0]["char_count"]
    assert source["chunk_text"] == MOCK_CHUNKS[0]["chunk_text"]


def test_stored_embedding_has_correct_dimensions(stored, opensearch_client, index_name):
    result = opensearch_client.get(index=index_name, id=f"{DOC_ID}_0")

    assert len(result["_source"]["embedding"]) == 1536


def test_document_count_matches(stored, opensearch_client, index_name):
    response = opensearch_client.count(
        index=index_name,
        body={"query": {"term": {"doc_id": DOC_ID}}},
    )

    assert response["count"] == len(MOCK_CHUNKS)


def test_restore_overwrites_rather_than_duplicates(
    stored, opensearch_client, index_name
):
    # {doc_id}_{chunk_index} is the document ID so storing the same
    # chunks again must not grow the index
    store_chunks(embed_chunks(MOCK_CHUNKS))
    opensearch_client.indices.refresh(index=index_name)

    response = opensearch_client.count(
        index=index_name,
        body={"query": {"term": {"doc_id": DOC_ID}}},
    )
    assert response["count"] == len(MOCK_CHUNKS)


def test_empty_input_stores_nothing():
    assert store_chunks([]) == 0