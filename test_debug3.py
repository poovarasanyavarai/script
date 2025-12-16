#!/usr/bin/env python3

import sys
import os
import traceback
import json

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

from dashboard_analytics.metrics_service import MetricsProcessor, query_records, get_settings, get_conversations
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
        settings_list = get_settings()
        conversation_list = get_conversations()
        settings_map = {s.get("chatbot_id"): s for s in settings_list}
        conv_map = {c.get("chatbot_id"): c for c in conversation_list}

        metrics = processor.process_chatbot(chatbot, snapshot_time, settings_map, conv_map)

        if metrics:
            print(f"\nSuccessfully got metrics for {metrics.get('name', 'Unknown')}")
            print(f"Metrics has {len(metrics)} keys")

            # Check all required keys exist
            required_keys = [
                "snapshot_time", "chatbot_id", "name", "profile_url", "bot_created_at",
                "languages", "total_coversation", "coversation_diff", "leads", "leads_diff",
                "platform", "ai_resolved", "human_resolved", "ai_resolved_diff",
                "human_resolved_diff", "feedback_total", "feedback_pos", "feedback_neg",
                "feedback_avg", "ai_csat", "alerts", "fb_geo", "fb_channel",
                "trends", "net_impact", "net_impact_graph", "perform_by_geo"
            ]

            all_keys_present = True
            for key in required_keys:
                if key not in metrics:
                    print(f"ERROR: Missing key in metrics: {key}")
                    all_keys_present = False
                else:
                    value = metrics[key]
                    # Check if JSON fields are properly serialized
                    if key in ["languages", "platform", "alerts", "fb_geo", "fb_channel", "trends", "net_impact_graph", "perform_by_geo"]:
                        if not isinstance(value, str):
                            print(f"ERROR: {key} should be a JSON string but is {type(value)}")
                            all_keys_present = False
                            # Try to fix it
                            metrics[key] = json.dumps(value)
                            print(f"Fixed: Converted {key} to JSON string")

            if all_keys_present:
                print("\n✓ All required keys are present in metrics dictionary")

                # Try to save to database
                try:
                    processor.save_to_database([metrics])
                    print("✓ Successfully saved to database")
                except IndexError as e:
                    print(f"\n❌ IndexError saving to database: {e}")
                    print("This might be a mismatch between the number of values and placeholders in SQL")

                    # Let's check what we're trying to insert
                    print("\nDebugging the INSERT values:")
                    values = (
                        metrics["snapshot_time"], metrics["chatbot_id"], metrics["name"],
                        metrics["profile_url"], metrics["bot_created_at"], metrics["languages"],
                        metrics["total_coversation"], metrics["coversation_diff"], metrics["leads"],
                        metrics["leads_diff"], metrics["platform"], metrics["ai_resolved"],
                        metrics["human_resolved"], metrics["ai_resolved_diff"], metrics["human_resolved_diff"],
                        metrics["feedback_total"], metrics["feedback_pos"], metrics["feedback_neg"],
                        metrics["feedback_avg"], metrics["ai_csat"], metrics["alerts"], metrics["fb_geo"],
                        metrics["fb_channel"], metrics["trends"], metrics["net_impact"],
                        metrics["net_impact_graph"], metrics["perform_by_geo"]
                    )
                    print(f"Number of values: {len(values)}")

                    traceback.print_exc()
                except Exception as e:
                    print(f"\n❌ Other error saving to database: {e}")
                    traceback.print_exc()
        else:
            print(f"Failed to get metrics")

    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_with_actual_data()