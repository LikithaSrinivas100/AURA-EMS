"""AURA-EMS dashboard — Calculated Caliber UI; same FastAPI wiring."""
from datetime import datetime

import pandas as pd
import streamlit as st

from components.ahead_chart import render_ahead_chart
from components.forecast_chart import render_forecast_chart
from components.peaks_table import render_peaks_table
from components.theme import apply_theme, kpi_html
from services import api_client
from services.config import DEFAULT_PEAKS_LIMIT

st.set_page_config(
    page_title="AURA-EMS | Campus Energy Demand Forecasting",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_theme()

data_range, range_error = api_client.get_data_range()
if data_range and not range_error:
    default_start = pd.to_datetime(data_range["min_ts"]).to_pydatetime()
    default_end = pd.to_datetime(data_range["max_ts"]).to_pydatetime()
else:
    default_start = datetime(2025, 9, 2)
    default_end = datetime(2026, 9, 1)

with st.sidebar:
    st.markdown("### Filters")
    st.caption("Start/End → history, peaks, carbon · End → forecast ahead")
    start_date = st.date_input("Start window", value=default_start.date())
    start_time = st.time_input("Start time", value=default_start.time(), label_visibility="collapsed")
    end_date = st.date_input("End window", value=default_end.date())
    end_time = st.time_input("End time", value=default_end.time(), label_visibility="collapsed")
    peaks_limit = st.number_input("Peaks limit", min_value=1, max_value=50, value=DEFAULT_PEAKS_LIMIT)
    show_model_lines = st.checkbox("Show XGB / LGB lines", value=False)
    forecast_from_end = st.checkbox("Forecast ahead from selected end date", value=True)
    st.button("Refresh", width="stretch")

start_dt = datetime.combine(start_date, start_time).isoformat()
end_dt = datetime.combine(end_date, end_time).isoformat()
end_ts, max_ts, min_ts = pd.Timestamp(end_dt), pd.Timestamp(default_end), pd.Timestamp(default_start)
earliest_as_of = min_ts + pd.Timedelta(hours=24)
as_of_note = None
as_of = None
if forecast_from_end:
    if end_ts > max_ts:
        as_of = max_ts.isoformat()
        as_of_note = f"End date is after available history. Forecasting from last observation {max_ts}."
    elif end_ts < earliest_as_of:
        as_of = earliest_as_of.isoformat()
        as_of_note = f"End date needs 24h of prior history. Forecasting from {earliest_as_of}."
    else:
        as_of = end_ts.isoformat()
else:
    as_of_note = "Using last meter observation as forecast anchor (checkbox off)."

health, health_error = api_client.get_health()
if health_error:
    st.markdown(f'<div class="aura-warn">Backend unavailable · {health_error}</div>', unsafe_allow_html=True)

metrics, metrics_error = api_client.get_metrics()
if metrics_error:
    st.markdown(f'<div class="aura-warn">{metrics_error}</div>', unsafe_allow_html=True)
elif metrics:
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(kpi_html("Active model", str(metrics.get("active_model", "—")), sub="Production model"), unsafe_allow_html=True)
    c2.markdown(kpi_html("RMSE", f"{metrics.get('rmse', 0):.2f}", "kW", "Root mean squared error"), unsafe_allow_html=True)
    c3.markdown(kpi_html("MAPE", f"{metrics.get('mape', 0):.2f}", "%", "Mean absolute pct error"), unsafe_allow_html=True)
    c4.markdown(kpi_html("MAE", f"{metrics.get('mae', 0):.2f}", "kW", "Mean absolute error"), unsafe_allow_html=True)

st.markdown('<div class="aura-card"><div class="aura-sec-title">Actual vs predicted demand</div>', unsafe_allow_html=True)
forecasts, forecasts_error = api_client.get_forecasts(start_dt, end_dt)
if forecasts_error:
    st.markdown(f'<div class="aura-warn">{forecasts_error}</div>', unsafe_allow_html=True)
elif forecasts:
    items = forecasts.get("items", [])
    if not items:
        st.info("No data for the selected dates")
    else:
        render_forecast_chart(items, show_model_lines=show_model_lines)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="aura-card"><div class="aura-sec-title">Demand forecast ahead</div>', unsafe_allow_html=True)
if as_of_note:
    st.info(as_of_note)
horizon = st.radio("Horizon", ["Next 24 hours", "Next 7 days"], horizontal=True, label_visibility="collapsed")
hours = 24 if horizon == "Next 24 hours" else 168
ahead, ahead_error = api_client.get_forecast_ahead(hours, as_of=as_of)
if ahead_error:
    st.markdown(f'<div class="aura-warn">{ahead_error}</div>', unsafe_allow_html=True)
elif ahead:
    ahead_df = pd.DataFrame(ahead.get("items", []))
    if not ahead_df.empty:
        ahead_df["ts"] = pd.to_datetime(ahead_df["ts"])
        st.markdown(
            f'<div class="aura-sec-sub">From {ahead["generated_from"]} · Horizon: {hours}h · '
            f'Weather: {ahead["weather_source"]} · '
            f'Exam intervals: {int(ahead_df["is_exam"].sum())}, Vacation: {int(ahead_df["is_vacation"].sum())}</div>',
            unsafe_allow_html=True,
        )
        render_ahead_chart(ahead_df)
        high = ahead_df[ahead_df["risk_level"] == "HIGH"]
        if high.empty:
            st.markdown('<div class="aura-ok">No HIGH peaks expected.</div>', unsafe_allow_html=True)
        else:
            st.markdown(
                f'<div class="aura-warn">{len(high)} HIGH peak intervals expected — peak '
                f'{high["total_kw"].max():.1f} kW at {high.loc[high["total_kw"].idxmax(), "ts"]}.</div>',
                unsafe_allow_html=True,
            )
st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="aura-sec-title">Green Skills: carbon and cost impact</div>', unsafe_allow_html=True)
carbon, carbon_error = api_client.get_carbon(hours, as_of=as_of, start=start_dt, end=end_dt)
if carbon_error:
    st.markdown(f'<div class="aura-warn">{carbon_error}</div>', unsafe_allow_html=True)
elif carbon:
    if carbon["energy_avoided_kwh"] == 0 and "No rows" in carbon.get("notes", ""):
        st.info(carbon["notes"])
    else:
        g1, g2, g3, g4 = st.columns(4)
        g1.markdown(kpi_html("CO₂ avoided", f"{carbon['co2_avoided_kg']:.1f}", "kg", "Peak-shave estimate", True), unsafe_allow_html=True)
        g2.markdown(kpi_html("Cost saved", f"₹{carbon['cost_saved_inr']:.0f}", "", "Avoided surcharges", True), unsafe_allow_html=True)
        g3.markdown(kpi_html("Energy avoided", f"{carbon['energy_avoided_kwh']:.1f}", "kWh", "Curtailment & load shifting"), unsafe_allow_html=True)
        g4.markdown(kpi_html("Trees equivalent", f"{carbon['trees_equivalent']:.2f}", "trees", "Annual sequestration index"), unsafe_allow_html=True)
        st.caption(carbon.get("notes", ""))

st.markdown('<div class="aura-card"><div class="aura-sec-title">Peak risk windows</div>', unsafe_allow_html=True)
peaks, peaks_error = api_client.get_peaks(limit=int(peaks_limit), start=start_dt, end=end_dt)
if peaks_error:
    st.markdown(f'<div class="aura-warn">{peaks_error}</div>', unsafe_allow_html=True)
elif peaks:
    render_peaks_table(peaks.get("items", []))
st.markdown("</div>", unsafe_allow_html=True)

footer_cols = st.columns(2)
footer_cols[0].caption("Decision-support tool, not a replacement for official BESCOM billing.")
if metrics and not metrics_error:
    footer_cols[1].caption(f"Model in use: {metrics.get('active_model', 'n/a')}")
