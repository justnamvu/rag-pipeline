import os
import sys
import time

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
)

from app.services.parser import parse_document
from app.services.cleaner import clean_text
from app.services.chunker import chunk_text
from app.services.embedder import embed_chunks
from app.services.vector_store import store_chunks, search_chunks
from app.services.llm import generate_answer

FIXTURE = "backend/tests/fixtures/sample.txt"
CONTENT_TYPE = "text/plain"
QUERY = "What is SpaceX's ticker symbol on Nasdaq?"


def timed(label, fn):
    start = time.perf_counter()
    result = fn()
    elapsed = (time.perf_counter() - start) * 1000
    print(f"{label:<20} {elapsed:>8.1f} ms")
    return result


def main():
    with open(FIXTURE, "rb") as f:
        contents = f.read()

    print(f"\nProfiling pipeline for: {QUERY}\n" + "-" * 40)

    raw = timed("parse", lambda: parse_document(contents, CONTENT_TYPE))
    cleaned = timed("clean", lambda: clean_text(raw))
    chunks = timed("chunk", lambda: chunk_text(cleaned, "profile-doc", "sample.txt"))
    embedded = timed("embed", lambda: embed_chunks(chunks))
    timed("store", lambda: store_chunks(embedded))

    time.sleep(1)

    print("-" * 40)
    results = timed("search", lambda: search_chunks(QUERY, top_k=5))
    timed("generate", lambda: generate_answer(QUERY, results))

    print("-" * 40)


if __name__ == "__main__":
    main()
