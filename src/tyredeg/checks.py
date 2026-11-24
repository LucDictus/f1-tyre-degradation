import pandas as pd

from tyredeg.config import SESSIONS


def check_negative_tyre_age(laps: pd.DataFrame) -> pd.DataFrame:
    """Return laps with a negative tyre age."""
    bad = laps["tyre_age"] < 0
    return laps[bad]


def check_unknown_compound(laps: pd.DataFrame) -> pd.DataFrame:
    """Return laps with an unknown tyre compound."""
    known_compounds = ["SOFT", "MEDIUM", "HARD"]
    bad = ~laps["compound"].isin(known_compounds)
    return laps[bad]


def check_non_positive_lap_time(laps: pd.DataFrame) -> pd.DataFrame:
    """Return laps with zero or negative lap duration."""
    bad = laps["lap_duration"] <= 0
    return laps[bad]


def check_duplicate_laps(laps: pd.DataFrame) -> pd.DataFrame:
    """Return all copies of laps that appear more than once."""
    bad = laps.duplicated(
        ["race", "driver_number", "lap_number"],
        keep=False,
    )
    return laps[bad]


def check_min_laps_per_race(
    laps: pd.DataFrame,
    min_laps: int = 500,
) -> list[str]:
    """Return races with fewer than the required number of laps."""
    # 500 is safely below Monza's 914 clean laps.
    lap_counts = laps["race"].value_counts()

    bad_races = []

    for race in SESSIONS:
        if lap_counts.get(race, 0) < min_laps:
            bad_races.append(race)

    return bad_races


def run_checks(laps: pd.DataFrame) -> None:
    """Run all data-quality checks and raise if any fail."""
    problems = []

    dataframe_checks = [
        check_negative_tyre_age,
        check_unknown_compound,
        check_non_positive_lap_time,
        check_duplicate_laps,
    ]

    for check in dataframe_checks:
        bad = check(laps)
        if not bad.empty:
            problems.append(f"{check.__name__}: {len(bad)} bad rows")

    bad_races = check_min_laps_per_race(laps)
    if bad_races:
        problems.append(f"too few laps: {bad_races}")

    if problems:
        raise ValueError("Data quality checks failed:\n" + "\n".join(problems))
