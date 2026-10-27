"""Forecast error statistics. Convention: error = actual - forecast (MW).

Positive error = more wind than forecast (we bought too much).
Negative error = less wind than forecast (we must buy more at short notice).
"""
import numpy as np
import pandas as pd

from app.config import HORIZON_BINS, UK_TZ
from app.forecast import delivery_day


def summary(df: pd.DataFrame) -> dict:
    """Headline numbers for rows that have both a forecast and an actual."""
    df = df.dropna(subset=["actual", "forecast"])
    if df.empty:
        return {"count": 0}
    error = df["error"]
    mae = error.abs().mean()
    return {
        "count": int(len(df)),
        "mae": round(float(mae)),
        "rmse": round(float(np.sqrt((error**2).mean()))),
        "bias": round(float(error.mean())),
        "nmae_pct": round(float(mae / df["actual"].mean() * 100), 1),
        "max_abs_error": round(float(error.abs().max())),
        "p10": round(float(error.quantile(0.10))),
        "p50": round(float(error.quantile(0.50))),
        "p90": round(float(error.quantile(0.90))),
        "mean_actual": round(float(df["actual"].mean())),
        "mean_forecast": round(float(df["forecast"].mean())),
    }


def by_hour(df: pd.DataFrame) -> list[dict]:
    """MAE and bias for each UK hour of day (0-23)."""
    df = df.dropna(subset=["error"])
    hours = df["startTime"].dt.tz_convert(UK_TZ).dt.hour
    grouped = df.groupby(hours)["error"]
    return [
        {"hour": int(hour), "mae": round(float(errors.abs().mean())), "bias": round(float(errors.mean()))}
        for hour, errors in grouped
    ]


def daily(df: pd.DataFrame) -> list[dict]:
    """MAE and bias for each delivery day."""
    df = df.dropna(subset=["error"])
    return [
        {
            "date": day.date().isoformat(),
            "mae": round(float(rows["error"].abs().mean())),
            "bias": round(float(rows["error"].mean())),
            "mean_actual": round(float(rows["actual"].mean())),
        }
        for day, rows in df.groupby("day")
    ]


def bias_correction(df: pd.DataFrame, warmup_days: int = 3) -> dict:
    """How much better would a simple bias-corrected forecast be?

    Each day's forecast is shifted by the mean error of all *earlier* days only (walk-forward),
    so the correction never uses information from the future. The first `warmup_days` are skipped.
    """
    df = df.dropna(subset=["error"])
    days = sorted(df["day"].unique())[warmup_days:]
    raw, corrected = [], []
    for day in days:
        past_bias = df.loc[df["day"] < day, "error"].mean()
        today = df.loc[df["day"] == day, "error"]
        raw += list(today.abs())
        corrected += list((today - past_bias).abs())
    if not raw:
        return {}
    raw_mae, corrected_mae = float(np.mean(raw)), float(np.mean(corrected))
    return {
        "days_evaluated": len(days),
        "raw_mae": round(raw_mae),
        "corrected_mae": round(corrected_mae),
        "improvement_pct": round((1 - corrected_mae / raw_mae) * 100, 1),
    }


def histogram(df: pd.DataFrame, bin_width: int = 500) -> list[dict]:
    """Counts of errors in fixed-width MW bins."""
    error = df["error"].dropna()
    if error.empty:
        return []
    low = int(np.floor(error.min() / bin_width) * bin_width)
    high = int(np.ceil(error.max() / bin_width) * bin_width) + bin_width
    counts, edges = np.histogram(error, bins=range(low, high + 1, bin_width))
    return [{"from": int(edges[i]), "to": int(edges[i + 1]), "count": int(c)} for i, c in enumerate(counts)]


def by_horizon(forecasts: pd.DataFrame, actuals: pd.DataFrame, start, end) -> list[dict]:
    """MAE by lead time, using every forecast run (not only the decision-time one).

    Shows how forecast quality improves as the target hour gets closer.
    """
    df = forecasts.merge(actuals.rename(columns={"generation": "actual"}), on="startTime")
    days = delivery_day(df["startTime"])
    df = df[(days >= pd.Timestamp(start)) & (days <= pd.Timestamp(end))].copy()
    df["horizon_h"] = (df["startTime"] - df["publishTime"]).dt.total_seconds() / 3600
    df["abs_error"] = (df["actual"] - df["generation"]).abs()

    edges = HORIZON_BINS
    df["bucket"] = pd.cut(df["horizon_h"], bins=edges, right=False)
    result = []
    for interval, rows in df.groupby("bucket", observed=True):
        result.append(
            {
                "horizon": f"{int(interval.left)}-{int(interval.right)}h",
                "mae": round(float(rows["abs_error"].mean())),
                "count": int(len(rows)),
            }
        )
    return result
