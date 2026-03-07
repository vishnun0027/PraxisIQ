"""
Mental Clarity Journal — Streamlit Demo UI
Talks to the FastAPI backend via HTTP.
"""

import streamlit as st
import httpx
from datetime import datetime

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
API_BASE = "http://localhost:8000"

st.set_page_config(
    page_title="Mental Clarity Journal",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Custom CSS — dark glassmorphism on top of Streamlit
# ---------------------------------------------------------------------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* Global overrides */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: #0a0e1a;
}

/* Hide Streamlit branding */
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}

/* Main container */
.block-container {
    max-width: 800px;
    padding-top: 2rem;
}

/* Glass card wrapper */
.glass-card {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    padding: 1.5rem;
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    margin-bottom: 1rem;
    transition: border-color 0.25s ease, box-shadow 0.25s ease;
}
.glass-card:hover {
    border-color: rgba(139, 92, 246, 0.3);
    box-shadow: 0 0 20px rgba(139, 92, 246, 0.12);
}
.glass-card-quote {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-left: 3px solid #8b5cf6;
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1rem;
}

/* Section titles */
.section-title {
    font-size: 0.8rem;
    font-weight: 600;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 0.5rem;
}

/* Text content */
.card-text {
    color: #f1f5f9;
    font-size: 0.95rem;
    line-height: 1.7;
}
.card-text-sm {
    color: #f1f5f9;
    font-size: 0.9rem;
    line-height: 1.7;
}
.card-text-italic {
    color: #f1f5f9;
    font-size: 0.9rem;
    line-height: 1.7;
    font-style: italic;
}
.card-text-quote {
    color: #94a3b8;
    font-style: italic;
    font-size: 0.9rem;
    line-height: 1.7;
}
.muted-text {
    color: #64748b;
}

/* Emotion chip */
.emotion-chip {
    display: inline-block;
    padding: 0.3rem 0.8rem;
    border-radius: 9999px;
    font-size: 0.82rem;
    font-weight: 500;
    margin: 0.2rem 0.3rem 0.2rem 0;
}
.emotion-stress       { background: rgba(244,63,94,0.12);  color: #f43f5e; border: 1px solid rgba(244,63,94,0.25); }
.emotion-anxiety      { background: rgba(245,158,11,0.12); color: #f59e0b; border: 1px solid rgba(245,158,11,0.25); }
.emotion-frustration  { background: rgba(239,68,68,0.12);  color: #ef4444; border: 1px solid rgba(239,68,68,0.25); }
.emotion-burnout      { background: rgba(99,102,241,0.12); color: #6366f1; border: 1px solid rgba(99,102,241,0.25); }
.emotion-sadness      { background: rgba(59,130,246,0.12); color: #3b82f6; border: 1px solid rgba(59,130,246,0.25); }
.emotion-positive     { background: rgba(16,185,129,0.12); color: #10b981; border: 1px solid rgba(16,185,129,0.25); }

/* Distortion chip */
.distortion-chip {
    display: inline-block;
    padding: 0.3rem 0.8rem;
    background: rgba(245,158,11,0.1);
    color: #f59e0b;
    border: 1px solid rgba(245,158,11,0.25);
    border-radius: 9999px;
    font-size: 0.82rem;
    font-weight: 500;
    margin: 0.2rem 0.3rem 0.2rem 0;
}

/* Action step */
.action-step {
    display: flex;
    align-items: flex-start;
    gap: 0.5rem;
    padding: 0.5rem 0.8rem;
    background: rgba(16,185,129,0.06);
    border-radius: 8px;
    border-left: 3px solid #10b981;
    margin-bottom: 0.4rem;
    font-size: 0.9rem;
    color: #f1f5f9;
}
.step-num {
    flex-shrink: 0;
    width: 22px;
    height: 22px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #10b981;
    color: white;
    font-size: 0.72rem;
    font-weight: 700;
    border-radius: 50%;
}

/* Crisis banner */
.crisis-banner {
    background: rgba(244,63,94,0.1);
    border: 1px solid rgba(244,63,94,0.35);
    border-radius: 12px;
    padding: 1.2rem;
    margin-bottom: 1rem;
    animation: pulseBorder 2s ease-in-out infinite;
}
.crisis-banner h4 { color: #f43f5e; margin-bottom: 0.4rem; }
.crisis-banner p  { color: #94a3b8; font-size: 0.9rem; line-height: 1.7; }
.crisis-banner a  { color: #f43f5e; font-weight: 600; }

@keyframes pulseBorder {
    0%, 100% { border-color: rgba(244,63,94,0.35); }
    50%      { border-color: rgba(244,63,94,0.6); }
}

/* Intensity - use CSS classes instead of inline styles */
.intensity-track {
    height: 8px;
    background: rgba(255,255,255,0.06);
    border-radius: 9999px;
    overflow: hidden;
    margin-top: 0.3rem;
}
.intensity-fill {
    height: 100%;
    border-radius: 9999px;
    display: block;
    background: linear-gradient(90deg, #10b981, #f59e0b, #f43f5e);
}
/* Pre-defined intensity widths */
.intensity-w-10 { width: 10%; }
.intensity-w-20 { width: 20%; }
.intensity-w-30 { width: 30%; }
.intensity-w-40 { width: 40%; }
.intensity-w-50 { width: 50%; }
.intensity-w-60 { width: 60%; }
.intensity-w-70 { width: 70%; }
.intensity-w-80 { width: 80%; }
.intensity-w-90 { width: 90%; }
.intensity-w-100 { width: 100%; }

/* Gradient header text */
.gradient-header {
    font-size: 2.2rem;
    font-weight: 700;
    background: linear-gradient(135deg, #8b5cf6, #06b6d4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-align: center;
    margin-bottom: 0.2rem;
}
.tagline {
    text-align: center;
    color: #94a3b8;
    font-size: 0.95rem;
    font-weight: 300;
    margin-bottom: 1.5rem;
}

/* Intensity big number */
.intensity-big {
    font-size: 1.8rem;
    font-weight: 700;
    background: linear-gradient(135deg, #8b5cf6, #06b6d4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

/* History helpers */
.history-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.4rem;
}
.history-date {
    font-size: 0.78rem;
    color: #64748b;
}
.history-preview {
    font-size: 0.9rem;
    color: #94a3b8;
    margin-top: 0.3rem;
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
}
.intensity-badge {
    font-size: 0.78rem;
    font-weight: 600;
    padding: 2px 10px;
    border-radius: 9999px;
    background: rgba(139,92,246,0.15);
    color: #8b5cf6;
}
.emotion-row {
    margin-top: 0.5rem;
}
.empty-state {
    text-align: center;
    padding: 3rem 0;
    color: #64748b;
}
.empty-icon {
    font-size: 2.5rem;
    margin-bottom: 0.8rem;
    opacity: 0.5;
}
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown('<p class="gradient-header">🧠 Mental Clarity Journal</p>', unsafe_allow_html=True)
st.markdown('<p class="tagline">AI-powered emotional analysis &amp; CBT insights</p>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
EMOTION_ICONS = {
    "stress": "😰",
    "anxiety": "😟",
    "frustration": "😤",
    "burnout": "🔥",
    "sadness": "😢",
    "positive": "😊",
}


def emotion_chips_html(emotions: list[str]) -> str:
    chips = ""
    for e in emotions:
        icon = EMOTION_ICONS.get(e, "")
        chips += f'<span class="emotion-chip emotion-{e}">{icon} {e}</span>'
    return chips


def distortion_chips_html(distortions: list[str]) -> str:
    return "".join(
        f'<span class="distortion-chip">⚠️ {d.replace("_", " ")}</span>'
        for d in distortions
    )


def action_steps_html(steps: list[str]) -> str:
    html = ""
    for i, step in enumerate(steps, 1):
        html += f'<p class="action-step"><span class="step-num">{i}</span><span>{step}</span></p>'
    return html


def intensity_bar_html(value: int) -> str:
    pct = max(1, min(value, 10)) * 10
    return f"""<p class="intensity-big">{value}/10</p>
<p class="intensity-track"><span class="intensity-fill intensity-w-{pct}"></span></p>"""


def render_analysis(analysis: dict) -> None:
    """Render analysis cards for a given analysis dict."""
    # Crisis banner
    if analysis.get("crisis_detected"):
        st.markdown(
            '<p class="crisis-banner">'
            "<strong>⚠️ We noticed signs of distress</strong><br>"
            "If you or someone you know is in crisis, please reach out:<br>"
            '<strong>National Suicide Prevention Lifeline:</strong> <a href="tel:988">988</a><br>'
            "<strong>Crisis Text Line:</strong> Text HOME to "
            '<a href="sms:741741">741741</a><br>'
            '<strong>iCall (India):</strong> <a href="tel:9152987821">9152987821</a>'
            "</p>",
            unsafe_allow_html=True,
        )

    # Row 1: Emotions + Intensity
    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown(
            '<p class="section-title">😟 Detected Emotions</p>'
            + emotion_chips_html(analysis.get("detected_emotions", [])),
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            '<p class="section-title">📊 Intensity</p>'
            + intensity_bar_html(analysis.get("emotional_intensity", 0)),
            unsafe_allow_html=True,
        )

    # Emotion summary
    st.markdown(
        '<p class="section-title">🧠 Emotion Summary</p>'
        f'<p class="card-text">{analysis.get("emotion_summary", "")}</p>',
        unsafe_allow_html=True,
    )

    # Row 2: Distortions + Root cause
    col3, col4 = st.columns(2)

    with col3:
        distortions = analysis.get("cognitive_distortions", [])
        content = distortion_chips_html(distortions) if distortions else '<span class="muted-text">None detected</span>'
        st.markdown(
            '<p class="section-title">⚠️ Cognitive Distortions</p>' + content,
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            '<p class="section-title">🔍 Root Cause</p>'
            f'<p class="card-text-sm">{analysis.get("root_cause_analysis", "")}</p>',
            unsafe_allow_html=True,
        )

    # Action steps
    st.markdown(
        '<p class="section-title">✅ Action Steps</p>'
        + action_steps_html(analysis.get("action_steps", [])),
        unsafe_allow_html=True,
    )

    # Row 3: Reframing + Motivation
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


def format_date(iso_str: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%b %d, %Y · %I:%M %p")
    except Exception:
        return iso_str


# ---------------------------------------------------------------------------
# State init
# ---------------------------------------------------------------------------
if "last_analysis" not in st.session_state:
    st.session_state.last_analysis = None
if "last_text" not in st.session_state:
    st.session_state.last_text = None


# ---------------------------------------------------------------------------
# Journal Input
# ---------------------------------------------------------------------------
st.markdown('<p class="section-title">✍️ Write your journal entry</p>', unsafe_allow_html=True)

entry_text = st.text_area(
    label="Journal entry",
    placeholder="How are you feeling today? Write freely about your thoughts, emotions, and experiences...",
    height=160,
    max_chars=5000,
    label_visibility="collapsed",
    key="journal_input",
)

col_count, col_btn = st.columns([3, 1])
with col_count:
    st.caption(f"{len(entry_text)} / 5,000 characters")
with col_btn:
    analyze_clicked = st.button("🔍 Analyze", type="primary", use_container_width=True)


# ---------------------------------------------------------------------------
# Analyze action
# ---------------------------------------------------------------------------
if analyze_clicked and entry_text.strip():
    with st.spinner("🧠 Analyzing your entry..."):
        try:
            resp = httpx.post(
                f"{API_BASE}/journal",
                json={"text": entry_text},
                timeout=120.0,
            )
            if resp.status_code == 200:
                data = resp.json()
                st.session_state.last_analysis = data["analysis"]
                st.session_state.last_text = data["text"]
                st.toast("✅ Analysis complete!", icon="🧠")
            elif resp.status_code == 422:
                st.error(f"Validation error: {resp.json().get('detail', 'Invalid input')}")
            elif resp.status_code == 502:
                st.error("The AI model returned an invalid response. Please try again.")
            elif resp.status_code == 503:
                st.error("Analysis service is temporarily unavailable. Please try again shortly.")
            else:
                st.error(f"Unexpected error (HTTP {resp.status_code})")
        except httpx.ConnectError:
            st.error("Could not connect to the API server. Is it running on port 8000?")
        except httpx.TimeoutException:
            st.error("The request timed out — the LLM may need more time. Try a shorter entry.")
        except Exception as exc:
            st.error(f"Something went wrong: {exc}")
elif analyze_clicked:
    st.warning("Please write something before analyzing.")


# ---------------------------------------------------------------------------
# Tabs: Analysis / History
# ---------------------------------------------------------------------------
tab_analysis, tab_history = st.tabs(["📊 Analysis", "📔 History"])

# --- Analysis Tab ---
with tab_analysis:
    if st.session_state.last_analysis:
        st.markdown(
            f'<p class="card-text-quote">"{st.session_state.last_text}"</p>',
            unsafe_allow_html=True,
        )
        st.divider()
        render_analysis(st.session_state.last_analysis)
    else:
        st.markdown(
            '<p class="empty-state">'
            '<span class="empty-icon">🧠</span><br>'
            "Write a journal entry and click <strong>Analyze</strong> to see your results here."
            "</p>",
            unsafe_allow_html=True,
        )

# --- History Tab ---
with tab_history:
    try:
        resp = httpx.get(f"{API_BASE}/journal/history?limit=20", timeout=10.0)
        if resp.status_code == 200:
            entries = resp.json()
            if not entries:
                st.markdown(
                    '<p class="empty-state">'
                    '<span class="empty-icon">📔</span><br>'
                    "No journal entries yet.<br>Write your first entry above to get started."
                    "</p>",
                    unsafe_allow_html=True,
                )
            else:
                for entry in entries:
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
                        render_analysis(analysis)

                    st.divider()
        else:
            st.error("Failed to load history.")
    except httpx.ConnectError:
        st.info("Cannot load history — API server not reachable.")
    except Exception as exc:
        st.error(f"Error loading history: {exc}")
