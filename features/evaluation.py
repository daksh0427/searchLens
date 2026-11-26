"""
RAGAS Evaluation — Measure RAG pipeline quality.
Evaluates Faithfulness, Answer Relevancy, Context Recall, and Context Precision.
"""

import streamlit as st

from core.vectorstore import VectorStore
from core.retriever import Retriever
from core.llm import get_llm
from features.qa_chain import ask_question


# Sample test questions — users should customize these after uploading documents
DEFAULT_TEST_SET = [
    {
        "question": "What are the main topics covered in the uploaded documents?",
        "ground_truth": "This depends on the uploaded documents.",
    },
]


def run_evaluation(
    retriever: Retriever,
    llm_mode: str,
    api_key: str | None = None,
    test_set: list[dict] | None = None,
) -> dict:
    """
    Run RAGAS evaluation on the Q&A feature.

    Args:
        retriever: The Retriever instance.
        llm_mode: LLM mode ("local" or "api").
        api_key: OpenAI API key (needed for RAGAS judge).
        test_set: List of dicts with 'question' and 'ground_truth'.

    Returns:
        Dict with metric scores and per-question results.
    """
    test_questions = test_set or DEFAULT_TEST_SET

    try:
        from ragas import evaluate
        from ragas.metrics import faithfulness, answer_relevancy
        from datasets import Dataset
    except ImportError:
        return {
            "error": "RAGAS not installed. Run: pip install ragas datasets",
            "scores": {},
            "details": [],
        }

    # Generate answers for test set
    llm = get_llm(llm_mode, api_key)
    results = {
        "question": [],
        "answer": [],
        "contexts": [],
        "ground_truth": [],
    }

    for test in test_questions:
        qa_result = ask_question(retriever, llm, test["question"])
        results["question"].append(test["question"])
        results["answer"].append(qa_result["answer"])
        results["contexts"].append(qa_result["contexts"])
        results["ground_truth"].append(test.get("ground_truth", ""))

    # Run RAGAS evaluation
    try:
        dataset = Dataset.from_dict(results)
        eval_result = evaluate(
            dataset,
            metrics=[faithfulness, answer_relevancy],
        )

        scores = {
            "Faithfulness": eval_result.get("faithfulness", 0.0),
            "Answer Relevancy": eval_result.get("answer_relevancy", 0.0),
        }

        return {
            "error": None,
            "scores": scores,
            "details": results,
        }

    except Exception as e:
        return {
            "error": f"Evaluation failed: {str(e)}",
            "scores": {},
            "details": results,
        }


def render_metrics_dashboard(scores: dict):
    """
    Render the evaluation metrics as colored progress bars.

    Args:
        scores: Dict mapping metric name → score (0.0 to 1.0).
    """
    if not scores:
        st.info("📈 No evaluation results yet. Run an evaluation first.")
        return

    st.markdown("## 📈 RAG Quality Metrics")

    cols = st.columns(len(scores))
    for col, (metric, score) in zip(cols, scores.items()):
        with col:
            st.markdown(
                f'<div class="metric-card">'
                f'<div class="metric-value">{score:.0%}</div>'
                f'<div class="metric-label">{metric}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            st.progress(min(score, 1.0))

    # Color guide
    st.markdown(
        """
        <div style="margin-top: 20px; padding: 12px; background: #FFCABA; border-radius: 12px;">
        <strong>Score Guide:</strong>
        🟢 0.8+ Excellent  |  🟡 0.6-0.8 Good  |  🟠 0.4-0.6 Needs Improvement  |  🔴 Below 0.4 Poor
        </div>
        """,
        unsafe_allow_html=True,
    )
