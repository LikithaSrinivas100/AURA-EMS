"""Train per-zone XGBoost models (academic blocks, hostels) on the shared feature contract."""

from __future__ import annotations

import json

import joblib
import pandas as pd
from xgboost import XGBRegressor

from ml.evaluate import calculate_metrics
from ml.feature_engineering import create_chronological_split, engineer_features
from ml.utils import PROJECT_ROOT, TARGET_COLUMN, load_master_dataset

ZONES = {"academic": "Academic_Demand_kW", "hostel": "Hostel_Demand_kW"}


def main() -> None:
    frame = load_master_dataset()
    results = {}
    for zone, column in ZONES.items():
        features, target = engineer_features(frame.assign(**{TARGET_COLUMN: frame[column]}))
        x_train, x_test, y_train, y_test = create_chronological_split(features, target)
        model = XGBRegressor(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            objective="reg:squarederror",
            random_state=42,
            n_jobs=-1,
        )
        model.fit(x_train, y_train)
        results[zone] = calculate_metrics(y_test, pd.Series(model.predict(x_test), index=y_test.index))
        joblib.dump(model, PROJECT_ROOT / "models" / f"aura_ems_{zone}.pkl")
        print(f"{zone}: RMSE {results[zone]['rmse']:.3f} kW, MAPE {results[zone]['mape_percent']:.2f}%")
    (PROJECT_ROOT / "outputs" / "zone_metrics.json").write_text(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
