"""Clean, production-ready metrics processing service for chatbot analytics."""

import json
import logging
from datetime import datetime

from dashboard_analytics.analytics_repository import (
    get_feedback_stats_by_chatbot,
    get_language_distribution,
    get_feedback_by_channel,
    get_conversations,
)
from dashboard_analytics.config_query import get_settings, query_records
from dashboard_analytics.database_connection import get_connection

logger = logging.getLogger(__name__)

# Static dashboard analytics data
STATIC_FB_GEO = [
    {"country": "India", "percentage": "85", "country_code": "IN"},
    {"country": "USA", "percentage": "90", "country_code": "US"}
]

STATIC_FB_CHANNEL = [
    {"channel": "whatsapp", "count": 100},
    {"channel": "facebook", "count": 80}
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
    """Efficient metrics processor for chatbot analytics."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.success_count = 0
        self.failure_count = 0

    def process_chatbot(self, chatbot, snapshot_time, settings_map, conv_map):
        """Process a single chatbot and return comprehensive metrics."""
        chatbot_id = chatbot.get("id")
        name = chatbot.get("name", "Unknown")

        try:
            self.logger.info(f"Processing chatbot: {name}")

            # Get chatbot-specific data
            cb_settings = settings_map.get(chatbot_id, {})
            cb_conversation = conv_map.get(chatbot_id, {})

            # Extract core data
            total_conversations = cb_conversation.get("total_conversations", 0)
            profile_url = cb_settings.get("profile_image_url")
            bot_created_at = chatbot.get("created_at")

            # Get analytics data
            languages = get_language_distribution(chatbot_id)
            feedback_stats = get_feedback_stats_by_chatbot(chatbot_id)
            feedback_channel = get_feedback_by_channel(chatbot_id, snapshot_time)

            # Calculate conversation metrics
            ai_resolved = total_conversations
            human_resolved = 0

            # Get previous metrics for diff calculations
            prev_metrics = self._get_previous_metrics(chatbot_id, snapshot_time)
            conversation_diff = total_conversations - (prev_metrics.get("total_coversation", 0) or 0)
            ai_resolved_diff = ai_resolved - (prev_metrics.get("ai_resolved", 0) or 0)
            human_resolved_diff = human_resolved - (prev_metrics.get("human_resolved", 0) or 0)

            # Build metrics record
            metrics = {
                "snapshot_time": snapshot_time,
                "chatbot_id": chatbot_id,
                "name": name,
                "profile_url": profile_url,
                "bot_created_at": bot_created_at,
                "languages": json.dumps(languages),
                "total_coversation": total_conversations,
                "coversation_diff": conversation_diff,
                "leads": 0,
                "leads_diff": 0,
                "platform": json.dumps(cb_conversation.get("conversation_via", {})),
                "ai_resolved": ai_resolved,
                "human_resolved": human_resolved,
                "ai_resolved_diff": ai_resolved_diff,
                "human_resolved_diff": human_resolved_diff,
                "feedback_total": feedback_stats["feedback_total"],
                "feedback_pos": feedback_stats["feedback_pos"],
                "feedback_neg": feedback_stats["feedback_neg"],
                "feedback_avg": feedback_stats["feedback_avg"],
                "ai_csat": self._calculate_csat(feedback_stats),
                "alerts": json.dumps(STATIC_ALERTS),
                "fb_geo": json.dumps(STATIC_FB_GEO),
                "fb_channel": json.dumps(feedback_channel or STATIC_FB_CHANNEL),
                "trends": json.dumps(STATIC_TRENDS),
                "net_impact": self._calculate_net_impact(feedback_stats),
                "net_impact_graph": json.dumps({"ai": 14, "human": 12, "percentage": 30}),
                "perform_by_geo": json.dumps(STATIC_PERFORM_BY_GEO),
            }

            self.success_count += 1
            self.logger.info(f"✅ Successfully processed: {name}")
            return metrics

        except Exception as e:
            self.failure_count += 1
            self.logger.error(f"❌ Failed to process {name}: {str(e)}")
            return None

    def _get_previous_metrics(self, chatbot_id, snapshot_time):
        """Retrieve previous metrics for calculating differences."""
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT ai_resolved, human_resolved, total_coversation
                FROM chatbot_metrics
                WHERE chatbot_id = %s AND snapshot_time <= %s
                ORDER BY snapshot_time DESC LIMIT 1
                """,
                (chatbot_id, snapshot_time)
            )
            prev = cursor.fetchone()
            cursor.close()
            conn.close()

            if prev:
                return {
                    "ai_resolved": prev[0],
                    "human_resolved": prev[1],
                    "total_coversation": prev[2]
                }
            return {"ai_resolved": 0, "human_resolved": 0, "total_coversation": 0}

        except Exception as e:
            self.logger.warning(f"Could not get previous metrics: {e}")
            return {"ai_resolved": 0, "human_resolved": 0, "total_coversation": 0}

    def _calculate_csat(self, feedback_stats):
        """Calculate Customer Satisfaction (CSAT) score."""
        total = feedback_stats["feedback_total"]
        positive = feedback_stats["feedback_pos"]
        logger.info(f"##@@@## ai CSAT {positive}/{total} * 100")
        return (positive / total * 100) if total > 0 else 0

    def _calculate_net_impact(self, feedback_stats):
        """Calculate net impact score from feedback data."""
        total = feedback_stats["feedback_total"]
        positive = feedback_stats["feedback_pos"]

        if total == 0:
            return 0

        net_score = positive / total * 100
        return round(net_score, 2)

    def save_to_database(self, metrics_list):
        """Save processed metrics to database efficiently."""
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

        """Insert a complete metrics record into database."""
        sql = """
            INSERT INTO chatbot_metrics (
                chatbot_id, name, profile_url, bot_created_at,
                languages, total_coversation, coversation_diff, leads, leads_diff, platform,
                ai_resolved, human_resolved, ai_resolved_diff, human_resolved_diff,
                feedback_total, feedback_pos, feedback_neg, feedback_avg, ai_csat, human_csat,
                alerts, fb_geo, fb_channel, trends, net_impact, net_impact_graph, perform_by_geo,
                active_status, ongoing_calls, in_queue, unresolved
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (
            metrics["chatbot_id"], metrics["name"],
            metrics["profile_url"], metrics["bot_created_at"], metrics["languages"],
            metrics["total_coversation"], metrics["coversation_diff"], metrics["leads"],
            metrics["leads_diff"], metrics["platform"], metrics["ai_resolved"],
            metrics["human_resolved"], metrics["ai_resolved_diff"], metrics["human_resolved_diff"],
            metrics["feedback_total"], metrics["feedback_pos"], metrics["feedback_neg"],
            metrics["feedback_avg"], metrics["ai_csat"], metrics["ai_csat"],  # human_csat same as ai_csat
            metrics["alerts"], metrics["fb_geo"], metrics["fb_channel"],
            metrics["trends"], metrics["net_impact"],
            metrics["net_impact_graph"], metrics["perform_by_geo"],
            True, 0, 0, 0  # active_status, ongoing_calls, in_queue, unresolved
        ))

    def log_summary(self, total_chatbots):
        """Log processing summary with success metrics."""
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
    """Main function to process dashboard metrics for all chatbots."""
    processor = MetricsProcessor()
    snapshot_time = ref_datetime or datetime.now()

    try:
        logger.info("🚀 Starting dashboard metrics processing")

        # Get all chatbots from multiple accounts
        account_ids = ["86c3cb12-d1d1-5a0e-ab58-3230ec9fe11f", "8e9a3514-c5e8-52e7-842d-cb4e2a0a0cdb"]
        chatbots = []
        for acc_id in account_ids:
            chatbots.extend(query_records("chatbots", "account_id", acc_id))

        # Pre-fetch settings and conversations for efficiency
        settings_list = get_settings()
        conversation_list = get_conversations()
        print(conversation_list,"###########")
        settings_map = {s.get("chatbot_id"): s for s in settings_list}
        conv_map = {c.get("chatbot_id"): c for c in conversation_list}

        # Process all chatbots
        metrics_list = []
        for chatbot in chatbots:
            metrics = processor.process_chatbot(chatbot, snapshot_time, settings_map, conv_map)
            if metrics:
                metrics_list.append(metrics)

        # Save to database
        if metrics_list:
            processor.save_to_database(metrics_list)

        # Log final summary
        processor.log_summary(len(chatbots))
        logger.info("✅ Metrics processing completed successfully")
        print(f"Successfully processed {processor.success_count} out of {len(chatbots)} chatbots.")

    except Exception as e:
        logger.error(f"❌ Metrics processing failed: {str(e)}")
        raise