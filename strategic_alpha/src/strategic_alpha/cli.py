import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description="Strategic Alpha CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run analysis for a ticker")
    run_parser.add_argument("--ticker", default="NVDA", help="Ticker symbol")

    args = parser.parse_args()
    if args.command == "run":
        print(f"[demo] Running analysis for {args.ticker} ...")


if __name__ == "__main__":
    main()
