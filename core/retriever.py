"""
Retriever — Context retrieval with source grouping.
Wraps the VectorStore similarity search and groups retrieved chunks
by source document so the LLM can reason across sources.
"""

from collections import defaultdict

from langchain_core.documents import Document

import config
from core.vectorstore import VectorStore


class Retriever:
    """
    Smart retrieval layer that groups results by source document.

    Provides two retrieval modes:
    - retrieve_for_qa(): top-8 chunks for conversational Q&A
    - retrieve_for_generation(): top-15 chunks for content generation
    """

    def __init__(self, vectorstore: VectorStore):
        self._vs = vectorstore

    def _retrieve_and_group(
        self, query: str, k: int
    ) -> dict[str, list[Document]]:
        """
        Retrieve top-k chunks and group them by source document.

        Args:
            query: The search query.
            k: Number of chunks to retrieve.

        Returns:
            Dict mapping source filename → list of Documents from that source,
            ordered by chunk_index within each source.
        """
        results = self._vs.similarity_search(query, k=k)

        grouped = defaultdict(list)
        for doc in results:
            source = doc.metadata.get("source", "Unknown")
            grouped[source].append(doc)

        # Sort chunks within each source by their position in the original document
        for source in grouped:
            grouped[source].sort(
                key=lambda d: d.metadata.get("chunk_index", 0)
            )

        return dict(grouped)

    def retrieve_for_qa(self, query: str) -> dict[str, list[Document]]:
        """
        Retrieve context for Q&A — top 8 chunks grouped by source.

        Args:
            query: User's question.

        Returns:
            Dict mapping source filename → list of relevant Documents.
        """
        return self._retrieve_and_group(query, k=config.QA_TOP_K)

    def retrieve_for_generation(
        self, query: str
    ) -> dict[str, list[Document]]:
        """
        Retrieve context for content generation — top 15 chunks grouped by source.

        Args:
            query: Topic or subject for generation.

        Returns:
            Dict mapping source filename → list of relevant Documents.
        """
        return self._retrieve_and_group(query, k=config.GENERATION_TOP_K)

    def format_context(
        self, grouped_docs: dict[str, list[Document]]
    ) -> str:
        """
        Format grouped documents into a single context string for the LLM.

        Each source's chunks are grouped under a header with metadata,
        making it easy for the LLM to cite sources.

        Args:
            grouped_docs: Output from retrieve_for_qa or retrieve_for_generation.

        Returns:
            Formatted context string ready for prompt injection.
        """
        context_parts = []

        for source, docs in grouped_docs.items():
            # Build source header
            file_type = docs[0].metadata.get("file_type", "unknown")
            context_parts.append(f"\n--- Source: {source} ({file_type}) ---")

            for doc in docs:
                # Build location info
                location = ""
                if file_type == "pdf":
                    page = doc.metadata.get("page_number", "?")
                    location = f"[Page {page}]"
                elif file_type == "pptx":
                    slide = doc.metadata.get("slide_number", "?")
                    title = doc.metadata.get("slide_title", "")
                    location = f"[Slide {slide}"
                    if title:
                        location += f": {title}"
                    location += "]"
                elif file_type == "docx":
                    heading = doc.metadata.get("section_heading", "")
                    if heading:
                        location = f"[Section: {heading}]"
                elif file_type == "image":
                    location = "[OCR Text]"

                if location:
                    context_parts.append(location)
                context_parts.append(doc.page_content)
                context_parts.append("")  # blank line between chunks

        return "\n".join(context_parts)
