"""Calculated Caliber shell — readable contrast; sidebar stays open."""

import streamlit as st

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"], .stApp, .stMarkdown, .stText, button, input, label {
  font-family: Inter, system-ui, sans-serif !important;
  font-variant-numeric: tabular-nums;
}
.stApp { background: #F5F4F0 !important; color: #15181E !important; }

header[data-testid="stHeader"] {
  background: transparent !important;
  height: 0 !important;
  min-height: 0 !important;
}
#MainMenu, footer { visibility: hidden; }

/* Permanently hide every Streamlit sidebar collapse / hamburger control */
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="stSidebarCollapseButton"],
button[kind="header"],
button[kind="headerNoPadding"],
[data-testid="baseButton-header"],
[data-testid="baseButton-headerNoPadding"],
section[data-testid="stSidebar"] button[kind="header"],
section[data-testid="stSidebar"] button[kind="headerNoPadding"],
section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"],
section[data-testid="stSidebar"] [data-testid="baseButton-header"],
section[data-testid="stSidebar"] [data-testid="baseButton-headerNoPadding"],
section[data-testid="stSidebar"] [data-testid="stBaseButton-header"],
section[data-testid="stSidebar"] [data-testid="stBaseButton-headerNoPadding"] {
  display: none !important;
  visibility: hidden !important;
  pointer-events: none !important;
  width: 0 !important;
  height: 0 !important;
  opacity: 0 !important;
}

.aura-topnav {
  position: fixed; top: 0; left: 0; right: 0; height: 56px; z-index: 1000000;
  background: #FFFFFF;
  border-bottom: 1px solid #E7E5E0;
  border-top: 3px solid #6366F1;
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 1.25rem; box-sizing: border-box;
}
.aura-topnav .brand { display: flex; align-items: center; gap: 0.75rem; }
.aura-topnav .logo {
  width: 32px; height: 32px; border-radius: 8px; background: #0F766E;
  display: inline-flex; align-items: center; justify-content: center;
  color: #fff; font-size: 16px; font-weight: 700;
}
.aura-topnav .divider { width: 1px; height: 20px; background: #D1D5DB; }
.aura-topnav .brand-name { font-size: 18px; font-weight: 600; color: #15181E; }
.aura-topnav .badge {
  font-size: 11px; font-weight: 500; color: #374151; background: #F2F3FC;
  border: 1px solid #CBD5E1; border-radius: 999px; padding: 3px 10px;
}
.aura-topnav .right { display: flex; align-items: center; gap: 0.75rem; }
.aura-topnav .avatar {
  width: 32px; height: 32px; border-radius: 999px; background: #0F766E;
  color: #fff; display: inline-flex; align-items: center; justify-content: center;
}

section[data-testid="stSidebar"] {
  top: 56px !important; height: calc(100vh - 56px) !important;
  background: #FFFFFF !important;
  border-right: 1px solid #E7E5E0 !important;
  transform: none !important;
  margin-left: 0 !important;
  left: 0 !important;
  visibility: visible !important;
  display: block !important;
  opacity: 1 !important;
  min-width: 21rem !important;
  width: 21rem !important;
  z-index: 999999 !important;
}
section[data-testid="stSidebar"][aria-expanded="false"],
section[data-testid="stSidebar"].collapsed {
  transform: none !important;
  margin-left: 0 !important;
  left: 0 !important;
  visibility: visible !important;
  display: block !important;
}
div[data-testid="stSidebarContent"],
section[data-testid="stSidebar"] > div {
  background: #FFFFFF !important;
  visibility: visible !important;
  display: flex !important;
}
section[data-testid="stSidebar"] *,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
  color: #15181E !important;
}
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] { color: #4B5563 !important; }
section[data-testid="stSidebar"] input,
section[data-testid="stSidebar"] [data-baseweb="input"] input,
section[data-testid="stSidebar"] [data-baseweb="select"] > div {
  background: #FFFFFF !important; color: #15181E !important;
  border: 1px solid #E7E5E0 !important; border-radius: 6px !important;
}

.block-container {
  padding-top: 4.25rem !important;
  padding-bottom: 2rem !important;
  max-width: 1100px !important;
}

div[role="radiogroup"] label,
div[role="radiogroup"] p,
.stRadio label, .stCheckbox label, .stCheckbox span {
  color: #15181E !important;
  opacity: 1 !important;
}

.aura-card {
  background: #FFFFFF; border: 1px solid #E7E5E0; border-radius: 10px;
  padding: 1.25rem 1.35rem; margin-bottom: 1rem;
}
div[data-testid="stHorizontalBlock"] {
  gap: 12px !important;
  align-items: stretch !important;
  margin-bottom: 12px !important;
}
div[data-testid="stHorizontalBlock"] > div {
  width: 25% !important;
  flex: 1 1 0 !important;
}
.aura-kpi {
  background: #FFFFFF; border: 1px solid #E7E5E0; border-radius: 10px;
  padding: 1rem 1.1rem; box-sizing: border-box;
  min-height: 128px; height: 128px;
  display: flex; flex-direction: column; justify-content: space-between;
}
.aura-kpi .lbl {
  font-size: 11px; font-weight: 500; letter-spacing: 0.04em; text-transform: uppercase; color: #4B5563;
}
.aura-kpi .val {
  margin-top: 0.4rem; font-size: 22px; font-weight: 600; color: #15181E;
  line-height: 1.2; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.aura-kpi .unit { font-size: 14px; color: #4B5563; margin-left: 4px; }
.aura-kpi .sub { margin-top: 0.35rem; font-size: 12px; color: #4B5563; }
.aura-kpi .sub.good { color: #15803D; font-weight: 500; }
.aura-sec-title { font-size: 16px; font-weight: 600; color: #15181E; margin: 0 0 0.5rem 0; }
.aura-sec-sub { font-size: 12px; color: #374151; margin-bottom: 0.75rem; }
.aura-warn {
  background: #FEF2F2; border-left: 4px solid #B91C1C; color: #991B1B;
  padding: 12px 14px; border-radius: 0 6px 6px 0; font-size: 13px; font-weight: 500; margin: 8px 0;
}
.aura-ok {
  background: #F0FDF4; border-left: 4px solid #15803D; color: #166534;
  padding: 12px 14px; border-radius: 0 6px 6px 0; font-size: 13px; font-weight: 500; margin: 8px 0;
}
.aura-action {
  background: #FFFBEB; border: 1px solid #F59E0B; color: #92400E;
  padding: 12px 14px; border-radius: 6px; font-size: 13px; font-weight: 500; margin-top: 10px;
}
.stButton > button {
  background: #0F766E !important; color: #fff !important; border: none !important;
  border-radius: 6px !important; font-weight: 500 !important; height: 36px !important;
}
.stButton > button:hover { background: #0D655E !important; color: #fff !important; }
div[data-testid="stMetric"] { display: none !important; }
hr { border-color: #E7E5E0 !important; }
[data-testid="stCaptionContainer"] { color: #374151 !important; }
"""

HEADER = """
<div class="aura-topnav">
  <div class="brand">
    <div class="logo">⚡</div>
    <span class="divider"></span>
    <span class="brand-name">AURA-EMS</span>
    <span class="badge">Alliance University, Bangalore</span>
  </div>
  <div class="right">
    <span class="divider"></span>
    <div class="avatar">👤</div>
  </div>
</div>
"""


# Keep sidebar expanded: re-open if Streamlit collapses it, strip hide controls.
_SIDEBAR_LOCK_JS = """
<script>
(function () {
  const root = window.parent.document;
  function unlock() {
    const sidebar = root.querySelector('section[data-testid="stSidebar"]');
    if (sidebar) {
      sidebar.style.transform = 'none';
      sidebar.style.marginLeft = '0';
      sidebar.style.left = '0';
      sidebar.style.visibility = 'visible';
      sidebar.style.display = 'block';
      sidebar.setAttribute('aria-expanded', 'true');
    }
    root.querySelectorAll(
      '[data-testid="collapsedControl"],[data-testid="stSidebarCollapsedControl"],' +
      '[data-testid="stSidebarCollapseButton"],button[kind="header"],button[kind="headerNoPadding"]'
    ).forEach(function (el) {
      el.style.display = 'none';
      el.style.pointerEvents = 'none';
    });
    const expander = root.querySelector('[data-testid="collapsedControl"]');
    if (expander && expander.offsetParent !== null) {
      try { expander.click(); } catch (e) {}
    }
  }
  unlock();
  if (!window.__auraSidebarLock) {
    window.__auraSidebarLock = setInterval(unlock, 400);
  }
})();
</script>
"""


def apply_theme() -> None:
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)
    st.markdown(HEADER, unsafe_allow_html=True)
    st.components.v1.html(_SIDEBAR_LOCK_JS, height=0)


def kpi_html(label: str, value: str, unit: str = "", sub: str = "", good: bool = False) -> str:
    sub_cls = "sub good" if good else "sub"
    unit_html = f'<span class="unit">{unit}</span>' if unit else ""
    sub_html = f'<div class="{sub_cls}">{sub}</div>' if sub else ""
    return (
        f'<div class="aura-kpi"><div class="lbl">{label}</div>'
        f'<div class="val">{value}{unit_html}</div>{sub_html}</div>'
    )
