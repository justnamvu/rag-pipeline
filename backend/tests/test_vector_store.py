import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.embedder import embed_chunks
from app.services.vector_store import store_chunks
from app.services.opensearch_client import get_opensearch_client
from app.core.config import settings


def test_store_chunks():
    print("\n--- Test 1: Store embedded chunks ---")

    mock_chunks = [
        {
           "chunk_index": 0,
           "doc_id": "test-doc-001",
           "filename": "sample.txt",
           "chunk_text": "Professor Jay Ritter has collected data on U.S. IPOs since 1960.",
           "char_count": 64, 
        },
        {
            "chunk_index": 1,
            "doc_id": "test-doc-001",
            "filename": "sample.txt",
            "chunk_text": "CEO Elon Musk even suggested SpaceX's revenue could hit $1 trillion by 2030",
            "char_count": 75,
        },
    ]

    embedded = embed_chunks(mock_chunks)
    stored = store_chunks(embedded)

    print(f"Chunks embedded: {len(embedded)}")
    print(f"Chunks stored: {stored}")
    print(f"All stored: {stored == len(mock_chunks)}")


def test_verify_chunks_exist():
    print("\n--- Test 2: Verify chunks exist in OpenSearch ---")

    time.sleep(1)

    client = get_opensearch_client()
    index_name = settings.opensearch_index_name


    result = client.get(index=index_name, id="test-doc-001_0")
    source = result["_source"]

    print(f"Document ID: {source['doc_id']}")
    print(f"Filename: {source['filename']}")
    print(f"Chunk index: {source['chunk_index']}")
    print(f"Number of chars: {source['char_count']}")
    print(f"Chunk text: {source['chunk_text']}")
    print(f"Embedding dimensions: {len(source['embedding'])}")
    print(f"Embedding correct: {len(source['embedding']) == 1536}")


def test_count_documents():
    print("\n--- Test 3: Count documents in index ---")

    time.sleep(1)
    client = get_opensearch_client()
    index_name = settings.opensearch_index_name

    response = client.count(index=index_name)
    count = response["count"]
    print(f"Total documents in '{index_name}': {count}")


def test_empty_input():
    print("\n--- Test 4: Empty input ---")
    result = store_chunks([])
    print(f"Result for empty list: {result} (expected 0)")


test_store_chunks()
test_verify_chunks_exist()
test_count_documents()
test_empty_input()