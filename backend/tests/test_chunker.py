import pytest

from app.services.parser import parse_document
from app.services.cleaner import clean_text
from app.services.chunker import chunk_text
from conftest import SAMPLE_FILES

CHUNK_SIZE = 1200
OVERLAP = 200
DOC_ID = "test-doc-id"


def test_empty_string():
    assert chunk_text("", doc_id="x", filename="empty.txt") == []


def test_whitespace_only_string():
    assert chunk_text("   \n\n   ", doc_id="x", filename="blank.txt") == []


def test_short_string_is_one_chunk():
    result = chunk_text("Short text.", doc_id="x", filename="short.txt")

    assert len(result) == 1
    assert result[0]["chunk_text"] == "Short text."


def test_splits_on_sentence_boundary():
    prose = (
        f"The second factor is float. "
        f"SpaceX issued only about 4% of the company to the public. "
    ) * 10
    chunks = chunk_text(prose, "x", "prose.txt", chunk_size=200, overlap=40)

    assert chunks[0]["chunk_text"].endswith("."), (
        f"chunk did not end on a sentence: "
        f"...{chunks[0]['chunk_text'][-40:]!r}"
    )


def test_hard_cut_fallback_when_no_separators():
    chunks = chunk_text("A" * 500, "x", "blob.txt", chunk_size=200, overlap=0)

    assert [c["char_count"] for c in chunks] == [200, 200, 100]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"chunk_size": 0},
        {"chunk_size": -1},
        {"overlap": -1},
        {"chunk_size": 500, "overlap": 500},
        {"chunk_size": 500, "overlap": 600},
    ],
)
def test_invalid_arguments_raise(kwargs):
    with pytest.raises(ValueError):
        chunk_text("text", doc_id="x", filename="bad.txt", **kwargs)


def test_metadata_shape():
    chunks = chunk_text("Some text here.", DOC_ID, "meta.txt")
    chunk = chunks[0]

    assert set(chunk) == {
        "chunk_index",
        "doc_id",
        "filename",
        "chunk_text",
        "char_count",
    }
    assert chunk["doc_id"] == DOC_ID
    assert chunk["filename"] == "meta.txt"
    assert chunk["char_count"] == len(chunk["chunk_text"])


@pytest.fixture(params=SAMPLE_FILES)
def real_chunks(request):
    path, content_type = request.param.values
    cleaned = clean_text(parse_document(path.read_bytes(), content_type))
    return chunk_text(cleaned, DOC_ID, path.name, CHUNK_SIZE, OVERLAP), cleaned


def test_respects_size_ceiling(real_chunks):
    chunks, _ = real_chunks
    assert all(c["char_count"] <= CHUNK_SIZE + OVERLAP for c in chunks)


def test_indices_are_contiguous(real_chunks):
    chunks, _ = real_chunks
    assert [c["chunk_index"] for c in chunks] == list(range(len(chunks)))


def test_deterministic(real_chunks):
    chunks, cleaned = real_chunks
    again = chunk_text(cleaned, DOC_ID, chunks[0]["filename"], CHUNK_SIZE, OVERLAP)

    assert chunks == again


def test_overlap_carried_forward(real_chunks):
    chunks, _ = real_chunks
    if len(chunks) < 2:
        pytest.skip("fixture produced a single chunk — no overlap to check")

    tail = chunks[0]["chunk_text"][-30:]
    assert tail in chunks[1]["chunk_text"], "overlap not carried forward"