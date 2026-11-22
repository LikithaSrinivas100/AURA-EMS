"""Replay cursor over the hold-out test window (simulated meter stream)."""
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

try:
    from app.schemas import HIGH_RISK_KW
    from app.services.forecaster import parse_zone, zone_history_items, _assets
except ImportError:
    from schemas import HIGH_RISK_KW
    from services.forecaster import parse_zone, zone_history_items, _assets

router = APIRouter(prefix="/replay", tags=["replay"])

_SERIES: dict[str, list[dict]] = {}
_CURSORS: dict[str, int] = {}


def _norm(zone: str) -> str:
    try:
        parse_zone(zone)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return (zone or "campus").strip().lower()


def _test_items(zone: str) -> list[dict]:
    if zone not in _SERIES:
        _, _, history, _ = _assets()
        split = int(len(history) * 0.8)
        items = zone_history_items(zone, start=history.index[split])
        _SERIES[zone] = items
        _CURSORS.setdefault(zone, 0)
    return _SERIES[zone]


def _risk(v: float) -> str:
    return "HIGH" if v >= HIGH_RISK_KW else ("MEDIUM" if v >= HIGH_RISK_KW * 0.75 else "LOW")


@router.post("/reset")
def replay_reset(zone: str = Query("campus")):
    z = _norm(zone)
    _test_items(z)
    _CURSORS[z] = 0
    return {"zone": z, "cursor": 0, "remaining": len(_SERIES[z])}


@router.get("/next")
def replay_next(
    cursor: Optional[int] = Query(None, ge=0),
    n: int = Query(4, ge=1, le=96),
    zone: str = Query("campus"),
):
    z = _norm(zone)
    series = _test_items(z)
    idx = int(cursor) if cursor is not None else _CURSORS.get(z, 0)
    if idx > len(series):
        raise HTTPException(status_code=400, detail=f"cursor out of range 0..{len(series)}")
    chunk = series[idx : idx + n]
    nxt = idx + len(chunk)
    _CURSORS[z] = nxt
    peak_alerts = sum(1 for row in chunk if float(row["best_pred_kw"]) >= HIGH_RISK_KW)
    return {
        "zone": z,
        "cursor": idx,
        "next_cursor": nxt,
        "done": nxt >= len(series),
        "peak_alerts": peak_alerts,
        "items": [
            {
                **{k: v for k, v in row.items() if k != "ts"},
                "ts": row["ts"].isoformat() if hasattr(row["ts"], "isoformat") else row["ts"],
                "risk_level": _risk(float(row["best_pred_kw"])),
            }
            for row in chunk
        ],
    }
