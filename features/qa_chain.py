"""
Q&A Chain — Conversational question answering over uploaded documents.
Maintains chat history within the session and produces cited answers
with a References section.
"""

from langchain_core.language_models import BaseChatModel

from core.llm import invoke_llm
from core.retriever import Retriever


QA_PROMPT = """You are StudyLens, a helpful study assistant. Answer the question using ONLY 
the provided context from the student's uploaded documents.
Be clear and concise. Use bullet points where helpful.
At the end of your answer always include a References section listing:
- Document name
- Page or slide number
- A one-sentence excerpt from the source

If the context does not contain enough information to answer, say exactly:
"I couldn't find relevant information in your uploaded documents for this question."
Never make up information.

Context:
{context}

Question: {question}"""


def ask_question(
    retriever: Retriever,
    llm: BaseChatModel,
    question: str,
    chat_history: list[dict] | None = None,
) -> dict:
    """
    Answer a question using the uploaded documents.

    Retrieves relevant context, generates a cited answer, and returns
    both the answer and the retrieved context for evaluation.

    Args:
        retriever: The Retriever instance.
        llm: The LLM instance.
        question: The user's question.
        chat_history: Optional list of previous Q&A pairs for context.

    Returns:
        Dict with keys:
            - answer: The LLM's cited response
            - contexts: List of retrieved document chunks (for RAGAS eval)
            - sources: List of source filenames that contributed
    """
    # Retrieve relevant context
    grouped_docs = retriever.retrieve_for_qa(question)

    if not grouped_docs:
        return {
            "answer": "I couldn't find relevant information in your uploaded documents for this question.",
            "contexts": [],
            "sources": [],
        }

    context = retriever.format_context(grouped_docs)

    # Build the prompt with optional chat history
    full_prompt = ""
    if chat_history:
        history_text = "\n".join(
            f"Student: {h['question']}\nStudyLens: {h['answer']}"
            for h in chat_history[-3:]  # Last 3 exchanges for context
        )
        full_prompt += f"Previous conversation:\n{history_text}\n\n"

    full_prompt += QA_PROMPT.format(context=context, question=question)

    # Generate answer
    answer = invoke_llm(llm, full_prompt)

    # Collect sources
    sources = list(grouped_docs.keys())

    # Collect all context chunks for RAGAS evaluation
    all_contexts = []
    for docs in grouped_docs.values():
        for doc in docs:
            all_contexts.append(doc.page_content)

    return {
        "answer": answer,
        "contexts": all_contexts,
        "sources": sources,
    }
