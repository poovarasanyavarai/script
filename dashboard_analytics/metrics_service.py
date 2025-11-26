"""Clean, simple metrics insertion following KISS and DRY principles."""

import json
import logging
from datetime import datetime

from dashboard_analytics.analytics_repository import (
    get_feedback_stats_by_chatbot,
    get_language_distribution,
    get_feedback_by_channel,
    get_conversations,
)
from dashboard_analytics.database_connection import get_connection

# Setup logger
logger = logging.getLogger(__name__)


# Static data structures for dashboard analytics
STATIC_FB_GEO = [
    {"country": "India", "percentage": "85", "country_code": "IN"},
    {"country": "USA", "percentage": "90", "country_code": "US"}
]

STATIC_PERFORM_BY_GEO = {
    "dots": [
        {"lat": 13.0843, "lng": 80.2705, "country": "Tamilnadu",
         "code": "IN", "interactions": 80000},
        {"lat": 45.5122, "lng": -122.6587, "country": "Portland",
         "code": "US", "interactions": 58000},
        {"lat": 44.9778, "lng": -93.265, "country": "Minneapolis",
         "code": "US", "interactions": 62000},
        {"lat": 39.9526, "lng": -75.1652, "country": "Philadelphia",
         "code": "US", "interactions": 85000}
    ],
    "countryPerformance": [
        {"country": "USA", "interactions": 120000, "code": "US"},
        {"country": "Indonesia", "interactions": 80000, "code": "IN"},
        {"country": "United Kingdom", "interactions": 40000, "code": "GB"},
        {"country": "Sri Lanka", "interactions": 30000, "code": "LK"}
    ]
}

STATIC_ALERTS = [
    {"time": "1 hr ago", "message": "ABC Bot fallback rate hit 22%", "severity": "high"},
    {"time": "1 hr ago", "message": "Handovers spiked 20% showing automation losing ground in peak hours", "severity": "medium"},
    {"time": "1 hr ago", "message": "Queue delay persists: 12 users waiting over 5 minutes in XYZ Bot", "severity": "high"},
    {"time": "1 hr ago", "message": "9 out of 10 chats in ABC Bot had positive sentiment this week", "severity": "low"},
    {"time": "1 hr ago", "message": "Positive sentiment steady at 90% in ABC Bot this week", "severity": "low"},
    {"time": "1 hr ago", "message": "ABC Bot fallback rate remains elevated at 22%", "severity": "medium"},
    {"time": "1 hr ago", "message": "Human handovers surged 20% during peak hours", "severity": "medium"},
    {"time": "1 hr ago", "message": "Queue still blocked and unresolved in XYZ Bot", "severity": "high"},
    {"time": "45 min ago", "message": "Response time increased by 15% in support bot", "severity": "medium"},
    {"time": "30 min ago", "message": "Drop detected in conversation volume across all bots", "severity": "low"},
    {"time": "25 min ago", "message": "Average handle time exceeded SLA limit by 10%", "severity": "high"},
    {"time": "20 min ago", "message": "Bot accuracy dropped to 85% during live sessions", "severity": "medium"},
    {"time": "10 min ago", "message": "Human takeover ratio increased to 25%", "severity": "medium"},
    {"time": "5 min ago", "message": "XYZ Bot outage detected — unable to process requests", "severity": "critical"}
]

STATIC_TRENDS = [
    {"time": "1 hr ago", "message": "Fallback rate in ABC Bot stable at 22%", "severity": "medium"},
    {"time": "1 hr ago", "message": "Human handovers increased 20% during peak time", "severity": "medium"},
    {"time": "1 hr ago", "message": "Queue delay trending upward: average wait >5 min", "severity": "high"},
    {"time": "1 hr ago", "message": "Positive sentiment steady at 90%", "severity": "low"},
    {"time": "1 hr ago", "message": "Automation efficiency dropped 20% during rush hours", "severity": "medium"},
    {"time": "1 hr ago", "message": "User satisfaction holding steady at 90%", "severity": "low"},
    {"time": "45 min ago", "message": "Average response time rose by 15% this hour", "severity": "medium"},
    {"time": "30 min ago", "message": "Engagement rate dipped 10% during non-peak hours", "severity": "low"},
    {"time": "25 min ago", "message": "Resolution rate improved to 88% across all bots", "severity": "low"},
    {"time": "20 min ago", "message": "Fallback rate trending downward — improvement noted", "severity": "low"},
    {"time": "15 min ago", "message": "Customer satisfaction index up by 5% this week", "severity": "low"},
    {"time": "10 min ago", "message": "Queue backlog cleared 80% faster after system optimization", "severity": "low"},
    {"time": "5 min ago", "message": "Sentiment recovery detected — 3% rise in positive chats", "severity": "low"}
]


class MetricsProcessor:
    """Simple class to process metrics for chatbots."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.success_count = 0
        self.failure_count = 0

    def process_chatbot(self, chatbot, snapshot_time):
        """Process a single chatbot and return metrics data."""
        chatbot_id = chatbot.get("id")
        name = chatbot.get("name", "Unknown")

        try:
            self.logger.info(f"Processing chatbot: {name}")

            # Get all required data
            conversations = self._get_conversation_data(chatbot_id)
            feedback_stats = get_feedback_stats_by_chatbot(chatbot_id)
            languages = get_language_distribution(chatbot_id)
            feedback_channel = get_feedback_by_channel(chatbot_id, snapshot_time)

            # Build metrics record
            metrics = {
                "snapshot_time": snapshot_time,
                "chatbot_id": chatbot_id,
                "name": name,
                "total_conversations": conversations.get("total_conversations", 0),
                "feedback_total": feedback_stats["feedback_total"],
                "feedback_pos": feedback_stats["feedback_pos"],
                "feedback_neg": feedback_stats["feedback_neg"],
                "feedback_avg": feedback_stats["feedback_avg"],
                "languages": json.dumps(languages),
                "fb_channel": json.dumps(feedback_channel),
                "ai_csat": self._calculate_csat(feedback_stats),
                # Static data fields for dashboard
                "fb_geo": json.dumps(STATIC_FB_GEO),
                "perform_by_geo": json.dumps(STATIC_PERFORM_BY_GEO),
                "alerts": json.dumps(STATIC_ALERTS),
                "trends": json.dumps(STATIC_TRENDS),
                # Additional calculated metrics
                "net_impact": self._calculate_net_impact(feedback_stats),
                "automation_rate": self._calculate_automation_rate(conversations),
            }

            self.success_count += 1
            self.logger.info(f"✅ Successfully processed: {name}")
            return metrics

        except Exception as e:
            self.failure_count += 1
            self.logger.error(f"❌ Failed to process {name}: {str(e)}")
            return None

    def _get_conversation_data(self, chatbot_id):
        """Get conversation data for a chatbot."""
        conversations = get_conversations()
        conv_map = {c.get("chatbot_id"): c for c in conversations}
        return conv_map.get(chatbot_id, {})

    def _calculate_csat(self, feedback_stats):
        """Calculate CSAT score from feedback stats."""
        total = feedback_stats["feedback_total"]
        positive = feedback_stats["feedback_pos"]
        return (positive / total * 100) if total > 0 else 0

    def _calculate_net_impact(self, feedback_stats):
        """Calculate net impact score from feedback."""
        total = feedback_stats["feedback_total"]
        positive = feedback_stats["feedback_pos"]
        negative = feedback_stats["feedback_neg"]

        if total == 0:
            return 0

        # Net impact = (Positive - Negative) / Total * 100
        net_score = ((positive - negative) / total) * 100
        return round(net_score, 2)

    def _calculate_automation_rate(self, conversations):
        """Calculate automation rate based on conversations."""
        total_conv = conversations.get("total_conversations", 0)

        if total_conv == 0:
            return 0

        # Assuming 75% automation rate as default (can be customized)
        # This can be calculated based on human handovers vs total conversations
        automation_rate = 75.0  # Default rate
        return round(automation_rate, 2)

    def save_to_database(self, metrics_list):
        """Save metrics to database."""
        if not metrics_list:
            self.logger.warning("No metrics to save")
            return

        conn = get_connection()
        try:
            cursor = conn.cursor()

            for metrics in metrics_list:
                self._insert_metrics_record(cursor, metrics)

            conn.commit()
            self.logger.info(f"✅ Successfully saved {len(metrics_list)} records")

        except Exception as e:
            conn.rollback()
            self.logger.error(f"❌ Database error: {str(e)}")
            raise

        finally:
            cursor.close()
            conn.close()

    def _insert_metrics_record(self, cursor, metrics):
        """Insert a single metrics record."""
        sql = """
            INSERT INTO chatbot_metrics (
                snapshot_time, chatbot_id, name, total_coversation,
                feedback_total, feedback_pos, feedback_neg, feedback_avg,
                languages, fb_channel, ai_csat, fb_geo, perform_by_geo,
                alerts, trends, net_impact, automation_rate
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (
            metrics["snapshot_time"], metrics["chatbot_id"], metrics["name"],
            metrics["total_conversations"], metrics["feedback_total"],
            metrics["feedback_pos"], metrics["feedback_neg"], metrics["feedback_avg"],
            metrics["languages"], metrics["fb_channel"], metrics["ai_csat"],
            metrics["fb_geo"], metrics["perform_by_geo"], metrics["alerts"],
            metrics["trends"], metrics["net_impact"], metrics["automation_rate"]
        ))

    def log_summary(self, total_chatbots):
        """Log processing summary."""
        self.logger.info("=" * 50)
        self.logger.info("METRICS PROCESSING SUMMARY")
        self.logger.info("=" * 50)
        self.logger.info(f"Total chatbots: {total_chatbots}")
        self.logger.info(f"Successful: {self.success_count}")
        self.logger.info(f"Failed: {self.failure_count}")

        if total_chatbots > 0:
            success_rate = (self.success_count / total_chatbots) * 100
            self.logger.info(f"Success rate: {success_rate:.1f}%")

        self.logger.info("=" * 50)


def process_dashboard_metrics(ref_datetime=None):
    """Main function to insert metrics for all chatbots."""
    processor = MetricsProcessor()
    snapshot_time = ref_datetime or datetime.now()

    try:
        logger.info("Starting metrics insertion")

        # Get chatbots (simplified - using hardcoded account for now)
        from dashboard_analytics.config_query import query_records
        account_ids = ["86c3cb12-d1d1-5a0e-ab58-3230ec9fe11f"]
        chatbots = []
        for acc_id in account_ids:
            chatbots.extend(query_records("chatbots", "account_id", acc_id))

        # Process each chatbot
        metrics_list = []
        for chatbot in chatbots:
            metrics = processor.process_chatbot(chatbot, snapshot_time)
            if metrics:
                metrics_list.append(metrics)

        # Save to database
        if metrics_list:
            processor.save_to_database(metrics_list)

        # Log summary
        processor.log_summary(len(chatbots))
        logger.info("✅ Metrics insertion completed")

        print(f"Successfully processed {processor.success_count} out of {len(chatbots)} chatbots.")

    except Exception as e:
        logger.error(f"❌ Metrics insertion failed: {str(e)}")
        raise