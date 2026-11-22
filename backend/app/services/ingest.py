"""Meter reading ingestion with short-gap linear imputation (flagged)."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import pandas as pd

INTERVAL = timedelta(minutes=15)
MAX_IMPUTE = timedelta(hours=1)


def _parse_ts(value) -> datetime | None:
    ts = pd.to_datetime(value, errors="coerce")
    if pd.isna(ts):
        return None
    if getattr(ts, "tz", None) is not None:
        ts = ts.tz_convert("Asia/Kolkata").tz_localize(None)
    return ts.to_pydatetime()


def normalize_rows(raw_rows: list[dict]) -> tuple[list[dict], list[dict]]:
    """Validate rows → (valid [{ts, demand_kw}], rejected[{row, reason}])."""
    valid: list[dict] = []
    rejected: list[dict] = []
    seen: set[datetime] = set()
    for i, row in enumerate(raw_rows):
        if not isinstance(row, dict):
            rejected.append({"row": i, "reason": "row is not an object"})
            continue
        # flexible keys
        ts_raw = row.get("timestamp", row.get("ts", row.get("time")))
        kw_raw = row.get("demand_kw", row.get("demand_kW", row.get("kw")))
        ts = _parse_ts(ts_raw)
        if ts is None:
            rejected.append({"row": i, "reason": f"unparseable timestamp: {ts_raw!r}"})
            continue
        try:
            kw = float(kw_raw)
        except (TypeError, ValueError):
            rejected.append({"row": i, "reason": f"non-numeric demand_kw: {kw_raw!r}"})
            continue
        if kw < 0:
            rejected.append({"row": i, "reason": f"negative demand_kw: {kw}"})
            continue
        if ts in seen:
            rejected.append({"row": i, "reason": f"duplicate timestamp in batch: {ts.isoformat()}"})
            continue
        seen.add(ts)
        valid.append({"ts": ts, "demand_kw": kw, "imputed": False})
    return valid, rejected


def fill_short_gaps(valid: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    """Sort, impute ≤1h gaps, flag longer. Returns (to_write, imputed_only, long_gaps)."""
    if not valid:
        return [], [], []
    ordered = sorted(valid, key=lambda r: r["ts"])
    out = [ordered[0]]
    imputed: list[dict] = []
    long_gaps: list[dict] = []
    for nxt in ordered[1:]:
        prev = out[-1]
        delta = nxt["ts"] - prev["ts"]
        if delta <= INTERVAL:
            out.append(nxt)
            continue
        if delta <= MAX_IMPUTE:
            steps = int(delta / INTERVAL) - 1
            for s in range(1, steps + 1):
                ts = prev["ts"] + INTERVAL * s
                frac = s / (steps + 1)
                kw = prev["demand_kw"] + (nxt["demand_kw"] - prev["demand_kw"]) * frac
                row = {"ts": ts, "demand_kw": round(float(kw), 4), "imputed": True}
                out.append(row)
                imputed.append(row)
            out.append(nxt)
        else:
            long_gaps.append(
                {
                    "from": prev["ts"].isoformat(),
                    "to": nxt["ts"].isoformat(),
                    "gap_hours": round(delta.total_seconds() / 3600, 2),
                    "reason": "gap > 1 hour; not interpolated",
                }
            )
            out.append(nxt)
    return out, imputed, long_gaps


def process_payload(raw_rows: list[dict], existing_ts: set[datetime] | None = None) -> dict[str, Any]:
    valid, rejected = normalize_rows(raw_rows)
    existing_ts = existing_ts or set()
    kept: list[dict] = []
    for row in valid:
        if row["ts"] in existing_ts:
            rejected.append(
                {"row": row["ts"].isoformat(), "reason": "duplicate timestamp vs existing DB"}
            )
        else:
            kept.append(row)
    to_write, imputed, long_gaps = fill_short_gaps(kept)
    accepted = sum(1 for r in to_write if not r["imputed"])
    return {
        "accepted": accepted,
        "imputed": len(imputed),
        "rejected": len(rejected),
        "long_gaps": long_gaps,
        "rows": to_write,
        "reject_details": rejected,
    }
