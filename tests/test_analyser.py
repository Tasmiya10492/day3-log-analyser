import json
from datetime import datetime
from pathlib import Path

import pytest

from log_analyser.analyser import analyse_log_file, parse_log_line
from log_analyser.cli import save_summary
from log_analyser.exceptions import LogFileNotFoundError


def test_parse_valid_log_line() -> None:
    entry = parse_log_line(
        "2026-10-30 09:15:20 INFO Application started",
        1,
    )

    assert entry.timestamp == datetime(2026, 10, 30, 9, 15, 20)
    assert entry.level == "INFO"
    assert entry.message == "Application started"
    assert entry.line_number == 1


def test_parse_log_line_with_message_spaces() -> None:
    entry = parse_log_line(
        "2026-10-30 09:15:20 ERROR Database connection failed",
        2,
    )

    assert entry.message == "Database connection failed"


def test_parse_invalid_log_format() -> None:
    with pytest.raises(ValueError, match="Invalid log line format"):
        parse_log_line("INVALID LOG ENTRY", 1)


def test_parse_invalid_timestamp() -> None:
    with pytest.raises(ValueError, match="Invalid timestamp"):
        parse_log_line(
            "invalid-date 09:15:20 INFO Application started",
            1,
        )


def test_parse_invalid_log_level() -> None:
    with pytest.raises(ValueError, match="Invalid log level"):
        parse_log_line(
            "2026-10-30 09:15:20 UNKNOWN Application started",
            1,
        )


def test_analyse_log_counts(tmp_path: Path) -> None:
    log_file = tmp_path / "application.log"

    log_file.write_text(
        "2026-10-30 09:15:20 INFO Started\n"
        "2026-10-30 09:16:20 ERROR Database failed\n"
        "2026-10-30 09:17:20 ERROR Database failed\n"
        "2026-10-30 09:18:20 WARNING Disk space low\n",
        encoding="utf-8",
    )

    summary = analyse_log_file(log_file)

    assert summary.total_lines == 4
    assert summary.valid_lines == 4
    assert summary.malformed_lines == 0
    assert summary.counts_by_level == {
        "ERROR": 2,
        "INFO": 1,
        "WARNING": 1,
    }


def test_analyse_malformed_lines(tmp_path: Path) -> None:
    log_file = tmp_path / "application.log"

    log_file.write_text(
        "2026-10-30 09:15:20 INFO Started\n"
        "INVALID LOG ENTRY\n"
        "2026-10-30 09:17:20 ERROR Database failed\n",
        encoding="utf-8",
    )

    summary = analyse_log_file(log_file)

    assert summary.total_lines == 3
    assert summary.valid_lines == 2
    assert summary.malformed_lines == 1
    assert summary.malformed_line_numbers == [2]


def test_analyse_top_errors(tmp_path: Path) -> None:
    log_file = tmp_path / "application.log"

    log_file.write_text(
        "2026-10-30 09:15:20 ERROR Database failed\n"
        "2026-10-30 09:16:20 ERROR Payment failed\n"
        "2026-10-30 09:17:20 ERROR Database failed\n"
        "2026-10-30 09:18:20 ERROR Database failed\n",
        encoding="utf-8",
    )

    summary = analyse_log_file(log_file, top_n=1)

    assert len(summary.top_errors) == 1
    assert summary.top_errors[0].message == "Database failed"
    assert summary.top_errors[0].count == 3


def test_analyse_time_range(tmp_path: Path) -> None:
    log_file = tmp_path / "application.log"

    log_file.write_text(
        "2026-10-30 09:20:00 INFO Later entry\n2026-10-30 09:10:00 INFO Earlier entry\n",
        encoding="utf-8",
    )

    summary = analyse_log_file(log_file)

    assert summary.start_time == datetime(2026, 10, 30, 9, 10, 0)
    assert summary.end_time == datetime(2026, 10, 30, 9, 20, 0)


def test_analyse_empty_file(tmp_path: Path) -> None:
    log_file = tmp_path / "empty.log"
    log_file.write_text("", encoding="utf-8")

    summary = analyse_log_file(log_file)

    assert summary.total_lines == 0
    assert summary.valid_lines == 0
    assert summary.malformed_lines == 0
    assert summary.start_time is None
    assert summary.end_time is None


def test_missing_log_file(tmp_path: Path) -> None:
    log_file = tmp_path / "missing.log"

    with pytest.raises(LogFileNotFoundError):
        analyse_log_file(log_file)


def test_invalid_top_n(tmp_path: Path) -> None:
    log_file = tmp_path / "application.log"
    log_file.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="top_n must be at least 1"):
        analyse_log_file(log_file, top_n=0)


def test_save_summary_as_json(tmp_path: Path) -> None:
    log_file = tmp_path / "application.log"

    log_file.write_text(
        "2026-10-30 09:15:20 INFO Application started\n"
        "2026-10-30 09:16:20 ERROR Database failed\n",
        encoding="utf-8",
    )

    summary = analyse_log_file(log_file)
    output_file = tmp_path / "output" / "summary.json"

    save_summary(summary, output_file)

    assert output_file.exists()

    saved_data = json.loads(output_file.read_text(encoding="utf-8"))

    assert saved_data["total_lines"] == 2
    assert saved_data["valid_lines"] == 2
    assert saved_data["malformed_lines"] == 0
    assert saved_data["counts_by_level"] == {
        "ERROR": 1,
        "INFO": 1,
    }


def test_save_summary_with_empty_file(tmp_path: Path) -> None:
    log_file = tmp_path / "empty.log"
    log_file.write_text("", encoding="utf-8")

    summary = analyse_log_file(log_file)
    output_file = tmp_path / "summary.json"

    save_summary(summary, output_file)

    saved_data = json.loads(output_file.read_text(encoding="utf-8"))

    assert saved_data["total_lines"] == 0
    assert saved_data["start_time"] is None
    assert saved_data["end_time"] is None
