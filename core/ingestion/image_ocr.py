"""
Image OCR Loader — Extract text from handwritten notes and whiteboard photos.
Uses EasyOCR for robust handwriting recognition.
The reader is lazily initialized to avoid loading the model on import.
"""

import hashlib
from pathlib import Path

from langchain_core.documents import Document

# Lazy-loaded EasyOCR reader (avoids loading the ~100MB model on every import)
_reader = None


def _get_reader():
    """Get or create the EasyOCR reader singleton."""
    global _reader
    if _reader is None:
        import easyocr
        _reader = easyocr.Reader(["en"], gpu=False)  # CPU mode for compatibility
    return _reader


def _compute_file_hash(file_path: str) -> str:
    """Compute SHA256 hash of a file for duplicate detection."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def load_image(file_path: str) -> list[Document]:
    """
    Extract text from an image using EasyOCR.

    Supports JPG, PNG, BMP, TIFF images of handwritten notes,
    typed text, or whiteboard photos.

    Args:
        file_path: Path to the image file.

    Returns:
        List containing a single Document with the extracted text and metadata:
            - source: filename
            - file_type: "image"
            - doc_id: SHA256 hash of the file
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {file_path}")

    doc_id = _compute_file_hash(file_path)

    try:
        reader = _get_reader()
        results = reader.readtext(str(file_path))
    except Exception as e:
        raise ValueError(
            f"Could not process image '{path.name}': {e}. "
            "Make sure the image is not corrupted and is in a supported format."
        )

    # Extract text from results — each result is (bbox, text, confidence)
    text_parts = []
    for _, text, confidence in results:
        text = text.strip()
        if text and confidence > 0.3:  # Filter low-confidence junk
            text_parts.append(text)

    full_text = "\n".join(text_parts)

    if not full_text.strip():
        raise ValueError(
            f"No text could be extracted from image '{path.name}'. "
            "The image may be too blurry, too dark, or contain no readable text."
        )

    return [
        Document(
            page_content=full_text,
            metadata={
                "source": path.name,
                "file_type": "image",
                "doc_id": doc_id,
            },
        )
    ]
