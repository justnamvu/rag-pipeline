import pytest

from app.services.vector_store import search_chunks
from conftest import FIXTURES, TXT

pytestmark = pytest.mark.integration

DOC_ID = "test-eval-001"
FILENAME = "sample.txt"
TOP_K = 3
MIN_PRECISION = 0.6

EVAL_CASES = [
    pytest.param(
        "What is SpaceX's ticker symbol on Nasdaq?", 0, id="ticker-symbol"
    ),
    pytest.param(
        "When could SpaceX's revenue hit $1 trillion?", 0, id="revenue-1t"
    ),
    pytest.param(
        "Which professor has collected data on U.S. IPOs since 1960?", 1, id="professor"
    ),
    pytest.param(
        "What has been the average one-year return for IPO stocks since 1980?",
        1,
        id="avg-return",
    ),
    pytest.param(
        "Do tech companies generally fare better than non-tech ones?", 2, id="tech-vs-nontech"
    ),
]


@pytest.fixture(scope="module")
def evaluated():
    """Ingest the fixture once, run every eval query, return the hit map.

    Module-scoped so the document is embedded and stored a single time
    rather than once per case.
    """
    from app.services.parser import parse_document
    from app.services.cleaner import clean_text
    from app.services.chunker import chunk_text
    from app.services.embedder import embed_chunks
    from app.services.vector_store import store_chunks
    from app.services.opensearch_client import get_opensearch_client
    from app.core.config import settings
    from conftest import delete_doc

    client = get_opensearch_client()
    index = settings.opensearch_index_name

    path = FIXTURES / FILENAME
    cleaned = clean_text(parse_document(path.read_bytes(), TXT))
    chunks = chunk_text(cleaned, DOC_ID, FILENAME)
    store_chunks(embed_chunks(chunks))
    client.indices.refresh(index=index)

    outcomes = {}
    for case in EVAL_CASES:
        question, expected = case.values
        results = search_chunks(query=question, top_k=TOP_K)
        retrieved = [r["chunk_index"] for r in results if r["doc_id"] == DOC_ID]
        outcomes[question] = {
            "expected": expected,
            "retrieved": retrieved,
            "hit": expected in retrieved,
            "top_score": results[0]["score"] if results else 0.0,
            "top_text": results[0]["chunk_text"][:80] if results else "",
        }

    yield outcomes

    delete_doc(client, index, DOC_ID)


@pytest.mark.parametrize("question,expected_chunk_index", EVAL_CASES)
def test_expected_chunk_in_top_k(evaluated, question, expected_chunk_index):
    outcome = evaluated[question]

    assert outcome["hit"], (
        f"expected chunk {expected_chunk_index} not in top-{TOP_K} "
        f"(got {outcome['retrieved']})\n"
        f"top result: {outcome['top_text']}..."
    )


def test_precision_at_k_meets_threshold(evaluated):
    hits = sum(1 for o in evaluated.values() if o["hit"])
    precision = hits / len(evaluated)

    assert precision >= MIN_PRECISION, (
        f"precision@{TOP_K} = {hits}/{len(evaluated)} = {precision:.0%}, "
        f"below the {MIN_PRECISION:.0%} threshold — "
        f"consider tuning chunk_size or overlap"
    )