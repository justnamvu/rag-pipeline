import io
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import DocumentStream
from fastapi import HTTPException


def parse_pdf(contents: bytes) -> str:
    try:
        converter = DocumentConverter()
        source = DocumentStream(name="document.pdf", stream=io.BytesIO(contents))
        result = converter.convert(source)
        return result.document.export_to_markdown()
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse PDF: {str(e)}")


def parse_docx(contents: bytes) -> str:
    try:
        converter = DocumentConverter()
        source = DocumentStream(name="document.docx", stream=io.BytesIO(contents))
        result = converter.convert(source)
        return result.document.export_to_markdown()
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse DOCX: {str(e)}")


def parse_txt(contents: bytes) -> str:
    try:
        return contents.decode("utf-8")
    except UnicodeDecodeError:
        try:
            return contents.decode("latin-1")
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=f"Failed to decode text file: {str(e)}",
            )


PARSER_MAP = {
    "application/pdf": parse_pdf,
    "text/plain": parse_txt,
    (
        "application/vnd.openxmlformats-officedocument" ".wordprocessingml.document"
    ): parse_docx,
}


def parse_document(contents: bytes, content_type: str) -> str:
    parser = PARSER_MAP.get(content_type)
    if not parser:
        raise HTTPException(
            status_code=400,
            detail=f"No parser available for content type: {content_type}",
        )
    return parser(contents)
