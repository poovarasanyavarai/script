import psycopg2.extras
from collections import Counter
from datetime import datetime, timedelta
from psycopg2.extras import RealDictCursor

from .config_query import get_record_by_id
from .db_connection import get_connection


def get_conversations(ref_datetime=None):
    """
    Fetch conversation counts per chatbot with platform breakdown for the last 1 day.
    """
    try:
        conn = get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            start_time = ref_datetime - \
                timedelta(days=1) if ref_datetime else None
            if start_time:
                cursor.execute("""
                    SELECT
                        chatbot_id,
                        conversation_via,
                        COUNT(*) AS count
                    FROM conversations
                    WHERE deleted_at IS NULL
                      AND created_at >= %s
                    GROUP BY chatbot_id, conversation_via
                    ORDER BY chatbot_id;
                """, (start_time,))
            else:
                cursor.execute("""
                    SELECT
                        chatbot_id,
                        conversation_via,
                        COUNT(*) AS count
                    FROM conversations
                    WHERE deleted_at IS NULL
                      AND created_at >= NOW() - INTERVAL '1 day'
                    GROUP BY chatbot_id, conversation_via
                    ORDER BY chatbot_id;
                """)
            rows = cursor.fetchall()

        chatbot_data = {}
        for row in rows:
            cb_id = row["chatbot_id"]
            via = row["conversation_via"]
            count = row["count"]

            if cb_id not in chatbot_data:
                chatbot_data[cb_id] = {
                    "chatbot_id": cb_id,
                    "total_conversations": 0,
                    "conversation_via": {}
                }

            chatbot_data[cb_id]["conversation_via"][via] = count
            chatbot_data[cb_id]["total_conversations"] += count

        conn.close()
        return list(chatbot_data.values())

    except Exception as e:
        print(f"Error fetching conversation data: {e}")
        return []


def get_customers_by_chatbot(chatbot_id, ref_datetime=None):
    """
    Fetch customer details (country, region, city) for a specific chatbot
    for conversations in the last 1 day.
    Uses text comparison to avoid integer <-> uuid mismatches.
    """
    try:
        conn = get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            start_time = ref_datetime - \
                timedelta(days=1) if ref_datetime else None
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
                JOIN conversations conv
                    ON c.conversation_id::text = conv.conversation_id::text
                WHERE conv.chatbot_id = %s
                  AND c.deleted_at IS NULL
            """
            if start_time:
                query += " AND conv.created_at >= %s"
                cursor.execute(
                    query + " ORDER BY conv.created_at DESC LIMIT 1000;", (chatbot_id, start_time))
            else:
                query += " AND conv.created_at >= NOW() - INTERVAL '1 day'"
                cursor.execute(
                    query + " ORDER BY conv.created_at DESC LIMIT 1000;", (chatbot_id,))
            customers = cursor.fetchall()

        conn.close()
        return customers

    except Exception as e:
        print(f"Error fetching customers for chatbot {chatbot_id}: {e}")
        return []


def get_interactions_by_conversation(conversation_ids, ref_datetime=None):
    """
    Fetch number of interactions per conversation for given IDs in the last 1 day.
    Uses text comparison so conversation_ids can be mixed int/uuid as strings.
    Returns mapping with conversation_id as string -> interaction count.
    """
    if not conversation_ids:
        return {}
    try:
        # ensure list of strings
        conv_ids_text = [str(cid) for cid in conversation_ids]
        start_time = ref_datetime - timedelta(days=1) if ref_datetime else None

        conn = get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            if start_time:
                query = """
                    SELECT conversation_id::text AS conv_id_text, COUNT(*) as interactions
                    FROM chat_messages
                    WHERE conversation_id::text = ANY(%s)
                      AND created_at >= %s
                    GROUP BY conv_id_text;
                """
                cursor.execute(query, (conv_ids_text, start_time))
            else:
                query = """
                    SELECT conversation_id::text AS conv_id_text, COUNT(*) as interactions
                    FROM chat_messages
                    WHERE conversation_id::text = ANY(%s)
                      AND created_at >= NOW() - INTERVAL '1 day'
                    GROUP BY conv_id_text;
                """
                cursor.execute(query, (conv_ids_text,))
            rows = cursor.fetchall()

        conn.close()
        # return mapping with string keys
        return {row["conv_id_text"]: int(row["interactions"]) for row in rows}

    except Exception as e:
        print(f"Error fetching interactions: {e}")
        return {}


# def get_feedback_stats_by_chatbot(chatbot_id: str, ref_datetime=None):
#     """
#     Fetch feedback (reaction) stats for a chatbot from chat_messages:
#     - feedback_total: count of messages with a reaction
#     - feedback_pos: LIKE count
#     - feedback_neg: DISLIKE count
#     - feedback_avg: always 0 for now
#     """
#     try:
#         start_time = ref_datetime - timedelta(days=1) if ref_datetime else None
#         conn = get_connection()
#         with conn.cursor(cursor_factory=RealDictCursor) as cursor:
#             if start_time:
#                 cursor.execute("""
#                     SELECT cm.reaction
#                     FROM chat_messages cm
#                     JOIN conversations conv
#                       ON cm.conversation_id::text = conv.conversation_id::text
#                     WHERE conv.chatbot_id = %s
#                       AND cm.deleted_at IS NULL
#                       AND conv.deleted_at IS NULL
#                       AND cm.reaction IS NOT NULL
#                       AND cm.created_at >= %s;
#                 """, (chatbot_id, start_time))
#             else:
#                 cursor.execute("""
#                     SELECT cm.reaction
#                     FROM chat_messages cm
#                     JOIN conversations conv
#                       ON cm.conversation_id::text = conv.conversation_id::text
#                     WHERE conv.chatbot_id = %s
#                       AND cm.deleted_at IS NULL
#                       AND conv.deleted_at IS NULL
#                       AND cm.reaction IS NOT NULL
#                       AND cm.created_at >= NOW() - INTERVAL '1 day';
#                 """, (chatbot_id,))

#             rows = cursor.fetchall()

#         conn.close()

#         feedback_total = len(rows)
#         feedback_pos = sum(1 for r in rows if r["reaction"].upper() == "LIKE")
#         feedback_neg = sum(
#             1 for r in rows if r["reaction"].upper() == "DISLIKE")
#         feedback_avg = 0

#         return {
#             "feedback_total": feedback_total,
#             "feedback_pos": feedback_pos,
#             "feedback_neg": feedback_neg,
#             "feedback_avg": feedback_avg
#         }

#     except Exception as e:
#         print(f"Error fetching feedback for chatbot {chatbot_id}: {e}")
#         return {
#             "feedback_total": 0,
#             "feedback_pos": 0,
#             "feedback_neg": 0,
#             "feedback_avg": 0
#         }

def get_feedback_stats_by_chatbot(chatbot_id: str, ref_datetime=None):
    """
    Fetch feedback (reaction) stats for a chatbot from chat_messages:
    - feedback_total: count of messages with a reaction
    - feedback_pos: LIKE count
    - feedback_neg: DISLIKE count
    - feedback_avg: always 0 for now
    """
    try:
        # logger.info("get_feedback_stats_by_chatbot called")
        start_time = ref_datetime - timedelta(days=1) if ref_datetime else None
        conn = get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            if start_time:
                cursor.execute("""
                    SELECT cm.reaction
                    FROM chat_messages cm
                    JOIN conversations conv
                        ON cm.conversation_id = conv.id
                    WHERE conv.chatbot_id = %s
                      AND cm.deleted_at IS NULL
                      AND conv.deleted_at IS NULL
                      AND cm.reaction IS NOT NULL
                      AND cm.created_at >= %s;
                """, (chatbot_id, start_time))
            else:
                cursor.execute("""
                    SELECT cm.reaction
                    FROM chat_messages cm
                    JOIN conversations conv
                        ON cm.conversation_id = conv.id
                    WHERE conv.chatbot_id = %s
                      AND cm.deleted_at IS NULL
                      AND conv.deleted_at IS NULL
                      AND cm.reaction IS NOT NULL
                      AND cm.created_at >= NOW() - INTERVAL '1 day';
                """, (chatbot_id,))

            rows = cursor.fetchall()

        conn.close()

        feedback_total = len(rows)
        feedback_pos = sum(1 for r in rows if r["reaction"].upper() == "LIKE")
        feedback_neg = sum(1 for r in rows if r["reaction"].upper() == "DISLIKE")
        feedback_avg = 0

        return {
            "feedback_total": feedback_total,
            "feedback_pos": feedback_pos,
            "feedback_neg": feedback_neg,
            "feedback_avg": feedback_avg
        }

    except Exception as e:
        # logger.error(f"Error fetching feedback for chatbot {chatbot_id}: {e}")
        return {
            "feedback_total": 0,
            "feedback_pos": 0,
            "feedback_neg": 0,
            "feedback_avg": 0
        }

def get_language_distribution(chatbot_id: str, ref_datetime=None) -> dict:
    """
    Get the total number of conversations per language for a given chatbot.
    Example output: {"English": 23, "French": 2, "Spanish": 5}
    """
    try:
        start_time = ref_datetime - timedelta(days=1) if ref_datetime else None
        conn = get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            if start_time:
                cursor.execute("""
                    SELECT language_id
                    FROM conversations
                    WHERE chatbot_id = %s
                      AND deleted_at IS NULL
                      AND created_at >= %s;
                """, (chatbot_id, start_time))
            else:
                cursor.execute("""
                    SELECT language_id
                    FROM conversations
                    WHERE chatbot_id = %s
                      AND deleted_at IS NULL
                      AND created_at >= NOW() - INTERVAL '1 day';
                """, (chatbot_id,))
            rows = cursor.fetchall()
        conn.close()

        if not rows:
            return {}

        # Count occurrences of each language_id
        lang_counts = Counter(row["language_id"] for row in rows)

        # Fetch language names from config store and return integer counts
        lang_distribution = {}
        for lang_id, count in lang_counts.items():
            lang_record = get_record_by_id(
                table_name="languages",
                record_id=str(lang_id)
            )
            lang_name = lang_record.get(
                "name") if lang_record else f"Lang-{lang_id}"
            lang_distribution[lang_name] = count

        return lang_distribution

    except Exception as e:
        print(
            f"Error fetching language distribution for chatbot {chatbot_id}: {e}")
        return {}


def get_conversations_for_chatbot(chatbot_id, ref_datetime=None):
    """
    Fetch all conversation records for a specific chatbot ID from the 'conversations' table.
    Returns a list of dictionaries.
    """
    conn = get_connection()
    cursor = conn.cursor()

    start_time = ref_datetime - timedelta(days=1) if ref_datetime else None

    if start_time:
        query = """
            SELECT *
            FROM conversations
            WHERE chatbot_id = %s
              AND updated_at >= %s
        """
        cursor.execute(query, (chatbot_id, start_time))
    else:
        query = """
            SELECT *
            FROM conversations
            WHERE chatbot_id = %s
              AND updated_at >= NOW() - INTERVAL '1 day'
        """
        cursor.execute(query, (chatbot_id,))
    rows = cursor.fetchall()

    # Convert query results into list of dictionaries
    columns = [desc[0] for desc in cursor.description]
    conversations = [dict(zip(columns, row)) for row in rows]

    cursor.close()
    conn.close()

    return conversations


def get_customer_by_conversation(conversation_id, ref_datetime=None):
    """
    Fetch the customer details linked to a specific conversation ID
    from the 'customers' table.
    """
    conn = get_connection()
    cursor = conn.cursor()

    start_time = ref_datetime - timedelta(days=1) if ref_datetime else None

    if start_time:
        query = """
            SELECT *
            FROM customers
            WHERE conversation_id = %s
              AND updated_at >= %s
        """
        cursor.execute(query, (conversation_id, start_time))
    else:
        query = """
            SELECT *
            FROM customers
            WHERE conversation_id = %s
              AND updated_at >= NOW() - INTERVAL '1 day'
        """
        cursor.execute(query, (conversation_id,))
    row = cursor.fetchone()

    # Convert result to dict if found
    if row:
        columns = [desc[0] for desc in cursor.description]
        customer = dict(zip(columns, row))
    else:
        customer = None

    cursor.close()
    conn.close()

    return customer


def get_conversation_summary(conversation_id, ref_datetime=None):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT title, updated_at
        FROM conversation_summaries
        WHERE conversation_id = %s
        ORDER BY updated_at DESC
        LIMIT 1
    """
    cursor.execute(query, (conversation_id,))
    record = cursor.fetchone()

    print(f"[DEBUG] conversation_id={conversation_id}, record={record}")

    cursor.close()
    conn.close()
    return {"title": record[0]} if record else None