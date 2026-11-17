import pandas as pd
import pytest

from tyredeg.clean import (
    add_stint_info,
    check_no_red_flag,
    drop_first_lap,
    drop_in_laps,
    drop_missing_time,
    drop_out_laps,
    drop_safety_car_laps,
    drop_slow_laps,
)


def test_drop_first_lap():
    laps = pd.DataFrame({"lap_number": [1, 2, 3]})
    result = drop_first_lap(laps)
    assert list(result["lap_number"]) == [2, 3]


def test_drop_missing_time():
    laps = pd.DataFrame({"lap_duration": [90.0, None, 92.0]})
    result = drop_missing_time(laps)
    assert list(result["lap_duration"]) == [90.0, 92.0]


def test_drop_out_laps():
    laps = pd.DataFrame({"is_pit_out_lap": [False, True, False]})
    result = drop_out_laps(laps)
    assert result["is_pit_out_lap"].tolist() == [False, False]


def test_drop_in_laps():
    laps = pd.DataFrame(
        {
            "driver_number": [1, 1, 1],
            "lap_number": [5, 6, 7],
        }
    )
    pits = pd.DataFrame(
        {
            "driver_number": [1],
            "lap_number": [6],
        }
    )
    result = drop_in_laps(laps, pits)
    assert result["lap_number"].tolist() == [5, 7]


def test_drop_safety_car_laps():
    laps = pd.DataFrame({"lap_number": [30, 31, 32, 33, 34, 35, 36, 37]})
    race_control = pd.DataFrame(
        {
            "category": ["SafetyCar", "SafetyCar"],
            "message": ["SAFETY CAR DEPLOYED", "SAFETY CAR IN THIS LAP"],
            "lap_number": [32, 35],
        }
    )
    result = drop_safety_car_laps(laps, race_control)
    assert result["lap_number"].tolist() == [30, 31, 37]


def test_drop_slow_laps():
    laps = pd.DataFrame(
        {
            "lap_duration": [90.0, 91.0, 92.0, 105.0, 200.0],
        }
    )

    result = drop_slow_laps(laps)

    assert result["lap_duration"].tolist() == [90.0, 91.0, 92.0]


def test_check_no_red_flag():
    race_control = pd.DataFrame({"flag": ["GREEN", "YELLOW"]})
    assert check_no_red_flag(race_control) is None

    race_control = pd.DataFrame({"flag": ["GREEN", "RED"]})
    with pytest.raises(ValueError, match="Red flag"):
        check_no_red_flag(race_control)


def test_add_stint_info():
    laps = pd.DataFrame(
        {
            "driver_number": [1, 1, 1, 1],
            "session_key": [100] * 4,
            "meeting_key": [200] * 4,
            "lap_number": [1, 2, 3, 4],
        }
    )

    stints = pd.DataFrame(
        {
            "driver_number": [1, 1],
            "session_key": [100, 100],
            "meeting_key": [200, 200],
            "lap_start": [1, 3],
            "lap_end": [2, 4],
            "tyre_age_at_start": [3, 0],
            "stint_number": [1, 2],
            "compound": ["SOFT", "MEDIUM"],
        }
    )

    result = add_stint_info(laps, stints)

    assert result["lap_number"].tolist() == [1, 2, 3, 4]
    assert result["tyre_age"].tolist() == [3, 4, 0, 1]
    assert result["stint_number"].tolist() == [1, 1, 2, 2]


def test_drop_safety_car_laps_no_safety_car():
    laps = pd.DataFrame({"lap_number": [1, 2, 3]})
    race_control = pd.DataFrame(
        {
            "category": ["Green"],
            "message": ["GREEN FLAG"],
            "lap_number": [1],
        }
    )

    result = drop_safety_car_laps(laps, race_control)
    assert result["lap_number"].tolist() == [1, 2, 3]


def test_drop_safety_car_laps_multiple_safety_cars():
    laps = pd.DataFrame({"lap_number": [10, 20, 30]})
    race_control = pd.DataFrame(
        {
            "category": ["SafetyCar", "SafetyCar"],
            "message": ["SAFETY CAR DEPLOYED", "SAFETY CAR DEPLOYED"],
            "lap_number": [10, 20],
        }
    )

    with pytest.raises(ValueError, match="exactly 1"):
        drop_safety_car_laps(laps, race_control)
