import argparse
import json
import logging
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from log_analyser.analyser import analyse_log_file
from log_analyser.exceptions import LogAnalyserError
from log_analyser.models import AnalysisSummary

logger = logging.getLogger(__name__)


def configure_logging() -> None:
    """Configure application logging."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )


def build_argument_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""

    parser = argparse.ArgumentParser(description="Analyse a log file and generate a JSON summary.")

    parser.add_argument(
        "input_file",
        type=Path,
        help="Path to the log file",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output/summary.json"),
        help="Path where the JSON summary will be saved",
    )

    parser.add_argument(
        "--top",
        type=int,
        default=5,
        help="Number of top errors to include",
    )

    return parser


def convert_datetime(value: datetime | None) -> str | None:
    """Convert datetime values into JSON-compatible strings."""

    if value is None:
        return None

    return value.strftime("%Y-%m-%d %H:%M:%S")


def save_summary(summary: AnalysisSummary, output_path: Path) -> None:
    """Save the analysis summary as a JSON file."""

    output_path.parent.mkdir(parents=True, exist_ok=True)

    summary_data: dict[str, object] = asdict(summary)

    summary_data["start_time"] = convert_datetime(summary.start_time)
    summary_data["end_time"] = convert_datetime(summary.end_time)

    with output_path.open("w", encoding="utf-8") as output_file:
        json.dump(summary_data, output_file, indent=4)

    logger.info("JSON summary saved to %s", output_path)


def main() -> int:
    """Run the log analyser command-line application."""

    configure_logging()

    parser = build_argument_parser()
    args = parser.parse_args()

    try:
        summary = analyse_log_file(args.input_file, args.top)
        save_summary(summary, args.output)

    except (LogAnalyserError, ValueError, OSError) as error:
        logger.error("Log analysis failed: %s", error)
        return 1

    logger.info("Log analysis completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
