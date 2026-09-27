import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
import pandas as pd

# Ensure backend root is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

try:
    from app.db import Base, SessionLocal, engine
    from app.models import Forecast, ModelRegistry
except ImportError:
    from db import Base, SessionLocal, engine
    from models import Forecast, ModelRegistry

OUTPUTS_DIR = BASE_DIR / "outputs"
CSV_PATH = OUTPUTS_DIR / "dashboard_inference_feed.csv"
METRICS_PATH = OUTPUTS_DIR / "metrics.json"


def generate_mock_files():
    """Generates synthetic 96 rows of 15-minute interval forecast data and metrics.json."""
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 96 rows = 24 hours at 15-min intervals
    base_ts = pd.Timestamp.now().floor("D") - pd.Timedelta(days=1)
    timestamps = [base_ts + pd.Timedelta(minutes=15 * i) for i in range(96)]
    
    records = []
    np.random.seed(42)
    for i, ts in enumerate(timestamps):
        hour = ts.hour + ts.minute / 60.0
        # Diurnal energy curve: lower demand at night, peak during afternoon
        base_demand = 220.0 + 130.0 * np.sin(np.pi * (hour - 6) / 12) if 6 <= hour <= 20 else 180.0 + np.random.uniform(5, 25)
        noise = np.random.normal(0, 5)
        actual = round(max(120.0, float(base_demand + noise)), 2)
        xgb_pred = round(float(actual + np.random.normal(0, 4)), 2)
        lgb_pred = round(float(actual + np.random.normal(0, 3)), 2)
        best_pred = round(float(0.4 * xgb_pred + 0.6 * lgb_pred), 2)
        
        records.append({
            "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
            "Actual_Demand_kW": actual,
            "XGB_Predicted_Demand_kW": xgb_pred,
            "LGB_Predicted_Demand_kW": lgb_pred,
            "Best_Predicted_Demand_kW": best_pred,
        })
    
    df = pd.DataFrame(records)
    df.set_index("timestamp", inplace=True)
    df.to_csv(CSV_PATH)
    
    metrics = {
        "model_name": "LightGBM_Ensemble",
        "version": "v1.0.0",
        "rmse": 11.85,
        "mape": 3.42,
        "mae": 8.76,
        "artifact_path": "models/lightgbm_demand_v1.pkl"
    }
    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)


def main():
    force_mock = "--mock" in sys.argv or "--generate-mock" in sys.argv

    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    # If mock generation is explicitly requested
    if force_mock:
        generate_mock_files()

    # Check if files exist
    if not CSV_PATH.exists():
        print("ERROR: Missing required file: outputs/dashboard_inference_feed.csv")
        sys.exit(1)

    if not METRICS_PATH.exists():
        print("ERROR: Missing required file: outputs/metrics.json")
        sys.exit(1)

    # If files exist but are empty placeholders, generate synthetic mock data
    if CSV_PATH.stat().st_size == 0 or METRICS_PATH.stat().st_size == 0:
        generate_mock_files()

    # Read inference feed CSV
    try:
        df = pd.read_csv(CSV_PATH, index_col=0)
    except Exception as e:
        print(f"ERROR reading {CSV_PATH}: {e}")
        sys.exit(1)

    # Read metrics JSON
    try:
        with open(METRICS_PATH, "r") as f:
            metrics_data = json.load(f)
    except Exception as e:
        print(f"ERROR reading {METRICS_PATH}: {e}")
        sys.exit(1)

    db = SessionLocal()
    try:
        # Clear existing forecasts for fresh seed
        db.query(Forecast).delete()

        forecast_objs = []
        for idx_val, row in df.iterrows():
            ts_dt = pd.to_datetime(idx_val).to_pydatetime()
            actual_kw = float(row["Actual_Demand_kW"]) if pd.notnull(row.get("Actual_Demand_kW")) else None
            xgb_kw = float(row["XGB_Predicted_Demand_kW"]) if pd.notnull(row.get("XGB_Predicted_Demand_kW")) else None
            lgb_kw = float(row["LGB_Predicted_Demand_kW"]) if pd.notnull(row.get("LGB_Predicted_Demand_kW")) else None
            best_kw = float(row["Best_Predicted_Demand_kW"]) if pd.notnull(row.get("Best_Predicted_Demand_kW")) else 0.0

            abs_error = abs(best_kw - actual_kw) if (actual_kw is not None and best_kw is not None) else None

            forecast_objs.append(
                Forecast(
                    ts=ts_dt,
                    actual_demand_kw=actual_kw,
                    xgb_pred_kw=xgb_kw,
                    lgb_pred_kw=lgb_kw,
                    best_pred_kw=best_kw,
                    abs_error_kw=abs_error,
                )
            )

        db.add_all(forecast_objs)

        # Update model registry
        db.query(ModelRegistry).update({ModelRegistry.is_active: False})

        winner = metrics_data.get("winner", metrics_data.get("model_name", "UnknownModel"))
        all_metrics = metrics_data.get("metrics", {})
        winner_metrics = all_metrics.get(winner, {}) if isinstance(all_metrics, dict) else {}

        rmse = winner_metrics.get("rmse", metrics_data.get("rmse"))
        mae = winner_metrics.get("mae", metrics_data.get("mae"))
        mape = winner_metrics.get("mape_percent", metrics_data.get("mape"))
        train_rows = metrics_data.get("train_rows", 0)
        test_rows = metrics_data.get("test_rows", 0)

        active_model = ModelRegistry(
            model_name=winner,
            version="v1.0",
            rmse=rmse,
            mape=mape,
            mae=mae,
            artifact_path="models/aura_ems_best.pkl",
            train_rows=train_rows,
            test_rows=test_rows,
            is_active=True,
        )
        db.add(active_model)
        db.commit()

        print(f"Seeded {len(forecast_objs)} forecast rows | Model registry updated | Active model: {active_model.model_name}")

    except Exception as e:
        db.rollback()
        print(f"ERROR during database seeding: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
