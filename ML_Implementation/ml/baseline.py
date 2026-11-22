"""Persistence and seasonal-naive benchmarks for campus demand."""

from __future__ import annotations

import pandas as pd


class Persistence24HourBaseline:
    """Predict each interval using the observed demand 24 hours earlier (shift 96 @ 15 min)."""

    def predict(self, features: pd.DataFrame) -> pd.Series:
        if "Load_Lag_24hr" not in features:
            raise ValueError("Baseline requires the Load_Lag_24hr feature.")
        return features["Load_Lag_24hr"]


class SeasonalNaive7DayBaseline:
    """Predict using the same clock time one week earlier (shift 672 @ 15 min)."""

    STEPS = 672  # 7 * 24 * 4

    def predict_from_series(self, full_target: pd.Series, test_index: pd.Index) -> pd.Series:
        shifted = full_target.shift(self.STEPS)
        out = shifted.reindex(test_index)
        if out.isna().any():
            raise ValueError("7-day seasonal-naive needs ≥672 prior intervals before the test window.")
        return out.rename("SeasonalNaive7Day")
