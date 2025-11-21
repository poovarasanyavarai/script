"""
Optimized database query module with efficient connection management and batched operations.
"""

import logging
from collections import Counter
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from .config_query import get_record_by_id
from .db_connection import get_cursor, get_connection_context

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """Helper class for optimizing database queries with batching and caching."""

    def __init__(self):
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid."""
        if cache_key not in self._cache:
            return False

        cached_time, _ = self._cache[cache_key]
        return (datetime.now() - cached_time).total_seconds() < self._cache_ttl

    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """Get data from cache if valid."""
        if self._is_cache_valid(cache_key):
            _, data = self._cache[cache_key]
            return data
        return None

    def _set_cache(self, cache_key: str, data: Any) -> None:
        """Set data in cache with timestamp."""
        self._cache[cache_key] = (datetime.now(), data)


# Global optimizer instance
_optimizer = QueryOptimizer()


def get_conversations(ref_datetime: Optional[datetime] = None) -> List[Dict[str, Any]]:
    """
    Optimized version: Fetch conversation counts per chatbot with platform breakdown.
    Uses proper connection management and optimized SQL with CTEs.
    """
    try:
        start_time = ref_datetime - timedelta(days=1) if ref_datetime else None

        with get_cursor() as cursor:
            # Use CTE for better performance
            query = """
                WITH conversation_stats AS (
                    SELECT
                        chatbot_id,
                        conversation_via,
                        COUNT(*) AS count,
                        COUNT(*) OVER (PARTITION BY chatbot_id) as total_per_chatbot
                    FROM conversations
                    WHERE deleted_at IS NULL
                      AND created_at >= %s
                    GROUP BY chatbot_id, conversation_via
                )
                SELECT
                    chatbot_id,
                    conversation_via,
                    count,
                    total_per_chatbot,
                    SUM(count) OVER (PARTITION BY chatbot_id) as chatbot_total
                FROM conversation_stats
                ORDER BY chatbot_id, conversation_via;
            """

            cursor.execute(query, (start_time or (datetime.now() - timedelta(days=1)),))
            rows = cursor.fetchall()

        # Efficient data processing using dictionary comprehension
        chatbot_data = {}
        for row in rows:
            cb_id = row["chatbot_id"]
            if cb_id not in chatbot_data:
                chatbot_data[cb_id] = {
                    "chatbot_id": cb_id,
                    "total_conversations": row["chatbot_total"],
                    "conversation_via": {}
                }

            chatbot_data[cb_id]["conversation_via"][row["conversation_via"]] = row["count"]

        return list(chatbot_data.values())

    except Exception as e:
        logger.error(f"Error fetching conversation data: {e}")
        return []


def get_customers_by_chatbot_optimized(chatbot_id: str, ref_datetime: Optional[datetime] = None,
                                     limit: int = 1000) -> List[Dict[str, Any]]:
    """
    Optimized version: Fetch customer details with proper indexing and batched queries.
    """
    try:
        cache_key = f"customers_{chatbot_id}_{ref_datetime.isoformat() if ref_datetime else 'all'}"
        cached_data = _optimizer._get_from_cache(cache_key)
        if cached_data:
            return cached_data

        start_time = ref_datetime - timedelta(days=1) if ref_datetime else None

        with get_cursor() as cursor:
            # Optimized query with proper joins and indexing
            query = """
                SELECT
                    c.customer_id,
                    c.name,
                    c.email,
                    c.city,
                    c.region,
                    c.country,
                    c.conversation_id,
                    conv.chatbot_id,
                    conv.created_at as conv_created_at
                FROM customers c
                INNER JOIN conversations conv ON c.conversation_id = conv.id
                WHERE conv.chatbot_id = %s
                  AND c.deleted_at IS NULL
                  AND conv.deleted_at IS NULL
            """

            params = [chatbot_id]
            if start_time:
                query += " AND conv.created_at >= %s"
                params.append(start_time)
            else:
                query += " AND conv.created_at >= NOW() - INTERVAL '1 day'"

            query += " ORDER BY conv.created_at DESC LIMIT %s"
            params.append(limit)

            cursor.execute(query, params)
            customers = [dict(row) for row in cursor.fetchall()]

        _optimizer._set_cache(cache_key, customers)
        return customers

    except Exception as e:
        logger.error(f"Error fetching customers for chatbot {chatbot_id}: {e}")
        return []


def get_interactions_by_conversation_batch(conversation_ids: List[str],
                                         ref_datetime: Optional[datetime] = None) -> Dict[str, int]:
    """
    Optimized version: Batch fetch interaction counts with proper indexing.
    """
    if not conversation_ids:
        return {}

    try:
        cache_key = f"interactions_{hash(tuple(conversation_ids))}_{ref_datetime.isoformat() if ref_datetime else 'all'}"
        cached_data = _optimizer._get_from_cache(cache_key)
        if cached_data:
            return cached_data

        start_time = ref_datetime - timedelta(days=1) if ref_datetime else None

        with get_cursor() as cursor:
            # Use ANY for efficient batch processing
            query = """
                SELECT cm.conversation_id, COUNT(*) as interactions
                FROM chat_messages cm
                WHERE cm.conversation_id = ANY(%s)
                  AND cm.deleted_at IS NULL
            """

            params = [conversation_ids]
            if start_time:
                query += " AND cm.created_at >= %s"
                params.append(start_time)
            else:
                query += " AND cm.created_at >= NOW() - INTERVAL '1 day'"

            query += " GROUP BY cm.conversation_id"
            cursor.execute(query, params)

            rows = cursor.fetchall()
            interaction_map = {str(row["conversation_id"]): row["interactions"] for row in rows}

        _optimizer._set_cache(cache_key, interaction_map)
        return interaction_map

    except Exception as e:
        logger.error(f"Error fetching interactions: {e}")
        return {}


def get_feedback_stats_by_chatbot_optimized(chatbot_id: str,
                                          ref_datetime: Optional[datetime] = None) -> Dict[str, int]:
    """
    Optimized version: Use COUNT with CASE for better performance.
    """
    try:
        cache_key = f"feedback_{chatbot_id}_{ref_datetime.isoformat() if ref_datetime else 'all'}"
        cached_data = _optimizer._get_from_cache(cache_key)
        if cached_data:
            return cached_data

        start_time = ref_datetime - timedelta(days=1) if ref_datetime else None

        with get_cursor() as cursor:
            # Single query with conditional aggregation
            query = """
                SELECT
                    COUNT(*) as feedback_total,
                    COUNT(CASE WHEN UPPER(cm.reaction) = 'LIKE' THEN 1 END) as feedback_pos,
                    COUNT(CASE WHEN UPPER(cm.reaction) = 'DISLIKE' THEN 1 END) as feedback_neg
                FROM chat_messages cm
                INNER JOIN conversations conv ON cm.conversation_id = conv.id
                WHERE conv.chatbot_id = %s
                  AND cm.deleted_at IS NULL
                  AND conv.deleted_at IS NULL
                  AND cm.reaction IS NOT NULL
            """

            params = [chatbot_id]
            if start_time:
                query += " AND cm.created_at >= %s"
                params.append(start_time)
            else:
                query += " AND cm.created_at >= NOW() - INTERVAL '1 day'"

            cursor.execute(query, params)
            row = cursor.fetchone()

        result = {
            "feedback_total": row["feedback_total"] if row else 0,
            "feedback_pos": row["feedback_pos"] if row else 0,
            "feedback_neg": row["feedback_neg"] if row else 0,
            "feedback_avg": 0
        }

        _optimizer._set_cache(cache_key, result)
        return result

    except Exception as e:
        logger.error(f"Error fetching feedback for chatbot {chatbot_id}: {e}")
        return {"feedback_total": 0, "feedback_pos": 0, "feedback_neg": 0, "feedback_avg": 0}


def get_language_distribution_optimized(chatbot_id: str,
                                      ref_datetime: Optional[datetime] = None) -> Dict[str, int]:
    """
    Optimized version: Fetch language distribution with efficient counting and batched language name resolution.
    """
    try:
        start_time = ref_datetime - timedelta(days=1) if ref_datetime else None

        with get_cursor() as cursor:
            # Optimized query for language counting
            query = """
                SELECT language_id, COUNT(*) as count
                FROM conversations
                WHERE chatbot_id = %s
                  AND deleted_at IS NULL
                  AND language_id IS NOT NULL
            """

            params = [chatbot_id]
            if start_time:
                query += " AND created_at >= %s"
                params.append(start_time)
            else:
                query += " AND created_at >= NOW() - INTERVAL '1 day'"

            query += " GROUP BY language_id"
            cursor.execute(query, params)

            lang_counts = {row["language_id"]: row["count"] for row in cursor.fetchall()}

        if not lang_counts:
            return {}

        # Batch fetch language names
        lang_distribution = {}
        for lang_id, count in lang_counts.items():
            lang_record = get_record_by_id("languages", str(lang_id))
            lang_name = lang_record.get("name") if lang_record else f"Lang-{lang_id}"
            lang_distribution[lang_name] = count

        return lang_distribution

    except Exception as e:
        logger.error(f"Error fetching language distribution for chatbot {chatbot_id}: {e}")
        return {}


def get_conversations_for_chatbot_optimized(chatbot_id: str,
                                          ref_datetime: Optional[datetime] = None,
                                          limit: int = 5000) -> List[Dict[str, Any]]:
    """
    Optimized version: Fetch conversations with proper pagination and field selection.
    """
    try:
        start_time = ref_datetime - timedelta(days=1) if ref_datetime else None

        with get_cursor() as cursor:
            # Select only necessary fields for performance
            query = """
                SELECT
                    id, conversation_id, chatbot_id, customer_id, language_id,
                    conversation_via, status, created_at, updated_at
                FROM conversations
                WHERE chatbot_id = %s
                  AND deleted_at IS NULL
            """

            params = [chatbot_id]
            if start_time:
                query += " AND updated_at >= %s"
                params.append(start_time)
            else:
                query += " AND updated_at >= NOW() - INTERVAL '1 day'"

            query += " ORDER BY updated_at DESC LIMIT %s"
            params.append(limit)

            cursor.execute(query, params)
            conversations = [dict(row) for row in cursor.fetchall()]

        return conversations

    except Exception as e:
        logger.error(f"Error fetching conversations for chatbot {chatbot_id}: {e}")
        return []


def get_customer_by_conversation_optimized(conversation_id: str,
                                         ref_datetime: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
    """
    Optimized version: Fetch customer with proper connection management.
    """
    try:
        cache_key = f"customer_{conversation_id}_{ref_datetime.isoformat() if ref_datetime else 'all'}"
        cached_data = _optimizer._get_from_cache(cache_key)
        if cached_data:
            return cached_data

        start_time = ref_datetime - timedelta(days=1) if ref_datetime else None

        with get_cursor() as cursor:
            query = """
                SELECT customer_id, name, email, phone, city, region, country, conversation_id
                FROM customers
                WHERE conversation_id = %s
                  AND deleted_at IS NULL
            """

            params = [conversation_id]
            if start_time:
                query += " AND updated_at >= %s"
                params.append(start_time)
            else:
                query += " AND updated_at >= NOW() - INTERVAL '1 day'"

            cursor.execute(query, params)
            row = cursor.fetchone()

            customer = dict(row) if row else None

        if customer:
            _optimizer._set_cache(cache_key, customer)
        return customer

    except Exception as e:
        logger.error(f"Error fetching customer for conversation {conversation_id}: {e}")
        return None


def get_conversation_summary_optimized(conversation_id: str,
                                     ref_datetime: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
    """
    Optimized version: Fetch conversation summary with caching.
    """
    try:
        cache_key = f"summary_{conversation_id}_{ref_datetime.isoformat() if ref_datetime else 'all'}"
        cached_data = _optimizer._get_from_cache(cache_key)
        if cached_data:
            return cached_data

        with get_cursor() as cursor:
            query = """
                SELECT title, updated_at
                FROM conversation_summaries
                WHERE conversation_id = %s
                ORDER BY updated_at DESC
                LIMIT 1
            """

            cursor.execute(query, (conversation_id,))
            row = cursor.fetchone()

            summary = {"title": row["title"]} if row else None

        if summary:
            _optimizer._set_cache(cache_key, summary)
        return summary

    except Exception as e:
        logger.error(f"Error fetching conversation summary for {conversation_id}: {e}")
        return None


# Batch operations for better performance
def batch_get_conversation_summaries(conversation_ids: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
    """
    Batch fetch multiple conversation summaries for efficiency.
    """
    if not conversation_ids:
        return {}

    try:
        with get_cursor() as cursor:
            query = """
                SELECT conversation_id, title, updated_at,
                       ROW_NUMBER() OVER (PARTITION BY conversation_id ORDER BY updated_at DESC) as rn
                FROM conversation_summaries
                WHERE conversation_id = ANY(%s)
            """
            cursor.execute(query, (conversation_ids,))

            summaries = {}
            for row in cursor.fetchall():
                if row["rn"] == 1:  # Only take the most recent summary
                    summaries[row["conversation_id"]] = {"title": row["title"]}

            # Ensure all requested IDs are in the result
            for conv_id in conversation_ids:
                if conv_id not in summaries:
                    summaries[conv_id] = None

            return summaries

    except Exception as e:
        logger.error(f"Error batch fetching conversation summaries: {e}")
        return {conv_id: None for conv_id in conversation_ids}