"""
Quiz Component — Premium practice questions with animated reveals.
"""

import streamlit as st


def render_quiz(questions: dict):
    """Render practice questions with premium styling and animated reveals."""
    if not any(questions.values()):
        st.markdown(
            """<div class="empty-state">
                <span class="empty-state-icon">✏️</span>
                <p class="empty-state-title">No practice questions yet</p>
                <p class="empty-state-text">Generate questions from your study material</p>
            </div>""",
            unsafe_allow_html=True,
        )
        return

    # ─── MCQ ──────────────────────────────────────────
    mcq_list = questions.get("mcq", [])
    if mcq_list:
        st.markdown(
            """<div class="section-header">
                <span class="section-icon">🔘</span>
                <span class="section-title">Multiple Choice</span>
            </div>
            <p class="section-desc">Select the correct answer, then reveal to check</p>""",
            unsafe_allow_html=True,
        )

        for i, q in enumerate(mcq_list):
            st.markdown(
                f"""<div class="quiz-card">
                    <div style="display:flex; align-items:flex-start; gap:10px;">
                        <span class="quiz-num">{i + 1}</span>
                        <div>
                            <div style="font-weight:700; color:#2D2D3F; line-height:1.5;">{q['question']}</div>
                            <span class="quiz-source">📖 {q.get('source', '')}</span>
                        </div>
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )

            options = q.get("options", {})
            st.radio(
                f"Select answer:",
                [f"**{k}.** {v}" for k, v in options.items()],
                key=f"mcq_{i}",
                label_visibility="collapsed",
            )

            col1, col2 = st.columns([1, 4])
            with col1:
                reveal_key = f"reveal_mcq_{i}"
                if st.button("🔍 Reveal", key=f"btn_mcq_{i}", use_container_width=True):
                    st.session_state[reveal_key] = not st.session_state.get(reveal_key, False)
                    st.rerun()

            if st.session_state.get(f"reveal_mcq_{i}"):
                correct = q.get("correct_answer", "?")
                correct_text = options.get(correct, "")
                st.markdown(
                    f'<div class="quiz-reveal">✅ <strong>{correct}</strong> — {correct_text}</div>',
                    unsafe_allow_html=True,
                )

            st.markdown("")

    # ─── Short Answer ─────────────────────────────────
    sa_list = questions.get("short_answer", [])
    if sa_list:
        st.markdown('<div class="fancy-divider"></div>', unsafe_allow_html=True)
        st.markdown(
            """<div class="section-header">
                <span class="section-icon">✍️</span>
                <span class="section-title">Short Answer</span>
            </div>
            <p class="section-desc">Write your answer, then reveal the model answer</p>""",
            unsafe_allow_html=True,
        )

        for i, q in enumerate(sa_list):
            st.markdown(
                f"""<div class="quiz-card">
                    <div style="display:flex; align-items:flex-start; gap:10px;">
                        <span class="quiz-num">{i + 1}</span>
                        <div>
                            <div style="font-weight:700; color:#2D2D3F; line-height:1.5;">{q['question']}</div>
                            <span class="quiz-source">📖 {q.get('source', '')}</span>
                        </div>
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )

            st.text_area(
                "Your answer:",
                key=f"sa_input_{i}",
                height=80,
                label_visibility="collapsed",
                placeholder="Type your answer here...",
            )

            col1, col2 = st.columns([1, 4])
            with col1:
                reveal_key = f"reveal_sa_{i}"
                if st.button("🔍 Reveal", key=f"btn_sa_{i}", use_container_width=True):
                    st.session_state[reveal_key] = not st.session_state.get(reveal_key, False)
                    st.rerun()

            if st.session_state.get(f"reveal_sa_{i}"):
                st.markdown(
                    f'<div class="quiz-reveal">📖 <strong>Model Answer:</strong><br>{q.get("answer", "N/A")}</div>',
                    unsafe_allow_html=True,
                )

            st.markdown("")

    # ─── Descriptive ──────────────────────────────────
    desc_list = questions.get("descriptive", [])
    if desc_list:
        st.markdown('<div class="fancy-divider"></div>', unsafe_allow_html=True)
        st.markdown(
            """<div class="section-header">
                <span class="section-icon">📝</span>
                <span class="section-title">Descriptive</span>
            </div>
            <p class="section-desc">Write a detailed response, then check the guidelines</p>""",
            unsafe_allow_html=True,
        )

        for i, q in enumerate(desc_list):
            st.markdown(
                f"""<div class="quiz-card">
                    <div style="display:flex; align-items:flex-start; gap:10px;">
                        <span class="quiz-num">{i + 1}</span>
                        <div>
                            <div style="font-weight:700; color:#2D2D3F; line-height:1.5;">{q['question']}</div>
                            <span class="quiz-source">📖 {q.get('source', '')}</span>
                        </div>
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )

            st.text_area(
                "Your answer:",
                key=f"desc_input_{i}",
                height=120,
                label_visibility="collapsed",
                placeholder="Write your detailed answer...",
            )

            col1, col2 = st.columns([1, 4])
            with col1:
                reveal_key = f"reveal_desc_{i}"
                if st.button("🔍 Reveal", key=f"btn_desc_{i}", use_container_width=True):
                    st.session_state[reveal_key] = not st.session_state.get(reveal_key, False)
                    st.rerun()

            if st.session_state.get(f"reveal_desc_{i}"):
                st.markdown(
                    f'<div class="quiz-reveal">📋 <strong>Guidelines:</strong><br>{q.get("guidelines", "N/A")}</div>',
                    unsafe_allow_html=True,
                )

            st.markdown("")
