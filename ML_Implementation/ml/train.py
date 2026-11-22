"""Train XGBoost and LightGBM on the prepared chronological training split."""

from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import pandas as pd
from lightgbm import LGBMRegressor
from xgboost import XGBRegressor

from ml.baseline import Persistence24HourBaseline
from ml.feature_engineering import FEATURE_COLUMNS
from ml.utils import PROJECT_ROOT, TARGET_COLUMN


def read_split(data_dir: Path) -> tuple[pd.DataFrame, pd.Series]:
    features = pd.read_csv(data_dir / "X_train.csv", index_col=0, parse_dates=True)
    target_frame = pd.read_csv(data_dir / "y_train.csv", index_col=0, parse_dates=True)
    if features.columns.tolist() != FEATURE_COLUMNS:
        raise ValueError("X_train.csv feature columns do not match the published feature contract.")
    if target_frame.shape[1] != 1:
        raise ValueError("y_train.csv must contain exactly one target column.")
    target = target_frame.iloc[:, 0]
    if not features.index.equals(target.index):
        raise ValueError("Training feature and target timestamps do not match.")
    return features, target.rename(TARGET_COLUMN)


def train_models(data_dir: Path, model_dir: Path) -> None:
    x_train, y_train = read_split(data_dir)
    model_dir.mkdir(parents=True, exist_ok=True)

    xgb_model = XGBRegressor(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="reg:squarederror",
        random_state=42,
        n_jobs=-1,
    )
    lightgbm_model = LGBMRegressor(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        subsample_freq=1,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1,
        verbosity=-1,
    )

    xgb_model.fit(x_train, y_train)
    lightgbm_model.fit(x_train, y_train)
    joblib.dump(xgb_model, model_dir / "aura_ems_xgboost_exp.pkl")
    joblib.dump(lightgbm_model, model_dir / "aura_ems_lightgbm_exp.pkl")
    joblib.dump(Persistence24HourBaseline(), model_dir / "aura_ems_baseline_exp.pkl")
    print(f"Saved XGBoost, LightGBM, and persistence baseline artifacts to {model_dir}.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=PROJECT_ROOT / "outputs")
    parser.add_argument("--model-dir", type=Path, default=PROJECT_ROOT / "models")
    args = parser.parse_args()
    train_models(args.data_dir, args.model_dir)


if __name__ == "__main__":
    main()