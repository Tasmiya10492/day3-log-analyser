# Day 3 – Log Analyser

## Project Overview

The Log Analyser is a Python command-line application that reads application log files, analyses their contents, and generates a JSON summary.

It handles malformed log entries safely. Invalid lines are counted and reported through logging without stopping the analysis.

## Features

- Reads application log files.
- Parses timestamps, log levels, and messages.
- Counts log entries by level.
- Identifies the most frequent error messages.
- Calculates the earliest and latest log timestamps.
- Counts and reports malformed lines.
- Generates a JSON summary.
- Uses type hints, dataclasses, and custom exceptions.
- Includes automated tests using pytest.

## Project Structure

```text
day3-log-analyser/
├── src/
│   └── log_analyser/
│       ├── __init__.py
│       ├── models.py
│       ├── exceptions.py
│       ├── analyser.py
│       └── cli.py
├── tests/
│   └── test_analyser.py
├── sample_logs/
│   └── application.log
├── pyproject.toml
└── README.md
```

## Requirements

- Python 3.14 or compatible version
- uv
- pytest
- Ruff
- Pyright

## Setup

Clone the repository and navigate into the project directory.

Create a virtual environment:

```bash
uv venv
```

Activate it on Linux or WSL:

```bash
source .venv/bin/activate
```

Install the project and development dependencies:

```bash
uv pip install -e ".[dev]"
```

## Run the Application

Run the analyser using the sample log file:

```bash
python -m log_analyser.cli sample_logs/application.log
```

By default, the JSON summary is saved to:

```text
output/summary.json
```

To specify a different output location:

```bash
python -m log_analyser.cli sample_logs/application.log --output results/summary.json
```

To change the number of top errors:

```bash
python -m log_analyser.cli sample_logs/application.log --top 3
```

## Run Tests

Run all automated tests:

```bash
pytest -v
```

## Code Quality Checks

Format the code:

```bash
ruff format .
```

Check linting:

```bash
ruff check .
```

Check types:

```bash
pyright
```

## Error Handling

Malformed log entries are counted and reported through Python logging. They do not stop the analysis.

Custom exceptions handle missing files, invalid file paths, and file-reading errors.

## Current Test Results

- 14 automated tests passed.
- Ruff checks passed.
- Pyright reported zero errors, warnings, and informations.

## Output

The application generates a JSON summary containing:

- Total lines
- Valid lines
- Malformed lines
- Counts by log level
- Top error messages
- Start and end timestamps
- Malformed line numbers
