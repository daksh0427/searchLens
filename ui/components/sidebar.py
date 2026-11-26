"""
Sidebar Component — Premium dark sidebar with upload, file management, and settings.
"""

import hashlib
import streamlit as st
from pathlib import Path

import config
from core.ingestion.pdf_loader import load_pdf
from core.ingestion.pptx_loader import load_pptx
from core.ingestion.docx_loader import load_docx
from core.ingestion.image_ocr import load_image
from core.chunker import chunk_documents
from core.vectorstore import VectorStore


FILE_ICONS = {"pdf": "📄", "pptx": "📊", "docx": "📝", "image": "🖼️"}


def render_sidebar(vectorstore: VectorStore):
    """Render the premium dark sidebar."""
    with st.sidebar:
        # ─── Logo ─────────────────────────────────────
        st.markdown(
            """
            <div style="text-align:center; padding: 8px 0 4px;">
                <div style="font-size:2.2em; margin-bottom:2px;">🔍</div>
                <div style="font-size:1.4em; font-weight:900; color:#FED448; letter-spacing:-0.5px;">
                    StudyLens
                </div>
                <div style="font-size:0.72em; color:rgba(255,255,255,0.5); font-weight:500; letter-spacing:1.5px; text-transform:uppercase;">
                    AI Study Assistant
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")

        # ─── Upload Section ───────────────────────────
        st.markdown("### ☁️ Upload Materials")

        uploaded_files = st.file_uploader(
            "Upload study materials",
            type=["pdf", "pptx", "docx", "jpg", "jpeg", "png", "bmp", "tiff"],
            accept_multiple_files=True,
            key="file_uploader",
            label_visibility="collapsed",
            help="Supports PDF, PowerPoint, Word docs, and images of handwritten notes",
        )

        if uploaded_files:
            _process_uploads(uploaded_files, vectorstore)

        st.markdown("---")

        # ─── Document List ────────────────────────────
        doc_list = vectorstore.get_all_doc_ids()

        st.markdown(f"### 📚 Documents ({len(doc_list)})")

        if doc_list:
            for doc in doc_list:
                icon = FILE_ICONS.get(doc["file_type"], "📄")
                col1, col2 = st.columns([6, 1])
                with col1:
                    st.markdown(
                        f'<div class="doc-pill">{icon} {doc["source"]}</div>',
                        unsafe_allow_html=True,
                    )
                with col2:
                    if st.button("✕", key=f"del_{doc['doc_id']}", help=f"Remove {doc['source']}"):
                        vectorstore.delete_document(doc["doc_id"])
                        st.rerun()
        else:
            st.markdown(
                """<div style="text-align:center; padding:16px 0;">
                    <div style="font-size:1.8em; opacity:0.3; margin-bottom:4px;">📂</div>
                    <p style="opacity:0.4; font-size:0.82em; margin:0;">No documents yet</p>
                </div>""",
                unsafe_allow_html=True,
            )

        st.markdown("---")

        # ─── LLM Settings ────────────────────────────
        st.markdown("### ⚡ AI Model")

        llm_mode = st.radio(
            "Select mode",
            ["🏠 Local (Ollama)", "☁️ API (OpenAI)"],
            key="llm_mode_radio",
            label_visibility="collapsed",
            horizontal=True,
        )

        st.session_state["llm_mode"] = "local" if "🏠" in llm_mode else "api"

        if st.session_state["llm_mode"] == "api":
            api_key = st.text_input(
                "🔑 API Key",
                type="password",
                value=st.session_state.get("api_key", config.OPENAI_API_KEY),
                key="api_key_input",
                placeholder="sk-...",
            )
            st.session_state["api_key"] = api_key
            if not api_key or api_key == "your_key_here":
                st.caption("⚠️ Enter your OpenAI API key above")
        else:
            st.caption("💡 Requires Ollama + `llama3` model")

        # ─── Status Footer ────────────────────────────
        st.markdown("---")

        total_docs = len(doc_list)
        total_chunks = vectorstore.count()
        mode_icon = "🏠" if st.session_state.get("llm_mode") == "local" else "☁️"

        st.markdown(
            f"""<div class="status-bar">
                <span class="status-item">📚 {total_docs}</span>
                <span class="status-item">🧩 {total_chunks}</span>
                <span class="status-item">{mode_icon}</span>
            </div>""",
            unsafe_allow_html=True,
        )


def _process_uploads(uploaded_files, vectorstore: VectorStore):
    """Process uploaded files through ingestion pipeline."""
    for uploaded_file in uploaded_files:
        file_key = f"processed_{uploaded_file.name}_{uploaded_file.size}"
        if file_key in st.session_state:
            continue

        save_path = config.UPLOAD_DIR / uploaded_file.name
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        file_hash = hashlib.sha256(uploaded_file.getbuffer()).hexdigest()
        if vectorstore.document_exists(file_hash):
            st.session_state[file_key] = True
            st.toast(f"ℹ️ '{uploaded_file.name}' already indexed", icon="ℹ️")
            continue

        file_type = config.get_file_type(uploaded_file.name)
        if not file_type:
            st.toast(f"❌ Unsupported: {uploaded_file.name}", icon="❌")
            continue

        try:
            with st.status(f"Processing {uploaded_file.name}...", expanded=True) as status:
                st.write("📖 Extracting text...")
                loaders = {
                    "pdf": load_pdf,
                    "pptx": load_pptx,
                    "docx": load_docx,
                    "image": load_image,
                }
                docs = loaders[file_type](str(save_path))

                st.write(f"✂️ Chunking {len(docs)} sections...")
                chunks = chunk_documents(docs)

                st.write(f"🧮 Embedding {len(chunks)} chunks...")
                added = vectorstore.add_documents(chunks)

                status.update(
                    label=f"✅ {uploaded_file.name} — {added} chunks",
                    state="complete",
                )
                st.session_state[file_key] = True

        except Exception as e:
            st.error(f"❌ {uploaded_file.name}: {e}")
