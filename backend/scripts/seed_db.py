import json
import sys
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

try:
    from app.db import Base, SessionLocal, engine
    from app.models import EnergyLog, Forecast, ModelPerformanceMetric, ModelRegistry
except ImportError:
    from db import Base, SessionLocal, engine
    from models import EnergyLog, Forecast, ModelPerformanceMetric, ModelRegistry

ML_ROOT = BASE_DIR.parent / "ML Implementation"
ML_OUTPUTS = ML_ROOT / "outputs"
ML_DATA = ML_ROOT / "data"
OUTPUTS_DIR = ML_OUTPUTS if (ML_OUTPUTS / "metrics.json").exists() else BASE_DIR / "outputs"
CSV_PATH = OUTPUTS_DIR / "dashboard_inference_feed.csv"
METRICS_PATH = OUTPUTS_DIR / "metrics.json"
MASTER_PATH = ML_DATA / "alliance_campus_energy_master.csv"
if not MASTER_PATH.exists():
    MASTER_PATH = BASE_DIR / "data" / "alliance_campus_energy_master.csv"


def main():
    Base.metadata.create_all(bind=engine)

    if "--mock" in sys.argv or "--generate-mock" in sys.argv:
        print("ERROR: mock seeding disabled. Provide real ML outputs under ML Implementation/outputs.")
        sys.exit(1)

    if not CSV_PATH.exists() or CSV_PATH.stat().st_size == 0:
        print(f"ERROR: Missing or empty inference feed: {CSV_PATH}")
        sys.exit(1)
    if not METRICS_PATH.exists() or METRICS_PATH.stat().st_size == 0:
        print(f"ERROR: Missing or empty metrics file: {METRICS_PATH}")
        sys.exit(1)

    try:
        df = pd.read_csv(CSV_PATH, index_col=0)
        metrics_data = json.loads(METRICS_PATH.read_text())
    except Exception as exc:
        print(f"ERROR reading ML outputs: {exc}")
        sys.exit(1)

    db = SessionLocal()
    try:
        db.query(Forecast).delete()
        db.query(EnergyLog).delete()
        db.query(ModelPerformanceMetric).delete()

        forecast_objs = []
        for idx_val, row in df.iterrows():
            ts_dt = pd.to_datetime(idx_val).to_pydatetime()
            actual_kw = float(row["Actual_Demand_kW"]) if pd.notnull(row.get("Actual_Demand_kW")) else None
            xgb_kw = float(row["XGB_Predicted_Demand_kW"]) if pd.notnull(row.get("XGB_Predicted_Demand_kW")) else None
            lgb_kw = float(row["LGB_Predicted_Demand_kW"]) if pd.notnull(row.get("LGB_Predicted_Demand_kW")) else None
            best_kw = float(row["Best_Predicted_Demand_kW"]) if pd.notnull(row.get("Best_Predicted_Demand_kW")) else 0.0
            abs_error = abs(best_kw - actual_kw) if actual_kw is not None else None
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

        if MASTER_PATH.exists():
            master = pd.read_csv(MASTER_PATH, index_col=0, parse_dates=True)
            energy_objs = [
                EnergyLog(
                    ts=ts.to_pydatetime(),
                    demand_kw=float(row["Total_Campus_Demand_kW"]),
                    academic_kw=float(row["Academic_Demand_kW"]) if "Academic_Demand_kW" in row else None,
                    hostel_kw=float(row["Hostel_Demand_kW"]) if "Hostel_Demand_kW" in row else None,
                    temperature_c=float(row["Temperature_C"]) if "Temperature_C" in row else None,
                    is_weekend=int(row["Is_Weekend"]) if "Is_Weekend" in row else None,
                    is_vacation=int(row["Is_Vacation"]) if "Is_Vacation" in row else None,
                    is_exam_cycle=int(row["Is_Exam_Cycle"]) if "Is_Exam_Cycle" in row else None,
                )
                for ts, row in master.iterrows()
            ]
            db.add_all(energy_objs)
            print(f"Seeded {len(energy_objs)} energy_logs rows")
        else:
            print(f"WARNING: master CSV missing at {MASTER_PATH}; skipped energy_logs")

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

        perf_rows = []
        if isinstance(all_metrics, dict) and all_metrics:
            for name, m in all_metrics.items():
                perf_rows.append(
                    ModelPerformanceMetric(
                        model_name=name,
                        version="v1.0",
                        rmse=m.get("rmse"),
                        mape=m.get("mape_percent"),
                        mae=m.get("mae"),
                        train_rows=train_rows,
                        test_rows=test_rows,
                        artifact_path="models/aura_ems_best.pkl" if name == winner else None,
                        is_active=(name == winner),
                    )
                )
        else:
            perf_rows.append(
                ModelPerformanceMetric(
                    model_name=winner,
                    version="v1.0",
                    rmse=rmse,
                    mape=mape,
                    mae=mae,
                    train_rows=train_rows,
                    test_rows=test_rows,
                    artifact_path="models/aura_ems_best.pkl",
                    is_active=True,
                )
            )
        db.add_all(perf_rows)
        db.commit()
        print(
            f"Seeded {len(forecast_objs)} forecasts | {len(perf_rows)} model_performance_metrics | "
            f"Active model: {active_model.model_name}"
        )
    except Exception as exc:
        db.rollback()
        print(f"ERROR during database seeding: {exc}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
