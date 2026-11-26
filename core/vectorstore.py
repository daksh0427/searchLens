"""
Vector Store — Persistent ChromaDB wrapper for document storage and retrieval.
Handles adding, querying, and deleting documents with duplicate detection
via file hash checking.
"""

from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

import config
from core.embedder import get_embeddings


class VectorStore:
    """
    Wrapper around ChromaDB providing persistent document storage.

    Documents survive across sessions — re-uploading the same file
    is detected and skipped using SHA256 hash comparison.
    """

    def __init__(self):
        self._db = Chroma(
            collection_name=config.CHROMA_COLLECTION_NAME,
            embedding_function=get_embeddings(),
            persist_directory=config.CHROMA_PERSIST_DIR,
        )

    def document_exists(self, doc_id: str) -> bool:
        """
        Check if a document with the given hash already exists in the store.

        Args:
            doc_id: SHA256 hash of the file.

        Returns:
            True if the document has already been indexed.
        """
        results = self._db.get(where={"doc_id": doc_id})
        return len(results["ids"]) > 0

    def add_documents(self, documents: list[Document]) -> int:
        """
        Add chunked documents to the vector store.

        Checks for duplicates using doc_id (file hash). If the document
        already exists, it is skipped entirely.

        Args:
            documents: List of chunked Document objects to store.

        Returns:
            Number of chunks actually added (0 if duplicate).
        """
        if not documents:
            return 0

        # Check for duplicate using the first chunk's doc_id
        doc_id = documents[0].metadata.get("doc_id", "")
        if doc_id and self.document_exists(doc_id):
            return 0  # Already indexed

        self._db.add_documents(documents)
        return len(documents)

    def similarity_search(self, query: str, k: int = 8) -> list[Document]:
        """
        Perform cosine similarity search over stored documents.

        Args:
            query: The search query string.
            k: Number of top results to return.

        Returns:
            List of the top-k most similar Documents.
        """
        return self._db.similarity_search(query, k=k)

    def get_all_doc_ids(self) -> list[dict]:
        """
        Get a list of all unique documents in the store.

        Returns:
            List of dicts with 'doc_id', 'source', and 'file_type' for each
            unique document.
        """
        all_data = self._db.get()
        if not all_data["metadatas"]:
            return []

        seen = {}
        for meta in all_data["metadatas"]:
            doc_id = meta.get("doc_id", "unknown")
            if doc_id not in seen:
                seen[doc_id] = {
                    "doc_id": doc_id,
                    "source": meta.get("source", "Unknown"),
                    "file_type": meta.get("file_type", "unknown"),
                }

        return list(seen.values())

    def delete_document(self, doc_id: str) -> int:
        """
        Delete all chunks belonging to a specific document.

        Args:
            doc_id: SHA256 hash of the file to remove.

        Returns:
            Number of chunks deleted.
        """
        results = self._db.get(where={"doc_id": doc_id})
        ids_to_delete = results["ids"]

        if ids_to_delete:
            self._db.delete(ids=ids_to_delete)

        return len(ids_to_delete)

    def count(self) -> int:
        """Return the total number of chunks in the store."""
        return self._db._collection.count()

    def get_all_chunks(self) -> list[Document]:
        """
        Retrieve ALL chunks from the store (for generation tasks).

        Returns:
            List of all Document objects in the store.
        """
        all_data = self._db.get(include=["documents", "metadatas"])
        documents = []
        for content, meta in zip(all_data["documents"], all_data["metadatas"]):
            documents.append(
                Document(page_content=content, metadata=meta)
            )
        return documents
