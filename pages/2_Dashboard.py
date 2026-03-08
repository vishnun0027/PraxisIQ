"""
Page 2 — Dashboard
View history, trends, charts, and past analysis results.
"""

from collections import Counter

import streamlit as st
import httpx
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ui.helpers import (
    inject_css,
    render_analysis,
    emotion_chips_html,
    format_date,
    make_history_trend,
    make_emotion_frequency,
    API_BASE,
    EMOTION_COLORS,
    EMOTION_ICONS,
)

inject_css()

# --- Header ---
st.markdown('<p class="gradient-header">📊 Dashboard</p>', unsafe_allow_html=True)
st.markdown('<p class="tagline">Your emotional journey at a glance</p>', unsafe_allow_html=True)


# --- Fetch history (cached for 30s to avoid re-fetching on every widget rerun) ---
@st.cache_data(ttl=30)
def fetch_history() -> list[dict]:
    resp = httpx.get(f"{API_BASE}/journal/history?limit=50", timeout=10.0)
    resp.raise_for_status()
    return resp.json()


try:
    entries = fetch_history()
except httpx.ConnectError:
    st.error("Cannot connect to API server. Is it running on port 8000?")
    st.stop()
except Exception as exc:
    st.error(f"Error: {exc}")
    st.stop()

if not entries:
    st.markdown(
        '<p class="empty-state">'
        '<span class="empty-icon">📊</span><br>'
        "No journal entries yet.<br>Go to <strong>Journal Entry</strong> to write your first entry."
        "</p>",
        unsafe_allow_html=True,
    )
    st.stop()

# --- Summary stats ---
total = len(entries)
avg_intensity = sum(
    e.get("analysis", {}).get("emotional_intensity", 0) for e in entries
) / total
latest_intensity = entries[0].get("analysis", {}).get("emotional_intensity", 0)

# Collect all emotions across entries
emotion_counter: Counter[str] = Counter()
for e in entries:
    for em in e.get("analysis", {}).get("detected_emotions", []):
        emotion_counter[em] += 1
top_emotion = emotion_counter.most_common(1)[0][0] if emotion_counter else "—"

col_s1, col_s2, col_s3, col_s4 = st.columns(4)
with col_s1:
    st.markdown(
        f'<p class="stat-number">{total}</p><p class="stat-label">Total Entries</p>',
        unsafe_allow_html=True,
    )
with col_s2:
    st.markdown(
        f'<p class="stat-number">{avg_intensity:.1f}</p><p class="stat-label">Avg Intensity</p>',
        unsafe_allow_html=True,
    )
with col_s3:
    st.markdown(
        f'<p class="stat-number">{latest_intensity}</p><p class="stat-label">Latest Intensity</p>',
        unsafe_allow_html=True,
    )
with col_s4:
    icon = EMOTION_ICONS.get(top_emotion, "")
    st.markdown(
        f'<p class="stat-number">{icon}</p><p class="stat-label">Top: {top_emotion}</p>',
        unsafe_allow_html=True,
    )

st.divider()

# --- Charts ---
tab_trends, tab_emotions, tab_history = st.tabs(["📈 Trends", "🎭 Emotions", "📔 History"])

with tab_trends:
    trend_fig = make_history_trend(entries)
    if trend_fig:
        st.markdown('<p class="section-title">📈 Emotional Intensity Over Time</p>', unsafe_allow_html=True)
        st.plotly_chart(trend_fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Need at least 2 entries to show trends. Keep journaling!")

with tab_emotions:
    freq_fig = make_emotion_frequency(entries)
    if freq_fig:
        st.markdown('<p class="section-title">🎭 Most Frequent Emotions</p>', unsafe_allow_html=True)
        st.plotly_chart(freq_fig, use_container_width=True, config={"displayModeBar": False})

    # Show emotion breakdown as a table
    if emotion_counter:
        st.divider()
        st.markdown('<p class="section-title">📋 Emotion Breakdown</p>', unsafe_allow_html=True)
        for em, count in emotion_counter.most_common():
            pct = (count / total) * 100
            icon = EMOTION_ICONS.get(em, "")
            color = EMOTION_COLORS.get(em, "#8b5cf6")
            st.markdown(
                f'<p><span class="emotion-chip emotion-{em}">{icon} {em}</span> '
                f'<span class="muted-text">— {count} entries ({pct:.0f}%)</span></p>',
                unsafe_allow_html=True,
            )

with tab_history:
    for idx, entry in enumerate(entries):
        analysis = entry.get("analysis", {})
        emotions_html = emotion_chips_html(analysis.get("detected_emotions", []))
        intensity = analysis.get("emotional_intensity", "?")
        date_str = format_date(entry.get("created_at", ""))
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
            render_analysis(analysis, key_prefix=f"hist_{idx}")

        st.divider()
