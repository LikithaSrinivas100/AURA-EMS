"""Live Open-Meteo weather + 24h today-peak inference."""
import json
import urllib.request
from datetime import datetime

import numpy as np
import pandas as pd

LAT, LON = 12.9716, 77.5946
EF = 0.71

try:
    from app.services.forecaster import ZONES, _assets, _calendar_flags
except ImportError:
    from services.forecaster import ZONES, _assets, _calendar_flags


def fetch_live_weather():
    """Current + 48h hourly temps from Open-Meteo (Bengaluru)."""
    url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}"
        f"&current=temperature_2m&hourly=temperature_2m&timezone=Asia%2FKolkata&forecast_days=2"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "AURA-EMS/1.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.load(resp)
    current = float(data["current"]["temperature_2m"])
    idx = pd.to_datetime(data["hourly"]["time"])
    if getattr(idx, "tz", None) is not None:
        idx = idx.tz_convert("Asia/Kolkata").tz_localize(None)
    hourly = pd.Series(data["hourly"]["temperature_2m"], index=idx, dtype=float).dropna()
    return current, hourly.resample("15min").interpolate()


def today_peak() -> dict:
    models, feature_columns, history, calendar = _assets()
    hist = history.copy()
    hist.index = pd.to_datetime(hist.index)
    now = pd.Timestamp.now(tz="Asia/Kolkata").tz_localize(None).floor("15min")
    future = pd.date_range(now, periods=96, freq="15min")
    last_temp = float(hist["Temperature_C"].iloc[-1])
    try:
        live_now, live = fetch_live_weather()
    except Exception:
        live_now, live = last_temp, None
    day_flags = {d: _calendar_flags(calendar, pd.Timestamp(d)) for d in pd.unique(future.normalize())}

    context = []
    for ts in future:
        if live is not None:
            val = live.asof(ts)
            temp = float(val) if pd.notna(val) else float(live_now)
        else:
            temp = float(live_now)
        vac, exam = day_flags[ts.normalize()]
        context.append({
            "Hour": ts.hour, "DayOfWeek": ts.dayofweek, "Month": ts.month,
            "Temperature_C": temp, "Is_Weekend": int(ts.dayofweek >= 5),
            "Is_Vacation": vac, "Is_Exam_Cycle": exam,
        })

    # Seed lags from last history day at the same clock hour (not CSV midnight).
    same_hour = hist.index[hist.index.hour == now.hour]
    anchor = same_hour[-1] if len(same_hour) else hist.index[-1]
    seed = hist.loc[:anchor].iloc[-96:]
    demand = seed[ZONES["total"][0]].astype(float).tolist()
    campus = hist[ZONES["total"][0]].astype(float)
    p90, p75 = float(campus.quantile(0.90)), float(campus.quantile(0.75))

    col_i = {c: i for i, c in enumerate(feature_columns)}
    model = models["total"]
    x = np.empty((1, len(feature_columns)), dtype=float)
    preds = []
    for base in context:
        recent = np.asarray(demand[-16:], dtype=float)
        row = {
            **base,
            "Load_Lag_1hr": demand[-4], "Load_Lag_2hr": demand[-8], "Load_Lag_24hr": demand[-96],
            "Load_Rolling_Mean_4hr": float(recent.mean()), "Load_Rolling_Std_4hr": float(recent.std(ddof=1) or 0.0),
        }
        for c, i in col_i.items():
            x[0, i] = row[c]
        pred = max(0.0, float(model.predict(x)[0]))
        demand.append(pred)
        preds.append(pred)

    peak_i = int(np.argmax(preds))
    peak = float(preds[peak_i])
    shaved = [min(v, p75) if v >= p90 else v for v in preds]
    co2 = max(0.0, (sum(preds) - sum(shaved)) * 0.25 * EF)
    risk = "HIGH" if peak >= 350 or peak >= p90 else "MEDIUM" if peak >= p75 else "LOW"
    peak_ts = future[peak_i]
    return {
        "live_temp_c": round(float(live_now), 1),
        "expected_peak_kw": round(peak, 1),
        "target_peak_time": peak_ts.strftime("%d %b, %H:%M"),
        "target_peak_iso": peak_ts.strftime("%Y-%m-%d %H:%M:%S"),
        "risk_status": risk,
        "carbon_avoided_kg": round(co2, 2),
        "generated_at": now.isoformat(timespec="seconds"),
    }
