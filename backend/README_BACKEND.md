# AURA-EMS Backend API

AURA-EMS is a campus electricity demand forecasting backend for Alliance University, Bangalore, predicting future power demand based on diurnal cycles, academic calendars, and temperature.

---

## 1. Setup and Run Instructions

### Step 1: Create a Virtual Environment
```bash
python -m venv venv
```

### Step 2: Activate the Virtual Environment
- **Windows (PowerShell)**:
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
- **Windows (Command Prompt)**:
  ```cmd
  .\venv\Scripts\activate.bat
  ```
- **macOS / Linux**:
  ```bash
  source venv/bin/activate
  ```

### Step 3: Install Backend Dependencies
```bash
pip install -r requirements-backend.txt
```

### Step 4: Run the Database Seed Script
```bash
python scripts/seed_db.py
```
*(If ML output files are empty or not yet generated, the script will automatically synthesize 96 intervals / 24 hours of 15-minute campus forecast data and populate the SQLite database).*

### Step 5: Start the FastAPI Server
```bash
uvicorn app.main:app --reload --port 8000
```
- API Base URL: `http://localhost:8000`
- Interactive Swagger API Docs: `http://localhost:8000/docs`

---

## 2. API Endpoints and Example curl Commands

### 1. Health Check
Checks if the backend API service is operational.
- **Endpoint**: `GET /health`
- **Example curl**:
  ```bash
  curl -X GET "http://localhost:8000/health"
  ```
- **Sample Response**:
  ```json
  {
    "status": "ok",
    "service": "aura-ems-backend"
  }
  ```

### 2. Model Metrics Summary
Retrieves accuracy metrics and metadata for the currently active ML model.
- **Endpoint**: `GET /metrics/summary`
- **Example curl**:
  ```bash
  curl -X GET "http://localhost:8000/metrics/summary"
  ```
- **Sample Response**:
  ```json
  {
    "active_model": "LightGBM_Ensemble",
    "rmse": 11.85,
    "mape": 3.42,
    "mae": 8.76,
    "train_rows": 0,
    "test_rows": 0
  }
  ```

### 3. Forecast Data
Retrieves demand forecasts and actual readings. If no `start` or `end` timestamp is provided, it defaults to the last 48 hours of available data.
- **Endpoint**: `GET /forecasts`
- **Example curls**:
  ```bash
  # Default (last 48 hours of data)
  curl -X GET "http://localhost:8000/forecasts"

  # Filtered by date range
  curl -X GET "http://localhost:8000/forecasts?start=2026-09-25T00:00:00&end=2026-09-25T23:45:00"
  ```
- **Sample Response**:
  ```json
  {
    "count": 96,
    "items": [
      {
        "ts": "2026-09-25T00:00:00",
        "actual_demand_kw": 188.54,
        "best_pred_kw": 187.92,
        "xgb_pred_kw": 186.45,
        "lgb_pred_kw": 188.90
      }
    ]
  }
  ```

### 4. Peak Demand Analysis
Calculates the 90th percentile (HIGH risk) and 75th percentile (MEDIUM risk) thresholds across all predictions and returns the top highest peak periods.
- **Endpoint**: `GET /forecasts/peaks`
- **Example curls**:
  ```bash
  # Default (top 10 peaks)
  curl -X GET "http://localhost:8000/forecasts/peaks"

  # Custom limit
  curl -X GET "http://localhost:8000/forecasts/peaks?limit=5"
  ```
- **Sample Response**:
  ```json
  {
    "items": [
      {
        "ts": "2026-09-25T12:45:00",
        "best_pred_kw": 359.24,
        "risk_level": "HIGH"
      },
      {
        "ts": "2026-09-25T11:45:00",
        "best_pred_kw": 356.52,
        "risk_level": "HIGH"
      }
    ]
  }
  ```

---

## 3. Swapping Mock Data with Real ML Outputs

When Likitha (ML Engineer) has completed model training and inference:

1. **Obtain the 2 output files**:
   - `dashboard_inference_feed.csv`: CSV containing timestamps as index with columns:
     - `Actual_Demand_kW`
     - `XGB_Predicted_Demand_kW`
     - `LGB_Predicted_Demand_kW`
     - `Best_Predicted_Demand_kW`
   - `metrics.json`: JSON file with keys:
     - `model_name`
     - `version`
     - `rmse`
     - `mape`
     - `mae`
     - `artifact_path`

2. **Place the files into the outputs directory**:
   - Save the CSV to: `backend/outputs/dashboard_inference_feed.csv`
   - Save the JSON to: `backend/outputs/metrics.json`

3. **Re-run the seed script**:
   ```bash
   python scripts/seed_db.py
   ```
   The script will read the new production files, refresh the `forecasts` table, compute absolute error metrics, and activate the model in `model_registry`.

---

## 4. Team Integration Notes

- **Likitha (ML Engineer) -> Anushka (Backend Engineer)**:
  - Supplies the model evaluation metrics file (`outputs/metrics.json`) and batch inference forecast feed (`outputs/dashboard_inference_feed.csv`).
  - Stores model serialization artifacts in `models/`.

- **Anushka (Backend Engineer) -> Risha (Frontend Engineer)**:
  - Exposes REST endpoints serving forecast time-series data, peak alerts, and model accuracy statistics.
  - Configures CORS middleware enabling seamless requests from Streamlit (`http://localhost:8501`).

- **Frontend Configuration**:
  - Risha's Base API URL: `http://localhost:8000`
  - Streamlit Dashboard Origin: `http://localhost:8501` or `http://127.0.0.1:8501`
