import argparse


def main(argv: list[str] | None = None) -> None:
    # 1. Create the argument parser
    parser = argparse.ArgumentParser(prog="tyredeg")

    # 2. Create subcommands
    subparsers = parser.add_subparsers(dest="command", required=True)

    # 3. Register commands
    subparsers.add_parser("ingest")
    subparsers.add_parser("analyze")

    # 4. Parse arguments
    args = parser.parse_args(argv)

    # 5. Execute the selected command
    if args.command == "ingest":
        print("Ingesting F1 tyre data...")

    elif args.command == "analyze":
        print("Analyzing F1 tyre degradation...")
