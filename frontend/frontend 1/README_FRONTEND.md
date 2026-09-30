# AURA-EMS — Frontend Dashboard

Streamlit dashboard for campus energy demand forecasting.

## What this is

A read-only dashboard that answers, at a glance: **"Are we about to hit a
high-demand window?"** It consumes Anushka's FastAPI backend only — it
never loads `.pkl` model files directly.

## Folder structure

```
frontend/
  app.py                       # entry point — run this with streamlit
  components/
    metrics_cards.py           # Section B: KPI cards
    forecast_chart.py          # Section C: actual vs predicted chart
    peaks_table.py             # Section D: peak risk panel
  services/
    api_client.py              # GET wrappers for the 4 backend endpoints
    config.py                  # API_BASE_URL, timeout, risk colors
  requirements-frontend.txt
  README_FRONTEND.md
```

## Setup

```bash
cd frontend
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements-frontend.txt
```

## Run

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501` by default.

## Backend API

This dashboard calls Anushka's live FastAPI backend directly — there is no
mock-data mode. Base URL is set in `services/config.py`:

```python
API_BASE_URL = "http://127.0.0.1:8001"
```

Before running the app:

1. Confirm Anushka's FastAPI backend is running on port `8001`
   (`GET http://127.0.0.1:8001/health` should return `{"status": "ok", ...}`).
2. Start this Streamlit app.
3. Confirm the health indicator at the top turns green.

| Endpoint | Used for |
|---|---|
| `GET /health` | health indicator |
| `GET /metrics/summary` | KPI cards (active model, RMSE, MAPE, MAE) |
| `GET /forecasts?start=&end=` | actual vs predicted chart |
| `GET /forecasts/peaks?limit=` | peak risk table |

If Anushka changes any field names, the fix is a one-line change in the
matching `components/*.py` file — don't guess at renamed fields, confirm
with her first.

## Error handling

Every API call in `services/api_client.py` returns `(data, error)`. If
`error` is set (backend down, timeout, bad response), the dashboard shows:

> Backend unavailable. Please start FastAPI on port 8001.

instead of crashing.

## 90-second demo script

1. "Alliance campus energy demand is dynamic; reactive billing is not enough."
2. "Our system fuses meter data with calendar and weather context."
3. "The ML model predicts short-term demand; these cards show accuracy on
   future test data." *(point at KPI cards)*
4. "This chart compares actual vs predicted demand." *(point at chart)*
5. "This panel flags upcoming peak-risk windows for facilities action."
   *(point at peaks table)*
6. "Backend API + DB make this production-shaped, not just a notebook."

## Definition of done (frontend)

- [x] `streamlit run app.py` works
- [x] Final path uses backend API (not local ML pickle)
- [x] KPI metrics visible
- [x] Actual vs Predicted chart visible
- [x] Peak risk panel visible
- [x] Clear error state if API is down
- [x] Filters work (date range, peaks limit)
- [x] Connected to live backend on port 8001 (mock mode removed)
- [x] README has run steps
- [ ] 90-second demo script rehearsed out loud
- [ ] PR opened from `frontend-dashboard` → `main`
