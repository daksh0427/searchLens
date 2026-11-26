"""
Diagram Generator — Generate Mermaid.js diagrams from study material.
Detects content type (process, hierarchy, timeline, relationship) and
produces the appropriate diagram type.
"""

from langchain_core.language_models import BaseChatModel

from core.llm import invoke_llm
from core.retriever import Retriever


DIAGRAM_PROMPT = """You are an expert Mermaid.js diagram generator. Analyze the context below and generate a flowchart diagram that best represents the structure, process, or relationships described.
You MUST ONLY generate a top-down flowchart using the "flowchart TD" declaration.
Use standard flowchart syntax (e.g., A[Node] --> B[Node] or A[Node] -->|Label text| B[Node]).
CRITICAL: Do NOT use invalid arrow syntax like "-->|Text|>" or "->". The arrow must be exactly "-->" or "-->|Text|".
Return ONLY the raw Mermaid syntax starting with "flowchart TD".
Do not include any explanation, markdown code fences, or unsupported characters like "...".

Context:
{context}

Topic: {topic}"""


# Valid Mermaid diagram type declarations
VALID_DIAGRAM_STARTS = [
    "graph ",
    "flowchart ",
]


def generate_diagram(
    retriever: Retriever,
    llm: BaseChatModel,
    topic: str,
) -> dict:
    """
    Generate a Mermaid.js diagram for a given topic.

    Args:
        retriever: The Retriever instance.
        llm: The LLM instance.
        topic: The topic to create a diagram for.

    Returns:
        Dict with keys:
            - mermaid_code: Raw Mermaid syntax string
            - diagram_type: Detected diagram type (e.g., "flowchart")
            - valid: Boolean indicating if the syntax appears valid
            - error: Error message if generation failed
    """
    grouped_docs = retriever.retrieve_for_generation(topic)

    if not grouped_docs:
        return {
            "mermaid_code": "",
            "diagram_type": "unknown",
            "valid": False,
            "error": "No documents found. Please upload some study material first.",
        }

    context = retriever.format_context(grouped_docs)
    prompt = DIAGRAM_PROMPT.format(context=context, topic=topic)

    # Generate diagram with retry
    for attempt in range(2):
        response = invoke_llm(llm, prompt)
        mermaid_code = _clean_mermaid(response)
        diagram_type = _detect_diagram_type(mermaid_code)

        if diagram_type != "unknown":
            return {
                "mermaid_code": mermaid_code,
                "diagram_type": diagram_type,
                "valid": True,
                "error": None,
            }

        # Retry with more explicit instructions
        prompt = (
            "Your previous response was not valid Mermaid syntax. "
            "Return ONLY a flowchart diagram starting with 'flowchart TD'. "
            "Use '-->' for connections. Do not use '->'. "
            "No explanation, no code fences.\n\n" + prompt
        )

    return {
        "mermaid_code": mermaid_code,
        "diagram_type": "unknown",
        "valid": False,
        "error": "Could not generate valid Mermaid syntax. Try a different topic.",
    }


def _clean_mermaid(response: str) -> str:
    """Strip markdown code fences and extra whitespace from Mermaid output."""
    text = response.strip()

    # Remove markdown code fences
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:]  # Remove opening fence
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]  # Remove closing fence
        text = "\n".join(lines).strip()

    # Fix common LLM hallucinated arrow syntax e.g. -->|Text|>
    text = text.replace("|>", "| ")

    return text


def _detect_diagram_type(code: str) -> str:
    """Detect the diagram type from Mermaid code."""
    first_line = code.split("\n")[0].strip().lower() if code else ""
    for start in VALID_DIAGRAM_STARTS:
        if first_line.startswith(start.lower()):
            return start.strip()
    return "unknown"
