"""
PPTX Loader — Extract text from PowerPoint presentations slide by slide.
Preserves slide number and slide title in metadata for citations.
"""

import hashlib
from pathlib import Path

from pptx import Presentation
from langchain_core.documents import Document


def _compute_file_hash(file_path: str) -> str:
    """Compute SHA256 hash of a file for duplicate detection."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def load_pptx(file_path: str) -> list[Document]:
    """
    Extract text from a PPTX file slide by slide.

    Args:
        file_path: Path to the PPTX file.

    Returns:
        List of Document objects, one per slide, with metadata:
            - source: filename
            - file_type: "pptx"
            - slide_number: 1-indexed slide number
            - slide_title: title of the slide (if present)
            - doc_id: SHA256 hash of the file
            - total_slides: total number of slides
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"PPTX file not found: {file_path}")

    doc_id = _compute_file_hash(file_path)
    documents = []

    try:
        prs = Presentation(file_path)
    except Exception as e:
        raise ValueError(f"Could not open PPTX '{path.name}': {e}")

    total_slides = len(prs.slides)

    for slide_num, slide in enumerate(prs.slides, start=1):
        # Extract slide title
        slide_title = ""
        if slide.shapes.title and slide.shapes.title.text:
            slide_title = slide.shapes.title.text.strip()

        # Extract all text from the slide
        text_parts = []
        for shape in slide.shapes:
            if shape.has_text_frame:
                for paragraph in shape.text_frame.paragraphs:
                    para_text = paragraph.text.strip()
                    if para_text:
                        text_parts.append(para_text)

            # Also extract text from tables
            if shape.has_table:
                for row in shape.table.rows:
                    row_text = []
                    for cell in row.cells:
                        cell_text = cell.text.strip()
                        if cell_text:
                            row_text.append(cell_text)
                    if row_text:
                        text_parts.append(" | ".join(row_text))

        text = "\n".join(text_parts)

        if text:
            documents.append(
                Document(
                    page_content=text,
                    metadata={
                        "source": path.name,
                        "file_type": "pptx",
                        "slide_number": slide_num,
                        "slide_title": slide_title,
                        "total_slides": total_slides,
                        "doc_id": doc_id,
                    },
                )
            )

    if not documents:
        raise ValueError(f"No text could be extracted from '{path.name}'.")

    return documents
