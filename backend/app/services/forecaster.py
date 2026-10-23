"""Recursive multi-step demand forecasting for the whole campus and per zone."""

import json
import urllib.request
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

BACKEND_DIR = Path(__file__).resolve().parents[2]
ML_DIR = BACKEND_DIR.parent / "ML Implementation"
CAMPUS_LAT, CAMPUS_LON = 12.7286, 77.7027  # Alliance University, Anekal, Bengaluru
ZONES = {
    "total": ("Total_Campus_Demand_kW", "aura_ems_best.pkl"),
    "academic": ("Academic_Demand_kW", "aura_ems_academic.pkl"),
    "hostel": ("Hostel_Demand_kW", "aura_ems_hostel.pkl"),
}


def _ml_path(sub: str, name: str) -> Path:
    preferred = ML_DIR / sub / name
    return preferred if preferred.exists() else BACKEND_DIR / sub / name


@lru_cache(maxsize=1)
def _assets():
    models = {zone: joblib.load(_ml_path("models", file)) for zone, (_, file) in ZONES.items()}
    feature_columns = json.loads(_ml_path("outputs", "metrics.json").read_text())["feature_columns"]
    history = pd.read_csv(_ml_path("data", "alliance_campus_energy_master.csv"), index_col=0, parse_dates=True)
    calendar = pd.read_csv(_ml_path("data", "academic_calendar.csv"), parse_dates=["start_date", "end_date"])
    return models, feature_columns, history, calendar


def _fetch_temperature(start: pd.Timestamp, end: pd.Timestamp):
    """Fast weather fetch; fail quickly so Render does not hit frontend timeouts."""
    params = (
        f"latitude={CAMPUS_LAT}&longitude={CAMPUS_LON}&hourly=temperature_2m&timezone=Asia%2FKolkata"
        f"&start_date={start:%Y-%m-%d}&end_date={end:%Y-%m-%d}"
    )
    for host in ("api.open-meteo.com/v1/forecast", "archive-api.open-meteo.com/v1/archive"):
        try:
            with urllib.request.urlopen(f"https://{host}?{params}", timeout=3) as resp:
                hourly = json.load(resp)["hourly"]
            series = pd.Series(hourly["temperature_2m"], index=pd.to_datetime(hourly["time"]), dtype=float).dropna()
            if len(series):
                return series.resample("15min").interpolate(), "Open-Meteo"
        except Exception:
            continue
    return None, "previous-day fallback (weather API unreachable)"


def _calendar_flags(calendar: pd.DataFrame, ts: pd.Timestamp) -> tuple[int, int]:
    day = ts.normalize()
    events = calendar.loc[(calendar.start_date <= day) & (calendar.end_date >= day), "event"]
    return int((events == "vacation").any()), int((events == "exam").any())


def count_calendar_intervals(start, end) -> tuple[int, int]:
    """15-min exam/vacation counts inside the queried Start→End window."""
    _, _, _, calendar = _assets()
    start, end = pd.Timestamp(start), pd.Timestamp(end)
    if end < start:
        start, end = end, start
    rng = pd.date_range(start, end, freq="15min")
    if rng.empty:
        return 0, 0
    days = rng.normalize()
    exam = vac = 0
    for _, row in calendar.iterrows():
        s, e = pd.Timestamp(row.start_date).normalize(), pd.Timestamp(row.end_date).normalize()
        n = int(((days >= s) & (days <= e)).sum())
        if not n:
            continue
        ev = str(row.event).lower()
        if ev == "exam":
            exam += n
        elif ev == "vacation":
            vac += n
    return exam, vac


def predict_one(features: dict, zone: str = "total") -> float:
    models, feature_columns, _, _ = _assets()
    if zone not in models:
        raise KeyError(f"Unknown zone: {zone}")
    missing = [c for c in feature_columns if c not in features]
    if missing:
        raise ValueError(f"Missing features: {missing}")
    x = np.array([[float(features[c]) for c in feature_columns]], dtype=float)
    return max(0.0, float(models[zone].predict(x)[0]))


@lru_cache(maxsize=64)
def forecast_ahead(hours: int, as_of: str = "") -> dict:
    models, feature_columns, history, calendar = _assets()
    hist = history
    if as_of:
        hist = history.loc[: pd.Timestamp(as_of)]
        if len(hist) < 96:
            raise ValueError("as_of needs at least 24h of prior history (96 intervals)")
    last_ts = hist.index[-1]
    n_steps = hours * 4
    future = pd.date_range(last_ts + pd.Timedelta(minutes=15), periods=n_steps, freq="15min")
    live_temps, weather_source = _fetch_temperature(future[0], future[-1])

    # Calendar flags once per calendar day (not every 15-min step)
    day_flags = {}
    for day in pd.unique(future.normalize()):
        day_flags[day] = _calendar_flags(calendar, pd.Timestamp(day))

    hist_temp = hist["Temperature_C"]
    last_temp = float(hist_temp.iloc[-1])
    temps = hist_temp.to_dict()
    context = []
    for ts in future:
        fallback = float(temps.get(ts - pd.Timedelta(hours=24), last_temp))
        if live_temps is not None:
            try:
                temp = float(live_temps.loc[ts])
            except KeyError:
                temp = fallback
        else:
            temp = fallback
        temps[ts] = temp
        vacation, exam = day_flags[ts.normalize()]
        context.append({
            "Hour": ts.hour,
            "DayOfWeek": ts.dayofweek,
            "Month": ts.month,
            "Temperature_C": temp,
            "Is_Weekend": int(ts.dayofweek >= 5),
            "Is_Vacation": vacation,
            "Is_Exam_Cycle": exam,
        })

    col_i = {c: i for i, c in enumerate(feature_columns)}
    n_feat = len(feature_columns)
    preds = {}
    for zone, (column, _) in ZONES.items():
        demand = hist[column].iloc[-96:].astype(float).tolist()
        model = models[zone]
        out = []
        x = np.empty((1, n_feat), dtype=float)
        for base in context:
            recent = np.asarray(demand[-16:], dtype=float)
            row = {
                **base,
                "Load_Lag_1hr": demand[-4],
                "Load_Lag_2hr": demand[-8],
                "Load_Lag_24hr": demand[-96],
                "Load_Rolling_Mean_4hr": float(recent.mean()),
                "Load_Rolling_Std_4hr": float(recent.std(ddof=1)),
            }
            for c, i in col_i.items():
                x[0, i] = row[c]
            pred = max(0.0, float(model.predict(x)[0]))
            demand.append(pred)
            out.append(pred)
        preds[zone] = out

    p90, p75 = hist["Total_Campus_Demand_kW"].quantile([0.9, 0.75])
    items = []
    for i, ts in enumerate(future):
        total = preds["total"][i]
        items.append({
            "ts": ts.isoformat(),
            "total_kw": round(total, 2),
            "academic_kw": round(preds["academic"][i], 2),
            "hostel_kw": round(preds["hostel"][i], 2),
            "temperature_c": round(context[i]["Temperature_C"], 1),
            "is_vacation": context[i]["Is_Vacation"],
            "is_exam": context[i]["Is_Exam_Cycle"],
            "risk_level": "HIGH" if total >= p90 else "MEDIUM" if total >= p75 else "LOW",
        })
    return {
        "generated_from": last_ts.isoformat(),
        "hours": hours,
        "weather_source": weather_source,
        "count": len(items),
        "items": items,
    }
