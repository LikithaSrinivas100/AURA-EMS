"""AURA-EMS Streamlit dashboard — consumes FastAPI only."""
from datetime import datetime

import pandas as pd
import streamlit as st

from components.forecast_chart import render_forecast_chart
from components.metrics_cards import render_metrics_cards
from components.peaks_table import render_peaks_table
from components.theme import apply_theme
from services import api_client
from services.config import DEFAULT_PEAKS_LIMIT

st.set_page_config(page_title="AURA-EMS | Campus Energy Demand Forecasting", layout="wide")
apply_theme()

st.title("AURA-EMS")
st.caption("Campus energy demand forecasting · Predictive demand forecasting to reduce peak-load risk and energy waste")

data_range, range_error = api_client.get_data_range()
if data_range and not range_error:
    default_start = pd.to_datetime(data_range["min_ts"]).to_pydatetime()
    default_end = pd.to_datetime(data_range["max_ts"]).to_pydatetime()
else:
    default_start = datetime(2025, 9, 2)
    default_end = datetime(2026, 9, 1)

with st.sidebar:
    st.header("Filters")
    st.caption(
        "Start/End → Actual vs Predicted, Peaks, Carbon. "
        "End date → Demand Forecast Ahead starts from that moment (clamped to available history)."
    )
    start_date = st.date_input("Start date", value=default_start.date())
    start_time = st.time_input("Start time", value=default_start.time())
    end_date = st.date_input("End date", value=default_end.date())
    end_time = st.time_input("End time", value=default_end.time())
    peaks_limit = st.number_input("Peaks limit", min_value=1, max_value=50, value=DEFAULT_PEAKS_LIMIT)
    show_model_lines = st.checkbox("Show XGB / LGB lines", value=False)
    st.button("Refresh", width="stretch")

start_dt = datetime.combine(start_date, start_time).isoformat()
end_dt = datetime.combine(end_date, end_time).isoformat()
# Always anchor ahead forecast on End date, clamped into history (needs ≥24h prior)
end_ts = pd.Timestamp(end_dt)
max_ts = pd.Timestamp(default_end)
min_ts = pd.Timestamp(default_start)
earliest_as_of = min_ts + pd.Timedelta(hours=24)
as_of_note = None
if end_ts > max_ts:
    as_of = max_ts.isoformat()
    as_of_note = f"End date is after available history. Forecasting from last observation {max_ts}."
elif end_ts < earliest_as_of:
    as_of = earliest_as_of.isoformat()
    as_of_note = f"End date needs 24h of prior history. Forecasting from {earliest_as_of}."
else:
    as_of = end_ts.isoformat()

health, health_error = api_client.get_health()
if health_error:
    st.error(f"Backend unavailable · {health_error}")
elif health:
    st.success("Backend online")

st.divider()
metrics, metrics_error = api_client.get_metrics()
if metrics_error:
    st.error(metrics_error)
elif metrics:
    render_metrics_cards(metrics)

st.divider()
st.subheader("Actual vs Predicted Demand")
forecasts, forecasts_error = api_client.get_forecasts(start_dt, end_dt)
if forecasts_error:
    st.error(forecasts_error)
elif forecasts:
    items = forecasts.get("items", [])
    if not items:
        st.info("No rows in the selected date range. Widen the filter.")
    else:
        render_forecast_chart(items, show_model_lines=show_model_lines)

st.divider()
st.subheader("Demand Forecast Ahead")
st.caption(
    "Forecast starts right after your sidebar End date (24h or 7 days forward). "
    "Change End date within available history to jump the chart."
)
if as_of_note:
    st.info(as_of_note)
horizon = st.radio("Horizon", ["Next 24 hours", "Next 7 days"], horizontal=True)
hours = 24 if horizon == "Next 24 hours" else 168
ahead, ahead_error = api_client.get_forecast_ahead(hours, as_of=as_of)
if ahead_error:
    st.error(ahead_error)
elif ahead:
    ahead_df = pd.DataFrame(ahead.get("items", []))
    if not ahead_df.empty:
        ahead_df["ts"] = pd.to_datetime(ahead_df["ts"])
        st.caption(
            f"From last observation at {ahead['generated_from']} | Weather: {ahead['weather_source']} | "
            f"Exam intervals: {int(ahead_df['is_exam'].sum())} | Vacation intervals: {int(ahead_df['is_vacation'].sum())}"
        )
        zone_cols = {"total_kw": "Total campus", "academic_kw": "Academic blocks", "hostel_kw": "Hostels"}
        chart_df = ahead_df.set_index("ts")[list(zone_cols)].rename(columns=zone_cols)
        # Keep Streamlit line_chart for interactivity; theme CSS styles the page chrome
        st.line_chart(chart_df, color=["#15181E", "#0F766E", "#64748B"])
        high = ahead_df[ahead_df["risk_level"] == "HIGH"]
        if high.empty:
            st.success(f"No HIGH peak-risk intervals expected in the {horizon.lower()}.")
        else:
            st.warning(
                f"{len(high)} HIGH peak-risk intervals expected — peak {high['total_kw'].max():.1f} kW "
                f"at {high.loc[high['total_kw'].idxmax(), 'ts']}."
            )

st.divider()
st.subheader("Green Skills — Carbon & Cost Impact")
st.caption("Uses your sidebar Start/End dates (same window as Actual vs Predicted / Peaks).")
carbon, carbon_error = api_client.get_carbon(hours, as_of=as_of, start=start_dt, end=end_dt)
if carbon_error:
    st.error(carbon_error)
elif carbon:
    if carbon["energy_avoided_kwh"] == 0 and "No rows" in carbon.get("notes", ""):
        st.info(carbon["notes"])
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("CO₂ avoided (kg)", f"{carbon['co2_avoided_kg']:.1f}")
        c2.metric("Cost saved (₹)", f"{carbon['cost_saved_inr']:.0f}")
        c3.metric("Energy avoided (kWh)", f"{carbon['energy_avoided_kwh']:.1f}")
        c4.metric("Trees equiv.", f"{carbon['trees_equivalent']:.2f}")
        st.caption(carbon.get("notes", ""))

st.divider()
st.subheader("Peak Risk Windows")
peaks, peaks_error = api_client.get_peaks(limit=int(peaks_limit), start=start_dt, end=end_dt)
if peaks_error:
    st.error(peaks_error)
elif peaks:
    render_peaks_table(peaks.get("items", []))

st.divider()
footer_cols = st.columns(2)
footer_cols[0].caption(
    "Data-driven decision support tool. Not a replacement for official BESCOM billing systems."
)
if metrics and not metrics_error:
    footer_cols[1].caption(f"Model in use: {metrics.get('active_model', 'n/a')}")
