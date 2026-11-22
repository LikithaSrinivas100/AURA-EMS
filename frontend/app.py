"""AURA-EMS dashboard — Calculated Caliber UI; same FastAPI wiring."""
from datetime import datetime
import time

import pandas as pd
import streamlit as st

from components.ahead_chart import render_ahead_chart
from components.forecast_chart import render_forecast_chart
from components.peaks_table import render_peaks_table
from components.theme import apply_theme, kpi_html
from services import api_client
from services.config import DEFAULT_PEAKS_LIMIT

ZONE_LABELS = {"campus": "Campus total", "academic": "Academic", "hostels": "Hostels"}
ZONE_TARGETS = {
    "campus": "Total_Campus_Demand_kW",
    "academic": "Academic_Demand_kW",
    "hostels": "Hostel_Demand_kW",
}

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

min_d, max_d = default_start.date(), default_end.date()
for _k, _v in (("aura_start", min_d), ("aura_end", max_d)):
    cur = st.session_state.get(_k)
    if cur is None or cur < min_d or cur > max_d:
        st.session_state[_k] = _v
with st.sidebar:
    st.markdown("### Filters")
    st.caption(f"Allowed dates: **{min_d}** → **{max_d}** (scroll sidebar for End window + times)")
    st.markdown("**1. Start window**")
    start_date = st.date_input(
        "Start date", min_value=min_d, max_value=max_d, key="aura_start"
    )
    start_time = st.time_input("Start time", value=default_start.time())
    st.markdown("**2. End window**")
    end_date = st.date_input(
        "End date", min_value=min_d, max_value=max_d, key="aura_end"
    )
    end_time = st.time_input("End time", value=default_end.time())
    st.markdown("**3. Other**")
    peaks_limit = st.number_input("Peaks limit", min_value=1, max_value=50, value=DEFAULT_PEAKS_LIMIT)
    show_model_lines = st.checkbox("Show XGB / LGB lines", value=False)
    forecast_from_end = st.checkbox("Forecast ahead from selected end date", value=True)
    st.button("Refresh", width="stretch")

zone = st.radio(
    "Zone",
    options=list(ZONE_LABELS.keys()),
    format_func=lambda z: ZONE_LABELS[z],
    horizontal=True,
    key="aura_zone",
)
if st.session_state.get("_replay_zone") != zone:
    st.session_state["_replay_zone"] = zone
    st.session_state["replay_items"] = []
    st.session_state["replay_cursor"] = 0
    st.session_state["replay_peaks"] = 0
    st.session_state["replay_running"] = False

start_dt = datetime.combine(start_date, start_time).isoformat()
end_dt = datetime.combine(end_date, end_time).isoformat()
start_ts = pd.Timestamp(start_dt)
end_ts = pd.Timestamp(end_dt)
max_ts, min_ts = pd.Timestamp(default_end), pd.Timestamp(default_start)
start_ts = min(max(start_ts, min_ts), max_ts)
end_ts = min(max(end_ts, min_ts), max_ts)
if end_ts < start_ts:
    start_ts, end_ts = end_ts, start_ts
earliest_as_of = min_ts + pd.Timedelta(hours=24)
raw_window_hours = max(1, int((end_ts - start_ts).total_seconds() // 3600) or 1)
window_hours = min(168, raw_window_hours)

health, health_error = api_client.get_health()
if health_error:
    st.markdown(f'<div class="aura-warn">Backend unavailable · {health_error}</div>', unsafe_allow_html=True)

live, live_error = api_client.get_today_peak()
if live and not live_error:
    peak_kw = float(live.get("expected_peak_kw") or 0)
    risk = str(live.get("risk_status", "LOW"))
    l1, l2, l3, l4 = st.columns(4)
    l1.markdown(kpi_html("Live Bengaluru temp", f"{live.get('live_temp_c', '—')}", "°C", "Open-Meteo now"), unsafe_allow_html=True)
    l2.markdown(kpi_html("Expected peak demand", f"{peak_kw:.1f}", "kW", f"Risk: {risk}", risk != "HIGH"), unsafe_allow_html=True)
    l3.markdown(kpi_html("Target peak window", str(live.get("target_peak_time", "—")), sub="Next 24h IST"), unsafe_allow_html=True)
    l4.markdown(kpi_html("Carbon mitigated", f"{float(live.get('carbon_avoided_kg') or 0):.1f}", "kg CO₂", "Peak-shave next 24h", True), unsafe_allow_html=True)
elif live_error:
    st.markdown(f'<div class="aura-warn">Live peak banner: {live_error}</div>', unsafe_allow_html=True)

# Next HIGH window — answer at a glance (F6)
peaks, peaks_error = api_client.get_peaks(
    limit=int(peaks_limit),
    start=start_ts.isoformat(),
    end=end_ts.isoformat(),
    zone=zone,
)
_next_high = None
if peaks and not peaks_error:
    _highs = [p for p in peaks.get("items", []) if p.get("risk_level") == "HIGH"]
    if _highs:
        _next_high = sorted(_highs, key=lambda p: p["ts"])[0]
if _next_high:
    st.markdown(
        f'<div class="aura-warn"><strong>Next HIGH window</strong> · '
        f'{_next_high["ts"]} · {_next_high["best_pred_kw"]:.1f} kW · '
        f'{_next_high.get("recommended_action", "")}</div>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        '<div class="aura-ok"><strong>Next HIGH window</strong> · none in selected range</div>',
        unsafe_allow_html=True,
    )

metrics, metrics_error = api_client.get_metrics(zone=zone)
if metrics_error:
    st.markdown(f'<div class="aura-warn">{metrics_error}</div>', unsafe_allow_html=True)
elif metrics:
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(kpi_html("Active model", str(metrics.get("active_model", "—")), sub=f"Zone · {ZONE_LABELS[zone]}"), unsafe_allow_html=True)
    c2.markdown(kpi_html("RMSE", f"{metrics.get('rmse', 0):.2f}", "kW", "Hold-out test error"), unsafe_allow_html=True)
    c3.markdown(kpi_html("MAPE", f"{metrics.get('mape', 0):.2f}", "%", "Hold-out test error"), unsafe_allow_html=True)
    c4.markdown(kpi_html("MAE", f"{metrics.get('mae', 0):.2f}", "kW", "Hold-out test error"), unsafe_allow_html=True)

chart_title = f"{ZONE_LABELS[zone]} · {ZONE_TARGETS[zone]} (kW) · simulated"
st.markdown('<div class="aura-card"><div class="aura-sec-title">Actual vs predicted demand</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="aura-sec-sub">{chart_title} · {start_ts.isoformat()} → {end_ts.isoformat()}</div>',
    unsafe_allow_html=True,
)
forecasts, forecasts_error = api_client.get_forecasts(
    start_ts.isoformat(), end_ts.isoformat(), zone=zone
)
if forecasts_error:
    st.markdown(f'<div class="aura-warn">{forecasts_error}</div>', unsafe_allow_html=True)
elif forecasts:
    items = forecasts.get("items", [])
    if not items:
        st.info("No data for the selected dates")
    else:
        render_forecast_chart(items, show_model_lines=show_model_lines, title=chart_title)
        fcsv, ferr = api_client.get_forecasts_csv(
            start_ts.isoformat(), end_ts.isoformat(), zone=zone
        )
        if fcsv and not ferr:
            st.download_button(
                "Download forecasts CSV",
                data=fcsv,
                file_name=f"forecasts_{zone}.csv",
                mime="text/csv",
                key="dl_forecasts",
            )
st.markdown("</div>", unsafe_allow_html=True)

# --- REPLAY (simulated) ---
st.markdown(
    '<div class="aura-card"><div class="aura-sec-title">REPLAY (simulated)</div>',
    unsafe_allow_html=True,
)
st.caption("Streams hold-out test intervals via /replay — not a live meter.")
for k, v in (
    ("replay_running", False),
    ("replay_cursor", 0),
    ("replay_items", []),
    ("replay_peaks", 0),
):
    st.session_state.setdefault(k, v)

r1, r2, r3, r4 = st.columns([1, 1, 1, 2])
if r1.button("Start", key="replay_start"):
    st.session_state.replay_running = True
if r2.button("Pause", key="replay_pause"):
    st.session_state.replay_running = False
if r3.button("Reset", key="replay_reset_btn"):
    api_client.replay_reset(zone=zone)
    st.session_state.replay_running = False
    st.session_state.replay_cursor = 0
    st.session_state.replay_items = []
    st.session_state.replay_peaks = 0
speed = r4.select_slider(
    "Speed (intervals / tick)", options=[1, 2, 4, 8, 16], value=4, key="replay_speed"
)
st.metric("Peak alerts raised (replay)", int(st.session_state.replay_peaks))

if st.session_state.replay_running:
    batch, err = api_client.replay_next(
        cursor=int(st.session_state.replay_cursor), n=int(speed), zone=zone
    )
    if err:
        st.warning(err)
        st.session_state.replay_running = False
    elif batch:
        st.session_state.replay_items.extend(batch.get("items") or [])
        st.session_state.replay_cursor = int(batch.get("next_cursor", st.session_state.replay_cursor))
        st.session_state.replay_peaks += int(batch.get("peak_alerts") or 0)
        if batch.get("done"):
            st.session_state.replay_running = False
            st.info("Replay finished test window.")
        else:
            time.sleep(0.35)
            st.rerun()

if st.session_state.replay_items:
    render_forecast_chart(
        st.session_state.replay_items,
        show_model_lines=False,
        title=f"REPLAY (simulated) · {ZONE_LABELS[zone]} · kW",
    )
st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="aura-card"><div class="aura-sec-title">Demand forecast ahead</div>', unsafe_allow_html=True)
horizon = st.radio(
    "Horizon",
    ["Match Start→End window", "Next 24 hours", "Next 7 days"],
    horizontal=True,
    label_visibility="collapsed",
)
# Match = forecast forward from Start for window length (capped 7d).
# 24h/7d presets = from End (checkbox) or last obs.
if horizon == "Match Start→End window":
    hours = window_hours
    anchor_ts = start_ts
    anchor_lbl = "Start"
    if raw_window_hours > 168:
        st.info(
            f"Selected window is ~{raw_window_hours // 24} days. "
            f"Ahead forecast max is 7 days — chart starts at Start ({start_ts.date()}) for 168h. "
            "Use Actual vs predicted above for the full Jun–Sep history."
        )
elif horizon == "Next 24 hours":
    hours = 24
    anchor_ts = end_ts if forecast_from_end else max_ts
    anchor_lbl = "End" if forecast_from_end else "last observation"
else:
    hours = 168
    anchor_ts = end_ts if forecast_from_end else max_ts
    anchor_lbl = "End" if forecast_from_end else "last observation"

as_of_note = None
if anchor_ts < earliest_as_of:
    as_of = earliest_as_of.isoformat()
    as_of_note = f"Anchor needs ≥24h prior history. Forecasting from {earliest_as_of}."
elif anchor_ts > max_ts:
    as_of = max_ts.isoformat()
    as_of_note = f"Anchor after history. Forecasting from last observation {max_ts}."
else:
    as_of = anchor_ts.isoformat()
if as_of_note:
    st.info(as_of_note)

with st.spinner("Computing demand forecast ahead…"):
    ahead, ahead_error = api_client.get_forecast_ahead(
        hours, as_of=as_of, start=start_ts.isoformat(), end=end_ts.isoformat()
    )
if ahead_error:
    st.markdown(
        f'<div class="aura-warn">{ahead_error} — try Next 24 hours, or Refresh after the backend wakes up.</div>',
        unsafe_allow_html=True,
    )
elif ahead:
    ahead_df = pd.DataFrame(ahead.get("items", []))
    if not ahead_df.empty:
        ahead_df["ts"] = pd.to_datetime(ahead_df["ts"])
        st.markdown(
            f'<div class="aura-sec-sub">'
            f'Filters: {start_ts.isoformat()} → {end_ts.isoformat()} · '
            f'Forecast from ({anchor_lbl}): {ahead["generated_from"]} · Horizon: {hours}h · '
            f'Weather: {ahead["weather_source"]} · '
            f'Exam intervals: {int(ahead.get("exam_intervals", ahead_df["is_exam"].sum()))}, '
            f'Vacation: {int(ahead.get("vacation_intervals", ahead_df["is_vacation"].sum()))}'
            f'</div>',
            unsafe_allow_html=True,
        )
        render_ahead_chart(ahead_df)
        high = ahead_df[ahead_df["risk_level"] == "HIGH"]
        if high.empty:
            st.markdown('<div class="aura-ok">No HIGH peaks in this ahead horizon (table below is Start→End history, not this chart).</div>', unsafe_allow_html=True)
        else:
            st.markdown(
                f'<div class="aura-warn">{len(high)} HIGH peak intervals expected — peak '
                f'{high["total_kw"].max():.1f} kW at {high.loc[high["total_kw"].idxmax(), "ts"]}.</div>',
                unsafe_allow_html=True,
            )
st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="aura-sec-title">Green Skills: carbon and cost impact</div>', unsafe_allow_html=True)
carbon, carbon_error = api_client.get_carbon(
    hours, as_of=as_of, start=start_ts.isoformat(), end=end_ts.isoformat()
)
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
st.markdown(
    f'<div class="aura-sec-sub">Start→End history · mix of HIGH/MEDIUM/LOW · HIGH ≥ max(350 kW, P90) · '
    f'{start_ts.isoformat()} → {end_ts.isoformat()}</div>',
    unsafe_allow_html=True,
)
if peaks_error:
    st.markdown(f'<div class="aura-warn">{peaks_error}</div>', unsafe_allow_html=True)
elif peaks:
    render_peaks_table(peaks.get("items", []))
    pcsv, perr = api_client.get_peaks_csv(
        limit=int(peaks_limit),
        start=start_ts.isoformat(),
        end=end_ts.isoformat(),
        zone=zone,
    )
    if pcsv and not perr:
        st.download_button(
            "Download peaks CSV",
            data=pcsv,
            file_name=f"peaks_{zone}.csv",
            mime="text/csv",
            key="dl_peaks",
        )
st.markdown("</div>", unsafe_allow_html=True)

footer_cols = st.columns(2)
footer_cols[0].caption("Decision-support tool, not a replacement for official BESCOM billing. · Simulated data.")
if metrics and not metrics_error:
    footer_cols[1].caption(
        f"Model: {metrics.get('active_model', 'n/a')} · "
        f"target={metrics.get('target', 'Total_Campus_Demand_kW')} · "
        f"{metrics.get('interval_minutes', 15)} min · max {metrics.get('max_horizon_hours', 168)} h · "
        f"source={metrics.get('data_source', 'simulated')}"
    )
