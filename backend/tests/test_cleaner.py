import pytest

from app.services.cleaner import clean_text
from app.services.parser import parse_document
from conftest import SAMPLE_FILES

DIRTY = (
    "This   has\t\ttabs  and   spaces.\n\n\n\n"
    "Too many newlines.\xa0Non-breaking space.\xadSoft hyphen.\u2022 Bullet point."
)


def test_removes_noise_characters():
    cleaned = clean_text(DIRTY)

    assert "\xa0" not in cleaned, "non-breaking space survived"
    assert "\xad" not in cleaned, "soft hyphen survived"
    assert "\u2022" not in cleaned, "bullet character survived"
    assert "\t" not in cleaned, "tab survived"


def test_collapses_whitespace():
    cleaned = clean_text(DIRTY)

    assert "   " not in cleaned, "multiple spaces not collapsed"
    assert "\n\n\n" not in cleaned, "3+ newlines not collapsed"


def test_preserves_real_content():
    cleaned = clean_text(DIRTY)

    for word in ["tabs", "spaces", "newlines", "Bullet point"]:
        assert word in cleaned, f"cleaner removed real content: {word}"


def test_strips_leading_and_trailing():
    assert clean_text("   hello   ") == "hello"


def test_empty_and_whitespace_input():
    assert clean_text("") == ""
    assert clean_text("   \n\n   ") == ""


def test_idempotent():
    once = clean_text(DIRTY)
    assert clean_text(once) == once, "cleaning twice changed the output"


@pytest.mark.parametrize("path,content_type", SAMPLE_FILES)
def test_conservative_on_real_files(path, content_type):
    raw = parse_document(path.read_bytes(), content_type)
    cleaned = clean_text(raw)

    assert len(cleaned) > 0
    removed_ratio = (len(raw) - len(cleaned)) / len(raw)
    assert removed_ratio < 0.20, (
        f"{path.name}: cleaner removed {removed_ratio:.0%} of the text "
        f"({len(raw)} -> {len(cleaned)} chars)"
    )
    assert "SpaceX" in cleaned