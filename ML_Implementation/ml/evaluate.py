"""Compare baselines and tree models; peak-alert + horizon errors; export artifacts."""

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
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from ml.baseline import Persistence24HourBaseline, SeasonalNaive7DayBaseline
from ml.feature_engineering import FEATURE_COLUMNS
from ml.utils import PROJECT_ROOT, TARGET_COLUMN

HIGH_RISK_KW = 350.0
HORIZON_HOURS = (1, 6, 24, 72, 168)


def read_test_split(data_dir: Path) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    features = pd.read_csv(data_dir / "X_test.csv", index_col=0, parse_dates=True)
    target_frame = pd.read_csv(data_dir / "y_test.csv", index_col=0, parse_dates=True)
    if features.columns.tolist() != FEATURE_COLUMNS:
        raise ValueError("X_test.csv feature columns do not match the published feature contract.")
    target = target_frame.iloc[:, 0].rename(TARGET_COLUMN)
    if not features.index.equals(target.index):
        raise ValueError("Test feature and target timestamps do not match.")
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
        "rmse": float(math.sqrt(mean_squared_error(actual_values, predicted_values))),
        "mae": float(mean_absolute_error(actual_values, predicted_values)),
        "mape_percent": mape,
        "r2": float(r2_score(actual_values, predicted_values)),
        "mape_zero_actual_rows_excluded": int((~nonzero_actual).sum()),
    }


def peak_alert_metrics(y_train: pd.Series, y_test: pd.Series, y_pred: np.ndarray | pd.Series) -> dict[str, Any]:
    train_p90 = float(y_train.quantile(0.90))
    threshold = max(HIGH_RISK_KW, train_p90)
    actual_peak = y_test.to_numpy(dtype=float) >= threshold
    pred_peak = np.asarray(y_pred, dtype=float) >= threshold
    tp = int((actual_peak & pred_peak).sum())
    fp = int((~actual_peak & pred_peak).sum())
    fn = int((actual_peak & ~pred_peak).sum())
    tn = int((~actual_peak & ~pred_peak).sum())
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    non_peak = int((~actual_peak).sum())
    false_alarm_rate = fp / non_peak if non_peak else 0.0
    return {
        "threshold_kw": threshold,
        "threshold_rule": "max(350, train_p90)",
        "train_p90_kw": train_p90,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "false_alarm_rate": false_alarm_rate,
    }


def recursive_horizon_errors(
    model: Any,
    x_test: pd.DataFrame,
    y_test: pd.Series,
    y_train: pd.Series,
    max_hours: int = 168,
) -> pd.DataFrame:
    """Recursive walk from train end over test start; exogenous from X_test."""
    n_steps = min(max_hours * 4, len(x_test), len(y_test))
    buf = y_train.iloc[-96:].astype(float).tolist()
    if len(buf) < 96:
        raise ValueError("Need ≥96 train intervals to seed recursive lags.")
    preds: list[float] = []
    actuals: list[float] = []
    for i in range(n_steps):
        base = x_test.iloc[i]
        recent = np.asarray(buf[-16:], dtype=float)
        feat = {c: float(base[c]) for c in FEATURE_COLUMNS[:7]}
        feat.update(
            {
                "Load_Lag_1hr": buf[-4],
                "Load_Lag_2hr": buf[-8],
                "Load_Lag_24hr": buf[-96],
                "Load_Rolling_Mean_4hr": float(recent.mean()),
                "Load_Rolling_Std_4hr": float(recent.std(ddof=1) or 0.0),
            }
        )
        x = pd.DataFrame([[feat[c] for c in FEATURE_COLUMNS]], columns=FEATURE_COLUMNS)
        pred = max(0.0, float(model.predict(x)[0]))
        buf.append(pred)
        preds.append(pred)
        actuals.append(float(y_test.iloc[i]))
    rows = []
    for h in HORIZON_HOURS:
        k = min(h * 4, len(preds))
        m = calculate_metrics(pd.Series(actuals[:k]), pd.Series(preds[:k]))
        rows.append(
            {
                "horizon_hours": h,
                "steps": k,
                "rmse": m["rmse"],
                "mape_percent": m["mape_percent"],
                "mae": m["mae"],
                "r2": m["r2"],
            }
        )
    return pd.DataFrame(rows)


def evaluate_models(data_dir: Path, model_dir: Path, output_dir: Path, report_path: Path) -> None:
    x_test, y_test, baseline_24 = read_test_split(data_dir)
    y_train = pd.read_csv(data_dir / "y_train.csv", index_col=0, parse_dates=True).iloc[:, 0]
    y_train.name = TARGET_COLUMN
    x_train = pd.read_csv(data_dir / "X_train.csv", index_col=0, parse_dates=True)

    full_y = pd.concat([y_train, y_test]).sort_index()
    seasonal = SeasonalNaive7DayBaseline().predict_from_series(full_y, y_test.index)

    model_paths = {
        "XGBoost": model_dir / "aura_ems_xgboost_exp.pkl",
        "LightGBM": model_dir / "aura_ems_lightgbm_exp.pkl",
    }
    predictions: dict[str, Any] = {
        "Baseline": baseline_24,
        "SeasonalNaive7Day": seasonal,
    }
    model_objects: dict[str, Any] = {"Baseline": Persistence24HourBaseline()}
    for name, path in model_paths.items():
        if not path.is_file():
            raise FileNotFoundError(f"Missing {path}")
        model_objects[name] = joblib.load(path)
        predictions[name] = model_objects[name].predict(x_test)

    metrics = {name: calculate_metrics(y_test, pred) for name, pred in predictions.items()}
    # Winner among forecasting models (exclude baselines for production pkl preference toward trees if tied)
    tree_metrics = {k: v for k, v in metrics.items() if k in ("XGBoost", "LightGBM")}
    winner = min(tree_metrics, key=lambda n: tree_metrics[n]["rmse"])
    joblib.dump(model_objects[winner], model_dir / "aura_ems_best.pkl")

    best_pred = np.asarray(predictions[winner], dtype=float)
    peak = peak_alert_metrics(y_train, y_test, best_pred)
    horizon_df = recursive_horizon_errors(model_objects[winner], x_test, y_test, y_train)
    output_dir.mkdir(parents=True, exist_ok=True)
    horizon_path = output_dir / "horizon_error.csv"
    horizon_df.to_csv(horizon_path, index=False)

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(horizon_df["horizon_hours"], horizon_df["rmse"], marker="o", label="RMSE kW")
    ax.set_xlabel("Horizon (hours)")
    ax.set_ylabel("RMSE (kW)")
    ax.set_title("Recursive forecast RMSE vs horizon (simulated data)")
    ax.grid(alpha=0.3)
    ax.legend()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(report_path.parent / "horizon_error.png", dpi=140)
    plt.close(fig)

    inference_feed = pd.DataFrame(
        {
            "Actual_Demand_kW": y_test,
            "XGB_Predicted_Demand_kW": predictions["XGBoost"],
            "LGB_Predicted_Demand_kW": predictions["LightGBM"],
            "Best_Predicted_Demand_kW": best_pred,
        },
        index=y_test.index,
    )
    inference_feed.index.name = "Timestamp"
    inference_feed.to_csv(output_dir / "dashboard_inference_feed.csv")

    metrics_payload = {
        "selection_metric": "lowest test RMSE among XGBoost/LightGBM",
        "winner": winner,
        "target_column": TARGET_COLUMN,
        "target": TARGET_COLUMN,
        "interval_minutes": 15,
        "max_horizon_hours": 168,
        "data_source": "simulated",
        "feature_columns": FEATURE_COLUMNS,
        "train_rows": len(x_train),
        "test_rows": len(y_test),
        "data_start": str(x_train.index.min()),
        "data_end": str(x_test.index.max()),
        "metrics": metrics,
        "peak_alert": peak,
        "horizon_error": horizon_df.to_dict(orient="records"),
    }
    with (output_dir / "metrics.json").open("w", encoding="utf-8") as f:
        json.dump(metrics_payload, f, indent=2, allow_nan=False)

    _save_actual_vs_predicted(y_test, best_pred, predictions["Baseline"], report_path.parent)
    _save_feature_importance(model_objects, winner, tree_metrics, report_path.parent)
    _write_report(report_path, x_test, y_test, metrics_payload)
    print(f"Winner: {winner} RMSE={metrics[winner]['rmse']:.3f}")
    print(f"Peak threshold={peak['threshold_kw']:.2f} F1={peak['f1']:.4f} FAR={peak['false_alarm_rate']:.4f}")
    print(f"Wrote {horizon_path}")


def _save_actual_vs_predicted(actual, best, baseline, output_dir: Path) -> None:
    figure, axis = plt.subplots(figsize=(12, 5))
    axis.plot(actual.index, actual, label="Actual", linewidth=1.2)
    axis.plot(actual.index, best, label="Best model", linewidth=1.1)
    axis.plot(actual.index, baseline, label="24-hour baseline", linewidth=0.9, alpha=0.8)
    axis.set(title="AURA-EMS: actual vs predicted (simulated data)", ylabel="Demand (kW)")
    axis.legend()
    axis.grid(alpha=0.2)
    figure.tight_layout()
    figure.savefig(output_dir / "actual_vs_predicted.png", dpi=160)
    plt.close(figure)


def _save_feature_importance(models, winner, metrics, output_dir: Path) -> None:
    importance = getattr(models[winner], "feature_importances_", None)
    if importance is None:
        return
    order = np.argsort(importance)
    figure, axis = plt.subplots(figsize=(9, 6))
    axis.barh(np.array(FEATURE_COLUMNS)[order], np.asarray(importance)[order])
    axis.set(title=f"{winner} feature importance", xlabel="Importance")
    figure.tight_layout()
    figure.savefig(output_dir / "feature_importance.png", dpi=160)
    plt.close(figure)


def _write_report(report_path: Path, x_test: pd.DataFrame, y_test: pd.Series, payload: dict[str, Any]) -> None:
    lines = [f"| {n} | {s['rmse']:.3f} | {s['mae']:.3f} | {s['mape_percent']:.2f}% | {s['r2']:.4f} |" for n, s in payload["metrics"].items()]
    peak = payload["peak_alert"]
    report = f"""# AURA-EMS ML Evaluation (simulated data)

Target: `{payload['target']}` · Interval: {payload['interval_minutes']} min · Max horizon: {payload['max_horizon_hours']} h

## Results
| Model | RMSE | MAE | MAPE | R2 |
|---|---:|---:|---:|---:|
{chr(10).join(lines)}

Winner (trees): **{payload['winner']}** by lowest test RMSE.

## Peak-alert (threshold from TRAIN only)
- Rule: {peak['threshold_rule']} → **{peak['threshold_kw']:.2f} kW** (train P90={peak['train_p90_kw']:.2f})
- Precision={peak['precision']:.4f} Recall={peak['recall']:.4f} F1={peak['f1']:.4f} FAR={peak['false_alarm_rate']:.4f}

## Horizon error
See `outputs/horizon_error.csv` and `reports/horizon_error.png`.
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
