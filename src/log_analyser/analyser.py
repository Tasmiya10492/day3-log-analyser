import logging
from collections import Counter
from datetime import datetime
from pathlib import Path

from log_analyser.exceptions import (
    InvalidLogFileError,
    LogFileNotFoundError,
    LogFileReadError,
)
from log_analyser.models import (
    AnalysisSummary,
    ErrorCount,
    LogEntry,
)

logger = logging.getLogger(__name__)

TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


def parse_log_line(line: str, line_number: int) -> LogEntry:
    """Parse one log line and return a LogEntry."""

    parts = line.strip().split(maxsplit=3)

    if len(parts) != 4:
        raise ValueError("Invalid log line format")

    timestamp_text = f"{parts[0]} {parts[1]}"
    level = parts[2]
    message = parts[3]

    try:
        timestamp = datetime.strptime(timestamp_text, TIMESTAMP_FORMAT)
    except ValueError as error:
        raise ValueError("Invalid timestamp") from error

    if level not in VALID_LOG_LEVELS:
        raise ValueError("Invalid log level")

    if not message.strip():
        raise ValueError("Log message cannot be empty")

    return LogEntry(
        timestamp=timestamp,
        level=level,
        message=message,
        line_number=line_number,
    )


def analyse_log_file(
    file_path: Path,
    top_n: int = 5,
) -> AnalysisSummary:
    """Analyse a log file and return its summary."""

    if top_n < 1:
        raise ValueError("top_n must be at least 1")

    if not file_path.exists():
        raise LogFileNotFoundError(f"Log file not found: {file_path}")

    if not file_path.is_file():
        raise InvalidLogFileError(f"Path is not a file: {file_path}")

    summary = AnalysisSummary()
    log_levels: Counter[str] = Counter()
    errors: Counter[str] = Counter()
    timestamps: list[datetime] = []

    try:
        with file_path.open("r", encoding="utf-8") as log_file:
            for line_number, line in enumerate(log_file, start=1):
                summary.total_lines += 1

                if not line.strip():
                    summary.malformed_lines += 1
                    summary.malformed_line_numbers.append(line_number)
                    logger.warning(
                        "Malformed empty line at line %s",
                        line_number,
                    )
                    continue

                try:
                    entry = parse_log_line(line, line_number)
                except ValueError as error:
                    summary.malformed_lines += 1
                    summary.malformed_line_numbers.append(line_number)
                    logger.warning(
                        "Malformed log line %s: %s",
                        line_number,
                        error,
                    )
                    continue

                summary.valid_lines += 1
                log_levels[entry.level] += 1
                timestamps.append(entry.timestamp)

                if entry.level == "ERROR":
                    errors[entry.message] += 1

    except OSError as error:
        raise LogFileReadError(f"Unable to read log file: {file_path}") from error

    summary.counts_by_level = dict(sorted(log_levels.items()))

    summary.top_errors = [
        ErrorCount(message=message, count=count) for message, count in errors.most_common(top_n)
    ]

    if timestamps:
        summary.start_time = min(timestamps)
        summary.end_time = max(timestamps)

    logger.info(
        "Analysis completed: %s valid lines, %s malformed lines",
        summary.valid_lines,
        summary.malformed_lines,
    )

    return summary
