"""
Notes Generator — Auto-generate structured markdown study notes
from uploaded documents with proper citations.
"""

from langchain_core.language_models import BaseChatModel

from core.llm import invoke_llm
from core.retriever import Retriever


NOTES_PROMPT = """You are an expert academic note-taker. Using only the context provided below, 
generate comprehensive structured notes in markdown format. 
Use H2 headings for main topics, H3 for subtopics, bullet points for key facts, 
and bold for important terms. End each section with a 2-line summary. 
Cite the source document name after each section in italics.
Do not add any information not present in the context.

Context:
{context}

Topic: {topic}"""


def generate_notes(
    retriever: Retriever,
    llm: BaseChatModel,
    topic: str = "all topics from the uploaded documents",
) -> str:
    """
    Generate structured markdown notes from uploaded material.

    Retrieves top-15 chunks per topic and produces clean markdown
    with H1/H2/H3 headings, bullet points, bold terms, section
    summaries, and source citations.

    Args:
        retriever: The Retriever instance for context retrieval.
        llm: The LLM instance for generation.
        topic: Specific topic to generate notes for, or "all topics".

    Returns:
        Markdown-formatted notes string.
    """
    # Retrieve relevant context
    grouped_docs = retriever.retrieve_for_generation(topic)

    if not grouped_docs:
        return "⚠️ No documents found. Please upload some study material first."

    context = retriever.format_context(grouped_docs)

    # Generate notes
    prompt = NOTES_PROMPT.format(context=context, topic=topic)
    notes = invoke_llm(llm, prompt)

    return notes


def notes_to_download(notes: str, topic: str = "notes") -> tuple[str, str]:
    """
    Prepare notes for download as a .md file.

    Args:
        notes: The markdown notes content.
        topic: Topic name for the filename.

    Returns:
        Tuple of (filename, content) for Streamlit download.
    """
    safe_topic = "".join(
        c if c.isalnum() or c in " -_" else "_" for c in topic
    ).strip()
    filename = f"StudyLens_{safe_topic}_Notes.md"
    return filename, notes
