"""All app constants live here, so dates, paths and defaults are easy to find and change."""
from datetime import date
from pathlib import Path

# Decisions are made in January 2026 on day D-1, so delivery days run 2 Jan -> 1 Feb 2026.
DELIVERY_START = date(2026, 1, 2)
DELIVERY_END = date(2026, 2, 1)

# Default decision time on D-1 (UK local hour). Day-ahead auctions close mid-morning.
DEFAULT_CUTOFF_HOUR = 10

UK_TZ = "Europe/London"

# Horizon buckets (hours ahead) used in the "error vs horizon" analysis.
HORIZON_BINS = [0, 6, 12, 18, 24, 30, 36, 42, 48]

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ACTUALS_CSV = DATA_DIR / "actuals_wind.csv"
FORECASTS_CSV = DATA_DIR / "forecasts_wind.csv"
