import json
from pathlib import Path

import pandas as pd

from tyredeg.checks import run_checks
from tyredeg.config import SESSIONS
from tyredeg.ingest import PROJECT_ROOT, atomic_write, raw_path


def load_raw(race: str, endpoint: str) -> pd.DataFrame:
    path = raw_path(race, endpoint)
    records = json.loads(path.read_text())
    df = pd.DataFrame(records)
    return df


def add_stint_info(laps: pd.DataFrame, stints: pd.DataFrame) -> pd.DataFrame:
    m = laps.merge(stints, on=["driver_number", "session_key", "meeting_key"])

    inside = (m["lap_number"] >= m["lap_start"]) & (m["lap_number"] <= m["lap_end"])
    m = m[inside].copy()

    m["tyre_age"] = m["tyre_age_at_start"] + (m["lap_number"] - m["lap_start"])

    return m


def drop_first_lap(laps: pd.DataFrame) -> pd.DataFrame:
    keep = laps["lap_number"] != 1
    return laps[keep]


def drop_missing_time(laps: pd.DataFrame) -> pd.DataFrame:
    keep = laps["lap_duration"].notna()
    return laps[keep]


def drop_out_laps(laps: pd.DataFrame) -> pd.DataFrame:
    keep = ~laps["is_pit_out_lap"]
    return laps[keep]


def drop_in_laps(laps: pd.DataFrame, pits: pd.DataFrame) -> pd.DataFrame:
    pit_laps = pits[["driver_number", "lap_number"]]

    m = laps.merge(pit_laps, on=["driver_number", "lap_number"], how="left", indicator=True)

    m = m[m["_merge"] == "left_only"]
    return m.drop(columns=["_merge"])


def drop_safety_car_laps(laps: pd.DataFrame, race_control: pd.DataFrame) -> pd.DataFrame:
    sc = race_control[race_control["category"] == "SafetyCar"]

    if sc.empty:
        return laps

    deployed = sc[sc["message"].str.contains("DEPLOYED")]

    if len(deployed) != 1:
        raise ValueError(
            f"expected exactly 1 safety car, found {len(deployed)}; "
            "multiple safety cars or VSC are not supported"
        )

    start = deployed["lap_number"].iloc[0]
    end = sc[sc["message"].str.contains("IN THIS LAP")]["lap_number"].iloc[0]

    keep = ~laps["lap_number"].between(start, end + 1)

    return laps[keep]


def drop_slow_laps(laps: pd.DataFrame) -> pd.DataFrame:
    median = laps["lap_duration"].median()
    keep = laps["lap_duration"] <= 1.07 * median
    return laps[keep]


def check_no_red_flag(race_control: pd.DataFrame) -> None:
    if (race_control["flag"] == "RED").any():
        raise ValueError("Red flag detected; tyre age may be incorrect")


CLEAN_DIR = PROJECT_ROOT / "data" / "clean"


def clean_path() -> Path:
    return CLEAN_DIR / "laps.parquet"


def save_clean(laps: pd.DataFrame, path: Path) -> None:
    """Save cleaned laps atomically as Parquet."""
    atomic_write(path, lambda p: laps.to_parquet(p, index=False))


def run() -> pd.DataFrame:
    """Clean each race separately and combine the results."""
    cleaned_races = []

    for race in SESSIONS:
        print(f"\nCleaning {race}...")

        laps = load_raw(race, "laps")
        stints = load_raw(race, "stints")
        pits = load_raw(race, "pit")
        race_control = load_raw(race, "race_control")

        # Check assumptions before cleaning.
        check_no_red_flag(race_control)

        # Add stint and tyre information.
        result = add_stint_info(laps, stints)

        # Apply filters.
        result = drop_first_lap(result)
        result = drop_missing_time(result)
        result = drop_out_laps(result)
        result = drop_in_laps(result, pits)
        result = drop_safety_car_laps(result, race_control)

        # Always apply the slow-lap filter last, per race.
        result = drop_slow_laps(result)

        result["race"] = race

        print(f"  Cleaned laps: {len(result)}")

        cleaned_races.append(result)

    # Combine only after every race has been cleaned.
    combined = pd.concat(cleaned_races, ignore_index=True)

    # Validate all cleaned data before saving.
    run_checks(combined)

    # Save atomically.
    path = clean_path()
    save_clean(combined, path)

    print(f"\nSaved {len(combined)} cleaned laps to {path}")

    return combined
