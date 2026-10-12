from __future__ import annotations

import io

from docx import Document
from pypdf import PdfReader


class CVParsingError(Exception):
    """Raised when a CV file can't be read or has no extractable text."""


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


def _extract_pdf_text(file_bytes: bytes) -> str:
    """Extract text from a PDF file."""
    reader = PdfReader(io.BytesIO(file_bytes))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages)


def _extract_docx_text(file_bytes: bytes) -> str:
    """Extract text from a DOCX file."""
    document = Document(io.BytesIO(file_bytes))
    paragraphs = [p.text for p in document.paragraphs]
    
    for table in document.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text:
                    paragraphs.append(cell.text)

    return "\n".join(paragraphs)


def extract_text(file_bytes: bytes, filename: str) -> str:
    """
    Extract plain text from a CV file's raw bytes, based on its extension.
    """

    suffix = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if suffix not in SUPPORTED_EXTENSIONS:
        raise CVParsingError(
            f"Unsupported CV file type '{suffix or filename}'. "
            f"Supported: {sorted(SUPPORTED_EXTENSIONS)}"
        )

    try:
        if suffix == ".pdf":
            text = _extract_pdf_text(file_bytes)
        elif suffix == ".docx":
            text = _extract_docx_text(file_bytes)
        else:  # .txt / .md
            text = file_bytes.decode("utf-8", errors="ignore")
    except CVParsingError:
        raise
    except Exception as exc:
        raise CVParsingError(f"Could not read {filename}: {exc}") from exc

    text = text.strip()

    if not text:
        raise CVParsingError(
            f"No extractable text found in {filename}. If this is a "
            "scanned PDF (image only), it needs OCR before it can be used."
        )

    return text