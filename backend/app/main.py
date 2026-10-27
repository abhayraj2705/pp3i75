"""HTTP API. Routes only validate input and call the logic in forecast.py / metrics.py."""
from datetime import date
from functools import lru_cache

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app import metrics
from app.config import DEFAULT_CUTOFF_HOUR, DELIVERY_END, DELIVERY_START, UK_TZ
from app.data_store import load_actuals, load_forecasts
from app.forecast import decision_cutoff, decision_forecasts, one_day, with_actuals

app = FastAPI(title="GB Wind Forecast Monitor API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"])

CutoffHour = Query(DEFAULT_CUTOFF_HOUR, ge=0, le=23, description="Decision hour on D-1 (UK time)")


@lru_cache(maxsize=24)
def decision_data(cutoff_hour: int) -> pd.DataFrame:
    """Decision-time forecast joined with actuals for every delivery hour (one row per hour)."""
    return with_actuals(decision_forecasts(load_forecasts(), cutoff_hour), load_actuals())


@lru_cache(maxsize=24)
def month_summary(cutoff_hour: int) -> dict:
    return metrics.summary(decision_data(cutoff_hour))


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/meta")
def meta():
    return {
        "delivery_start": DELIVERY_START.isoformat(),
        "delivery_end": DELIVERY_END.isoformat(),
        "default_cutoff_hour": DEFAULT_CUTOFF_HOUR,
    }


@app.get("/api/day-ahead")
def day_ahead(date: date = Query(..., description="Delivery day, e.g. 2026-01-15"), cutoff_hour: int = CutoffHour):
    if not DELIVERY_START <= date <= DELIVERY_END:
        raise HTTPException(400, f"date must be between {DELIVERY_START} and {DELIVERY_END}")

    rows = one_day(decision_data(cutoff_hour), date)
    month = month_summary(cutoff_hour)
    cutoff = decision_cutoff(pd.Series([pd.Timestamp(date)]), cutoff_hour).iloc[0]

    points = [
        {
            "time": row.startTime.isoformat(),
            "hour_uk": row.startTime.tz_convert(UK_TZ).strftime("%H:%M"),
            "forecast": int(row.forecast),
            "actual": None if pd.isna(row.actual) else int(row.actual),
            "error": None if pd.isna(row.error) else int(row.error),
            "horizon_h": row.horizon_h,
            # Likely range for the actual, from January's P10/P90 errors.
            "band_low": max(0, int(row.forecast + month["p10"])),
            "band_high": int(row.forecast + month["p90"]),
        }
        for row in rows.itertuples()
    ]
    publish_times = rows["publishTime"]
    return {
        "date": date.isoformat(),
        "cutoff_hour": cutoff_hour,
        "cutoff": cutoff.isoformat(),
        "forecast_published": None if publish_times.empty else publish_times.max().isoformat(),
        "points": points,
        "summary": metrics.summary(rows),
        "band": {"p10": month["p10"], "p90": month["p90"]},
    }


@app.get("/api/accuracy")
def accuracy(cutoff_hour: int = CutoffHour):
    data = decision_data(cutoff_hour)
    return {
        "cutoff_hour": cutoff_hour,
        "summary": month_summary(cutoff_hour),
        "histogram": metrics.histogram(data),
        "by_hour": metrics.by_hour(data),
        "daily": metrics.daily(data),
        "bias_correction": metrics.bias_correction(data),
        "by_horizon": metrics.by_horizon(load_forecasts(), load_actuals(), DELIVERY_START, DELIVERY_END),
    }
