"""Calculated Caliber design tokens — inject once; does not touch API logic."""

import streamlit as st

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"], .stApp, .stMarkdown, .stText, .stMetric {
  font-family: Inter, system-ui, sans-serif !important;
  font-variant-numeric: tabular-nums;
}
.stApp { background: #F5F4F0 !important; color: #15181E !important; }
[data-testid="stSidebar"] {
  background: #FFFFFF !important;
  border-right: 1px solid #E7E5E0 !important;
}
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: #15181E !important; font-weight: 600 !important; }
.block-container { padding-top: 1.5rem !important; max-width: 1100px !important; }
h1 { color: #15181E !important; font-weight: 600 !important; letter-spacing: -0.02em !important; }
h2, h3 { color: #15181E !important; font-weight: 600 !important; }
.stCaption, [data-testid="stCaptionContainer"] { color: #6B7280 !important; }
div[data-testid="stMetric"] {
  background: #FFFFFF;
  border: 1px solid #E7E5E0;
  border-radius: 10px;
  padding: 1rem 1.1rem;
  box-shadow: none !important;
}
div[data-testid="stMetricLabel"] { color: #6B7280 !important; text-transform: uppercase;
  letter-spacing: 0.02em; font-size: 11px !important; font-weight: 500 !important; }
div[data-testid="stMetricValue"] { color: #15181E !important; font-weight: 600 !important; }
.stButton > button {
  background: #0F766E !important; color: #fff !important; border: none !important;
  border-radius: 6px !important; font-weight: 500 !important; height: 36px;
}
.stButton > button:hover { background: #0D655E !important; color: #fff !important; }
.stTextInput input, .stNumberInput input, .stDateInput input, .stTimeInput input,
div[data-baseweb="select"] > div {
  border: 1px solid #E7E5E0 !important; border-radius: 6px !important;
  background: #FFFFFF !important; color: #15181E !important;
}
.stAlert { border-radius: 6px !important; border: 1px solid #E7E5E0 !important; }
hr { border-color: #E7E5E0 !important; }
[data-testid="stHorizontalBlock"] { gap: 0.75rem; }
"""


def apply_theme() -> None:
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)
