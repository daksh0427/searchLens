"""
Text Chunker — Split documents into overlapping chunks for embedding.
Uses LangChain's RecursiveCharacterTextSplitter with the configured
chunk size and overlap, preserving all metadata on each chunk.
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

import config


def chunk_documents(documents: list[Document]) -> list[Document]:
    """
    Split a list of Documents into smaller chunks.

    Uses RecursiveCharacterTextSplitter which tries to split on
    paragraph breaks, then sentences, then words — keeping chunks
    as semantically coherent as possible.

    Args:
        documents: List of Documents from any loader.

    Returns:
        List of chunked Documents with all original metadata preserved,
        plus a 'chunk_index' field added to metadata.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
        is_separator_regex=False,
    )

    chunks = splitter.split_documents(documents)

    # Add chunk index to metadata for ordering
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = i

    return chunks
