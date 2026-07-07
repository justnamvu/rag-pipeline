from typing import List


def _split_into_chunks(text: str, chunk_size: int, overlap: int) -> List[str]:
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]

        chunk = chunk.strip()
        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break

        start = end - overlap

    return chunks


def _attach_metadata(
    chunks: List[str],
    doc_id: str,
    filename: str,
) -> List[dict]:
    return [
        {
            "chunk_index": i,
            "doc_id": doc_id,
            "filename": filename,
            "chunk_text": chunk,
            "char_count": len(chunk),
        }
        for i, chunk in enumerate(chunks)
    ]


def chunk_text(
    text: str,
    doc_id: str,
    filename: str,
    chunk_size: int = 500,
    overlap: int = 50,
) -> List[dict]:
    if not text.strip():
        return []

    raw_chunks = _split_into_chunks(text, chunk_size, overlap)
    chunks = _attach_metadata(raw_chunks, doc_id, filename)
    return chunks
