"""Section D — Peak Risk panel, sourced from /forecasts/peaks."""
import pandas as pd
import streamlit as st

from services.config import RISK_COLORS


def _risk_badge(level: str) -> str:
    color = RISK_COLORS.get(level, "#888888")
    return (
        f"<span style='background-color:{color};color:white;padding:2px 10px;"
        f"border-radius:10px;font-size:0.8rem;font-weight:600;'>{level}</span>"
    )


def render_peaks_table(items: list) -> None:
    """Render the peak-risk table with risk badges and a facilities-action note.

    items: list of dicts shaped like the /forecasts/peaks "items" array
           (ts, best_pred_kw, risk_level)
    """
    if not items:
        st.info("No peak-risk windows in the current data.")
        return

    df = pd.DataFrame(items)
    df["Time"] = pd.to_datetime(df["ts"]).dt.strftime("%d %b, %H:%M")
    df["Predicted Demand (kW)"] = df["best_pred_kw"].map(lambda v: f"{v:.1f}")
    df["Risk"] = df["risk_level"].apply(_risk_badge)

    display_df = df[["Time", "Predicted Demand (kW)", "Risk"]]
    st.write(display_df.to_html(escape=False, index=False), unsafe_allow_html=True)

    if (df["risk_level"] == "HIGH").any():
        st.warning(
            "Facilities action: stagger HVAC / defer non-critical loads during "
            "this window."
        )
