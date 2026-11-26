"""
Practice Question Generator — Generate MCQ, short answer, and descriptive
exam questions from uploaded study material.
"""

import json

from langchain_core.language_models import BaseChatModel

from core.llm import invoke_llm
from core.retriever import Retriever


QUESTION_PROMPT = """You are an exam question setter. From the context below generate:
- 5 multiple choice questions with options A B C D and the correct answer marked
- 5 short answer questions with model answers under 3 sentences
- 3 descriptive questions with answer guidelines

Return as structured JSON with keys: mcq, short_answer, descriptive.

For mcq, each item must have: "question", "options" (object with keys A, B, C, D), 
"correct_answer" (the letter), "source" (document name and page/slide number).

For short_answer, each item must have: "question", "answer", "source".

For descriptive, each item must have: "question", "guidelines", "source".

Context:
{context}"""


def generate_questions(
    retriever: Retriever,
    llm: BaseChatModel,
    topic: str = "all topics",
) -> dict:
    """
    Generate practice questions from uploaded material.

    Produces three types of questions:
    - MCQ: Multiple choice with 4 options and correct answer
    - Short answer: With model answers under 3 sentences
    - Descriptive: With answer guidelines

    Args:
        retriever: The Retriever instance.
        llm: The LLM instance.
        topic: Specific topic or "all topics".

    Returns:
        Dict with keys: 'mcq', 'short_answer', 'descriptive'.
        Each contains a list of question dicts.
        Returns empty structure if generation fails.
    """
    empty_result = {"mcq": [], "short_answer": [], "descriptive": []}

    grouped_docs = retriever.retrieve_for_generation(topic)

    if not grouped_docs:
        return empty_result

    context = retriever.format_context(grouped_docs)
    prompt = QUESTION_PROMPT.format(context=context)

    # Attempt generation with retry
    for attempt in range(3):
        response = invoke_llm(llm, prompt)
        questions = _parse_questions(response)
        if questions:
            return questions

        prompt = (
            "Your previous response was not valid JSON. "
            "Return ONLY a JSON object with keys: mcq, short_answer, descriptive. "
            "No markdown, no explanation.\n\n" + prompt
        )

    return empty_result


def _parse_questions(response: str) -> dict | None:
    """Parse LLM response into structured question dict."""
    text = response.strip()

    # Strip code fences
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines)

    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return _validate_questions(data)
    except json.JSONDecodeError:
        pass

    # Try to find JSON object in response
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        try:
            data = json.loads(text[start : end + 1])
            if isinstance(data, dict):
                return _validate_questions(data)
        except json.JSONDecodeError:
            pass

    return None


def _validate_questions(data: dict) -> dict:
    """Validate and normalize question structure."""
    result = {"mcq": [], "short_answer": [], "descriptive": []}

    # Validate MCQs
    for q in data.get("mcq", []):
        if isinstance(q, dict) and "question" in q:
            result["mcq"].append({
                "question": str(q["question"]),
                "options": q.get("options", {"A": "", "B": "", "C": "", "D": ""}),
                "correct_answer": str(q.get("correct_answer", "A")),
                "source": str(q.get("source", "Unknown")),
            })

    # Validate short answer
    for q in data.get("short_answer", []):
        if isinstance(q, dict) and "question" in q:
            result["short_answer"].append({
                "question": str(q["question"]),
                "answer": str(q.get("answer", "")),
                "source": str(q.get("source", "Unknown")),
            })

    # Validate descriptive
    for q in data.get("descriptive", []):
        if isinstance(q, dict) and "question" in q:
            result["descriptive"].append({
                "question": str(q["question"]),
                "guidelines": str(q.get("guidelines", "")),
                "source": str(q.get("source", "Unknown")),
            })

    return result
