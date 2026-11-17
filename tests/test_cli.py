import pytest

from tyredeg import cli


def test_ingest_command(monkeypatch):
    called = []

    def fake_run():
        called.append(True)

    monkeypatch.setattr(cli.ingest, "run", fake_run)

    cli.main(["ingest"])

    assert called == [True]


def test_analyze_command(monkeypatch):
    called = []

    def fake_run():
        called.append(True)

    monkeypatch.setattr(cli.clean, "run", fake_run)

    cli.main(["analyze"])

    assert called == [True]


def test_unknown_command():
    with pytest.raises(SystemExit):
        cli.main(["unknown"])


def test_missing_command():
    with pytest.raises(SystemExit):
        cli.main([])
