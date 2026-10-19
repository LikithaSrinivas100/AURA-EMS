"""Section B — KPI cards."""
import streamlit as st


def render_metrics_cards(metrics: dict) -> None:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Active model", str(metrics.get("active_model", "—")))
    col2.metric("RMSE (kW)", f"{metrics.get('rmse', 0):.2f}")
    col3.metric("MAPE (%)", f"{metrics.get('mape', 0):.2f}")
    col4.metric("MAE (kW)", f"{metrics.get('mae', 0):.2f}")
