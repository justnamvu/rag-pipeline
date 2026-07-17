import pytest
from fastapi import HTTPException

from app.services.llm import generate_answer

pytestmark = pytest.mark.integration

REFUSAL = "enough information"

MOCK_CHUNKS = [
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


def test_answers_when_context_is_sufficient():
    answer = generate_answer(
        query="When could SpaceX's revenue hit $1 trillion?",
        context_chunks=MOCK_CHUNKS,
    )

    assert len(answer) > 0
    assert REFUSAL not in answer.lower(), (
        f"refused a question the context answers: {answer}"
    )
    assert "2030" in answer


def test_does_not_fabricate_beyond_context():
    answer = generate_answer(
        query="What is SpaceX and what does it do?",
        context_chunks=MOCK_CHUNKS,
    )
    fabricated = [
        word
        for word in ["starlink", "spacecraft", "rocket", "nasa", "satellite"]
        if word in answer.lower()
    ]

    assert not fabricated, f"fabricated details not in context: {fabricated}"


def test_refuses_out_of_context_question():
    answer = generate_answer(
        query="What is the GDP of Vietnam in 2025?",
        context_chunks=MOCK_CHUNKS,
    )

    assert REFUSAL in answer.lower(), f"hallucinated an answer: {answer}"


def test_empty_chunks_returns_fallback():
    answer = generate_answer(query="What happened?", context_chunks=[])

    assert REFUSAL in answer.lower()


@pytest.mark.parametrize("query", ["", "   ", "\n\t"])
def test_empty_query_raises_400(query):
    with pytest.raises(HTTPException) as exc:
        generate_answer(query=query, context_chunks=MOCK_CHUNKS)

    assert exc.value.status_code == 400


def test_deterministic_at_temperature_zero():
    kwargs = {
        "query": "Which professor collected IPO data?",
        "context_chunks": MOCK_CHUNKS,
    }

    assert generate_answer(**kwargs) == generate_answer(**kwargs)