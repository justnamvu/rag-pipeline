import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.parser import parse_document
from app.services.cleaner import clean_text
from app.services.chunker import chunk_text

CHUNK_SIZE = 1200
OVERLAP = 200
DOC_ID = "test-doc-id"


def test_chunk(path: str, content_type: str):
    print(f"\n{'-' * 60}")
    print(f"Testing full pipeline: {path}")
    print(f"{'-' * 60}")

    with open(path, "rb") as f:
        contents = f.read()

    filename = os.path.basename(path)
    cleaned_text = clean_text(parse_document(contents, content_type))
    chunks = chunk_text(cleaned_text, DOC_ID, filename, CHUNK_SIZE, OVERLAP)

    print(f"\nChunks: {len(chunks)}")
    print(f"Sizes: {[c['char_count'] for c in chunks]}")

    print("\nFirst chunk preview:")
    print(f"Index: {chunks[0]['chunk_index']}")
    print(f"Document ID: {chunks[0]['doc_id']}")
    print(f"Filename: {chunks[0]['filename']}")
    print(f"Number of chars: {chunks[0]['char_count']}")
    print(f"Content: {chunks[0]['chunk_text'][:200]}")

    assert all(c["char_count"] <= CHUNK_SIZE + OVERLAP for c in chunks)
    # Indices stay contiguous so {doc_id}_{chunk_index} IDs stay idempotent
    assert [c["chunk_index"] for c in chunks] == list(range(len(chunks)))
    # Same input, same output
    assert chunks == chunk_text(cleaned_text, DOC_ID, filename, CHUNK_SIZE, OVERLAP)

    if len(chunks) > 1:
        print("\nOverlap check:")
        tail = chunks[0]["chunk_text"][-200:]
        print(f"Last 200 chars of chunk 0: ...{tail!r}")
        print(f"First 200 chars of chunk 1: {chunks[1]['chunk_text'][:200]!r}...")

        assert tail[-30:] in chunks[1]["chunk_text"], "overlap not carried forward"

    print("\nPassed.")


def test_edge_cases():
    print(f"\n{'-' * 50}")
    print("Testing edge cases")
    print(f"{'-' * 50}")

    print("\n--- Empty string ---")
    result = chunk_text("", doc_id="x", filename="empty.txt")
    print(f"Chunks from empty string: {len(result)} (expected 0)")
    assert result == []

    print("\n--- Whitespace-only string ---")
    result = chunk_text("     \n\n     ", doc_id="x", filename="blank.txt")
    print(f"Chunks from whitespace string: {len(result)} (expected 0)")
    assert result == []

    print("\n--- Short string ---")
    result = chunk_text("Short text.", doc_id="x", filename="short.txt")
    print(f"Chunks from short string: {len(result)} (expected 1)")
    print(f"Content: {result[0]['chunk_text']!r}")
    assert len(result) == 1 and result[0]["chunk_text"] == "Short text."

    print("\n--- Sentence boundaries (no mid-word cuts) ---")
    prose = f"The second factor is float. SpaceX issued only about 4% of the company to the public. " * 10
    chunks = chunk_text(prose, "x", "prose.txt", chunk_size=200, overlap=40)
    print(f"Chunks: {len(chunks)}, sizes: {[c['char_count'] for c in chunks]}")
    print(f"Chunk 0 ends: ...{chunks[0]['chunk_text'][-40:]!r}")
    assert chunks[0]["chunk_text"].endswith("."), "chunk did not end on a sentence"

    print("\n--- No separators (hard-cut fallback) ---")
    chunks = chunk_text("A" * 500, "x", "blob.txt", chunk_size=200, overlap=0)
    print(f"Chunks: {len(chunks)}, sizes: {[c['char_count'] for c in chunks]}")
    assert [c["char_count"] for c in chunks] == [200, 200, 100]

    print("\n--- Invalid arguments ---")
    for kwargs in [
        {"chunk_size": 0},
        {"overlap": -1},
        {"chunk_size": 500, "overlap": 500},
    ]:
        try:
            chunk_text("text", doc_id="x", filename="bad.txt", **kwargs)
            raise AssertionError(f"expected ValueError for {kwargs}")
        except ValueError as e:
            print(f"{kwargs} -> ValueError: {e}")

    print("\nPassed.")


test_edge_cases()
test_chunk("backend/tests/fixtures/sample.txt", "text/plain")
test_chunk("backend/tests/fixtures/sample.pdf", "application/pdf")
test_chunk(
    "backend/tests/fixtures/sample.docx",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
)