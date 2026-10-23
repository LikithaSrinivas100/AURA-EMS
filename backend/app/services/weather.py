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


def fetch_hourly_temps(start: pd.Timestamp, end: pd.Timestamp):
    params = (
        f"latitude={LAT}&longitude={LON}&hourly=temperature_2m&timezone=Asia%2FKolkata"
        f"&start_date={start:%Y-%m-%d}&end_date={end:%Y-%m-%d}&forecast_days=2"
    )
    for host in ("api.open-meteo.com/v1/forecast", "archive-api.open-meteo.com/v1/archive"):
        try:
            with urllib.request.urlopen(f"https://{host}?{params}", timeout=6) as resp:
                hourly = json.load(resp)["hourly"]
            series = pd.Series(hourly["temperature_2m"], index=pd.to_datetime(hourly["time"]), dtype=float).dropna()
            if len(series):
                return series.resample("15min").interpolate(), "Open-Meteo"
        except Exception:
            continue
    return None, "fallback"


def today_peak() -> dict:
    models, feature_columns, history, calendar = _assets()
    now = pd.Timestamp.now(tz="Asia/Kolkata").tz_localize(None).floor("15min")
    future = pd.date_range(now, periods=96, freq="15min")
    live, _ = fetch_hourly_temps(future[0], future[-1])
    last_temp = float(history["Temperature_C"].iloc[-1])
    day_flags = {d: _calendar_flags(calendar, pd.Timestamp(d)) for d in pd.unique(future.normalize())}

    context = []
    for ts in future:
        if live is not None:
            try:
                temp = float(live.loc[ts])
            except KeyError:
                temp = last_temp
        else:
            temp = last_temp
        vac, exam = day_flags[ts.normalize()]
        context.append({
            "Hour": ts.hour, "DayOfWeek": ts.dayofweek, "Month": ts.month,
            "Temperature_C": temp, "Is_Weekend": int(ts.dayofweek >= 5),
            "Is_Vacation": vac, "Is_Exam_Cycle": exam,
        })

    col_i = {c: i for i, c in enumerate(feature_columns)}
    demand = history[ZONES["total"][0]].iloc[-96:].astype(float).tolist()
    model = models["total"]
    x = np.empty((1, len(feature_columns)), dtype=float)
    preds = []
    for base in context:
        recent = np.asarray(demand[-16:], dtype=float)
        row = {
            **base,
            "Load_Lag_1hr": demand[-4], "Load_Lag_2hr": demand[-8], "Load_Lag_24hr": demand[-96],
            "Load_Rolling_Mean_4hr": float(recent.mean()), "Load_Rolling_Std_4hr": float(recent.std(ddof=1)),
        }
        for c, i in col_i.items():
            x[0, i] = row[c]
        pred = max(0.0, float(model.predict(x)[0]))
        demand.append(pred)
        preds.append(pred)

    p90, p75 = float(np.percentile(preds, 90)), float(np.percentile(preds, 75))
    peak_i = int(np.argmax(preds))
    peak = float(preds[peak_i])
    shaved = [min(v, p75) if v >= p90 else v for v in preds]
    co2 = max(0.0, (sum(preds) - sum(shaved)) * 0.25 * EF)
    live_now = context[0]["Temperature_C"]
    return {
        "live_temp_c": round(live_now, 1),
        "expected_peak_kw": round(peak, 1),
        "target_peak_time": future[peak_i].strftime("%Y-%m-%d %H:%M:%S"),
        "risk_status": "HIGH" if peak >= p90 else "MEDIUM" if peak >= p75 else "LOW",
        "carbon_avoided_kg": round(co2, 2),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }
