import copy

import pytest

from app.services.embedder import embed_single, embed_chunks

pytestmark = pytest.mark.integration

DIMENSIONS = 1536

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


@pytest.fixture
def vector():
    return embed_single(
        "CEO Elon Musk even suggested SpaceX's revenue could hit $1 trillion by 2030"
    )


def test_single_vector_dimensions(vector):
    assert len(vector) == DIMENSIONS


def test_single_vector_values_are_floats(vector):
    assert all(isinstance(v, float) for v in vector)


def test_single_vector_values_in_range(vector):
    # text-embedding-3-small returns unit vectors 
    # Anything outside [-1, 1] means the response is not a normalised embedding
    assert all(-1.0 <= v <= 1.0 for v in vector)


def test_single_vector_is_not_all_zeros(vector):
    assert any(v != 0.0 for v in vector)


def test_embed_chunks_attaches_vectors():
    embedded = embed_chunks(copy.deepcopy(MOCK_CHUNKS))

    assert len(embedded) == len(MOCK_CHUNKS)
    for chunk in embedded:
        assert "embedding" in chunk
        assert len(chunk["embedding"]) == DIMENSIONS


def test_embed_chunks_preserves_metadata():
    embedded = embed_chunks(copy.deepcopy(MOCK_CHUNKS))

    for original, result in zip(MOCK_CHUNKS, embedded):
        for key in original:
            assert result[key] == original[key]


def test_embed_chunks_does_not_mutate_input():
    chunks = copy.deepcopy(MOCK_CHUNKS)
    embed_chunks(chunks)

    assert all("embedding" not in c for c in chunks), (
        "embed_chunks mutated its input — the dict(chunk) copy is missing"
    )


def test_embed_chunks_empty_input():
    assert embed_chunks([]) == []


def test_different_text_produces_different_vectors():
    a = embed_single("SpaceX launched a rocket")
    b = embed_single("The recipe calls for three eggs")

    assert a != b