"""
DOCX Loader — Extract text from Word documents preserving structure.
Headings and paragraphs are extracted with document structure metadata.
"""

import hashlib
from pathlib import Path

from docx import Document as DocxDocument
from langchain_core.documents import Document


def _compute_file_hash(file_path: str) -> str:
    """Compute SHA256 hash of a file for duplicate detection."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def load_docx(file_path: str) -> list[Document]:
    """
    Extract text from a DOCX file preserving document structure.

    Groups content under headings into logical sections. Each section
    becomes a Document with the heading as part of the content.

    Args:
        file_path: Path to the DOCX file.

    Returns:
        List of Document objects, one per section, with metadata:
            - source: filename
            - file_type: "docx"
            - section_heading: the heading text for this section
            - heading_level: the heading level (1-9, or 0 for body text)
            - doc_id: SHA256 hash of the file
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"DOCX file not found: {file_path}")

    doc_id = _compute_file_hash(file_path)

    try:
        docx_doc = DocxDocument(file_path)
    except Exception as e:
        raise ValueError(f"Could not open DOCX '{path.name}': {e}")

    # Group paragraphs by sections (split at headings)
    sections: list[dict] = []
    current_section = {
        "heading": "Introduction",
        "heading_level": 0,
        "paragraphs": [],
    }

    for paragraph in docx_doc.paragraphs:
        text = paragraph.text.strip()
        if not text:
            continue

        style_name = paragraph.style.name.lower() if paragraph.style else ""

        # Detect headings
        if "heading" in style_name:
            # Save current section if it has content
            if current_section["paragraphs"]:
                sections.append(current_section)

            # Parse heading level from style name (e.g., "Heading 1" → 1)
            level = 0
            for char in style_name:
                if char.isdigit():
                    level = int(char)
                    break

            current_section = {
                "heading": text,
                "heading_level": level,
                "paragraphs": [],
            }
        else:
            current_section["paragraphs"].append(text)

    # Don't forget the last section
    if current_section["paragraphs"]:
        sections.append(current_section)

    # Convert sections to Documents
    documents = []
    for section in sections:
        # Build section content with heading
        content_parts = []
        if section["heading"]:
            prefix = "#" * max(section["heading_level"], 1)
            content_parts.append(f"{prefix} {section['heading']}")
        content_parts.extend(section["paragraphs"])
        text = "\n\n".join(content_parts)

        if text.strip():
            documents.append(
                Document(
                    page_content=text,
                    metadata={
                        "source": path.name,
                        "file_type": "docx",
                        "section_heading": section["heading"],
                        "heading_level": section["heading_level"],
                        "doc_id": doc_id,
                    },
                )
            )

    # Fallback: if no sections detected, return all text as one document
    if not documents:
        full_text = "\n\n".join(
            p.text.strip() for p in docx_doc.paragraphs if p.text.strip()
        )
        if full_text:
            documents.append(
                Document(
                    page_content=full_text,
                    metadata={
                        "source": path.name,
                        "file_type": "docx",
                        "section_heading": "Full Document",
                        "heading_level": 0,
                        "doc_id": doc_id,
                    },
                )
            )

    if not documents:
        raise ValueError(f"No text could be extracted from '{path.name}'.")

    return documents
