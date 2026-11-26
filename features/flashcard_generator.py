"""
Flashcard Generator — Generate interactive study flashcards from uploaded material.
Produces JSON-structured flashcards with front/back/source fields.
"""

import json
import csv
import io

from langchain_core.language_models import BaseChatModel

from core.llm import invoke_llm
from core.retriever import Retriever


FLASHCARD_PROMPT = """You are a study assistant. From the context below generate {n} flashcards.
Return ONLY a JSON array with objects containing "front", "back", and "source" keys.
Front should be a question or term. Back should be the answer or definition.
Source should be the document name it came from.
Do not include any text outside the JSON array.

Context:
{context}"""


def generate_flashcards(
    retriever: Retriever,
    llm: BaseChatModel,
    num_cards: int = 15,
    topic: str = "all topics",
) -> list[dict]:
    """
    Generate flashcards from uploaded material.

    Each flashcard has:
    - front: A question or term
    - back: The answer or definition
    - source: The source document name

    Args:
        retriever: The Retriever instance for context retrieval.
        llm: The LLM instance for generation.
        num_cards: Minimum number of flashcards to generate.
        topic: Specific topic or "all topics".

    Returns:
        List of flashcard dicts with 'front', 'back', 'source' keys.
    """
    grouped_docs = retriever.retrieve_for_generation(topic)

    if not grouped_docs:
        return []

    context = retriever.format_context(grouped_docs)
    prompt = FLASHCARD_PROMPT.format(n=num_cards, context=context)

    # Attempt generation with retry on JSON parse failure
    for attempt in range(3):
        response = invoke_llm(llm, prompt)
        flashcards = _parse_flashcards(response)
        if flashcards:
            return flashcards

        # Retry with a more explicit prompt
        prompt = (
            "Your previous response was not valid JSON. "
            "Please return ONLY a JSON array. No markdown, no explanation. "
            "Example: [{\"front\": \"Q\", \"back\": \"A\", \"source\": \"doc.pdf\"}]\n\n"
            + prompt
        )

    return []


def _parse_flashcards(response: str) -> list[dict]:
    """
    Parse LLM response into flashcard dicts.
    Handles common issues like markdown code fences around JSON.
    """
    # Strip markdown code fences if present
    text = response.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first and last lines (code fences)
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)

    try:
        data = json.loads(text)
        if isinstance(data, list):
            # Validate each card has the required keys
            valid_cards = []
            for card in data:
                if isinstance(card, dict) and "front" in card and "back" in card:
                    valid_cards.append({
                        "front": str(card["front"]),
                        "back": str(card["back"]),
                        "source": str(card.get("source", "Unknown")),
                    })
            return valid_cards
    except json.JSONDecodeError:
        pass

    # Try to find a JSON array within the text
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        try:
            data = json.loads(text[start : end + 1])
            if isinstance(data, list):
                return [
                    {
                        "front": str(c.get("front", "")),
                        "back": str(c.get("back", "")),
                        "source": str(c.get("source", "Unknown")),
                    }
                    for c in data
                    if isinstance(c, dict) and "front" in c and "back" in c
                ]
        except json.JSONDecodeError:
            pass

    return []


def flashcards_to_csv(flashcards: list[dict]) -> str:
    """
    Export flashcards as a CSV string.

    Args:
        flashcards: List of flashcard dicts.

    Returns:
        CSV string with columns: Question, Answer, Source.
    """
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Question", "Answer", "Source"])
    for card in flashcards:
        writer.writerow([card["front"], card["back"], card["source"]])
    return output.getvalue()
