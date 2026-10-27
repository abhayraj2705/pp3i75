"""Download wind actuals (FUELHH) and wind forecasts (WINDFOR) from Elexon and save them as CSV.

Run from the backend/ folder:  python -m scripts.fetch_data

The data for January 2026 is historical, so we fetch it once and commit the CSVs.
Re-running the script is safe: it overwrites the files with fresh data.
"""
from datetime import date, datetime, timedelta, timezone

import pandas as pd
import requests

from app.config import ACTUALS_CSV, DATA_DIR, FORECASTS_CSV

BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1/datasets"

# Forecasts: every run published from 30 Dec 2025 up to the end of 31 Jan 2026
# (the last possible decision time). Earlier runs are kept for the horizon analysis.
FORECAST_PUBLISH_FROM = datetime(2025, 12, 30, tzinfo=timezone.utc)
FORECAST_PUBLISH_TO = datetime(2026, 2, 1, tzinfo=timezone.utc)

# Actuals: every settlement day we might compare against.
ACTUALS_FROM = date(2026, 1, 1)
ACTUALS_TO = date(2026, 2, 1)


def get_json(url: str, params: dict) -> list:
    for attempt in range(3):
        try:
            response = requests.get(url, params=params, timeout=60)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as error:
            print(f"  retry {attempt + 1}: {error}")
    raise RuntimeError(f"Failed to fetch {url} {params}")


def fetch_forecasts() -> pd.DataFrame:
    rows = []
    start = FORECAST_PUBLISH_FROM
    while start < FORECAST_PUBLISH_TO:
        end = start + timedelta(days=1)
        print(f"WINDFOR published {start:%Y-%m-%d}")
        rows += get_json(
            f"{BASE_URL}/WINDFOR/stream",
            {
                "publishDateTimeFrom": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "publishDateTimeTo": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
        )
        start = end

    df = pd.DataFrame(rows)[["publishTime", "startTime", "generation"]]
    # Day chunks share their boundary timestamp, so drop the overlap.
    df = df.drop_duplicates(["publishTime", "startTime"])
    return df.sort_values(["publishTime", "startTime"])


def fetch_actuals() -> pd.DataFrame:
    print(f"FUELHH WIND {ACTUALS_FROM} -> {ACTUALS_TO}")
    rows = get_json(
        f"{BASE_URL}/FUELHH/stream",
        {
            "settlementDateFrom": ACTUALS_FROM.isoformat(),
            "settlementDateTo": ACTUALS_TO.isoformat(),
            "fuelType": "WIND",
        },
    )
    df = pd.DataFrame(rows)
    df = df[df["fuelType"] == "WIND"][["startTime", "generation"]]
    df = df.drop_duplicates("startTime")
    return df.sort_values("startTime")


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    forecasts = fetch_forecasts()
    forecasts.to_csv(FORECASTS_CSV, index=False)
    print(f"Saved {len(forecasts)} forecast rows -> {FORECASTS_CSV}")

    actuals = fetch_actuals()
    actuals.to_csv(ACTUALS_CSV, index=False)
    print(f"Saved {len(actuals)} actual rows -> {ACTUALS_CSV}")


if __name__ == "__main__":
    main()
