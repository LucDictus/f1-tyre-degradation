import pytest

from tyredeg import cli


def test_ingest_command(monkeypatch):
    called = []

    def fake_run():
        called.append(True)

    monkeypatch.setattr(cli.ingest, "run", fake_run)

    cli.main(["ingest"])

    assert called == [True]


def test_analyze_command(capsys):
    cli.main(["analyze"])

    captured = capsys.readouterr()

    assert captured.out == "Analyzing F1 tyre degradation...\n"


def test_unknown_command():
    with pytest.raises(SystemExit):
        cli.main(["unknown"])


def test_missing_command():
    with pytest.raises(SystemExit):
        cli.main([])
