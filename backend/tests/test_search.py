import pytest

from app.services.vector_store import search_chunks
from conftest import FIXTURES, TXT

pytestmark = pytest.mark.integration

DOC_ID = "test-search-001"


@pytest.fixture
def sample_ingested(ingest):
    return ingest(FIXTURES / "sample.txt", TXT, DOC_ID)


def test_empty_query_returns_no_results():
    assert search_chunks("", top_k=3) == []


def test_whitespace_query_returns_no_results():
    assert search_chunks("   ", top_k=3) == []


def test_top_k_caps_result_count(sample_ingested):
    results = search_chunks("IPO", top_k=2)
    assert len(results) <= 2


def test_result_shape(sample_ingested):
    results = search_chunks("What is SpaceX's ticker symbol on Nasdaq?", top_k=3)
    assert len(results) > 0
    for result in results:
        assert set(result) == {
            "doc_id",
            "filename",
            "chunk_index",
            "chunk_text",
            "char_count",
            "score",
        }
        assert "embedding" not in result


def test_results_are_sorted_by_score_desc(sample_ingested):
    results = search_chunks("What is SpaceX's ticker symbol on Nasdaq?", top_k=3)
    scores = [r["score"] for r in results]
    assert scores == sorted(scores, reverse=True)


def test_relevant_query_scores_higher_than_irrelevant(sample_ingested):
    relevant = search_chunks("SpaceX IPO stock debut", top_k=1)
    irrelevant = search_chunks("Vietnam's GDP in 2025", top_k=1)
    assert relevant[0]["score"] > irrelevant[0]["score"]