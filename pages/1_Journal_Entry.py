"""
Journal Entry page — write and submit a new entry for AI analysis.
"""

import streamlit as st
import httpx
import sys
from pathlib import Path

# Add project root to path so we can import ui.helpers
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ui.helpers import inject_css, render_analysis, API_BASE

inject_css()

# --- Header ---
st.markdown('<p class="gradient-header">✍️ Journal Entry</p>', unsafe_allow_html=True)
st.markdown('<p class="tagline">Write freely — your AI therapist is listening</p>', unsafe_allow_html=True)

# --- State ---
if "last_analysis" not in st.session_state:
    st.session_state.last_analysis = None
if "last_text" not in st.session_state:
    st.session_state.last_text = None

# --- Input ---
st.markdown('<p class="section-title">📝 What\'s on your mind?</p>', unsafe_allow_html=True)

entry_text = st.text_area(
    label="Journal entry",
    placeholder="How are you feeling today? Write freely about your thoughts, emotions, and experiences...",
    height=200,
    max_chars=5000,
    label_visibility="collapsed",
    key="journal_input",
)

col_count, col_btn = st.columns([3, 1])
with col_count:
    st.caption(f"{len(entry_text)} / 5,000 characters")
with col_btn:
    analyze_clicked = st.button("🔍 Analyze", type="primary", use_container_width=True)

# --- Submit ---
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
                st.error("Your entry couldn't be processed. Please try writing it a bit differently.")
            elif resp.status_code == 502:
                st.error("The analysis returned an unexpected result. Please try again.")
            elif resp.status_code == 503:
                st.error("Analysis is temporarily unavailable. Please try again in a moment.")
            else:
                st.error("Something went wrong. Please try again.")
        except httpx.ConnectError:
            st.error("Could not connect to the app. Please make sure everything is running.")
        except httpx.TimeoutException:
            st.error("This is taking longer than usual. Please try again — the AI may be busy.")
        except Exception:
            st.error("Something went wrong. Please try again.")
elif analyze_clicked:
    st.warning("Please write something before analyzing.")

# --- Show latest result ---
if st.session_state.last_analysis:
    st.divider()
    st.markdown(
        f'<p class="card-text-quote">"{st.session_state.last_text}"</p>',
        unsafe_allow_html=True,
    )
    st.divider()
    render_analysis(st.session_state.last_analysis)
    st.markdown("---")
    st.info("💡 Visit the **Dashboard** page in the sidebar to see your full history and trends.")
