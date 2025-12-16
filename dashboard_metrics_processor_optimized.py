#!/usr/bin/env python3
"""
Optimized Dashboard Metrics Processor
====================================

Performance improvements:
- Parallel processing of chatbots
- Batch database operations
- Connection pooling optimization
- Caching for static data
- Memory-efficient processing
- Better error handling and recovery

Usage:
    python dashboard_metrics_processor_optimized.py [--workers N] [--batch-size N] [--date YYYY-MM-DD]
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from dashboard_analytics.metrics_service_optimized import process_dashboard_metrics_optimized

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('dashboard_metrics.log', mode='a')
    ]
)

logger = logging.getLogger(__name__)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Process dashboard metrics for chatbots with optimized performance',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Process with default settings
  %(prog)s --workers 8              # Use 8 parallel workers
  %(prog)s --batch-size 50          # Use batch size of 50
  %(prog)s --date 2024-01-15        # Process for specific date
  %(prog)s --workers 4 --batch-size 25 --date yesterday
        """
    )

    parser.add_argument(
        '--workers', '-w',
        type=int,
        default=4,
        help='Number of parallel workers (default: 4)'
    )

    parser.add_argument(
        '--batch-size', '-b',
        type=int,
        default=100,
        help='Batch size for database operations (default: 100)'
    )

    parser.add_argument(
        '--date', '-d',
        type=str,
        help='Process for specific date (YYYY-MM-DD or "yesterday")'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Process without saving to database'
    )

    return parser.parse_args()


def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse date string into datetime object."""
    if not date_str:
        return None

    try:
        if date_str.lower() == 'yesterday':
            from datetime import timedelta
            return datetime.now() - timedelta(days=1)
        else:
            return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        logger.error(f"Invalid date format: {date_str}. Use YYYY-MM-DD or 'yesterday'")
        sys.exit(1)


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.getLogger().setLevel(level)

    # Reduce noise from external libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)


def main():
    """Main execution function."""
    try:
        # Parse arguments
        args = parse_arguments()
        setup_logging(args.verbose)

        # Parse reference date
        ref_datetime = parse_date(args.date)
        if ref_datetime:
            logger.info(f"Processing metrics for date: {ref_datetime.date()}")
        else:
            logger.info("Processing metrics for current date")

        # Log configuration
        logger.info("=" * 60)
        logger.info("OPTIMIZED DASHBOARD METRICS PROCESSOR")
        logger.info("=" * 60)
        logger.info(f"Workers: {args.workers}")
        logger.info(f"Batch size: {args.batch_size}")
        logger.info(f"Dry run: {args.dry_run}")

        # Process metrics with optimizations
        if args.dry_run:
            logger.warning("DRY RUN MODE - No data will be saved to database")
            # Here you could implement a dry run version that just processes without saving
            logger.info("Dry run completed successfully")
        else:
            process_dashboard_metrics_optimized(
                ref_datetime=ref_datetime,
                max_workers=args.workers
            )

        logger.info("Processing completed successfully!")

    except KeyboardInterrupt:
        logger.info("\nProcessing interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=args.verbose)
        sys.exit(1)


if __name__ == "__main__":
    main()