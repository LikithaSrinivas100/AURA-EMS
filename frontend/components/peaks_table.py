"""Section D — Peak risk table with design-system risk chips."""
import pandas as pd
import streamlit as st

CHIP = {
    "HIGH": ("#FEF2F2", "#FCA5A5", "#B91C1C"),
    "MEDIUM": ("#FFF7ED", "#FDBA74", "#C2410C"),
    "LOW": ("#F0FDF4", "#86EFAC", "#15803D"),
}


def _risk_badge(level: str) -> str:
    bg, border, text = CHIP.get(level, ("#F5F4F0", "#E7E5E0", "#6B7280"))
    return (
        f"<span style='background:{bg};border:1px solid {border};color:{text};"
        f"padding:2px 8px;border-radius:4px;font-size:11px;font-weight:500;'>{level}</span>"
    )


def render_peaks_table(items: list) -> None:
    if not items:
        st.info("No peak-risk windows in the current data.")
        return

    df = pd.DataFrame(items)
    df["Time"] = pd.to_datetime(df["ts"]).dt.strftime("%d %b, %H:%M")
    df["Predicted Demand (kW)"] = df["best_pred_kw"].map(lambda v: f"{v:.1f}")
    df["Risk"] = df["risk_level"].apply(_risk_badge)
    display_df = df[["Time", "Predicted Demand (kW)", "Risk"]]
    st.markdown(
        "<div style='background:#FFF;border:1px solid #E7E5E0;border-radius:10px;padding:8px 12px;"
        "overflow:auto;font-family:Inter,system-ui,sans-serif;font-size:13px;color:#15181E;'>"
        + display_df.to_html(escape=False, index=False)
        + "</div>",
        unsafe_allow_html=True,
    )
    if (df["risk_level"] == "HIGH").any():
        st.markdown(
            '<div class="aura-action">Facilities action: stagger HVAC / defer non-critical loads during this window.</div>',
            unsafe_allow_html=True,
        )
