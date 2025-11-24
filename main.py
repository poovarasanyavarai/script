#!/usr/bin/env python3
"""Chatbot metrics processing script with clean, efficient architecture."""

import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Final

from dashboard_analytics.insert_metrics import insert_metrics


# Constants
LOG_FORMAT: Final = "%(asctime)s - %(levelname)s - %(message)s"
DEFAULT_LOG_FILE: Final = "/tmp/chatbot_metrics.log"


def setup_logging(log_file: str = DEFAULT_LOG_FILE) -> logging.Logger:
    """Configure logging with console and file handlers."""
    logger = logging.getLogger(__name__)

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(LOG_FORMAT)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


def parse_date(reference_date: str) -> datetime:
    """Parse reference date string to datetime object."""
    now = datetime.now(timezone.utc)
    date_str = reference_date.lower().strip()

    # Relative dates
    if date_str == "now":
        return now
    elif date_str == "yesterday":
        return now - timedelta(days=1)
    elif date_str.startswith("yesterday-"):
        try:
            days = int(date_str.split("-")[1])
            return now - timedelta(days=days + 1)
        except (IndexError, ValueError):
            raise ValueError(f"Invalid format: {reference_date}. Use 'yesterday-N'")

    # ISO and standard formats
    formats = [None, "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"]

    for fmt in formats:
        try:
            if fmt is None:
                return datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
            return datetime.strptime(date_str, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue

    raise ValueError(f"Invalid date: {reference_date}. Use 'now', 'yesterday[-N]', or 'YYYY-MM-DD'")


def process_with_logging(operation, reference_time: datetime, logger: logging.Logger) -> None:
    """Execute operation with consistent error handling and logging."""
    try:
        logger.info(f"Starting {operation.__name__}")
        operation(reference_time)
        logger.info(f"Completed {operation.__name__}")
    except Exception as e:
        logger.error(f"Error in {operation.__name__}: {e}", exc_info=True)
        raise


def show_help() -> None:
    """Display usage information."""
    print("""Usage: python main.py [reference_date]

Arguments:
    reference_date    Reference date for processing (default: "now")
                     Options: "now", "yesterday", "yesterday-N", "YYYY-MM-DD"

Examples:
    python main.py           # Current time
    python main.py yesterday # Yesterday
    python main.py 2024-01-15 # Specific date""")


def main() -> None:
    """Main entry point."""
    logger = setup_logging()

    # Handle command line arguments
    if len(sys.argv) > 1 and sys.argv[1].lower() in ('-h', '--help'):
        show_help()
        return

    reference_date = sys.argv[1] if len(sys.argv) > 1 else "now"

    try:
        reference_time = parse_date(reference_date)
        logger.info(f"Processing for: {reference_time.isoformat()}")

        # Process metrics
        process_with_logging(insert_metrics, reference_time, logger)

        # Conversations currently disabled

        logger.info("Processing completed successfully")

    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
