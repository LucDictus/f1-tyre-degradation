import argparse

from tyredeg import clean, ingest


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="tyredeg")

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    subparsers.add_parser("ingest")
    subparsers.add_parser("analyze")

    args = parser.parse_args(argv)

    if args.command == "ingest":
        ingest.run()
    elif args.command == "analyze":
        clean.run()


if __name__ == "__main__":
    main()
