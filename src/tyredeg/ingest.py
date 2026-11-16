import json
import tempfile
import time
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from tyredeg.config import BASE_URL, ENDPOINTS, SESSIONS

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"


def create_session() -> requests.Session:
    """Create an HTTP session with retries for temporary API errors."""
    retry = Retry(
        total=3,
        connect=3,
        read=3,
        status=3,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        respect_retry_after_header=True,
    )

    adapter = HTTPAdapter(max_retries=retry)

    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    return session


def raw_path(race: str, endpoint: str) -> Path:
    """Build the deterministic path for one race and endpoint."""
    return RAW_DIR / race / f"{endpoint}.json"


def fetch_endpoint(
    session: requests.Session,
    endpoint: str,
    session_key: int,
) -> list[dict]:
    """Fetch all records for one endpoint and session."""
    url = f"{BASE_URL}/{endpoint}"

    response = session.get(
        url,
        params={"session_key": session_key},
        timeout=30,
    )
    response.raise_for_status()

    data = response.json()

    if not isinstance(data, list):
        raise TypeError(f"Expected a list from {endpoint}, got {type(data).__name__}")

    if not data:
        raise ValueError(f"Received an empty response from {endpoint}")

    return data


def save_raw(records: list[dict], path: Path) -> None:
    """Save raw records atomically as JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)

    tmp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            suffix=".json",
            dir=path.parent,
            delete=False,
        ) as tmp_file:
            tmp_path = Path(tmp_file.name)

        with tmp_path.open("w", encoding="utf-8") as file:
            json.dump(records, file, indent=2, ensure_ascii=False)

        tmp_path.replace(path)

    finally:
        if tmp_path is not None and tmp_path.exists():
            tmp_path.unlink()


def print_race_summary(
    race: str,
    session_results: list[dict],
    stints: list[dict],
) -> None:
    """Print winner lap count and stint counts per compound."""
    print(f"\n{race}")

    winner = next(result for result in session_results if int(result["position"]) == 1)

    print(f"Winner: {winner['driver_number']} — {int(winner['number_of_laps'])} laps")

    print("Stints per compound:")

    counts = {}

    for stint in stints:
        compound = stint.get("compound") or "UNKNOWN"
        counts[compound] = counts.get(compound, 0) + 1

    for compound in sorted(counts):
        print(f"  {compound}: {counts[compound]}")


def run() -> None:
    """Fetch and save all configured races and endpoints."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    with create_session() as session:
        for race, session_key in SESSIONS.items():
            print(f"\nFetching {race} (session {session_key})")

            race_data = {}

            for endpoint in ENDPOINTS:
                records = fetch_endpoint(session, endpoint, session_key)

                # Save the API records unchanged: no joins or filtering.
                path = raw_path(race, endpoint)
                save_raw(records, path)

                race_data[endpoint] = records

                print(f"  {endpoint}: {len(records)} rows saved to {path}")

                # Small pause between requests to be considerate of the API.
                time.sleep(0.2)

            print_race_summary(
                race,
                race_data["session_result"],
                race_data["stints"],
            )
