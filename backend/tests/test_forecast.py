from datetime import date

import pandas as pd

from app.data_store import load_forecasts
from app.forecast import decision_cutoff, decision_forecasts, one_day, with_actuals


def make_forecasts(rows):
    """rows: (publishTime, startTime, generation) as UTC strings."""
    df = pd.DataFrame(rows, columns=["publishTime", "startTime", "generation"])
    df["publishTime"] = pd.to_datetime(df["publishTime"], utc=True)
    df["startTime"] = pd.to_datetime(df["startTime"], utc=True)
    return df


# Three runs that all forecast 15 Jan 12:00. Cutoff for 15 Jan is 14 Jan at cutoff_hour.
RUNS = make_forecasts(
    [
        ("2026-01-13T22:30Z", "2026-01-15T12:00Z", 50),
        ("2026-01-14T09:30Z", "2026-01-15T12:00Z", 100),
        ("2026-01-14T11:30Z", "2026-01-15T12:00Z", 999),
    ]
)


def forecast_value(cutoff_hour):
    return one_day(decision_forecasts(RUNS, cutoff_hour), date(2026, 1, 15))["forecast"].tolist()


def test_uses_latest_run_before_cutoff():
    assert forecast_value(10) == [100]


def test_never_uses_run_published_after_cutoff():
    assert 999 not in forecast_value(10)
    assert forecast_value(12) == [999]


def test_falls_back_to_older_run_with_early_cutoff():
    assert forecast_value(2) == [50]


def test_no_forecast_when_nothing_published_before_cutoff():
    assert forecast_value(0) == [50]  # 13 Jan 22:30 is before 14 Jan 00:00
    early_only = make_forecasts([("2026-01-14T09:30Z", "2026-01-15T12:00Z", 100)])
    assert decision_forecasts(early_only, 5).empty


def test_midnight_belongs_to_the_new_day():
    runs = make_forecasts(
        [
            ("2026-01-14T09:30Z", "2026-01-15T23:00Z", 1),
            ("2026-01-14T09:30Z", "2026-01-16T00:00Z", 2),
            ("2026-01-15T09:30Z", "2026-01-16T00:00Z", 3),
        ]
    )
    selected = decision_forecasts(runs, 10)
    assert one_day(selected, date(2026, 1, 15))["forecast"].tolist() == [1]
    # 16 Jan 00:00 is decided on 15 Jan, so the newer run (3) is allowed.
    assert one_day(selected, date(2026, 1, 16))["forecast"].tolist() == [3]


def test_cutoff_is_uk_local_time():
    winter = decision_cutoff(pd.Series([pd.Timestamp("2026-01-15")]), 10).iloc[0]
    summer = decision_cutoff(pd.Series([pd.Timestamp("2026-07-15")]), 10).iloc[0]
    assert winter == pd.Timestamp("2026-01-14T10:00Z")
    assert summer == pd.Timestamp("2026-07-14T09:00Z")  # BST = UTC+1


def test_error_is_actual_minus_forecast():
    selected = decision_forecasts(RUNS, 10)
    actuals = pd.DataFrame({"startTime": pd.to_datetime(["2026-01-15T12:00Z"], utc=True), "generation": [130]})
    assert with_actuals(selected, actuals)["error"].tolist() == [30]


def test_real_data_has_no_look_ahead():
    for cutoff_hour in range(24):
        selected = decision_forecasts(load_forecasts(), cutoff_hour)
        cutoffs = decision_cutoff(selected["day"], cutoff_hour)
        assert (selected["publishTime"].values <= cutoffs.values).all()
        assert selected["startTime"].is_unique


def test_real_data_coverage():
    # From 03:00 the 02:30 run (66.5h ahead) is available, so every hour of 2 Jan -> 1 Feb is covered.
    assert len(decision_forecasts(load_forecasts(), 3)) == 31 * 24
    # Before that, the latest run is D-2 22:30, which only reaches 46.5h ahead: D 22:00-23:00 has no forecast.
    early = decision_forecasts(load_forecasts(), 0)
    assert len(early) == 31 * 22
    assert set(early["startTime"].dt.hour) == set(range(22))
