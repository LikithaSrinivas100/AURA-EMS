"""Shared paths and validation helpers for the AURA-EMS ML pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_PATH = PROJECT_ROOT / "data" / "alliance_campus_energy_master.csv"
TARGET_COLUMN = "Total_Campus_Demand_kW"
EXPECTED_INTERVAL = pd.Timedelta(minutes=15)


@dataclass(frozen=True)
class DataQualitySummary:
    rows: int
    start: pd.Timestamp
    end: pd.Timestamp
    median_interval: pd.Timedelta | None
    irregular_intervals: int
    negative_target_rows: int
    missing_values: int


def load_master_dataset(path: str | Path = DEFAULT_DATA_PATH) -> pd.DataFrame:
    """Load a CSV whose first column contains timestamps and validate its index."""
    csv_path = Path(path)
    if not csv_path.is_file():
        raise FileNotFoundError(
            f"Master dataset not found at {csv_path}. Place it at "
            "data/alliance_campus_energy_master.csv or pass --input."
        )

    frame = pd.read_csv(csv_path, index_col=0)
    parsed_index = pd.to_datetime(frame.index, errors="coerce")
    if parsed_index.isna().any():
        invalid_count = int(parsed_index.isna().sum())
        raise ValueError(f"Timestamp index contains {invalid_count} unparseable values.")

    frame.index = pd.DatetimeIndex(parsed_index, name="Timestamp")
    if frame.index.has_duplicates:
        duplicate_count = int(frame.index.duplicated(keep=False).sum())
        raise ValueError(f"Timestamp index contains {duplicate_count} duplicate rows.")

    frame = frame.sort_index()
    if TARGET_COLUMN not in frame.columns:
        raise ValueError(f"Required target column {TARGET_COLUMN!r} is missing.")

    frame[TARGET_COLUMN] = pd.to_numeric(frame[TARGET_COLUMN], errors="coerce")
    if frame[TARGET_COLUMN].isna().any():
        invalid_count = int(frame[TARGET_COLUMN].isna().sum())
        raise ValueError(f"Target column contains {invalid_count} missing or non-numeric values.")

    summary = summarize_data_quality(frame)
    print_data_quality_summary(summary)
    if summary.negative_target_rows:
        raise ValueError(
            f"Target contains {summary.negative_target_rows} negative demand values; "
            "inspect and correct these source rows before training."
        )
    if summary.median_interval != EXPECTED_INTERVAL or summary.irregular_intervals:
        raise ValueError(
            "Expected a continuous 15-minute timestamp index for shift-based features; "
            f"median interval is {summary.median_interval}, with "
            f"{summary.irregular_intervals} non-15-minute intervals."
        )
    return frame


def summarize_data_quality(frame: pd.DataFrame) -> DataQualitySummary:
    if frame.empty:
        raise ValueError("Dataset is empty.")
    if not isinstance(frame.index, pd.DatetimeIndex):
        raise TypeError("Dataset index must be a pandas DatetimeIndex.")
    if not frame.index.is_monotonic_increasing:
        raise ValueError("Dataset must be sorted oldest to newest.")

    intervals = frame.index.to_series().diff().dropna()
    median_interval = intervals.median() if not intervals.empty else None
    irregular_intervals = int((intervals != EXPECTED_INTERVAL).sum())
    negative_target_rows = (
        int((frame[TARGET_COLUMN] < 0).sum()) if TARGET_COLUMN in frame else 0
    )
    return DataQualitySummary(
        rows=len(frame),
        start=frame.index.min(),
        end=frame.index.max(),
        median_interval=median_interval,
        irregular_intervals=irregular_intervals,
        negative_target_rows=negative_target_rows,
        missing_values=int(frame.isna().sum().sum()),
    )


def print_data_quality_summary(summary: DataQualitySummary) -> None:
    print("Data quality summary")
    print(f"  Rows: {summary.rows:,}")
    print(f"  Date range: {summary.start} to {summary.end}")
    print(f"  Median interval: {summary.median_interval}")
    print(f"  Non-15-minute intervals: {summary.irregular_intervals:,}")
    print(f"  Negative target rows: {summary.negative_target_rows:,}")
    print(f"  Missing values: {summary.missing_values:,}")