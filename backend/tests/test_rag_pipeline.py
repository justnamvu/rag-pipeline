import pytest

from app.services.vector_store import search_chunks
from app.services.llm import generate_answer
from conftest import FIXTURES, TXT

pytestmark = pytest.mark.integration

DOC_ID = "test-pipeline-001"
QUERY = "What is SpaceX's ticker symbol on Nasdaq?"


@pytest.fixture
def pipeline(ingest):
    ingest(FIXTURES / "sample.txt", TXT, DOC_ID)
    results = search_chunks(query=QUERY, top_k=3)
    answer = generate_answer(query=QUERY, context_chunks=results)
    return results, answer


def test_retrieval_returns_chunks(pipeline):
    results, _ = pipeline

    assert len(results) > 0
    assert results[0]["score"] > 0


def test_answer_is_generated(pipeline):
    _, answer = pipeline

    assert len(answer) > 0
    assert "error" not in answer.lower()


def test_answer_is_grounded_in_the_document(pipeline):
    _, answer = pipeline

    assert "SPCX" in answer, f"answer not grounded in the document: {answer}"


def test_out_of_scope_query_is_refused(ingest):
    ingest(FIXTURES / "sample.txt", TXT, DOC_ID)
    query = "What is the GDP of Vietnam in 2025?"

    results = search_chunks(query=query, top_k=3)
    answer = generate_answer(query=query, context_chunks=results)

    assert "enough information" in answer.lower(), (
        f"hallucinated an out-of-scope answer: {answer}"
    )