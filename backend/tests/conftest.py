import os
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

FIXTURES = Path(__file__).parent / "fixtures"

TXT = "text/plain"
PDF = "application/pdf"
DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

SAMPLE_FILES = [
    pytest.param(FIXTURES / "sample.txt", TXT, id="txt"),
    pytest.param(FIXTURES / "sample.pdf", PDF, id="pdf"),
    pytest.param(FIXTURES / "sample.docx", DOCX, id="docx"),
]


@pytest.fixture(scope="session")
def opensearch_client():
    from app.services.opensearch_client import get_opensearch_client

    return get_opensearch_client()


@pytest.fixture(scope="session")
def index_name():
    from app.core.config import settings

    return settings.opensearch_index_name


def delete_doc(client, index, doc_id: str) -> None:
    client.delete_by_query(
        index=index,
        body={"query": {"term": {"doc_id": doc_id}}},
        refresh=True,
        ignore_unavailable=True,
        conflicts="proceed",
    )


@pytest.fixture
def cleanup_doc(opensearch_client, index_name):
    doc_ids: list[str] = []

    def register(doc_id: str) -> str:
        doc_ids.append(doc_id)
        return doc_id

    yield register

    for doc_id in doc_ids:
        delete_doc(opensearch_client, index_name, doc_id)


@pytest.fixture
def ingest(cleanup_doc, opensearch_client, index_name):
    from app.services.parser import parse_document
    from app.services.cleaner import clean_text
    from app.services.chunker import chunk_text
    from app.services.embedder import embed_chunks
    from app.services.vector_store import store_chunks

    def _ingest(path: Path, content_type: str, doc_id: str) -> str:
        cleanup_doc(doc_id)
        contents = path.read_bytes()
        cleaned = clean_text(parse_document(contents, content_type))
        chunks = chunk_text(cleaned, doc_id, path.name)
        stored = store_chunks(embed_chunks(chunks))
        assert stored == len(chunks)
        opensearch_client.indices.refresh(index=index_name)
        return doc_id

    return _ingest