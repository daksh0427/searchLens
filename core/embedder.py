"""
Embedder — Singleton wrapper for the HuggingFace sentence-transformer model.
Uses all-MiniLM-L6-v2 for fast, CPU-friendly semantic embeddings.
"""

from langchain_huggingface import HuggingFaceEmbeddings

import config

# Singleton instance — initialized on first access
_embeddings = None


def get_embeddings() -> HuggingFaceEmbeddings:
    """
    Get or create the embedding model singleton.

    Returns the HuggingFace all-MiniLM-L6-v2 model, downloading it
    on first run (~80MB). Subsequent calls return the cached instance.

    Returns:
        HuggingFaceEmbeddings instance ready for use with ChromaDB.
    """
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(
            model_name=config.EMBEDDING_MODEL_NAME,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
    return _embeddings
