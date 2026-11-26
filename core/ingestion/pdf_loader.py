"""
PDF Loader — Extract text page-by-page using PyMuPDF.
Each page becomes a Document with rich metadata for citations.
"""

import hashlib
from pathlib import Path

import fitz  # PyMuPDF
from langchain_core.documents import Document


def _compute_file_hash(file_path: str) -> str:
    """Compute SHA256 hash of a file for duplicate detection."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def load_pdf(file_path: str) -> list[Document]:
    """
    Extract text from a PDF file page by page.

    Args:
        file_path: Path to the PDF file.

    Returns:
        List of Document objects, one per page, with metadata:
            - source: filename
            - file_type: "pdf"
            - page_number: 1-indexed page number
            - doc_id: SHA256 hash of the file
            - total_pages: total number of pages
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {file_path}")

    doc_id = _compute_file_hash(file_path)
    documents = []

    try:
        pdf_doc = fitz.open(file_path)
    except Exception as e:
        raise ValueError(f"Could not open PDF '{path.name}': {e}")

    total_pages = len(pdf_doc)

    for page_num in range(total_pages):
        page = pdf_doc[page_num]
        text = page.get_text("text").strip()

        if not text:
            # Try OCR-style extraction for image-only pages
            text = page.get_text("blocks")
            text = " ".join(
                block[4].strip()
                for block in text
                if isinstance(block[4], str) and block[4].strip()
            )

        if text:
            documents.append(
                Document(
                    page_content=text,
                    metadata={
                        "source": path.name,
                        "file_type": "pdf",
                        "page_number": page_num + 1,
                        "total_pages": total_pages,
                        "doc_id": doc_id,
                    },
                )
            )

    pdf_doc.close()

    if not documents:
        raise ValueError(
            f"No text could be extracted from '{path.name}'. "
            "The PDF may be image-only — try uploading as an image for OCR processing."
        )

    return documents
