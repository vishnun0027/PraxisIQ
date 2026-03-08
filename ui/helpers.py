"""
Shared UI helpers — CSS, HTML builders, Plotly charts.
Imported by both pages.
"""

from collections import Counter

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime

API_BASE = "http://localhost:8000"

# ---------------------------------------------------------------------------
# Emotion / Distortion data
# ---------------------------------------------------------------------------
EMOTION_ICONS = {
    "joy": "😊", "gratitude": "🙏", "calm": "😌", "hope": "🌟",
    "love": "❤️", "excitement": "🤩", "pride": "🏆",
    "sadness": "😢", "anxiety": "😟", "stress": "😰", "anger": "😠",
    "frustration": "😤", "fear": "😨", "disgust": "🤢", "shame": "😳",
    "guilt": "😔", "loneliness": "🫂", "jealousy": "😒",
    "burnout": "🔥", "overwhelm": "😵",
}

ALL_EMOTIONS = list(EMOTION_ICONS.keys())

EMOTION_COLORS = {
    "joy": "#10b981", "gratitude": "#14b8a6", "calm": "#38bdf8",
    "hope": "#22d3ee", "love": "#ec4899", "excitement": "#fb923c",
    "pride": "#a855f7",
    "sadness": "#3b82f6", "anxiety": "#f59e0b", "stress": "#f43f5e",
    "anger": "#dc2626", "frustration": "#ef4444", "fear": "#d97706",
    "disgust": "#84cc16", "shame": "#c084fc", "guilt": "#fbbf24",
    "loneliness": "#818cf8", "jealousy": "#4ade80",
    "burnout": "#6366f1", "overwhelm": "#f87171",
}


# ---------------------------------------------------------------------------
# CSS injection
# ---------------------------------------------------------------------------
def inject_css() -> None:
    st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: #0a0e1a; }
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.block-container { max-width: 900px; padding-top: 1rem; }

.glass-card {
    background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1);
    border-radius: 16px; padding: 1.5rem; backdrop-filter: blur(12px);
    margin-bottom: 1rem; transition: border-color 0.25s, box-shadow 0.25s;
}
.glass-card:hover { border-color: rgba(139,92,246,0.3); box-shadow: 0 0 20px rgba(139,92,246,0.12); }

.section-title { font-size: 0.8rem; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 0.5rem; }
.card-text    { color: #f1f5f9; font-size: 0.95rem; line-height: 1.7; }
.card-text-sm { color: #f1f5f9; font-size: 0.9rem;  line-height: 1.7; }
.card-text-italic { color: #f1f5f9; font-size: 0.9rem; line-height: 1.7; font-style: italic; }
.card-text-quote  { color: #94a3b8; font-style: italic; font-size: 0.9rem; line-height: 1.7; }
.muted-text { color: #64748b; }

.emotion-chip { display: inline-block; padding: 0.3rem 0.8rem; border-radius: 9999px; font-size: 0.82rem; font-weight: 500; margin: 0.2rem 0.3rem 0.2rem 0; }
.emotion-stress       { background: rgba(244,63,94,0.12);  color: #f43f5e; border: 1px solid rgba(244,63,94,0.25); }
.emotion-anxiety      { background: rgba(245,158,11,0.12); color: #f59e0b; border: 1px solid rgba(245,158,11,0.25); }
.emotion-frustration  { background: rgba(239,68,68,0.12);  color: #ef4444; border: 1px solid rgba(239,68,68,0.25); }
.emotion-burnout      { background: rgba(99,102,241,0.12); color: #6366f1; border: 1px solid rgba(99,102,241,0.25); }
.emotion-sadness      { background: rgba(59,130,246,0.12); color: #3b82f6; border: 1px solid rgba(59,130,246,0.25); }
.emotion-joy          { background: rgba(16,185,129,0.12); color: #10b981; border: 1px solid rgba(16,185,129,0.25); }
.emotion-gratitude    { background: rgba(20,184,166,0.12); color: #14b8a6; border: 1px solid rgba(20,184,166,0.25); }
.emotion-calm         { background: rgba(56,189,248,0.12); color: #38bdf8; border: 1px solid rgba(56,189,248,0.25); }
.emotion-hope         { background: rgba(34,211,238,0.12); color: #22d3ee; border: 1px solid rgba(34,211,238,0.25); }
.emotion-love         { background: rgba(236,72,153,0.12); color: #ec4899; border: 1px solid rgba(236,72,153,0.25); }
.emotion-excitement   { background: rgba(251,146,60,0.12); color: #fb923c; border: 1px solid rgba(251,146,60,0.25); }
.emotion-pride        { background: rgba(168,85,247,0.12); color: #a855f7; border: 1px solid rgba(168,85,247,0.25); }
.emotion-anger        { background: rgba(220,38,38,0.12);  color: #dc2626; border: 1px solid rgba(220,38,38,0.25); }
.emotion-fear         { background: rgba(217,119,6,0.12);  color: #d97706; border: 1px solid rgba(217,119,6,0.25); }
.emotion-disgust      { background: rgba(132,204,22,0.12); color: #84cc16; border: 1px solid rgba(132,204,22,0.25); }
.emotion-shame        { background: rgba(192,132,252,0.12);color: #c084fc; border: 1px solid rgba(192,132,252,0.25); }
.emotion-guilt        { background: rgba(251,191,36,0.12); color: #fbbf24; border: 1px solid rgba(251,191,36,0.25); }
.emotion-loneliness   { background: rgba(129,140,248,0.12);color: #818cf8; border: 1px solid rgba(129,140,248,0.25); }
.emotion-jealousy     { background: rgba(74,222,128,0.12); color: #4ade80; border: 1px solid rgba(74,222,128,0.25); }
.emotion-overwhelm    { background: rgba(248,113,113,0.12);color: #f87171; border: 1px solid rgba(248,113,113,0.25); }

.distortion-chip { display: inline-block; padding: 0.3rem 0.8rem; background: rgba(245,158,11,0.1); color: #f59e0b; border: 1px solid rgba(245,158,11,0.25); border-radius: 9999px; font-size: 0.82rem; font-weight: 500; margin: 0.2rem 0.3rem 0.2rem 0; }

.action-step { display: flex; align-items: flex-start; gap: 0.5rem; padding: 0.5rem 0.8rem; background: rgba(16,185,129,0.06); border-radius: 8px; border-left: 3px solid #10b981; margin-bottom: 0.4rem; font-size: 0.9rem; color: #f1f5f9; }
.step-num { flex-shrink: 0; width: 22px; height: 22px; display: flex; align-items: center; justify-content: center; background: #10b981; color: white; font-size: 0.72rem; font-weight: 700; border-radius: 50%; }

.crisis-banner { background: rgba(244,63,94,0.1); border: 1px solid rgba(244,63,94,0.35); border-radius: 12px; padding: 1.2rem; margin-bottom: 1rem; animation: pulseBorder 2s ease-in-out infinite; }
@keyframes pulseBorder { 0%,100% { border-color: rgba(244,63,94,0.35); } 50% { border-color: rgba(244,63,94,0.6); } }

.gradient-header { font-size: 2.2rem; font-weight: 700; background: linear-gradient(135deg, #8b5cf6, #06b6d4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; text-align: center; margin-bottom: 0.2rem; }
.tagline { text-align: center; color: #94a3b8; font-size: 0.95rem; font-weight: 300; margin-bottom: 1.5rem; }

.history-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem; }
.history-date { font-size: 0.78rem; color: #64748b; }
.history-preview { font-size: 0.9rem; color: #94a3b8; margin-top: 0.3rem; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
.intensity-badge { font-size: 0.78rem; font-weight: 600; padding: 2px 10px; border-radius: 9999px; background: rgba(139,92,246,0.15); color: #8b5cf6; }
.emotion-row { margin-top: 0.5rem; }
.empty-state { text-align: center; padding: 3rem 0; color: #64748b; }
.empty-icon  { font-size: 2.5rem; margin-bottom: 0.8rem; opacity: 0.5; }
.stat-number { font-size: 2rem; font-weight: 700; color: #f1f5f9; }
.stat-label  { font-size: 0.78rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; }
</style>
""",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# HTML builders
# ---------------------------------------------------------------------------
def emotion_chips_html(emotions: list[str]) -> str:
    return "".join(
        f'<span class="emotion-chip emotion-{e}">{EMOTION_ICONS.get(e, "")} {e}</span>'
        for e in emotions
    )


def distortion_chips_html(distortions: list[str]) -> str:
    return "".join(
        f'<span class="distortion-chip">⚠️ {d.replace("_", " ")}</span>'
        for d in distortions
    )


def action_steps_html(steps: list[str]) -> str:
    return "".join(
        f'<p class="action-step"><span class="step-num">{i}</span><span>{step}</span></p>'
        for i, step in enumerate(steps, 1)
    )


def format_date(iso_str: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%b %d, %Y · %I:%M %p")
    except Exception:
        return iso_str


# ---------------------------------------------------------------------------
# Plotly charts
# ---------------------------------------------------------------------------
_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color="#94a3b8"),
    margin=dict(l=20, r=20, t=30, b=20),
)


def make_emotion_radar(detected: list[str]) -> go.Figure:
    values = [1 if e in detected else 0 for e in ALL_EMOTIONS]
    values.append(values[0])
    labels = [e.capitalize() for e in ALL_EMOTIONS] + [ALL_EMOTIONS[0].capitalize()]
    fig = go.Figure(go.Scatterpolar(
        r=values, theta=labels, fill="toself",
        fillcolor="rgba(139,92,246,0.15)",
        line=dict(color="#8b5cf6", width=2),
        marker=dict(
            size=8,
            color=[EMOTION_COLORS.get(e, "#8b5cf6") for e in ALL_EMOTIONS]
            + [EMOTION_COLORS.get(ALL_EMOTIONS[0], "#8b5cf6")],
        ),
    ))
    fig.update_layout(
        **_LAYOUT, height=300, showlegend=False,
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=False, range=[0, 1.2]),
            angularaxis=dict(linecolor="rgba(255,255,255,0.1)", gridcolor="rgba(255,255,255,0.06)"),
        ),
    )
    return fig


def make_intensity_gauge(value: int) -> go.Figure:
    bar_color = "#10b981" if value <= 3 else ("#f59e0b" if value <= 6 else "#f43f5e")
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=value,
        number=dict(font=dict(size=42, color="#f1f5f9"), suffix="/10"),
        gauge=dict(
            axis=dict(range=[0, 10], tickcolor="#64748b", dtick=2),
            bar=dict(color=bar_color, thickness=0.7),
            bgcolor="rgba(255,255,255,0.04)", borderwidth=0,
            steps=[
                dict(range=[0, 3], color="rgba(16,185,129,0.08)"),
                dict(range=[3, 6], color="rgba(245,158,11,0.08)"),
                dict(range=[6, 10], color="rgba(244,63,94,0.08)"),
            ],
        ),
    ))
    fig.update_layout(**_LAYOUT, height=220)
    return fig


def make_history_trend(entries: list[dict]) -> go.Figure | None:
    if not entries or len(entries) < 2:
        return None
    dates, intensities, texts = [], [], []
    for e in reversed(entries):
        try:
            dt = datetime.fromisoformat(e["created_at"])
        except Exception:
            continue  # Skip entries with invalid/missing dates (keeps all 3 lists in sync)
        raw_text = e.get("text", "")
        dates.append(dt)
        intensities.append(e.get("analysis", {}).get("emotional_intensity", 0))
        texts.append(raw_text[:60] + ("..." if len(raw_text) > 60 else ""))

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates, y=intensities, mode="lines+markers",
        line=dict(color="#8b5cf6", width=2.5, shape="spline"),
        marker=dict(size=8, color="#8b5cf6", line=dict(width=2, color="#0a0e1a")),
        text=texts,
        hovertemplate="<b>%{text}</b><br>Intensity: %{y}/10<br>%{x|%b %d, %I:%M %p}<extra></extra>",
        fill="tozeroy", fillcolor="rgba(139,92,246,0.08)",
    ))
    fig.add_hrect(y0=0, y1=3, fillcolor="rgba(16,185,129,0.04)", line_width=0)
    fig.add_hrect(y0=3, y1=6, fillcolor="rgba(245,158,11,0.04)", line_width=0)
    fig.add_hrect(y0=6, y1=10, fillcolor="rgba(244,63,94,0.04)", line_width=0)
    fig.update_layout(
        **_LAYOUT, height=300,
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)", linecolor="rgba(255,255,255,0.1)"),
        yaxis=dict(range=[0, 10.5], dtick=2, gridcolor="rgba(255,255,255,0.06)",
                   linecolor="rgba(255,255,255,0.1)", title=dict(text="Intensity", font=dict(size=11))),
        hovermode="x unified",
    )
    return fig


def make_emotion_frequency(entries: list[dict]) -> go.Figure | None:
    """Bar chart showing how often each emotion appears across all entries."""
    if not entries:
        return None
    counter: Counter[str] = Counter()
    for e in entries:
        for em in e.get("analysis", {}).get("detected_emotions", []):
            counter[em] += 1
    if not counter:
        return None
    sorted_items = counter.most_common()
    labels = [e.capitalize() for e, _ in sorted_items]
    counts = [c for _, c in sorted_items]
    colors = [EMOTION_COLORS.get(e, "#8b5cf6") for e, _ in sorted_items]
    fig = go.Figure(go.Bar(
        x=labels, y=counts,
        marker=dict(color=colors, line=dict(width=0)),
        hovertemplate="%{x}: %{y} times<extra></extra>",
    ))
    fig.update_layout(
        **_LAYOUT, height=280,
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.06)", title=dict(text="Count", font=dict(size=11))),
    )
    return fig


# ---------------------------------------------------------------------------
# Render full analysis (used in both pages)
# ---------------------------------------------------------------------------
def render_analysis(analysis: dict, key_prefix: str = "main") -> None:
    if analysis.get("crisis_detected"):
        st.markdown(
            '<p class="crisis-banner">'
            "<strong>⚠️ We noticed signs of distress</strong><br>"
            "If you or someone you know is in crisis, please reach out:<br>"
            '<strong>Suicide Prevention Lifeline:</strong> <a href="tel:988">988</a><br>'
            "<strong>Crisis Text Line:</strong> Text HOME to "
            '<a href="sms:741741">741741</a><br>'
            '<strong>iCall (India):</strong> <a href="tel:9152987821">9152987821</a></p>',
            unsafe_allow_html=True,
        )

    detected = analysis.get("detected_emotions", [])
    intensity = analysis.get("emotional_intensity", 0)

    col1, col2 = st.columns([3, 2])
    with col1:
        st.markdown(
            '<p class="section-title">😟 Detected Emotions</p>' + emotion_chips_html(detected),
            unsafe_allow_html=True,
        )
        if detected:
            st.plotly_chart(make_emotion_radar(detected), use_container_width=True, config={"displayModeBar": False}, key=f"{key_prefix}_radar")
    with col2:
        st.markdown('<p class="section-title">📊 Intensity</p>', unsafe_allow_html=True)
        st.plotly_chart(make_intensity_gauge(intensity), use_container_width=True, config={"displayModeBar": False}, key=f"{key_prefix}_gauge")

    st.markdown(
        '<p class="section-title">🧠 Emotion Summary</p>'
        f'<p class="card-text">{analysis.get("emotion_summary", "")}</p>',
        unsafe_allow_html=True,
    )

    col3, col4 = st.columns(2)
    with col3:
        distortions = analysis.get("cognitive_distortions", [])
        content = distortion_chips_html(distortions) if distortions else '<span class="muted-text">None detected</span>'
        st.markdown('<p class="section-title">⚠️ Cognitive Distortions</p>' + content, unsafe_allow_html=True)
    with col4:
        st.markdown(
            '<p class="section-title">🔍 Root Cause</p>'
            f'<p class="card-text-sm">{analysis.get("root_cause_analysis", "")}</p>',
            unsafe_allow_html=True,
        )

    st.markdown(
        '<p class="section-title">✅ Action Steps</p>' + action_steps_html(analysis.get("action_steps", [])),
        unsafe_allow_html=True,
    )

    col5, col6 = st.columns(2)
    with col5:
        st.markdown(
            '<p class="section-title">💡 Cognitive Reframing</p>'
            f'<p class="card-text-italic">"{analysis.get("reframing", "")}"</p>',
            unsafe_allow_html=True,
        )
    with col6:
        st.markdown(
            '<p class="section-title">💪 Motivation</p>'
            f'<p class="card-text-sm">{analysis.get("motivational_guidance", "")}</p>',
            unsafe_allow_html=True,
        )
