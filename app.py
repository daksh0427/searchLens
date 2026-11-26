"""
StudyLens — Premium AI-Powered Student Study Assistant
Main Streamlit Application Entry Point
"""

import streamlit as st
from pathlib import Path

# ─── PAGE CONFIG ──────────────────────────────────────────
st.set_page_config(
    page_title="StudyLens | AI Study Assistant",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── LOAD PREMIUM CSS ─────────────────────────────────────
css_path = Path(__file__).parent / "ui" / "styles" / "theme.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

# ─── IMPORTS ──────────────────────────────────────────────
from core.vectorstore import VectorStore
from core.retriever import Retriever
from core.llm import get_llm
from ui.components.sidebar import render_sidebar
from ui.components.flashcard_component import render_flashcards
from ui.components.quiz_component import render_quiz
from ui.components.chat_component import render_chat
from features.notes_generator import generate_notes, notes_to_download
from features.flashcard_generator import generate_flashcards, flashcards_to_csv
from features.diagram_generator import generate_diagram
from features.summary_generator import generate_all_summaries
from features.question_generator import generate_questions
from features.study_plan import generate_study_plan, plan_to_pdf_bytes
from features.evaluation import run_evaluation, render_metrics_dashboard


# ─── STATE & SERVICES ─────────────────────────────────────
@st.cache_resource
def init_vectorstore():
    return VectorStore()

@st.cache_resource
def init_retriever(_vectorstore):
    return Retriever(_vectorstore)

vectorstore = init_vectorstore()
retriever = init_retriever(vectorstore)

def get_current_llm():
    mode = st.session_state.get("llm_mode", "local")
    api_key = st.session_state.get("api_key", "")
    return get_llm(mode, api_key)


# ─── SIDEBAR ──────────────────────────────────────────────
render_sidebar(vectorstore)


# ─── MAIN HEADER ──────────────────────────────────────────
st.markdown(
    """<div class="hero-header">
        <h1 class="hero-title">StudyLens</h1>
        <div class="hero-subtitle">Your AI-Powered Study Assistant ✨</div>
    </div>""",
    unsafe_allow_html=True,
)


# ─── TABS ─────────────────────────────────────────────────
# We use emojis to make the tabs feel premium and distinct
tabs = st.tabs([
    "📝 Notes",
    "📊 Diagrams",
    "🃏 Flashcards",
    "📚 Summaries",
    "✏️ Practice",
    "💬 Chat",
    "📅 Study Plan",
    "📈 Metrics",
])

# ==============================================================================
# TAB 1 — Notes
# ==============================================================================
with tabs[0]:
    st.markdown(
        """<div class="section-header">
            <span class="section-icon">📝</span>
            <span class="section-title">Structured Notes</span>
        </div>
        <p class="section-desc">Generate beautifully formatted markdown notes from your materials.</p>""",
        unsafe_allow_html=True,
    )

    col_topic, col_btn = st.columns([3, 1], vertical_alignment="bottom")
    with col_topic:
        notes_topic = st.text_input(
            "Topic focus (optional):",
            placeholder="e.g., Neural Networks, History of Rome...",
            key="notes_topic",
            help="Leave blank to summarize everything.",
        )
    with col_btn:
        generate_btn = st.button("✨ Generate Notes", key="gen_notes", use_container_width=True)

    if generate_btn:
        if vectorstore.count() == 0:
            st.warning("⚠️ Please upload some documents first!")
        else:
            try:
                llm = get_current_llm()
                topic = notes_topic or "all topics from the uploaded documents"
                with st.spinner("✨ Crafting your notes..."):
                    notes = generate_notes(retriever, llm, topic)
                    st.session_state["generated_notes"] = notes
                    st.session_state["notes_topic_used"] = topic
            except Exception as e:
                st.error(f"❌ Error: {e}")

    if "generated_notes" in st.session_state:
        st.markdown(
            '<div class="notes-container animate-in">',
            unsafe_allow_html=True,
        )
        st.markdown(st.session_state["generated_notes"])
        st.markdown("</div>", unsafe_allow_html=True)

        filename, content = notes_to_download(
            st.session_state["generated_notes"],
            st.session_state.get("notes_topic_used", "notes"),
        )
        st.download_button(
            "⬇️ Download as Markdown",
            data=content,
            file_name=filename,
            mime="text/markdown",
            key="download_notes",
        )
    else:
        st.markdown(
            """<div class="empty-state">
                <span class="empty-state-icon">📄</span>
                <p class="empty-state-title">No notes generated yet</p>
                <p class="empty-state-text">Enter a topic and click Generate to start</p>
            </div>""",
            unsafe_allow_html=True,
        )

# ==============================================================================
# TAB 2 — Diagrams
# ==============================================================================
with tabs[1]:
    st.markdown(
        """<div class="section-header">
            <span class="section-icon">📊</span>
            <span class="section-title">Visual Diagrams</span>
        </div>
        <p class="section-desc">Turn complex concepts into clear flowcharts and diagrams.</p>""",
        unsafe_allow_html=True,
    )

    col_topic, col_btn = st.columns([3, 1], vertical_alignment="bottom")
    with col_topic:
        diagram_topic = st.text_input(
            "What should the diagram explain?",
            placeholder="e.g., Photosynthesis process, OSI Model layers...",
            key="diagram_topic",
        )
    with col_btn:
        generate_btn = st.button("🎨 Create Diagram", key="gen_diagram", use_container_width=True)

    if generate_btn:
        if not diagram_topic:
            st.warning("⚠️ Please enter a topic for the diagram.")
        elif vectorstore.count() == 0:
            st.warning("⚠️ Please upload some documents first!")
        else:
            try:
                llm = get_current_llm()
                with st.spinner("🎨 Designing your diagram..."):
                    result = generate_diagram(retriever, llm, diagram_topic)
                    st.session_state["diagram_result"] = result
            except Exception as e:
                st.error(f"❌ Error: {e}")

    if "diagram_result" in st.session_state:
        result = st.session_state["diagram_result"]
        if result.get("valid"):
            st.markdown(
                '<div class="mermaid-box animate-in">',
                unsafe_allow_html=True,
            )
            import streamlit.components.v1 as components
            html_code = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <script type="module">
                    import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
                    mermaid.initialize({{ startOnLoad: false, theme: 'default' }});
                    mermaid.run({{ querySelector: '.mermaid' }});
                </script>
            </head>
            <body style="margin: 0; padding: 0;">
                <pre class="mermaid" style="display: flex; justify-content: center; font-family: sans-serif; background: transparent; border: none; margin: 0; padding: 20px;">
{result['mermaid_code']}
                </pre>
            </body>
            </html>
            """
            components.html(html_code, height=500, scrolling=True)
            st.markdown("</div>", unsafe_allow_html=True)

            with st.expander("🔧 View Mermaid Code"):
                st.code(result["mermaid_code"], language="mermaid")
        elif result.get("error"):
            st.error(f"❌ {result['error']}")
    else:
         st.markdown(
            """<div class="empty-state">
                <span class="empty-state-icon">🗺️</span>
                <p class="empty-state-title">Visualize your knowledge</p>
                <p class="empty-state-text">Ask for a process, timeline, or hierarchy to generate a diagram</p>
            </div>""",
            unsafe_allow_html=True,
        )


# ==============================================================================
# TAB 3 — Flashcards
# ==============================================================================
with tabs[2]:
    st.markdown(
        """<div class="section-header">
            <span class="section-icon">🃏</span>
            <span class="section-title">Smart Flashcards</span>
        </div>
        <p class="section-desc">Interactive flashcards automatically generated from your notes.</p>""",
        unsafe_allow_html=True,
    )

    col_topic, col_count, col_btn = st.columns([2, 1, 1], vertical_alignment="bottom")
    with col_topic:
        fc_topic = st.text_input("Topic (optional):", key="fc_topic")
    with col_count:
        fc_count = st.number_input("Amount:", min_value=5, max_value=50, value=15, key="fc_count")
    with col_btn:
        generate_btn = st.button("🃏 Generate", key="gen_flashcards", use_container_width=True)

    if generate_btn:
        if vectorstore.count() == 0:
            st.warning("⚠️ Please upload some documents first!")
        else:
            try:
                llm = get_current_llm()
                topic = fc_topic or "all topics"
                with st.spinner("🃏 Crafting flashcards..."):
                    cards = generate_flashcards(retriever, llm, fc_count, topic)
                    if cards:
                        st.session_state["flashcards"] = cards
                        st.session_state["card_index"] = 0
                        st.toast(f"✅ Generated {len(cards)} flashcards!", icon="✅")
                    else:
                        st.error("❌ Could not generate flashcards. Try again.")
            except Exception as e:
                st.error(f"❌ Error: {e}")

    if "flashcards" in st.session_state:
        st.markdown('<div class="animate-in">', unsafe_allow_html=True)
        render_flashcards(st.session_state["flashcards"])
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="fancy-divider"></div>', unsafe_allow_html=True)
        csv_data = flashcards_to_csv(st.session_state["flashcards"])
        st.download_button(
            "⬇️ Export as CSV (Anki compatible)",
            data=csv_data,
            file_name="StudyLens_Flashcards.csv",
            mime="text/csv",
            key="download_flashcards",
        )
    else:
        render_flashcards([]) # Renders empty state


# ==============================================================================
# TAB 4 — Summaries
# ==============================================================================
with tabs[3]:
    st.markdown(
        """<div class="section-header">
            <span class="section-icon">📚</span>
            <span class="section-title">Cross-Doc Summaries</span>
        </div>
        <p class="section-desc">We detect topics across all your files and merge them into unified summaries.</p>""",
        unsafe_allow_html=True,
    )

    if st.button("📚 Analyze & Summarize All", key="gen_summaries"):
        if vectorstore.count() == 0:
            st.warning("⚠️ Please upload some documents first!")
        else:
            try:
                llm = get_current_llm()
                with st.spinner("📚 Analyzing topics and merging content..."):
                    summaries = generate_all_summaries(vectorstore, retriever, llm)
                    st.session_state["summaries"] = summaries
            except Exception as e:
                st.error(f"❌ Error: {e}")

    if "summaries" in st.session_state:
        st.markdown('<div class="animate-in">', unsafe_allow_html=True)
        for topic, summary in st.session_state["summaries"].items():
            st.markdown(
                f"""<div class="topic-card">
                    <div class="topic-badge">📌 {topic}</div>
                    <div style="margin-top:16px;">{summary}</div>
                </div>""",
                unsafe_allow_html=True,
            )
        st.markdown('</div>', unsafe_allow_html=True)
    else:
         st.markdown(
            """<div class="empty-state">
                <span class="empty-state-icon">📑</span>
                <p class="empty-state-title">Merge your knowledge</p>
                <p class="empty-state-text">Click generate to automatically find and summarize all topics</p>
            </div>""",
            unsafe_allow_html=True,
        )


# ==============================================================================
# TAB 5 — Practice
# ==============================================================================
with tabs[4]:
    st.markdown(
        """<div class="section-header">
            <span class="section-icon">✏️</span>
            <span class="section-title">Practice Test</span>
        </div>
        <p class="section-desc">Test your knowledge with auto-generated questions.</p>""",
        unsafe_allow_html=True,
    )

    col_topic, col_btn = st.columns([3, 1], vertical_alignment="bottom")
    with col_topic:
        pq_topic = st.text_input("Focus topic (optional):", key="pq_topic")
    with col_btn:
        generate_btn = st.button("✏️ Create Test", key="gen_questions", use_container_width=True)

    if generate_btn:
        if vectorstore.count() == 0:
            st.warning("⚠️ Please upload some documents first!")
        else:
            try:
                llm = get_current_llm()
                topic = pq_topic or "all topics"
                with st.spinner("✏️ Writing your practice test..."):
                    questions = generate_questions(retriever, llm, topic)
                    st.session_state["practice_questions"] = questions
                    total = (
                        len(questions.get("mcq", []))
                        + len(questions.get("short_answer", []))
                        + len(questions.get("descriptive", []))
                    )
                    if total > 0:
                        st.toast(f"✅ Ready! {total} questions generated.", icon="✅")
                    else:
                        st.error("❌ Could not generate questions. Try again.")
            except Exception as e:
                st.error(f"❌ Error: {e}")

    if "practice_questions" in st.session_state:
        st.markdown('<div class="animate-in">', unsafe_allow_html=True)
        render_quiz(st.session_state["practice_questions"])
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        render_quiz({})


# ==============================================================================
# TAB 6 — Chat
# ==============================================================================
with tabs[5]:
    if vectorstore.count() == 0:
        st.markdown(
            """<div class="empty-state" style="margin-top:40px;">
                <span class="empty-state-icon">💬</span>
                <p class="empty-state-title">Your AI Tutor is waiting</p>
                <p class="empty-state-text">Upload documents in the sidebar to start chatting</p>
            </div>""",
            unsafe_allow_html=True,
        )
    else:
        try:
            llm = get_current_llm()
            st.markdown('<div class="animate-in">', unsafe_allow_html=True)
            render_chat(retriever, llm)
            st.markdown('</div>', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"❌ Error: {e}")


# ==============================================================================
# TAB 7 — Study Plan
# ==============================================================================
with tabs[6]:
    st.markdown(
        """<div class="section-header">
            <span class="section-icon">📅</span>
            <span class="section-title">Study Planner</span>
        </div>
        <p class="section-desc">Enter your exam date, and we'll schedule what to study each day.</p>""",
        unsafe_allow_html=True,
    )

    col_date, col_btn = st.columns([2, 1], vertical_alignment="bottom")
    with col_date:
        deadline = st.date_input("When is your exam?", key="plan_deadline")
    with col_btn:
         generate_btn = st.button("📅 Plan Schedule", key="gen_plan", use_container_width=True)

    if generate_btn:
        if vectorstore.count() == 0:
            st.warning("⚠️ Please upload some documents first!")
        else:
            try:
                llm = get_current_llm()
                deadline_str = deadline.strftime("%Y-%m-%d")
                with st.spinner("📅 Calculating optimal study schedule..."):
                    plan_result = generate_study_plan(
                        vectorstore, retriever, llm, deadline_str
                    )
                    st.session_state["study_plan"] = plan_result
            except Exception as e:
                st.error(f"❌ Error: {e}")

    if "study_plan" in st.session_state:
        plan_result = st.session_state["study_plan"]

        if plan_result.get("error"):
            st.error(f"❌ {plan_result['error']}")
        elif plan_result.get("plan"):
            st.markdown('<div class="animate-in">', unsafe_allow_html=True)
            
            st.markdown(
                f"""<div class="feature-hint">
                    <span class="feature-hint-icon">🎯</span>
                    <span>Your plan covers <strong>{plan_result["total_days"]} days</strong> 
                    across <strong>{len(plan_result["topics"])} topics</strong>.</span>
                </div>""",
                unsafe_allow_html=True,
            )

            for day in plan_result["plan"]:
                topics_str = ", ".join(day["topics"]) if isinstance(day["topics"], list) else str(day["topics"])
                docs_str = ", ".join(day["documents_to_read"]) if isinstance(day["documents_to_read"], list) else str(day["documents_to_read"])

                read_html = f'<p style="margin:2px 0;"><strong>📄 Read:</strong> {docs_str}</p>' if docs_str else ''
                notes_html = f'<p style="margin:2px 0; color:#888;">💡 <em>{day.get("notes", "")}</em></p>' if day.get("notes") else ''
                
                st.markdown(
                    f'<div class="plan-day-card"><div class="plan-day-num"><small>Day</small><br>{day["day_number"]}</div><div class="plan-day-content"><div style="font-weight:800; color:#67C0AC; margin-bottom:4px; font-size:1.1em;">{day["date"]} <span style="font-weight:600; opacity:0.6; font-size:0.8em; margin-left:6px;">({day["study_hours"]}h)</span></div><p style="margin:2px 0;"><strong>📚 Topics:</strong> {topics_str}</p>{read_html}{notes_html}</div></div>',
                    unsafe_allow_html=True,
                )

            st.markdown('<div class="fancy-divider"></div>', unsafe_allow_html=True)
            try:
                pdf_bytes = plan_to_pdf_bytes(
                    plan_result["plan"],
                    plan_result["topics"],
                    deadline.strftime("%Y-%m-%d"),
                )
                st.download_button(
                    "⬇️ Download PDF Schedule",
                    data=pdf_bytes,
                    file_name="StudyLens_Schedule.pdf",
                    mime="application/pdf",
                    key="download_plan",
                )
            except Exception as e:
                st.warning(f"⚠️ PDF export failed: {e}")
            
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown(
            """<div class="empty-state">
                <span class="empty-state-icon">🗓️</span>
                <p class="empty-state-title">No schedule yet</p>
                <p class="empty-state-text">Pick your exam date and get a daily plan</p>
            </div>""",
            unsafe_allow_html=True,
        )


# ==============================================================================
# TAB 8 — Metrics
# ==============================================================================
with tabs[7]:
    st.markdown(
        """<div class="section-header">
            <span class="section-icon">📈</span>
            <span class="section-title">RAG Quality Metrics</span>
        </div>
        <p class="section-desc">Evaluate how well the AI answers questions based on your notes.</p>""",
        unsafe_allow_html=True,
    )

    st.markdown(
        """<div class="feature-hint" style="background:rgba(254,212,72,0.1); border-color:rgba(254,212,72,0.2);">
            <span class="feature-hint-icon">ℹ️</span>
            <span>RAGAS evaluation measures <strong>Faithfulness</strong> (no hallucinations) and 
            <strong>Relevancy</strong> (answers the prompt). It requires an OpenAI API key.</span>
        </div>""",
        unsafe_allow_html=True,
    )

    if st.button("🧪 Run Evaluation Suite", key="run_eval"):
        if vectorstore.count() == 0:
            st.warning("⚠️ Please upload some documents first!")
        else:
            api_key = st.session_state.get("api_key", "")
            if not api_key or api_key == "your_key_here":
                st.warning("⚠️ RAGAS evaluation requires an OpenAI API key in the sidebar.")
            else:
                try:
                    with st.spinner("🧪 Analyzing response quality..."):
                        eval_result = run_evaluation(
                            retriever,
                            st.session_state.get("llm_mode", "local"),
                            api_key,
                        )
                        st.session_state["eval_result"] = eval_result
                except Exception as e:
                    st.error(f"❌ Evaluation error: {e}")

    if "eval_result" in st.session_state:
        st.markdown('<div class="animate-in">', unsafe_allow_html=True)
        eval_result = st.session_state["eval_result"]
        if eval_result.get("error"):
            st.error(f"❌ {eval_result['error']}")
        else:
            scores = eval_result.get("scores", {})
            cols = st.columns(len(scores))
            for col, (metric, score) in zip(cols, scores.items()):
                with col:
                    st.markdown(
                        f"""<div class="metric-card">
                            <div class="metric-score">{score:.0%}</div>
                            <div class="metric-name">{metric}</div>
                        </div>""",
                        unsafe_allow_html=True,
                    )
                    st.progress(min(score, 1.0))
            
            st.markdown(
                """<div style="margin-top: 16px; padding: 12px; background: rgba(255,255,255,0.5); 
                border-radius: var(--radius-md); font-size: 0.85em; text-align:center;">
                <strong>Guide:</strong> 🟢 80%+ Excellent | 🟡 60-80% Good | 🟠 40-60% Needs Tuning | 🔴 <40% Poor
                </div>""",
                unsafe_allow_html=True,
            )
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown(
            """<div class="empty-state">
                <span class="empty-state-icon">📊</span>
                <p class="empty-state-title">No metrics run</p>
                <p class="empty-state-text">Run the suite to test system accuracy</p>
            </div>""",
            unsafe_allow_html=True,
        )
