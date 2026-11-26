"""
Study Plan Generator — Create a personalized day-by-day study plan
based on uploaded material and a user-provided deadline.
"""

import json
from datetime import datetime, timedelta

from langchain_core.language_models import BaseChatModel

from core.llm import invoke_llm
from core.vectorstore import VectorStore
from core.retriever import Retriever
from features.summary_generator import detect_topics


STUDY_PLAN_PROMPT = """You are an expert academic study planner. Based on the topics and materials below,
create a detailed day-by-day study plan.

Topics to cover: {topics}
Documents available: {documents}
Number of days available: {days}
Start date: {start_date}
Deadline: {deadline}

For each day, specify:
- Date (YYYY-MM-DD format)
- Topics to study
- Specific documents/pages to read
- Flashcards to review (if any previous topics need revision)
- Estimated study time in hours

Return ONLY a JSON array of day objects with keys:
"date", "day_number", "topics", "documents_to_read", "flashcards_review", "study_hours", "notes"

Distribute topics evenly. Include revision days before the deadline.
Harder/longer topics should get more days. Include at least one rest day if the schedule is more than 7 days.
Do not include any text outside the JSON array."""


def generate_study_plan(
    vectorstore: VectorStore,
    retriever: Retriever,
    llm: BaseChatModel,
    deadline: str,
) -> dict:
    """
    Generate a personalized study plan based on uploaded material.

    Args:
        vectorstore: For topic detection and document listing.
        retriever: For context about each topic's complexity.
        llm: For plan generation.
        deadline: Deadline date string in YYYY-MM-DD format.

    Returns:
        Dict with keys:
            - plan: List of day-plan dicts
            - topics: List of detected topics
            - total_days: Number of days until deadline
            - error: Error message if generation failed
    """
    # Detect topics
    topics = detect_topics(vectorstore, llm)
    if not topics:
        return {
            "plan": [],
            "topics": [],
            "total_days": 0,
            "error": "No topics detected. Please upload study material first.",
        }

    # Get document list
    docs = vectorstore.get_all_doc_ids()
    doc_names = [d["source"] for d in docs]

    # Calculate days
    try:
        deadline_date = datetime.strptime(deadline, "%Y-%m-%d").date()
    except ValueError:
        return {
            "plan": [],
            "topics": topics,
            "total_days": 0,
            "error": "Invalid date format. Please use YYYY-MM-DD.",
        }

    today = datetime.now().date()
    days_available = (deadline_date - today).days

    if days_available <= 0:
        return {
            "plan": [],
            "topics": topics,
            "total_days": 0,
            "error": "Deadline must be in the future.",
        }

    # Generate plan
    prompt = STUDY_PLAN_PROMPT.format(
        topics=", ".join(topics),
        documents=", ".join(doc_names),
        days=days_available,
        start_date=today.isoformat(),
        deadline=deadline,
    )

    for attempt in range(3):
        response = invoke_llm(llm, prompt)
        plan = _parse_plan(response)
        if plan:
            return {
                "plan": plan,
                "topics": topics,
                "total_days": days_available,
                "error": None,
            }

        prompt = (
            "Your previous response was not valid JSON. "
            "Return ONLY a JSON array of day objects. No markdown, no explanation.\n\n"
            + prompt
        )

    return {
        "plan": [],
        "topics": topics,
        "total_days": days_available,
        "error": "Could not generate a valid study plan. Please try again.",
    }


def _parse_plan(response: str) -> list[dict] | None:
    """Parse LLM response into study plan structure."""
    text = response.strip()

    if text.startswith("```"):
        lines = text.split("\n")[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines)

    try:
        data = json.loads(text)
        if isinstance(data, list):
            return _validate_plan(data)
    except json.JSONDecodeError:
        pass

    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end > start:
        try:
            data = json.loads(text[start : end + 1])
            if isinstance(data, list):
                return _validate_plan(data)
        except json.JSONDecodeError:
            pass

    return None


def _validate_plan(data: list) -> list[dict]:
    """Validate and normalize plan structure."""
    plan = []
    for item in data:
        if isinstance(item, dict):
            plan.append({
                "date": str(item.get("date", "")),
                "day_number": int(item.get("day_number", len(plan) + 1)),
                "topics": item.get("topics", []),
                "documents_to_read": item.get("documents_to_read", []),
                "flashcards_review": item.get("flashcards_review", []),
                "study_hours": float(item.get("study_hours", 2)),
                "notes": str(item.get("notes", "")),
            })
    return plan if plan else None


def plan_to_pdf_bytes(plan: list[dict], topics: list[str], deadline: str) -> bytes:
    """
    Export study plan as a PDF.

    Args:
        plan: List of day-plan dicts.
        topics: List of topic strings.
        deadline: Deadline date string.

    Returns:
        PDF file contents as bytes.
    """
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 15, "StudyLens Study Plan", ln=True, align="C")
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 8, f"Deadline: {deadline}", ln=True, align="C")
    pdf.cell(0, 8, f"Topics: {', '.join(topics)}", ln=True, align="C")
    pdf.ln(10)

    # Days
    for day in plan:
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_fill_color(103, 192, 172)  # #67C0AC
        pdf.set_text_color(255, 255, 255)
        pdf.cell(
            0, 10,
            f"Day {day['day_number']} - {day['date']} ({day['study_hours']}h)",
            ln=True, fill=True,
        )
        pdf.set_text_color(0, 0, 0)

        pdf.set_font("Helvetica", "", 11)

        # Topics
        topics_list = day.get("topics", [])
        if isinstance(topics_list, list):
            topics_str = ", ".join(str(t) for t in topics_list)
        else:
            topics_str = str(topics_list)
        pdf.cell(0, 7, f"  Topics: {topics_str}", ln=True)

        # Documents
        docs_list = day.get("documents_to_read", [])
        if isinstance(docs_list, list):
            docs_str = ", ".join(str(d) for d in docs_list)
        else:
            docs_str = str(docs_list)
        if docs_str:
            pdf.cell(0, 7, f"  Read: {docs_str}", ln=True)

        # Flashcards
        fc_list = day.get("flashcards_review", [])
        if isinstance(fc_list, list):
            fc_str = ", ".join(str(f) for f in fc_list)
        else:
            fc_str = str(fc_list)
        if fc_str:
            pdf.cell(0, 7, f"  Review flashcards: {fc_str}", ln=True)

        # Notes
        if day.get("notes"):
            pdf.set_font("Helvetica", "I", 10)
            pdf.cell(0, 7, f"  Note: {day['notes']}", ln=True)

        pdf.ln(5)

    return bytes(pdf.output())
