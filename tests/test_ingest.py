import json

import pytest
import requests
import responses

from tyredeg import ingest
from tyredeg.config import BASE_URL
from tyredeg.ingest import (
    create_session,
    fetch_endpoint,
    raw_path,
    save_raw,
)


@responses.activate
def test_fetch_endpoint_success():
    with create_session() as session:
        responses.add(
            responses.GET,
            f"{BASE_URL}/laps",
            json=[
                {
                    "session_key": 10014,
                    "driver_number": 1,
                    "lap_number": 1,
                    "lap_duration": 92.5,
                }
            ],
            status=200,
        )

        result = fetch_endpoint(session, "laps", 10014)

    assert len(result) == 1
    assert result[0]["driver_number"] == 1
    assert result[0]["lap_duration"] == 92.5


@responses.activate
def test_fetch_endpoint_retries_after_429():
    url = f"{BASE_URL}/laps"

    with create_session() as session:
        responses.add(
            responses.GET,
            url,
            json={"detail": "Too many requests"},
            status=429,
        )

        responses.add(
            responses.GET,
            url,
            json=[{"driver_number": 1, "lap_number": 1}],
            status=200,
        )

        result = fetch_endpoint(session, "laps", 10014)

    assert len(result) == 1
    assert result[0]["driver_number"] == 1
    assert len(responses.calls) == 2


@responses.activate
def test_fetch_endpoint_raises_for_http_error():
    with (
        create_session() as session,
        responses.RequestsMock() as mock,
    ):
        mock.add(
            responses.GET,
            f"{BASE_URL}/laps",
            status=400,
        )

        with pytest.raises(requests.HTTPError):
            fetch_endpoint(session, "laps", 10014)


@responses.activate
def test_fetch_endpoint_rejects_empty_response():
    with create_session() as session:
        responses.add(
            responses.GET,
            f"{BASE_URL}/laps",
            json=[],
            status=200,
        )

        with pytest.raises(
            ValueError,
            match="Received an empty response from laps",
        ):
            fetch_endpoint(session, "laps", 10014)


@responses.activate
def test_fetch_endpoint_rejects_non_list_response():
    with create_session() as session:
        responses.add(
            responses.GET,
            f"{BASE_URL}/laps",
            json={"error": "Invalid response"},
            status=200,
        )

        with pytest.raises(
            TypeError,
            match="Expected a list from laps",
        ):
            fetch_endpoint(session, "laps", 10014)


def test_raw_path():
    path = raw_path("2025_bahrain", "laps")

    assert path.name == "laps.json"
    assert path.parent.name == "2025_bahrain"


def test_save_raw(tmp_path):
    records = [
        {"driver_number": 1, "lap_number": 1},
        {"driver_number": 1, "lap_number": 2},
    ]

    path = tmp_path / "2025_bahrain" / "laps.json"

    save_raw(records, path)

    assert path.exists()

    with path.open(encoding="utf-8") as file:
        loaded = json.load(file)

    assert loaded == records


def test_save_raw_is_atomic_when_write_fails(tmp_path, monkeypatch):
    records = [
        {"driver_number": 1, "lap_number": 1},
    ]

    path = tmp_path / "2025_bahrain" / "laps.json"
    path.parent.mkdir(parents=True)

    old_records = [{"driver_number": 99, "lap_number": 10}]
    path.write_text(json.dumps(old_records), encoding="utf-8")

    def failing_dump(records, file, **kwargs):
        file.write("[")
        raise OSError("Simulated write failure")

    monkeypatch.setattr(ingest.json, "dump", failing_dump)

    with pytest.raises(OSError, match="Simulated write failure"):
        save_raw(records, path)

    # The original file must still contain its original data.
    with path.open(encoding="utf-8") as file:
        assert json.load(file) == old_records

    # The failed temporary file must have been removed.
    assert list(path.parent.iterdir()) == [path]
