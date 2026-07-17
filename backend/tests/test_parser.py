import pytest
from fastapi import HTTPException

from app.services.parser import parse_document
from conftest import SAMPLE_FILES, FIXTURES, TXT

@pytest.mark.parametrize("path,content_type", SAMPLE_FILES)
def test_parses_without_error(path, content_type):
    text = parse_document(path.read_bytes(), content_type)

    assert isinstance(text, str)
    assert len(text) > 0, f"{path.name} produced no text"
    assert text.strip(), f"{path.name} produced only whitespace"

@pytest.mark.parametrize("path,content_type", SAMPLE_FILES)
def test_extracts_known_content(path, content_type):
    text = parse_document(path.read_bytes(), content_type)
    assert "SpaceX" in text

def test_unsupported_content_type_raises():
    with pytest.raises(HTTPException) as exc:
        parse_document(b"fake image bytes", "image/jpeg")

    assert exc.value.status_code == 400
    assert "image/jpeg" in exc.value.detail

def test_corrupt_pdf_raises_422():
    with pytest.raises(HTTPException) as exc:
        parse_document(b"not a real pdf at all", "application/pdf")

    assert exc.value.status_code == 422

def test_latin1_fallback():
    text = parse_document(b"caf\xe9 society", TXT)
    assert "caf" in text

def test_txt_roundtrip_preserves_length():
    path = FIXTURES / "sample.txt"
    raw = path.read_bytes()
    text = parse_document(raw, TXT)
    assert len(text) == len(raw.decode("utf-8"))