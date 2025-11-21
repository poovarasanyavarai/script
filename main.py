#!/usr/bin/env python3
"""
Main entry point for chatbot metrics processing cron job.
Processes chatbot metrics and conversation data for dashboard analytics.
"""

import logging
import sys
from datetime import datetime, timedelta, timezone
from typing import Optional

from dashboard_analytics.insert_metrics import insert_metrics, insert_chatbot_conversations

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/tmp/chatbot_metrics.log')
    ]
)
logger = logging.getLogger(__name__)


def parse_reference_date(reference_date: str) -> datetime:
    """
    Parse reference date string and return datetime object.

    Args:
        reference_date: "now", "yesterday", or "YYYY-MM-DD"

    Returns:
        datetime object in UTC

    Raises:
        ValueError: If date format is invalid
    """
    now = datetime.now(timezone.utc)

    if reference_date.lower() == "now":
        return now
    elif reference_date.lower() == "yesterday":
        return now - timedelta(days=1)
    else:
        try:
            return datetime.fromisoformat(reference_date).replace(tzinfo=timezone.utc)
        except ValueError as e:
            raise ValueError(f"Invalid reference_date '{reference_date}'. Expected format: YYYY-MM-DD") from e


def main(reference_date: str = "now") -> None:
    """
    Main function to process chatbot metrics and conversations.

    Args:
        reference_date: Reference date for processing ("now", "yesterday", or "YYYY-MM-DD")
    """
    try:
        ref_datetime = parse_reference_date(reference_date)
        logger.info(f"Starting chatbot metrics processing for reference time: {ref_datetime.isoformat()}")

        # Process metrics
        logger.info("Processing chatbot metrics...")
        insert_metrics(ref_datetime)
        logger.info("Chatbot metrics processing completed successfully")

        # # Process conversations
        # logger.info("Processing chatbot conversations...")
        # insert_chatbot_conversations(ref_datetime)
        # logger.info("Chatbot conversation processing completed successfully")

        # logger.info("All processing completed successfully")

    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during processing: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    reference_date = sys.argv[1] if len(sys.argv) > 1 else "now"
    main(reference_date)
