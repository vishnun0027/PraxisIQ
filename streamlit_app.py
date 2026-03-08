"""
Mental Clarity Journal — Streamlit App Entry Point
Multi-page app: Journal Entry + Dashboard
"""

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ui.helpers import inject_css

st.set_page_config(
    page_title="Mental Clarity Journal",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="expanded",
)

inject_css()

# --- Landing page ---
st.markdown('<p class="gradient-header">🧠 Mental Clarity Journal</p>', unsafe_allow_html=True)
st.markdown('<p class="tagline">AI-powered emotional analysis &amp; CBT insights</p>', unsafe_allow_html=True)

st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        '<p class="section-title">✍️ Journal Entry</p>'
        '<p class="card-text-sm">Write a new journal entry and get instant AI-powered emotional analysis with CBT insights.</p>',
        unsafe_allow_html=True,
    )
    st.page_link("pages/1_Journal_Entry.py", label="✍️ Write Entry", icon="📝")

with col2:
    st.markdown(
        '<p class="section-title">📊 Dashboard</p>'
        '<p class="card-text-sm">View your emotional trends, most frequent emotions, intensity history, and past analyses.</p>',
        unsafe_allow_html=True,
    )
    st.page_link("pages/2_Dashboard.py", label="📊 View Dashboard", icon="📈")

with col3:
    st.markdown(
        '<p class="section-title">🔍 Find Similar Moments</p>'
        '<p class="card-text-sm">Describe a feeling or situation and we\'ll surface the most relevant past entries that match.</p>',
        unsafe_allow_html=True,
    )
    st.page_link("pages/3_Semantic_Search.py", label="🔍 Find Similar Moments", icon="🔍")
