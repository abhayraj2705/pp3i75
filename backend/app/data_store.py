"""Load the CSV snapshot into pandas once per process."""
from functools import lru_cache

import pandas as pd

from app.config import ACTUALS_CSV, FORECASTS_CSV


@lru_cache(maxsize=1)
def load_forecasts() -> pd.DataFrame:
    """Columns: publishTime, startTime (UTC, hourly), generation (MW)."""
    df = pd.read_csv(FORECASTS_CSV)
    df["publishTime"] = pd.to_datetime(df["publishTime"], utc=True)
    df["startTime"] = pd.to_datetime(df["startTime"], utc=True)
    return df


@lru_cache(maxsize=1)
def load_actuals() -> pd.DataFrame:
    """Columns: startTime (UTC), generation (MW).

    Only on-the-hour rows are kept, because forecasts are hourly and we compare like for like.
    """
    df = pd.read_csv(ACTUALS_CSV)
    df["startTime"] = pd.to_datetime(df["startTime"], utc=True)
    return df[df["startTime"].dt.minute == 0].reset_index(drop=True)
