import json

import pandas as pd

from tyredeg.ingest import raw_path


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
