import pytest

from tyredeg.cli import main


def test_ingest_command(capsys):
    main(["ingest"])

    captured = capsys.readouterr()

    assert captured.out == "Ingesting F1 tyre data...\n"


def test_unknown_command():
    with pytest.raises(SystemExit):
        main(["unknown"])
