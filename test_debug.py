#!/usr/bin/env python3

import sys
import os
import traceback

# Add the dashboard_analytics directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'dashboard_analytics'))

from metrics_service import MetricsProcessor

def test_single_chatbot():
    """Test processing a single chatbot to isolate the error."""
    print("Testing single chatbot processing...")

    try:
        processor = MetricsProcessor()

        # Just process one chatbot for debugging
        chatbots = processor.get_chatbot_list()
        if not chatbots:
            print("No chatbots found")
            return

        # Get first chatbot
        chatbot = chatbots[0]
        print(f"Processing chatbot: {chatbot}")

        # Process just this one chatbot
        metrics_list = []
        metrics = processor.get_chatbot_metrics(chatbot)

        if metrics:
            metrics_list.append(metrics)
            print(f"Successfully got metrics for {chatbot}")
            print(f"Metrics keys: {list(metrics.keys())}")

            # Try to save to database
            try:
                processor.save_to_database(metrics_list)
                print("Successfully saved to database")
            except Exception as e:
                print(f"Error saving to database: {e}")
                traceback.print_exc()
        else:
            print(f"Failed to get metrics for {chatbot}")

    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_single_chatbot()