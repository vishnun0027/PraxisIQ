"""
Page 3 — Semantic Search
Find conceptually similar past journal entries using Qdrant VectorDB.
"""

import streamlit as st
import httpx
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ui.helpers import inject_css, render_analysis, emotion_chips_html, format_date, API_BASE

inject_css()

# --- Header ---
st.markdown('<p class="gradient-header">🔍 Semantic Search</p>', unsafe_allow_html=True)
st.markdown('<p class="tagline">Find past entries by concept, feeling, or situation</p>', unsafe_allow_html=True)

st.markdown(
    '<p class="card-text-sm" style="text-align: center; color: #94a3b8; margin-bottom: 2rem;">'
    'Powered by <strong>all-MiniLM-L6-v2</strong> embeddings and <strong>Qdrant VectorDB</strong>. '
    'Search for concepts like <em>"feeling like an imposter at work"</em> or <em>"arguing with my partner"</em>.'
    '</p>',
    unsafe_allow_html=True,
)

# --- Search Input ---
query = st.text_input(
    "Search your emotional history",
    placeholder="What feeling or situation are you looking for?",
    key="semantic_query",
)

if query and len(query) >= 2:
    with st.spinner("Searching vectors in Qdrant..."):
        try:
            resp = httpx.get(
                f"{API_BASE}/journal/search",
                params={"q": query, "limit": 5},
                timeout=15.0,
            )
            if resp.status_code == 200:
                results = resp.json()
            else:
                st.error(f"Search failed: {resp.text}")
                results = []
        except Exception as exc:
            st.error(f"Error connecting to API: {exc}")
            results = []

    if not results:
        st.info("No conceptually similar entries found.")
    else:
        st.markdown(f'<p class="section-title">Found {len(results)} related entries</p>', unsafe_allow_html=True)
        st.divider()

        for idx, entry in enumerate(results):
            analysis = entry.get("analysis", {})
            date_str = format_date(entry.get("created_at", ""))
            intensity = analysis.get("emotional_intensity", "?")
            emotions_html = emotion_chips_html(analysis.get("detected_emotions", []))
            
            # Show a nice preview
            preview = entry.get("text", "")[:150]
            if len(entry.get("text", "")) > 150:
                preview += "..."

            st.markdown(
                f'<p class="history-row">'
                f'<span class="history-date">{date_str}</span>'
                f'<span class="intensity-badge">⚡ {intensity}/10</span>'
                f"</p>"
                f'<p class="history-preview">{preview}</p>'
                f'<p class="emotion-row">{emotions_html}</p>',
                unsafe_allow_html=True,
            )

            with st.expander(f"View full analysis — {date_str}"):
                st.markdown(
                    f'<p class="card-text-quote">"{entry.get("text", "")}"</p>',
                    unsafe_allow_html=True,
                )
                render_analysis(analysis, key_prefix=f"search_{idx}")

            st.divider()
