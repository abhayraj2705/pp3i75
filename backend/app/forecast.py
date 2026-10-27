"""Core business rule: which forecast did the trader actually have at decision time?

For every target hour T on delivery day D we use the forecast with the latest publishTime
that is <= the decision cutoff (D-1 at `cutoff_hour`, UK local time). Anything published
after the cutoff is ignored, so there is no look-ahead bias.
"""
from datetime import date

import pandas as pd

from app.config import DELIVERY_END, DELIVERY_START, UK_TZ


def delivery_day(start_times: pd.Series) -> pd.Series:
    """UK calendar day (as a naive midnight timestamp) that each UTC start time belongs to."""
    return start_times.dt.tz_convert(UK_TZ).dt.tz_localize(None).dt.normalize()


def decision_cutoff(days: pd.Series, cutoff_hour: int) -> pd.Series:
    """Decision time in UTC for each delivery day: D-1 at cutoff_hour, UK local time."""
    local = days - pd.Timedelta(days=1) + pd.Timedelta(hours=cutoff_hour)
    return local.dt.tz_localize(UK_TZ, nonexistent="shift_forward", ambiguous=False).dt.tz_convert("UTC")


def decision_forecasts(forecasts: pd.DataFrame, cutoff_hour: int) -> pd.DataFrame:
    """One row per target hour in the delivery range: the latest forecast available at the cutoff.

    Returns columns: startTime, publishTime, forecast, horizon_h, day.
    """
    df = forecasts.copy()
    df["day"] = delivery_day(df["startTime"])
    in_range = (df["day"] >= pd.Timestamp(DELIVERY_START)) & (df["day"] <= pd.Timestamp(DELIVERY_END))
    df = df[in_range]

    df = df[df["publishTime"] <= decision_cutoff(df["day"], cutoff_hour)]

    latest = df.sort_values("publishTime").groupby("startTime", as_index=False).last()
    latest = latest.rename(columns={"generation": "forecast"})
    latest["horizon_h"] = (latest["startTime"] - latest["publishTime"]).dt.total_seconds() / 3600
    return latest[["startTime", "publishTime", "forecast", "horizon_h", "day"]].sort_values("startTime")


def with_actuals(selected: pd.DataFrame, actuals: pd.DataFrame) -> pd.DataFrame:
    """Join forecasts to actuals on startTime and add error = actual - forecast."""
    merged = selected.merge(
        actuals.rename(columns={"generation": "actual"}), on="startTime", how="left"
    )
    merged["error"] = merged["actual"] - merged["forecast"]
    return merged


def one_day(selected: pd.DataFrame, day: date) -> pd.DataFrame:
    return selected[selected["day"] == pd.Timestamp(day)]
