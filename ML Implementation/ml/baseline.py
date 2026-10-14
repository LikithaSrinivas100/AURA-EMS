"""A 24-hour persistence benchmark for campus demand."""

from __future__ import annotations

import pandas as pd


class Persistence24HourBaseline:
    """Predict each interval using the observed demand 24 hours earlier."""

    def predict(self, features: pd.DataFrame) -> pd.Series:
        if "Load_Lag_24hr" not in features:
            raise ValueError("Baseline requires the Load_Lag_24hr feature.")
        return features["Load_Lag_24hr"]