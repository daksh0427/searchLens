"""
Flashcard Component — Premium interactive flip cards with smooth animations.
"""

import streamlit as st
import streamlit.components.v1 as components


def render_flashcards(flashcards: list[dict]):
    """Render an interactive flashcard deck with premium styling."""
    if not flashcards:
        st.markdown(
            """<div class="empty-state">
                <span class="empty-state-icon">🃏</span>
                <p class="empty-state-title">No flashcards yet</p>
                <p class="empty-state-text">Generate cards from your uploaded documents above</p>
            </div>""",
            unsafe_allow_html=True,
        )
        return

    if "card_index" not in st.session_state:
        st.session_state["card_index"] = 0

    idx = st.session_state["card_index"]
    total = len(flashcards)
    idx = max(0, min(idx, total - 1))
    card = flashcards[idx]

    # Flashcard HTML with embedded CSS + JS
    card_html = f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&display=swap');
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ background: transparent; }}
        .fc-wrap {{
            perspective: 1200px;
            width: 100%;
            max-width: 480px;
            height: 280px;
            margin: 0 auto;
            cursor: pointer;
            -webkit-tap-highlight-color: transparent;
        }}
        .fc {{
            position: relative; width: 100%; height: 100%;
            transform-style: preserve-3d;
            transition: transform 0.65s cubic-bezier(0.4, 0, 0.2, 1);
        }}
        .fc.flipped {{ transform: rotateY(180deg); }}
        .fc-face {{
            position: absolute; width: 100%; height: 100%;
            backface-visibility: hidden;
            border-radius: 24px;
            display: flex; flex-direction: column;
            align-items: center; justify-content: center;
            padding: 28px 32px;
            font-family: 'Nunito', sans-serif;
        }}
        .fc-front {{
            background: linear-gradient(145deg, #FED448 0%, #FFE88A 50%, #FED448 100%);
            color: #333;
            box-shadow: 0 12px 40px rgba(254,212,72,0.35), 0 2px 8px rgba(0,0,0,0.08);
            transform: rotate(-0.8deg);
        }}
        .fc-back {{
            background: linear-gradient(145deg, #FF6695 0%, #FF8FB5 50%, #FF6695 100%);
            color: #fff;
            box-shadow: 0 12px 40px rgba(255,102,149,0.35), 0 2px 8px rgba(0,0,0,0.08);
            transform: rotateY(180deg) rotate(0.8deg);
        }}
        .fc-label {{
            font-size: 0.65em; font-weight: 700;
            text-transform: uppercase; letter-spacing: 2px;
            opacity: 0.5; margin-bottom: 12px;
        }}
        .fc-text {{
            font-size: 1.12em; font-weight: 700;
            text-align: center; line-height: 1.5;
            max-height: 160px; overflow-y: auto;
        }}
        .fc-hint {{
            position: absolute; bottom: 14px;
            font-size: 0.65em; opacity: 0.4; font-weight: 600;
        }}
        .fc-source {{
            position: absolute; bottom: 14px;
            font-size: 0.65em; opacity: 0.5; font-weight: 600;
        }}
        .fc-counter {{
            text-align: center; margin-top: 14px;
            font-family: 'Nunito', sans-serif;
            font-weight: 700; color: #67C0AC; font-size: 0.9em;
        }}
        .fc-dots {{
            display: flex; justify-content: center; gap: 5px;
            margin-top: 8px;
        }}
        .fc-dot {{
            width: 8px; height: 8px; border-radius: 50%;
            background: #e0d5d0; transition: all 0.3s ease;
        }}
        .fc-dot.active {{
            background: #FF6695; transform: scale(1.3);
        }}
    </style>

    <div class="fc-wrap" onclick="this.querySelector('.fc').classList.toggle('flipped')">
        <div class="fc">
            <div class="fc-face fc-front">
                <div class="fc-label">Question</div>
                <div class="fc-text">{_esc(card['front'])}</div>
                <div class="fc-hint">tap to flip ↻</div>
            </div>
            <div class="fc-face fc-back">
                <div class="fc-label">Answer</div>
                <div class="fc-text">{_esc(card['back'])}</div>
                <div class="fc-source">📖 {_esc(card['source'])}</div>
            </div>
        </div>
    </div>

    <div class="fc-counter">{idx + 1} / {total}</div>
    <div class="fc-dots">
        {''.join(f'<div class="fc-dot {"active" if i == idx else ""}"></div>' for i in range(min(total, 15)))}
        {'<div style="color:#ccc;font-size:0.7em;align-self:center;">...</div>' if total > 15 else ''}
    </div>
    """

    components.html(card_html, height=400)

    # Navigation
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("⬅️ Previous", disabled=(idx == 0), key="fc_prev", use_container_width=True):
            st.session_state["card_index"] = idx - 1
            st.rerun()
    with col3:
        if st.button("Next ➡️", disabled=(idx >= total - 1), key="fc_next", use_container_width=True):
            st.session_state["card_index"] = idx + 1
            st.rerun()


def _esc(text: str) -> str:
    """Escape HTML."""
    return (
        text.replace("&", "&amp;").replace("<", "&lt;")
        .replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#39;")
    )
