"""Compare the baseline and tree models, then export integration artifacts."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error

from ml.baseline import Persistence24HourBaseline
from ml.feature_engineering import FEATURE_COLUMNS
from ml.utils import PROJECT_ROOT, TARGET_COLUMN


def read_test_split(data_dir: Path) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    features = pd.read_csv(data_dir / "X_test.csv", index_col=0, parse_dates=True)
    target_frame = pd.read_csv(data_dir / "y_test.csv", index_col=0, parse_dates=True)
    if features.columns.tolist() != FEATURE_COLUMNS:
        raise ValueError("X_test.csv feature columns do not match the published feature contract.")
    if target_frame.shape[1] != 1:
        raise ValueError("y_test.csv must contain exactly one target column.")
    target = target_frame.iloc[:, 0].rename(TARGET_COLUMN)
    if not features.index.equals(target.index):
        raise ValueError("Test feature and target timestamps do not match.")
    if features.empty:
        raise ValueError("Test split is empty.")
    return features, target, features["Load_Lag_24hr"]


def calculate_metrics(actual: pd.Series, predicted: pd.Series) -> dict[str, Any]:
    actual_values = actual.to_numpy(dtype=float)
    predicted_values = np.asarray(predicted, dtype=float)
    nonzero_actual = actual_values != 0
    mape = (
        float(np.mean(np.abs((actual_values[nonzero_actual] - predicted_values[nonzero_actual]) / actual_values[nonzero_actual])) * 100)
        if nonzero_actual.any()
        else None
    )
    return {
        "rmse": math.sqrt(mean_squared_error(actual_values, predicted_values)),
        "mae": mean_absolute_error(actual_values, predicted_values),
        "mape_percent": mape,
        "mape_zero_actual_rows_excluded": int((~nonzero_actual).sum()),
    }


def evaluate_models(data_dir: Path, model_dir: Path, output_dir: Path, report_path: Path) -> None:
    x_test, y_test, baseline_predictions = read_test_split(data_dir)
    model_paths = {
        "XGBoost": model_dir / "aura_ems_xgboost_exp.pkl",
        "LightGBM": model_dir / "aura_ems_lightgbm_exp.pkl",
    }
    predictions: dict[str, np.ndarray | pd.Series] = {
        "Baseline": baseline_predictions,
    }
    model_objects: dict[str, Any] = {"Baseline": Persistence24HourBaseline()}
    for model_name, model_path in model_paths.items():
        if not model_path.is_file():
            raise FileNotFoundError(f"Missing trained model {model_path}; run ml.train first.")
        model = joblib.load(model_path)
        model_objects[model_name] = model
        predictions[model_name] = model.predict(x_test)

    metrics = {
        name: calculate_metrics(y_test, model_predictions)
        for name, model_predictions in predictions.items()
    }
    winner = min(metrics, key=lambda name: metrics[name]["rmse"])
    model_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(model_objects[winner], model_dir / "aura_ems_best.pkl")

    output_dir.mkdir(parents=True, exist_ok=True)
    inference_feed = pd.DataFrame(
        {
            "Actual_Demand_kW": y_test,
            "XGB_Predicted_Demand_kW": predictions["XGBoost"],
            "LGB_Predicted_Demand_kW": predictions["LightGBM"],
            "Best_Predicted_Demand_kW": predictions[winner],
        },
        index=y_test.index,
    )
    inference_feed.index.name = "Timestamp"
    inference_feed.to_csv(output_dir / "dashboard_inference_feed.csv")

    x_train = pd.read_csv(data_dir / "X_train.csv", index_col=0, parse_dates=True)
    metrics_payload = {
        "selection_metric": "lowest test RMSE",
        "winner": winner,
        "target_column": TARGET_COLUMN,
        "feature_columns": FEATURE_COLUMNS,
        "train_rows": len(x_train),
        "test_rows": len(y_test),
        "data_start": str(x_train.index.min()),
        "data_end": str(x_test.index.max()),
        "metrics": metrics,
    }
    with (output_dir / "metrics.json").open("w", encoding="utf-8") as metrics_file:
        json.dump(metrics_payload, metrics_file, indent=2, allow_nan=False)

    report_path.parent.mkdir(parents=True, exist_ok=True)
    _save_actual_vs_predicted(y_test, predictions[winner], predictions["Baseline"], report_path.parent)
    _save_feature_importance(model_objects, winner, metrics, report_path.parent)
    _write_report(report_path, x_test, y_test, metrics_payload)
    print(f"Winner by test RMSE: {winner} ({metrics[winner]['rmse']:.3f} kW)")
    print(f"Saved metrics, inference feed, plots, and report; best model: {model_dir / 'aura_ems_best.pkl'}")


def _save_actual_vs_predicted(
    actual: pd.Series, best: np.ndarray | pd.Series, baseline: np.ndarray | pd.Series, output_dir: Path
) -> None:
    figure, axis = plt.subplots(figsize=(12, 5))
    axis.plot(actual.index, actual, label="Actual", linewidth=1.2)
    axis.plot(actual.index, best, label="Best model", linewidth=1.1)
    axis.plot(actual.index, baseline, label="24-hour baseline", linewidth=0.9, alpha=0.8)
    axis.set(title="AURA-EMS: actual vs predicted campus demand", ylabel="Demand (kW)")
    axis.legend()
    axis.grid(alpha=0.2)
    figure.tight_layout()
    figure.savefig(output_dir / "actual_vs_predicted.png", dpi=160)
    plt.close(figure)


def _save_feature_importance(
    models: dict[str, Any], winner: str, metrics: dict[str, Any], output_dir: Path
) -> None:
    tree_winner = winner
    if winner == "Baseline":
        tree_winner = min(("XGBoost", "LightGBM"), key=lambda name: metrics[name]["rmse"])
    importance = getattr(models[tree_winner], "feature_importances_", None)
    if importance is None:
        return
    order = np.argsort(importance)
    figure, axis = plt.subplots(figsize=(9, 6))
    axis.barh(np.array(FEATURE_COLUMNS)[order], np.asarray(importance)[order])
    axis.set(title=f"{tree_winner} feature importance", xlabel="Importance")
    figure.tight_layout()
    figure.savefig(output_dir / "feature_importance.png", dpi=160)
    plt.close(figure)


def _write_report(report_path: Path, x_test: pd.DataFrame, y_test: pd.Series, payload: dict[str, Any]) -> None:
    train_rows = payload["train_rows"]
    winner = payload["winner"]
    result_lines = []
    for name, scores in payload["metrics"].items():
        mape_display = (
            "N/A"
            if scores["mape_percent"] is None
            else f"{scores['mape_percent']:.2f}%"
        )
        result_lines.append(
            f"| {name} | {scores['rmse']:.3f} | {scores['mae']:.3f} | {mape_display} |"
        )
    result_rows = "\n".join(result_lines)
    report = f"""# AURA-EMS ML Evaluation

## Dataset
- Rows after feature-related dropna: {train_rows + len(y_test):,}
- Usable date range: {payload['data_start']} to {payload['data_end']}
- Evaluation date range: {y_test.index.min()} to {y_test.index.max()}
- Frequency: 15 minutes (validated before feature generation)
- Target: `{TARGET_COLUMN}`

## Split
- Method: chronological 80/20 (past for training, future for testing)
- Train size: {train_rows:,}
- Test size: {len(y_test):,}

## Features
{chr(10).join(f'- `{column}`' for column in FEATURE_COLUMNS)}

Lag features use past values only. Four-hour rolling statistics use `shift(1)` before a 16-row rolling window; no current or future target enters the features. No random shuffle is used.

## Results
| Model | RMSE (kW) | MAE (kW) | MAPE |
|---|---:|---:|---:|
{result_rows}

MAPE is computed over nonzero actual-demand rows; zero actual values are excluded because percentage error is undefined there. RMSE penalizes larger misses more heavily; MAE is the average absolute miss in kW.

## Winner
- Model: {winner}
- Rule: lowest RMSE on the held-out future test set.
- Production artifact: `models/aura_ems_best.pkl`

## Limitations
- This is a campus-total forecast, not zone-level forecasting.
- Temperature is assumed available at forecast time; future weather forecast error is not modeled.
- The benchmark and test period cover only the supplied dataset and may not represent future operating conditions.
"""
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=PROJECT_ROOT / "outputs")
    parser.add_argument("--model-dir", type=Path, default=PROJECT_ROOT / "models")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "outputs")
    parser.add_argument("--report", type=Path, default=PROJECT_ROOT / "reports" / "ml_evaluation.md")
    args = parser.parse_args()
    evaluate_models(args.data_dir, args.model_dir, args.output_dir, args.report)


if __name__ == "__main__":
    main()