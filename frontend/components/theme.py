"""Calculated Caliber shell — matches new_design/code.html chrome inside Streamlit."""

import streamlit as st

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
html, body, [class*="css"], .stApp, .stMarkdown, .stText, .stMetric, button, input, label {
  font-family: Inter, system-ui, sans-serif !important;
  font-variant-numeric: tabular-nums;
}
.stApp { background: #F5F4F0 !important; color: #15181E !important; }
header[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stSidebar"] {
  background: #FFFFFF !important;
  border-right: 1px solid #E7E5E0 !important;
  min-width: 260px !important;
}
[data-testid="stSidebar"] > div:first-child { padding-top: 0.5rem !important; }
.block-container {
  padding-top: 5.5rem !important;
  padding-bottom: 2rem !important;
  max-width: 1100px !important;
}
.aura-topnav {
  position: fixed; top: 0; left: 0; right: 0; height: 56px; z-index: 999990;
  background: #FFFFFF; border-bottom: 1px solid #E1E2EB;
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 1.25rem; font-family: Inter, system-ui, sans-serif;
}
.aura-topnav .brand { display: flex; align-items: center; gap: 0.75rem; }
.aura-topnav .brand strong { font-size: 18px; font-weight: 600; color: #15181E; }
.aura-topnav .badge {
  font-size: 11px; font-weight: 500; color: #505F76; background: #F2F3FC;
  border: 1px solid #BDC9C6; border-radius: 4px; padding: 2px 8px;
}
.aura-topnav .avatar {
  width: 32px; height: 32px; border-radius: 999px; background: #005C55;
  color: #fff; display: flex; align-items: center; justify-content: center; font-size: 12px;
}
.aura-card {
  background: #FFFFFF; border: 1px solid #E7E5E0; border-radius: 10px;
  padding: 1.25rem 1.35rem; margin-bottom: 1rem; box-shadow: none;
}
.aura-kpi {
  background: #FFFFFF; border: 1px solid #E7E5E0; border-radius: 10px;
  padding: 1.15rem 1.2rem; height: 100%;
}
.aura-kpi .lbl {
  font-size: 11px; font-weight: 500; letter-spacing: 0.04em; text-transform: uppercase; color: #6B7280;
}
.aura-kpi .val {
  margin-top: 0.65rem; font-size: 28px; font-weight: 600; color: #15181E; letter-spacing: -0.02em;
}
.aura-kpi .unit { font-size: 14px; color: #6B7280; margin-left: 4px; font-weight: 400; }
.aura-kpi .sub { margin-top: 0.35rem; font-size: 12px; color: #6B7280; }
.aura-kpi .sub.good { color: #15803D; font-weight: 500; }
.aura-status-ok { color: #15803D; font-size: 13px; font-weight: 500; }
.aura-status-bad {
  color: #B91C1C; background: #FEF2F2; border: 1px solid rgba(185,28,28,.4);
  border-radius: 6px; padding: 6px 10px; font-size: 12px; display: inline-block;
}
.aura-sec-title { font-size: 16px; font-weight: 600; color: #15181E; margin: 0 0 0.35rem 0; }
.aura-sec-sub { font-size: 12px; color: #6B7280; margin-bottom: 0.75rem; }
.stButton > button {
  background: #0F766E !important; color: #fff !important; border: none !important;
  border-radius: 6px !important; font-weight: 500 !important; height: 36px !important;
}
.stButton > button:hover { background: #0D655E !important; }
div[data-testid="stMetric"] { display: none !important; }
hr { border-color: #E7E5E0 !important; opacity: 1 !important; }
"""

HEADER = """
<div class="aura-topnav">
  <div class="brand">
    <strong>AURA-EMS</strong>
    <span class="badge">Alliance University, Bangalore</span>
  </div>
  <div class="avatar">AU</div>
</div>
"""


def apply_theme() -> None:
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)
    st.markdown(HEADER, unsafe_allow_html=True)


def kpi_html(label: str, value: str, unit: str = "", sub: str = "", good: bool = False) -> str:
    sub_cls = "sub good" if good else "sub"
    unit_html = f'<span class="unit">{unit}</span>' if unit else ""
    sub_html = f'<div class="{sub_cls}">{sub}</div>' if sub else ""
    return (
        f'<div class="aura-kpi"><div class="lbl">{label}</div>'
        f'<div class="val">{value}{unit_html}</div>{sub_html}</div>'
    )
