import pandas as pd
import pytest

from app import metrics


@pytest.fixture
def rows():
    start = pd.to_datetime(["2026-01-15T00:00Z", "2026-01-15T01:00Z", "2026-01-16T00:00Z", "2026-01-16T01:00Z"], utc=True)
    forecast = [1000, 1000, 2000, 2000]
    actual = [1100, 900, 2300, 1900]
    df = pd.DataFrame({"startTime": start, "forecast": forecast, "actual": actual})
    df["error"] = df["actual"] - df["forecast"]  # 100, -100, 300, -100
    df["day"] = df["startTime"].dt.tz_localize(None).dt.normalize()
    return df


def test_summary_matches_hand_calculation(rows):
    s = metrics.summary(rows)
    assert s["count"] == 4
    assert s["mae"] == 150  # (100+100+300+100)/4
    assert s["bias"] == 50  # (100-100+300-100)/4
    assert s["rmse"] == 173  # sqrt((1e4+1e4+9e4+1e4)/4) = 173.2
    assert s["max_abs_error"] == 300
    assert s["nmae_pct"] == 9.7  # 150 / 1550 (mean actual) * 100


def test_summary_ignores_missing_actuals(rows):
    rows.loc[2, ["actual", "error"]] = None
    assert metrics.summary(rows)["count"] == 3


def test_summary_empty():
    assert metrics.summary(pd.DataFrame(columns=["forecast", "actual", "error"])) == {"count": 0}


def test_by_hour_and_daily(rows):
    assert metrics.by_hour(rows) == [{"hour": 0, "mae": 200, "bias": 200}, {"hour": 1, "mae": 100, "bias": -100}]
    assert [d["mae"] for d in metrics.daily(rows)] == [100, 200]


def test_bias_correction_uses_only_past_days(rows):
    # Day 1 errors: +100, -100 (mean 0). Day 2 is corrected by day 1's bias only, which is 0.
    result = metrics.bias_correction(rows, warmup_days=1)
    assert result == {"days_evaluated": 1, "raw_mae": 200, "corrected_mae": 200, "improvement_pct": 0.0}


def test_histogram_counts_every_error(rows):
    bins = metrics.histogram(rows, bin_width=100)
    assert sum(b["count"] for b in bins) == 4


def test_by_horizon_buckets():
    forecasts = pd.DataFrame(
        {
            "publishTime": pd.to_datetime(["2026-01-15T00:00Z", "2026-01-14T00:00Z"], utc=True),
            "startTime": pd.to_datetime(["2026-01-15T03:00Z", "2026-01-15T03:00Z"], utc=True),
            "generation": [1000, 1400],
        }
    )
    actuals = pd.DataFrame({"startTime": pd.to_datetime(["2026-01-15T03:00Z"], utc=True), "generation": [1100]})
    result = metrics.by_horizon(forecasts, actuals, "2026-01-02", "2026-02-01")
    assert result == [{"horizon": "0-6h", "mae": 100, "count": 1}, {"horizon": "24-30h", "mae": 300, "count": 1}]
