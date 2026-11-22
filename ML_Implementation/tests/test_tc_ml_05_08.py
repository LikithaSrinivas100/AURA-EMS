"""TC_ML_05–08: baselines, peak-alert, horizon errors (read metrics artifacts)."""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
METRICS = ROOT / "outputs" / "metrics.json"
HORIZON = ROOT / "outputs" / "horizon_error.csv"


def _metrics():
    assert METRICS.is_file(), "Run python -m ml.evaluate first"
    return json.loads(METRICS.read_text(encoding="utf-8"))


def test_tc_ml_05_seasonal_naive_and_r2_present():
    m = _metrics()["metrics"]
    assert "Baseline" in m and "SeasonalNaive7Day" in m
    for name in ("Baseline", "SeasonalNaive7Day", "XGBoost", "LightGBM"):
        assert {"rmse", "mae", "mape_percent", "r2"} <= set(m[name])


def test_tc_ml_06_xgboost_beats_baselines_on_rmse():
    m = _metrics()["metrics"]
    xgb = m["XGBoost"]["rmse"]
    assert xgb < m["Baseline"]["rmse"]
    assert xgb < m["SeasonalNaive7Day"]["rmse"]


def test_tc_ml_07_peak_alert_train_threshold_and_rates():
    peak = _metrics()["peak_alert"]
    assert peak["threshold_rule"] == "max(350, train_p90)"
    assert peak["threshold_kw"] == max(350.0, peak["train_p90_kw"])
    for k in ("precision", "recall", "f1", "false_alarm_rate"):
        assert 0.0 <= peak[k] <= 1.0


def test_tc_ml_08_horizon_error_file():
    assert HORIZON.is_file()
    df = pd.read_csv(HORIZON)
    assert list(df["horizon_hours"]) == [1, 6, 24, 72, 168]
    assert {"rmse", "mape_percent"} <= set(df.columns)
