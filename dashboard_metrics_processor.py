#!/usr/bin/env python3
"""Dashboard Metrics Processing System - Main Entry Point."""

import logging
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Simple logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point for dashboard metrics processing."""
    try:
        logger.info("🚀 Starting dashboard metrics processing")

        # Import and run the metrics service
        from dashboard_analytics.metrics_service import process_dashboard_metrics

        # Run metrics processing
        process_dashboard_metrics()

        logger.info("✅ Dashboard metrics processing completed successfully!")

    except Exception as e:
        logger.error(f"❌ Processing failed: {e}")
        raise


if __name__ == "__main__":
    main()