# AURA-EMS Implementation Guide

## 1. Problem and approach (summary)

Alliance University tracks energy reactively from past bills and gets hit by BESCOM peak-tariff penalties. AURA-EMS forecasts short-term campus demand by fusing smart-meter data with calendar context (weekday, vacation, exams) and weather (temperature), then warns facilities staff about upcoming peaks.

Architecture (three independent modules connected by files and a REST API):

```
ML Implementation  --(aura_ems_best.pkl, metrics.json, dashboard_inference_feed.csv, X_test.csv)-->
Backend (FastAPI + SQLite)  --(REST JSON on :8000)-->
Frontend (Streamlit on :8501)
```

The frontend only talks to the backend API. The backend reads ML outputs directly from `ML Implementation/` (falling back to its own `outputs/` and `models/` copies).

## 2. Review findings

### Errors found and fixed

| # | Problem | Fix |
|---|---|---|
| 1 | Frontend called port 8001; backend runs on 8000 | `frontend/services/config.py` now uses 8000 |
| 2 | SQLite path `./aura_ems.db` depended on the folder you started from, so a different empty DB could be created | `backend/app/db.py` uses an absolute path to `backend/aura_ems.db` |
| 3 | Backend seeded from a stale copy of ML outputs in `backend/outputs` | `backend/scripts/seed_db.py` reads `ML Implementation/outputs` first |
| 4 | `plotly` (frontend) and `xgboost`/`lightgbm` (backend) were listed in requirements but not installed, so the dashboard crashed on load | Installed from the requirements files |
| 5 | The trained model was never used by the backend, and there was no future forecast; the dashboard only showed predictions on past test data. The problem statement's core value is "view impending load spikes 24 hours in advance" | Added `GET /forecasts/ahead` (24h / 7-day, total + academic + hostel, live weather + academic calendar) and a matching dashboard section |

### Areas of improvement (not yet done)

- **Peaks ignore the date filter.** `/forecasts/peaks` ranks the whole dataset, not the range selected in the sidebar.
- **Hardcoded dashboard dates.** `frontend/app.py` hardcodes 2025-09-02 to 2026-09-01; it should read the range from the API.
- **Duplicate routes.** `/peaks`, `/summary` and `""` are extra aliases that clutter `/docs`; `main.py` has a workaround that strips empty paths.
- **Deprecated APIs.** `@app.on_event("startup")` (FastAPI) and `use_container_width` (Streamlit) are deprecated.
- **Unpinned versions.** Backend and frontend requirements have no version pins; the pickled XGBoost model can warn or break if the backend's XGBoost version differs from the one used in training.
- **Mock data risk.** `seed_db.py` silently generates synthetic data if ML files are empty; it should fail loudly instead.
- **Optional `POST /predict`** from the API contract is not implemented.

## 3. What was built and how

### Zone models (`ML Implementation/ml/train_zones.py`)

Trains one XGBoost model each for `Academic_Demand_kW` and `Hostel_Demand_kW`, using the same 12 features and chronological 80/20 split as the main model. Saves `models/aura_ems_academic.pkl`, `models/aura_ems_hostel.pkl` and `outputs/zone_metrics.json`. Test results: academic blocks RMSE 9.65 kW, hostels RMSE 7.43 kW.

### Academic calendar (`ML Implementation/data/academic_calendar.csv`)

`start_date,end_date,event` rows (`exam` or `vacation`). Historical rows come from the dataset; the 2026-27 rows follow the same pattern (exams on November and May weekdays, vacations in December and June). **Replace these with the official university calendar when it's available.**

### Forecast endpoint: `GET /forecasts/ahead?hours=24|168` (`backend/app/services/forecaster.py`)

Recursive forecasting for total, academic and hostel demand:

1. Start from the latest 96 observed values (24h at 15-min intervals) in the master dataset.
2. For each future 15-min step, build the 12 model features: time features from the timestamp, **real temperature from the Open-Meteo API** for the campus (12.7286 N, 77.7027 E; free, no API key), **vacation and exam flags from the academic calendar**, and lag and rolling features from the history.
3. Predict, append the prediction to the history so later steps use it as a lag, and label total-demand risk as HIGH (≥ 90th percentile of historical demand), MEDIUM (≥ 75th) or LOW.

If Open-Meteo is unreachable, temperature falls back to the same time the previous day, and `weather_source` in the response says so. Results are cached per horizon. The first 7-day request takes about 10 seconds, so the frontend timeout is 30 seconds.

Response:
```json
{"generated_from": "2026-09-01T00:00:00", "hours": 24, "weather_source": "Open-Meteo", "count": 96,
 "items": [{"ts": "2026-09-01T00:15:00", "total_kw": 66.39, "academic_kw": 25.23, "hostel_kw": 40.05,
            "temperature_c": 20.9, "is_vacation": 0, "is_exam": 0, "risk_level": "LOW"}]}
```

### Dashboard section (`frontend/app.py`, `frontend/services/api_client.py`)

"Demand Forecast Ahead" has a 24-hour / 7-day switch. It charts total campus, academic block and hostel demand, shows the weather source and the number of exam and vacation intervals, and warns about HIGH-risk peaks.

## 4. How to run

Install once:
```
pip install -r "ML Implementation/requirements-ml.txt" -r backend/requirements-backend.txt -r frontend/requirements-frontend.txt
```

1. (Only after retraining) in `ML Implementation`: `python -m ml.feature_engineering`, `python -m ml.train`, `python -m ml.evaluate`, `python -m ml.train_zones`
2. In `backend`: `python scripts/seed_db.py`
3. In `backend`: `python -m uvicorn app.main:app --port 8000` (API docs at http://127.0.0.1:8000/docs)
4. In `frontend`: `python -m streamlit run app.py` (dashboard at http://localhost:8501)

## 5. Verification done

- All five API endpoints return data with no errors: `/health`, `/metrics/summary`, `/forecasts`, `/forecasts/peaks`, `/forecasts/ahead` (24h and 168h, both using live Open-Meteo weather).
- Dashboard tested on both horizons with no errors: 24h shows 8 HIGH-risk intervals (peak 375.4 kW); 7 days shows 40 (peak 386.3 kW).
- The database was seeded from ML outputs: 6,989 rows; active model XGBoost (RMSE 13.52 kW, MAE 9.09 kW, MAPE 9.59%, against a baseline RMSE of 79.44 kW).
- The dashboard runs headless with Streamlit's test runner with no exceptions, and renders all sections. The 24h forecast shows 15 HIGH-risk intervals peaking at 357.3 kW at 08:15.
