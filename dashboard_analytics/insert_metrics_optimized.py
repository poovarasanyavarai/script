"""
Optimized metrics insertion module with clean structure and efficient database operations.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

import pycountry

from .config_query import get_settings, query_records
from .db_query_optimized import (
    get_feedback_stats_by_chatbot_optimized,
    get_language_distribution_optimized
)
from .db_connection import get_cursor

logger = logging.getLogger(__name__)


class StaticDataManager:
    """Manages static data for metrics."""

    @staticmethod
    def get_country_code(name: str) -> str:
        """Get ISO country code from country name."""
        try:
            country = pycountry.countries.lookup(name)
            return country.alpha_2
        except Exception:
            return "XX"

    @staticmethod
    def get_static_feedback_geo() -> List[Dict[str, Any]]:
        """Static feedback geo data."""
        return [
            {"country": "India", "percentage": "85", "country_code": "IN"},
            {"country": "USA", "percentage": "90", "country_code": "US"}
        ]

    @staticmethod
    def get_static_feedback_channel() -> List[Dict[str, Any]]:
        """Static feedback channel data."""
        return [
            {"channel": "whatsapp", "count": 100},
            {"channel": "facebook", "count": 80}
        ]

    @staticmethod
    def get_static_performance_geo() -> Dict[str, Any]:
        """Static performance geo data."""
        return {
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
                {"country": "Indonesia", "interactions": 80000, "code": "ID"},
                {"country": "United Kingdom", "interactions": 40000, "code": "GB"},
                {"country": "Sri Lanka", "interactions": 30000, "code": "LK"}
            ]
        }

    @staticmethod
    def get_static_alerts() -> List[Dict[str, Any]]:
        """Static alerts data."""
        return [
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
            {"time": "5 min ago", "message": "XYZ Bot outage detected — unable to process requests", "severity": "critical"},
        ]

    @staticmethod
    def get_static_trends() -> List[Dict[str, Any]]:
        """Static trends data."""
        return [
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
            {"time": "5 min ago", "message": "Sentiment recovery detected — 3% rise in positive chats", "severity": "low"},
        ]


class MetricsCalculator:
    """Calculates metrics differences and values."""

    @staticmethod
    def calculate_metrics_differences(current_values: Dict[str, int],
                                    previous_values: Dict[str, int]) -> Dict[str, int]:
        """Calculate differences between current and previous metrics."""
        return {
            key: current_values.get(key, 0) - previous_values.get(key, 0)
            for key in current_values.keys()
        }

    @staticmethod
    def get_previous_metrics(chatbot_id: str, snapshot_time: datetime) -> Dict[str, int]:
        """Get previous metrics for a chatbot."""
        try:
            with get_cursor() as cursor:
                cursor.execute("""
                    SELECT ai_resolved, human_resolved, total_coversation
                    FROM chatbot_metrics
                    WHERE chatbot_id = %s
                    AND snapshot_time <= %s
                    ORDER BY snapshot_time DESC
                    LIMIT 1
                """, (chatbot_id, snapshot_time))

                row = cursor.fetchone()
                if row:
                    return {
                        "ai_resolved": row["ai_resolved"] or 0,
                        "human_resolved": row["human_resolved"] or 0,
                        "total_conversation": row["total_coversation"] or 0
                    }
                return {"ai_resolved": 0, "human_resolved": 0, "total_conversation": 0}

        except Exception as e:
            logger.error(f"Error fetching previous metrics for chatbot {chatbot_id}: {e}")
            return {"ai_resolved": 0, "human_resolved": 0, "total_conversation": 0}


class MetricsInserter:
    """Handles insertion of chatbot metrics."""

    def __init__(self):
        self.static_data = StaticDataManager()
        self.calculator = MetricsCalculator()

    def _get_chatbots_for_accounts(self, account_ids: List[str]) -> List[Dict[str, Any]]:
        """Get all chatbots for given account IDs."""
        chatbots = []
        for acc_id in account_ids:
            chatbots.extend(query_records("chatbots", "account_id", acc_id))
        return chatbots

    def _prepare_metrics_data(self, chatbot: Dict[str, Any],
                            conversation_data: Dict[str, Any],
                            settings_map: Dict[str, Dict[str, Any]],
                            snapshot_time: datetime) -> Dict[str, Any]:
        """Prepare metrics data for a single chatbot."""
        chatbot_id = chatbot.get("id")
        cb_settings = settings_map.get(chatbot_id, {})

        # Current metrics
        total_conversation = conversation_data.get("total_conversations", 0)
        ai_resolved = total_conversation  # Assuming all are AI resolved for now
        human_resolved = 0

        # Get previous metrics
        prev_metrics = self.calculator.get_previous_metrics(chatbot_id, snapshot_time)

        # Calculate differences
        conversation_diff = total_conversation - prev_metrics["total_conversation"]
        ai_resolved_diff = ai_resolved - prev_metrics["ai_resolved"]
        human_resolved_diff = human_resolved - prev_metrics["human_resolved"]

        # Get feedback stats
        feedback_stats = get_feedback_stats_by_chatbot_optimized(chatbot_id, snapshot_time)

        # Get language distribution
        languages = get_language_distribution_optimized(chatbot_id, snapshot_time)

        # Platform data
        platform = conversation_data.get("conversation_via", {})

        # Prepare data
        return {
            "snapshot_time": snapshot_time,
            "chatbot_id": chatbot_id,
            "name": chatbot.get("name"),
            "profile_url": cb_settings.get("profile_image_url"),
            "bot_created_at": chatbot.get("created_at"),
            "languages": json.dumps(languages),
            "total_conversation": total_conversation,
            "conversation_diff": conversation_diff,
            "leads": 0,  # Static for now
            "leads_diff": 0,
            "platform": json.dumps(platform),
            "ai_resolved": ai_resolved,
            "human_resolved": human_resolved,
            "ai_resolved_diff": ai_resolved_diff,
            "human_resolved_diff": human_resolved_diff,
            "feedback_total": feedback_stats["feedback_total"],
            "feedback_pos": feedback_stats["feedback_pos"],
            "feedback_neg": feedback_stats["feedback_neg"],
            "feedback_avg": feedback_stats["feedback_avg"],
            "alerts": json.dumps(self.static_data.get_static_alerts()),
            "fb_geo": json.dumps(self.static_data.get_static_feedback_geo()),
            "fb_channel": json.dumps(self.static_data.get_static_feedback_channel()),
            "trends": json.dumps(self.static_data.get_static_trends()),
            "net_impact": 20,
            "net_impact_graph": json.dumps({"ai": 14, "human": 12, "percentage": 30}),
            "perform_by_geo": json.dumps(self.static_data.get_static_performance_geo())
        }

    def insert_metrics(self, ref_datetime: Optional[datetime] = None) -> None:
        """
        Insert chatbot metrics with optimized queries and clean structure.
        """
        if ref_datetime is None:
            snapshot_time = datetime.now(timezone.utc)
        else:
            snapshot_time = ref_datetime

        # Hardcoded account ID for now
        account_ids = ["86c3cb12-d1d1-5a0e-ab58-3230ec9fe11f"]

        try:
            logger.info("Starting metrics insertion process")

            # Get chatbots
            chatbots = self._get_chatbots_for_accounts(account_ids)
            logger.info(f"Found {len(chatbots)} chatbots to process")

            # Get settings and conversation data
            settings_list = get_settings()
            from .db_query_optimized import get_conversations
            conversation_list = get_conversations(snapshot_time)

            settings_map = {s.get("chatbot_id"): s for s in settings_list}
            conv_map = {c.get("chatbot_id"): c for c in conversation_list}

            # Process in batches for better performance
            batch_size = 100
            metrics_data = []

            for i, chatbot in enumerate(chatbots):
                chatbot_id = chatbot.get("id")
                conversation_data = conv_map.get(chatbot_id, {})

                metrics_data.append(
                    self._prepare_metrics_data(chatbot, conversation_data, settings_map, snapshot_time)
                )

                # Insert in batches
                if len(metrics_data) >= batch_size or i == len(chatbots) - 1:
                    self._insert_metrics_batch(metrics_data)
                    metrics_data = []
                    logger.info(f"Processed {i + 1}/{len(chatbots)} chatbots")

            logger.info("Metrics insertion completed successfully")

        except Exception as e:
            logger.error(f"Error during metrics insertion: {e}")
            raise

    def _insert_metrics_batch(self, metrics_data: List[Dict[str, Any]]) -> None:
        """Insert a batch of metrics data."""
        if not metrics_data:
            return

        with get_cursor() as cursor:
            # Use executemany for batch insertion
            sql = """
                INSERT INTO chatbot_metrics (
                    snapshot_time, chatbot_id, name, profile_url, bot_created_at,
                    languages, total_coversation, coversation_diff, leads, leads_diff, platform,
                    ai_resolved, human_resolved, ai_resolved_diff, human_resolved_diff,
                    feedback_total, feedback_pos, feedback_neg, feedback_avg, alerts, fb_geo, fb_channel,
                    trends, net_impact, net_impact_graph, perform_by_geo
                )
                VALUES (%(snapshot_time)s, %(chatbot_id)s, %(name)s, %(profile_url)s, %(bot_created_at)s,
                       %(languages)s, %(total_conversation)s, %(conversation_diff)s, %(leads)s, %(leads_diff)s, %(platform)s,
                       %(ai_resolved)s, %(human_resolved)s, %(ai_resolved_diff)s, %(human_resolved_diff)s,
                       %(feedback_total)s, %(feedback_pos)s, %(feedback_neg)s, %(feedback_avg)s, %(alerts)s, %(fb_geo)s, %(fb_channel)s,
                       %(trends)s, %(net_impact)s, %(net_impact_graph)s, %(perform_by_geo)s)
            """

            cursor.executemany(sql, metrics_data)


# Global instances
_static_data = StaticDataManager()
_metrics_inserter = MetricsInserter()


def insert_metrics(ref_datetime: Optional[datetime] = None) -> None:
    """
    Main function to insert chatbot metrics.

    Args:
        ref_datetime: Reference datetime for metrics calculation
    """
    _metrics_inserter.insert_metrics(ref_datetime)


def insert_chatbot_conversations_optimized(ref_datetime: Optional[datetime] = None) -> None:
    """
    Optimized conversation insertion with batched operations.
    """
    if ref_datetime is None:
        snapshot_time = datetime.now(timezone.utc)
    else:
        snapshot_time = ref_datetime

    # Hardcoded account ID for now
    account_ids = ["86c3cb12-d1d1-5a0e-ab58-3230ec9fe11f"]

    try:
        logger.info("Starting conversation insertion process")

        # Get chatbots
        chatbots = []
        for acc_id in account_ids:
            chatbots.extend(query_records("chatbots", "account_id", acc_id))

        logger.info(f"Found {len(chatbots)} chatbots for conversation processing")

        total_inserted = 0
        batch_size = 500
        conversation_batch = []

        for chatbot in chatbots:
            chatbot_id = chatbot.get("id")
            chatbot_name = chatbot.get("name")

            from .db_query_optimized import get_conversations_for_chatbot_optimized, \
                batch_get_conversation_summaries, get_customer_by_conversation_optimized

            conversations = get_conversations_for_chatbot_optimized(chatbot_id, snapshot_time)
            conversation_ids = [conv.get("id") for conv in conversations]

            # Batch fetch summaries and customers
            summaries_map = batch_get_conversation_summaries(conversation_ids)
            customers_map = {}

            for conv_id in conversation_ids:
                customer = get_customer_by_conversation_optimized(conv_id, snapshot_time)
                if customer:
                    customers_map[conv_id] = customer

            # Prepare conversation records
            for conv in conversations:
                conversation_id = conv.get("id")
                summary_record = summaries_map.get(conversation_id)
                query_summary = (summary_record or {}).get("title") or "AI interaction with z-assist"

                customer = customers_map.get(conversation_id)
                channel = conv.get("conversation_via") or "Unknown"

                # Get language name
                language_name = None
                language_id = conv.get("language_id")
                if language_id:
                    language_record = get_record_by_id("languages", str(language_id))
                    language_name = language_record.get("name") if language_record else None

                conversation_data = {
                    "chatbot_id": chatbot_id,
                    "query": query_summary,
                    "customer_name": customer.get("name") if customer else None,
                    "ticket_number": "TICKET-AI",
                    "channel": channel,
                    "status": "success",
                    "contact": customer.get("email") if customer else None,
                    "city": customer.get("city") if customer else None,
                    "region": customer.get("region") if customer else None,
                    "agent": json.dumps([{
                        "name": "AI",
                        "profile_image": "https://zagentstoragedev94f5525a.blob.core.windows.net/data-connector-hub/welcome_avatar.svg?se=2045-10-19T07%3A53%3A48Z&sp=r&spr=https&sv=2025-11-05&sr=b&rscd=inline%3B%20filename%3Dwelcome_avatar.svg&rsct=image/svg%2Bxml&sig=ByHRzENC9L21IrmuEJ%2BhU4zbCfq%2Bqf4n8KTbOH3/a0Y%3D"
                    }]),
                    "language_selected": language_name,
                    "last_updated": conv.get("updated_at"),
                    "conversation_id": conversation_id
                }

                conversation_batch.append(conversation_data)
                total_inserted += 1

                # Insert in batches
                if len(conversation_batch) >= batch_size:
                    _insert_conversation_batch(conversation_batch)
                    conversation_batch = []

            # Insert remaining batch
            if conversation_batch:
                _insert_conversation_batch(conversation_batch)

        logger.info(f"Inserted {total_inserted} conversation records across {len(chatbots)} chatbots")

    except Exception as e:
        logger.error(f"Error during conversation insertion: {e}")
        raise


def _insert_conversation_batch(conversation_batch: List[Dict[str, Any]]) -> None:
    """Insert a batch of conversation data."""
    if not conversation_batch:
        return

    with get_cursor() as cursor:
        sql = """
            INSERT INTO chatbot_conversation (
                chatbot_id, query, customer_name, ticket_number, channel, status,
                contact, city, region, agent, language_selected, last_updated, conversation_id
            )
            VALUES (%(chatbot_id)s, %(query)s, %(customer_name)s, %(ticket_number)s, %(channel)s, %(status)s,
                   %(contact)s, %(city)s, %(region)s, %(agent)s, %(language_selected)s, %(last_updated)s, %(conversation_id)s)
        """

        cursor.executemany(sql, conversation_batch)


# Export functions for backward compatibility
insert_chatbot_conversations = insert_chatbot_conversations_optimized