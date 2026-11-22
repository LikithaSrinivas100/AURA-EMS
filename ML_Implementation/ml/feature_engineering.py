"""Create leak-safe features and chronological train/test CSVs."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from ml.utils import DEFAULT_DATA_PATH, PROJECT_ROOT, TARGET_COLUMN, load_master_dataset


FEATURE_COLUMNS = [
    "Hour",
    "DayOfWeek",
    "Month",
    "Temperature_C",
    "Is_Weekend",
    "Is_Vacation",
    "Is_Exam_Cycle",
    "Load_Lag_1hr",
    "Load_Lag_2hr",
    "Load_Lag_24hr",
    "Load_Rolling_Mean_4hr",
    "Load_Rolling_Std_4hr",
]


def engineer_features(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    missing_columns = [
        column
        for column in FEATURE_COLUMNS[:7] + [TARGET_COLUMN]
        if column not in frame.columns
    ]
    if missing_columns:
        raise ValueError(f"Dataset is missing required columns: {missing_columns}")

    features = frame.copy()
    demand = pd.to_numeric(features[TARGET_COLUMN], errors="coerce")
    features["Load_Lag_1hr"] = demand.shift(4)
    features["Load_Lag_2hr"] = demand.shift(8)
    features["Load_Lag_24hr"] = demand.shift(96)
    past_demand = demand.shift(1)
    features["Load_Rolling_Mean_4hr"] = past_demand.rolling(window=16).mean()
    features["Load_Rolling_Std_4hr"] = past_demand.rolling(window=16).std()

    usable = features[FEATURE_COLUMNS + [TARGET_COLUMN]].dropna()
    return usable[FEATURE_COLUMNS], usable[TARGET_COLUMN].rename(TARGET_COLUMN)


def create_chronological_split(
    features: pd.DataFrame, target: pd.Series, train_fraction: float = 0.8
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    if not 0 < train_fraction < 1:
        raise ValueError("train_fraction must be between 0 and 1.")
    if not features.index.equals(target.index):
        raise ValueError("Feature and target indexes must match exactly.")

    split_index = int(len(features) * train_fraction)
    if split_index == 0 or split_index == len(features):
        raise ValueError("Not enough usable rows for the requested chronological split.")
    return (
        features.iloc[:split_index],
        features.iloc[split_index:],
        target.iloc[:split_index],
        target.iloc[split_index:],
    )


def build_datasets(
    input_path: str | Path = DEFAULT_DATA_PATH,
    output_dir: str | Path = PROJECT_ROOT / "outputs",
    train_fraction: float = 0.8,
) -> None:
    frame = load_master_dataset(input_path)
    features, target = engineer_features(frame)
    x_train, x_test, y_train, y_test = create_chronological_split(
        features, target, train_fraction
    )

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    x_train.to_csv(destination / "X_train.csv")
    x_test.to_csv(destination / "X_test.csv")
    y_train.to_frame().to_csv(destination / "y_train.csv")
    y_test.to_frame().to_csv(destination / "y_test.csv")
    print(
        f"Saved chronological split: {len(x_train):,} train rows, "
        f"{len(x_test):,} test rows; features: {len(FEATURE_COLUMNS)}."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_DATA_PATH)
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "outputs")
    parser.add_argument("--train-fraction", type=float, default=0.8)
    args = parser.parse_args()
    build_datasets(args.input, args.output_dir, args.train_fraction)


if __name__ == "__main__":
    main()