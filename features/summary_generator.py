"""
Summary Generator — Generate topic-wise summaries across ALL uploaded documents.
Merges content from multiple sources under unified topic headings.
"""

from langchain_core.language_models import BaseChatModel

from core.llm import invoke_llm
from core.vectorstore import VectorStore
from core.retriever import Retriever


TOPIC_DETECTION_PROMPT = """Analyze the following text excerpts from multiple study documents.
Identify the main topics covered across ALL documents.
Return ONLY a JSON array of topic strings, nothing else.
Example: ["Neural Networks", "Sorting Algorithms", "Data Structures"]

Text excerpts:
{excerpts}"""


SUMMARY_PROMPT = """You are an expert academic summarizer. Using only the context below,
generate a comprehensive summary for the topic: {topic}

The context may come from multiple different documents. Merge all information
about this topic into one coherent summary.

Requirements:
- Start with a one-paragraph overview
- Use bullet points for key concepts
- Bold important terms
- At the end, list which source documents contributed to this summary in italics
- Do not add any information not present in the context

Context:
{context}"""


def detect_topics(
    vectorstore: VectorStore,
    llm: BaseChatModel,
    max_excerpts: int = 30,
) -> list[str]:
    """
    Detect main topics across all uploaded documents.

    Samples chunks from the vector store and uses the LLM to identify
    overarching topics.

    Args:
        vectorstore: The VectorStore instance.
        llm: The LLM instance.
        max_excerpts: Maximum number of chunks to sample.

    Returns:
        List of topic strings.
    """
    all_chunks = vectorstore.get_all_chunks()
    if not all_chunks:
        return []

    # Sample chunks evenly across the collection
    step = max(1, len(all_chunks) // max_excerpts)
    sampled = all_chunks[::step][:max_excerpts]

    excerpts = "\n---\n".join(
        f"[{doc.metadata.get('source', 'Unknown')}]: {doc.page_content[:200]}"
        for doc in sampled
    )

    prompt = TOPIC_DETECTION_PROMPT.format(excerpts=excerpts)
    response = invoke_llm(llm, prompt)

    # Parse topics from response
    import json

    text = response.strip()
    if text.startswith("```"):
        lines = text.split("\n")[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)

    try:
        topics = json.loads(text)
        if isinstance(topics, list):
            return [str(t) for t in topics]
    except json.JSONDecodeError:
        # Try to find array in response
        start = text.find("[")
        end = text.rfind("]")
        if start != -1 and end > start:
            try:
                topics = json.loads(text[start : end + 1])
                return [str(t) for t in topics]
            except json.JSONDecodeError:
                pass

    return []


def generate_summary(
    retriever: Retriever,
    llm: BaseChatModel,
    topic: str,
) -> str:
    """
    Generate a summary for a specific topic, merging content across all sources.

    Args:
        retriever: The Retriever instance.
        llm: The LLM instance.
        topic: The topic to summarize.

    Returns:
        Markdown-formatted summary string.
    """
    grouped_docs = retriever.retrieve_for_generation(topic)

    if not grouped_docs:
        return f"⚠️ No relevant content found for topic: {topic}"

    context = retriever.format_context(grouped_docs)
    prompt = SUMMARY_PROMPT.format(topic=topic, context=context)
    summary = invoke_llm(llm, prompt)

    # Add source tag header
    sources = list(grouped_docs.keys())
    source_tag = ", ".join(f"`{s}`" for s in sources)
    header = f"📚 **Sources:** {source_tag}\n\n"

    return header + summary


def generate_all_summaries(
    vectorstore: VectorStore,
    retriever: Retriever,
    llm: BaseChatModel,
) -> dict[str, str]:
    """
    Generate summaries for ALL detected topics.

    Args:
        vectorstore: For topic detection.
        retriever: For context retrieval per topic.
        llm: For generation.

    Returns:
        Dict mapping topic name → markdown summary.
    """
    topics = detect_topics(vectorstore, llm)

    if not topics:
        return {"General": "⚠️ Could not detect specific topics. Please upload more material."}

    summaries = {}
    for topic in topics:
        summaries[topic] = generate_summary(retriever, llm, topic)

    return summaries
