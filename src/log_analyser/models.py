from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class LogEntry:
    """Represent one successfully parsed log entry."""

    timestamp: datetime
    level: str
    message: str
    line_number: int


@dataclass
class ErrorCount:
    """Represent an error message and its occurrence count."""

    message: str
    count: int


@dataclass
class AnalysisSummary:
    """Store the complete result of log file analysis."""

    total_lines: int = 0
    valid_lines: int = 0
    malformed_lines: int = 0

    counts_by_level: dict[str, int] = field(default_factory=dict)
    top_errors: list[ErrorCount] = field(default_factory=list)

    start_time: datetime | None = None
    end_time: datetime | None = None

    malformed_line_numbers: list[int] = field(default_factory=list)
