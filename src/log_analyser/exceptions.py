class LogAnalyserError(Exception):
    """Base exception for log analyser errors."""


class LogFileNotFoundError(LogAnalyserError):
    """Raised when the requested log file does not exist."""


class LogFileReadError(LogAnalyserError):
    """Raised when the log file cannot be read."""


class InvalidLogFileError(LogAnalyserError):
    """Raised when the supplied log file is invalid."""
