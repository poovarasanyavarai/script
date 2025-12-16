#!/usr/bin/env python3
"""
Performance comparison between original and optimized metrics processors.

This script runs both versions and compares:
- Processing time
- Memory usage
- Database efficiency
- Error rates
"""

import time
import logging
import sys
import psutil
import os
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def measure_memory_usage():
    """Get current memory usage in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024


def run_original_processor():
    """Run the original metrics processor and measure performance."""
    logger.info("Running original metrics processor...")

    start_memory = measure_memory_usage()
    start_time = time.time()

    try:
        # Import and run original processor
        from dashboard_analytics.metrics_service import process_dashboard_metrics

        # Run for a small subset to measure performance
        process_dashboard_metrics()

        success = True
        error = None
    except Exception as e:
        success = False
        error = str(e)

    end_time = time.time()
    end_memory = measure_memory_usage()

    return {
        'version': 'original',
        'success': success,
        'error': error,
        'duration': end_time - start_time,
        'memory_used': end_memory - start_memory,
        'peak_memory': end_memory
    }


def run_optimized_processor():
    """Run the optimized metrics processor and measure performance."""
    logger.info("Running optimized metrics processor...")

    start_memory = measure_memory_usage()
    start_time = time.time()

    try:
        # Import and run optimized processor
        from dashboard_analytics.metrics_service_optimized import process_dashboard_metrics_optimized

        # Run with optimized settings
        process_dashboard_metrics_optimized(max_workers=4)

        success = True
        error = None
    except Exception as e:
        success = False
        error = str(e)

    end_time = time.time()
    end_memory = measure_memory_usage()

    return {
        'version': 'optimized',
        'success': success,
        'error': error,
        'duration': end_time - start_time,
        'memory_used': end_memory - start_memory,
        'peak_memory': end_memory
    }


def compare_performance(original_results, optimized_results):
    """Compare performance metrics between versions."""
    print("\n" + "=" * 60)
    print("PERFORMANCE COMPARISON")
    print("=" * 60)

    print(f"\nOriginal Processor:")
    print(f"  Status: {'✅ Success' if original_results['success'] else '❌ Failed'}")
    if original_results['error']:
        print(f"  Error: {original_results['error']}")
    print(f"  Duration: {original_results['duration']:.2f} seconds")
    print(f"  Memory Used: {original_results['memory_used']:.2f} MB")
    print(f"  Peak Memory: {original_results['peak_memory']:.2f} MB")

    print(f"\nOptimized Processor:")
    print(f"  Status: {'✅ Success' if optimized_results['success'] else '❌ Failed'}")
    if optimized_results['error']:
        print(f"  Error: {optimized_results['error']}")
    print(f"  Duration: {optimized_results['duration']:.2f} seconds")
    print(f"  Memory Used: {optimized_results['memory_used']:.2f} MB")
    print(f"  Peak Memory: {optimized_results['peak_memory']:.2f} MB")

    # Calculate improvements
    if original_results['success'] and optimized_results['success']:
        speed_improvement = ((original_results['duration'] - optimized_results['duration'])
                            / original_results['duration'] * 100)
        memory_improvement = ((original_results['memory_used'] - optimized_results['memory_used'])
                             / original_results['memory_used'] * 100) if original_results['memory_used'] > 0 else 0

        print(f"\n🚀 Performance Improvements:")
        print(f"  Speed Improvement: {speed_improvement:.1f}% faster")
        print(f"  Memory Efficiency: {memory_improvement:.1f}% less memory")

        if speed_improvement > 0:
            print(f"  Time Saved: {original_results['duration'] - optimized_results['duration']:.2f} seconds")

    print("\n" + "=" * 60)


def main():
    """Main execution function."""
    print("Starting performance comparison...")
    print(f"Python version: {sys.version}")
    print(f"System info: {os.name} - {psutil.cpu_count()} CPUs")
    print(f"Initial memory: {measure_memory_usage():.2f} MB")

    # Run original processor
    original_results = run_original_processor()

    # Wait a bit between runs
    time.sleep(2)

    # Run optimized processor
    optimized_results = run_optimized_processor()

    # Compare results
    compare_performance(original_results, optimized_results)


if __name__ == "__main__":
    main()