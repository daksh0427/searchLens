"""
Chat Component — Premium conversational Q&A with styled bubbles.
"""

import streamlit as st
from langchain_core.language_models import BaseChatModel

from core.retriever import Retriever
from features.qa_chain import ask_question


def render_chat(retriever: Retriever, llm: BaseChatModel):
    """Render premium chat interface with styled message bubbles."""

    # Initialize history
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    # Welcome message if empty
    if not st.session_state["chat_history"]:
        st.markdown(
            """<div style="text-align:center; padding:40px 20px;">
                <div style="font-size:3em; margin-bottom:8px;">💬</div>
                <p style="font-size:1.1em; font-weight:700; color:#2D2D3F; margin:0 0 4px;">
                    Ask me anything about your notes
                </p>
                <p style="font-size:0.88em; color:#999; margin:0;">
                    Every answer includes source citations from your documents
                </p>
            </div>""",
            unsafe_allow_html=True,
        )

    # Chat messages
    for msg in st.session_state["chat_history"]:
        if msg["role"] == "user":
            st.markdown(
                f"""<div class="chat-user-bubble">
                    <span class="chat-sender">You</span>
                    {msg["content"]}
                </div>""",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""<div class="chat-bot-bubble">
                    <span class="chat-sender">StudyLens</span>
                    {msg["content"]}
                </div>""",
                unsafe_allow_html=True,
            )

    # Input
    user_input = st.chat_input("Ask a question about your notes...")

    if user_input:
        st.session_state["chat_history"].append({"role": "user", "content": user_input})

        with st.spinner("🔍 Searching your documents..."):
            # Build history context
            history = []
            msgs = st.session_state["chat_history"]
            for i in range(0, len(msgs) - 1, 2):
                if i + 1 < len(msgs) and msgs[i]["role"] == "user" and msgs[i + 1]["role"] == "assistant":
                    history.append({
                        "question": msgs[i]["content"],
                        "answer": msgs[i + 1]["content"],
                    })

            result = ask_question(retriever, llm, user_input, history[-3:])

        st.session_state["chat_history"].append({"role": "assistant", "content": result["answer"]})
        st.rerun()

    # Clear button
    if st.session_state["chat_history"]:
        st.markdown("")
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            if st.button("🗑️ Clear", key="clear_chat", use_container_width=True):
                st.session_state["chat_history"] = []
                st.rerun()
