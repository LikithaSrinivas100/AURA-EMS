"""AURA-EMS | Campus Energy Demand Forecasting — Streamlit dashboard.

Owner: Risha (frontend). Consumes Anushka's FastAPI backend only —
never loads .pkl model files directly.

Run with:
    streamlit run app.py
"""
from datetime import datetime, timedelta

import streamlit as st

from components.forecast_chart import render_forecast_chart
from components.metrics_cards import render_metrics_cards
from components.peaks_table import render_peaks_table
from services import api_client
from services.config import DEFAULT_PEAKS_LIMIT

st.set_page_config(
    page_title="AURA-EMS | Campus Energy Demand Forecasting",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Section A — Header
# ---------------------------------------------------------------------------
st.title("AURA-EMS | Campus Energy Demand Forecasting")
st.caption("Predictive demand forecasting to reduce peak-load risk and energy waste.")

# ---------------------------------------------------------------------------
# Sidebar — Section E filters
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Filters")
    default_start = datetime(2025, 9, 2)
    default_end = datetime(2026, 9, 1)
    start_date = st.date_input("Start date", value=default_start.date())
    start_time = st.time_input("Start time", value=default_start.time())
    end_date = st.date_input("End date", value=default_end.date())
    end_time = st.time_input("End time", value=default_end.time())
    peaks_limit = st.number_input(
        "Peaks limit", min_value=1, max_value=50, value=DEFAULT_PEAKS_LIMIT
    )
    show_model_lines = st.checkbox("Show XGB / LGB lines", value=False)
    st.button("Refresh", use_container_width=True)  # st.button reruns the script on click

start_dt = datetime.combine(start_date, start_time).isoformat()
end_dt = datetime.combine(end_date, end_time).isoformat()

# ---------------------------------------------------------------------------
# Health indicator
# ---------------------------------------------------------------------------
health, health_error = api_client.get_health()

if health_error:
    st.error(f"🔴 {health_error}")

st.divider()

# ---------------------------------------------------------------------------
# Section B — KPI cards
# ---------------------------------------------------------------------------
metrics, metrics_error = api_client.get_metrics()

if metrics_error:
    st.error(metrics_error)
elif metrics:
    render_metrics_cards(metrics)

st.divider()

# ---------------------------------------------------------------------------
# Section C — Actual vs Predicted chart
# ---------------------------------------------------------------------------
st.subheader("Actual vs Predicted Demand")
forecasts, forecasts_error = api_client.get_forecasts(start_dt, end_dt)

if forecasts_error:
    st.error(forecasts_error)
elif forecasts:
    render_forecast_chart(forecasts.get("items", []), show_model_lines=show_model_lines)

st.divider()

# ---------------------------------------------------------------------------
# Section D — Peak risk panel
# ---------------------------------------------------------------------------
st.subheader("Peak Risk Windows")
peaks, peaks_error = api_client.get_peaks(limit=int(peaks_limit))

if peaks_error:
    st.error(peaks_error)
elif peaks:
    render_peaks_table(peaks.get("items", []))

st.divider()

# ---------------------------------------------------------------------------
# Section F — Footer
# ---------------------------------------------------------------------------
footer_cols = st.columns(2)
footer_cols[0].caption(
    "Data-driven decision support tool. Not a replacement for official "
    "BESCOM billing systems."
)
if metrics and not metrics_error:
    footer_cols[1].caption(f"Model in use: {metrics.get('active_model', 'n/a')}")
