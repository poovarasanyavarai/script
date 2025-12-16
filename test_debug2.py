#!/usr/bin/env python3

import sys
import os
import traceback

# Add the dashboard_analytics directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'dashboard_analytics'))

from metrics_service import MetricsProcessor, query_records
from datetime import datetime

def test_with_actual_data():
    """Test with actual data like the main function."""
    print("Testing with actual data...")

    try:
        # Get all chatbots from multiple accounts (like the main function)
        account_ids = ["86c3cb12-d1d1-5a0e-ab58-3230ec9fe11f", "8e9a3514-c5e8-52e7-842d-cb4e2a0a0cdb"]
        chatbots = []
        for acc_id in account_ids:
            chatbots.extend(query_records("chatbots", "account_id", acc_id))

        if not chatbots:
            print("No chatbots found")
            return

        # Get just the first chatbot
        chatbot = chatbots[0]
        print(f"Processing first chatbot: {chatbot.get('name', 'Unknown')}")

        processor = MetricsProcessor()
        snapshot_time = datetime.now()

        # Process just this one chatbot
        settings_list = processor.get_settings()
        conversation_list = processor.get_conversations()
        settings_map = {s.get("chatbot_id"): s for s in settings_list}
        conv_map = {c.get("chatbot_id"): c for c in conversation_list}

        metrics = processor.process_chatbot(chatbot, snapshot_time, settings_map, conv_map)

        if metrics:
            print(f"Successfully got metrics")
            print(f"Metrics has {len(metrics)} keys")
            print(f"Keys: {list(metrics.keys())}")

            # Check values before saving
            for key in ["snapshot_time", "chatbot_id", "name", "profile_url", "bot_created_at",
                       "languages", "total_coversation", "coversation_diff", "leads", "leads_diff",
                       "platform", "ai_resolved", "human_resolved", "ai_resolved_diff",
                       "human_resolved_diff", "feedback_total", "feedback_pos", "feedback_neg",
                       "feedback_avg", "ai_csat", "alerts", "fb_geo", "fb_channel",
                       "trends", "net_impact", "net_impact_graph", "perform_by_geo"]:
                if key not in metrics:
                    print(f"ERROR: Missing key in metrics: {key}")
                else:
                    print(f"✓ {key}: {type(metrics[key])}")

            # Try to save to database
            try:
                processor.save_to_database([metrics])
                print("Successfully saved to database")
            except IndexError as e:
                print(f"IndexError saving to database: {e}")
                traceback.print_exc()
            except Exception as e:
                print(f"Other error saving to database: {e}")
                traceback.print_exc()
        else:
            print(f"Failed to get metrics")

    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_with_actual_data()