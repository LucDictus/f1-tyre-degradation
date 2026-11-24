import pandas as pd
import pytest

from tyredeg import checks
from tyredeg.checks import (
    check_duplicate_laps,
    check_min_laps_per_race,
    check_negative_tyre_age,
    check_non_positive_lap_time,
    check_unknown_compound,
)


def test_negative_tyre_age_clean_data():
    laps = pd.DataFrame(
        {
            "tyre_age": [0, 5, 10, 15],
        }
    )

    result = check_negative_tyre_age(laps)

    assert len(result) == 0


def test_negative_tyre_age_finds_bad_row():
    laps = pd.DataFrame(
        {
            "tyre_age": [0, 5, -1],
        }
    )

    result = check_negative_tyre_age(laps)

    assert len(result) == 1
    assert result.iloc[0]["tyre_age"] == -1


def test_unknown_compound_clean_data():
    laps = pd.DataFrame(
        {
            "compound": ["SOFT", "MEDIUM", "HARD"],
        }
    )

    result = check_unknown_compound(laps)

    assert len(result) == 0


def test_unknown_compound_finds_bad_row():
    laps = pd.DataFrame(
        {
            "compound": ["SOFT", "MEDIUM", "INTERMEDIATE"],
        }
    )

    result = check_unknown_compound(laps)

    assert len(result) == 1
    assert result.iloc[0]["compound"] == "INTERMEDIATE"


def test_non_positive_lap_time_clean_data():
    laps = pd.DataFrame(
        {
            "lap_duration": [85.2, 90.5, 88.1],
        }
    )

    result = check_non_positive_lap_time(laps)

    assert len(result) == 0


def test_non_positive_lap_time_finds_bad_row():
    laps = pd.DataFrame(
        {
            "lap_duration": [85.2, 0, 88.1],
        }
    )

    result = check_non_positive_lap_time(laps)

    assert len(result) == 1
    assert result.iloc[0]["lap_duration"] == 0


def test_duplicate_laps_clean_data():
    laps = pd.DataFrame(
        {
            "race": ["Monza", "Monza", "Spa"],
            "driver_number": [1, 44, 1],
            "lap_number": [1, 1, 1],
        }
    )

    result = check_duplicate_laps(laps)

    assert len(result) == 0


def test_duplicate_laps_finds_both_copies():
    laps = pd.DataFrame(
        {
            "race": ["Monza", "Monza", "Monza"],
            "driver_number": [1, 1, 44],
            "lap_number": [1, 1, 1],
        }
    )

    result = check_duplicate_laps(laps)

    assert len(result) == 2
    assert (result["driver_number"] == 1).all()
    assert (result["lap_number"] == 1).all()


def test_min_laps_per_race_clean_data(monkeypatch):
    monkeypatch.setattr(
        checks,
        "SESSIONS",
        ["Monza", "Spa"],
    )

    laps = pd.DataFrame(
        {
            "race": ["Monza", "Monza", "Spa", "Spa"],
        }
    )

    result = check_min_laps_per_race(laps, min_laps=2)

    assert result == []


def test_min_laps_per_race_finds_small_and_missing_races(monkeypatch):
    monkeypatch.setattr(
        checks,
        "SESSIONS",
        ["Monza", "Spa"],
    )

    laps = pd.DataFrame(
        {
            "race": ["Monza"],
        }
    )

    result = check_min_laps_per_race(laps, min_laps=2)

    assert result == ["Monza", "Spa"]


def make_good_laps():
    return pd.DataFrame(
        {
            "race": ["test_race"] * 500,
            "driver_number": [1] * 500,
            "lap_number": list(range(1, 501)),
            "tyre_age": [1] * 500,
            "compound": ["SOFT"] * 500,
            "lap_duration": [90.0] * 500,
        }
    )


def test_run_checks_passes_clean_data(monkeypatch):
    monkeypatch.setattr(
        checks,
        "SESSIONS",
        ["test_race"],
    )

    laps = make_good_laps()

    result = checks.run_checks(laps)

    assert result is None


def test_run_checks_raises_on_bad_data(monkeypatch):
    monkeypatch.setattr(
        checks,
        "SESSIONS",
        ["test_race"],
    )

    laps = make_good_laps()
    laps.loc[0, "tyre_age"] = -1

    with pytest.raises(
        ValueError,
        match="check_negative_tyre_age: 1 bad rows",
    ):
        checks.run_checks(laps)


def test_run_checks_reports_all_problems(monkeypatch):
    monkeypatch.setattr(
        checks,
        "SESSIONS",
        ["test_race", "missing_race"],
    )

    laps = make_good_laps()

    # Plant one problem for each check.
    laps.loc[0, "tyre_age"] = -1
    laps.loc[1, "compound"] = "UNKNOWN"
    laps.loc[2, "lap_duration"] = 0

    # Duplicate a lap by giving row 3 the same lap number as row 4.
    laps.loc[3, "lap_number"] = laps.loc[4, "lap_number"]

    with pytest.raises(ValueError) as error:
        checks.run_checks(laps)

    message = str(error.value)

    assert "check_negative_tyre_age" in message
    assert "check_unknown_compound" in message
    assert "check_non_positive_lap_time" in message
    assert "check_duplicate_laps" in message
    assert "missing_race" in message
