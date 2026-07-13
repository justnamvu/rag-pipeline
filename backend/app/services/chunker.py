from typing import List

DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


def _split_keep(text: str, separator: str) -> List[str]:
    """Split on `separator`, reattaching it to the end of each piece.

    Keeps trailing punctuation (e.g. the "." of ". ") on the sentence it
    belongs to, so no non-whitespace characters are lost at chunk boundaries.
    Whitespace-only pieces are discarded later, since chunks are stripped.
    """
    parts = text.split(separator)
    return [part + separator for part in parts[:-1]] + [parts[-1]]


def _recursive_split(
    text: str,
    chunk_size: int,
    separators: List[str],
) -> List[str]:
    """Split `text` into pieces of at most `chunk_size` characters.

    Prefers to break on the coarsest separator available (paragraph, then
    line, then sentence, then word), only cutting mid-word when no separator
    can produce a small enough piece. Adjacent pieces are greedily packed
    together so chunks stay close to `chunk_size` rather than being tiny.
    """
    if len(text) <= chunk_size:
        return [text]

    if not separators:
        return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]

    separator, remaining = separators[0], separators[1:]

    if separator == "":
        return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]

    chunks: List[str] = []
    buffer = ""

    for part in _split_keep(text, separator):
        if len(part) > chunk_size:
            if buffer:
                chunks.append(buffer)
                buffer = ""
            chunks.extend(_recursive_split(part, chunk_size, remaining))
        elif len(buffer) + len(part) <= chunk_size:
            buffer += part
        else:
            if buffer:
                chunks.append(buffer)
            buffer = part

    if buffer:
        chunks.append(buffer)

    return [chunk for chunk in chunks if chunk.strip()]


def _overlap_tail(text: str, overlap: int) -> str:
    """Return the last `overlap` characters, trimmed to a word boundary."""
    tail = text[-overlap:]
    first_space = tail.find(" ")
    if first_space != -1:
        tail = tail[first_space + 1 :]
    return tail.strip()


def _merge_with_overlap(pieces: List[str], overlap: int) -> List[str]:
    """Prepend the tail of each piece to the one that follows it.

    A fact severed at a boundary then survives intact in the later chunk.
    Note: chunks may exceed `chunk_size` by up to `overlap` characters as a
    result. This is bounded and well within the embedding model's token limit.
    """
    merged: List[str] = []

    for i, piece in enumerate(pieces):
        if i > 0 and overlap > 0:
            tail = _overlap_tail(pieces[i - 1], overlap)
            if tail:
                piece = f"{tail} {piece}"
        merged.append(piece.strip())

    return [chunk for chunk in merged if chunk]


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
    chunk_size: int = 1200,
    overlap: int = 200,
) -> List[dict]:
    """Split cleaned document text into overlapping chunks with metadata.

    Chunks break on paragraph, line, sentence, and word boundaries in that
    order of preference. Deterministic: the same input always yields the same
    chunks and the same `chunk_index` values, which keeps the
    `{doc_id}_{chunk_index}` document IDs idempotent across re-uploads.
    """
    if chunk_size <= 0:
        raise ValueError(f"chunk_size must be positive, got {chunk_size}")
    if overlap < 0:
        raise ValueError(f"overlap must be non-negative, got {overlap}")
    if overlap >= chunk_size:
        raise ValueError(
            f"overlap ({overlap}) must be smaller than chunk_size ({chunk_size})"
        )

    if not text.strip():
        return []

    pieces = _recursive_split(text, chunk_size, DEFAULT_SEPARATORS)
    raw_chunks = _merge_with_overlap(pieces, overlap)
    return _attach_metadata(raw_chunks, doc_id, filename)
