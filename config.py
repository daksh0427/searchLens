"""
StudyLens — Central Configuration
All constants, paths, and model settings in one place.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ─── Paths ───────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "data" / "uploads"
CHROMA_PERSIST_DIR = str(BASE_DIR / "vectorstore" / "chroma_db")

# Ensure directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
(BASE_DIR / "vectorstore" / "chroma_db").mkdir(parents=True, exist_ok=True)

# ─── API Keys ────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# ─── Embedding Model ────────────────────────────────────
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

# ─── LLM Models ─────────────────────────────────────────
OLLAMA_MODEL = "llama3"
OPENAI_MODEL = "gpt-4o-mini"

# ─── Chunking ───────────────────────────────────────────
CHUNK_SIZE = 600
CHUNK_OVERLAP = 100

# ─── Retrieval ──────────────────────────────────────────
QA_TOP_K = 8           # Top chunks for Q&A
GENERATION_TOP_K = 15  # Top chunks for notes/flashcards/questions

# ─── ChromaDB ───────────────────────────────────────────
CHROMA_COLLECTION_NAME = "studylens_documents"

# ─── Supported File Types ───────────────────────────────
SUPPORTED_FILE_TYPES = {
    "pdf": [".pdf"],
    "pptx": [".pptx"],
    "docx": [".docx"],
    "image": [".jpg", ".jpeg", ".png", ".bmp", ".tiff"],
}

ALL_SUPPORTED_EXTENSIONS = []
for exts in SUPPORTED_FILE_TYPES.values():
    ALL_SUPPORTED_EXTENSIONS.extend(exts)


def get_file_type(filename: str) -> str | None:
    """Return the file type category for a given filename."""
    ext = Path(filename).suffix.lower()
    for file_type, extensions in SUPPORTED_FILE_TYPES.items():
        if ext in extensions:
            return file_type
    return None
