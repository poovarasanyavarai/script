import psycopg2.extras
from collections import Counter
from datetime import datetime, timedelta
from psycopg2.extras import RealDictCursor

from dashboard_analytics.config_query import get_record_by_id
from dashboard_analytics.database_connection import get_connection


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



def get_feedback_by_channel(chatbot_id, ref_datetime=None):
    """
    Get feedback counts grouped by channel for a specific chatbot.
    Joins conversation_overall_feedback with conversations table to get conversation_via.

    Relationship: conversation_overall_feedback.conversation_id = conversations.id
    (Both are Integer fields - conversations.conversation_id is UUID but not used in this join)

    Returns list of dicts with channel and count.
    Example: [{"channel": "whatsapp", "count": 100}, {"channel": "facebook", "count": 80}]
    """
    try:
        # Use today's date if ref_datetime is None, otherwise use provided date
        if ref_datetime is None:
            # Get today's date
            today = datetime.now()
            start_time = today.replace(hour=0, minute=0, second=0, microsecond=0)
            end_time = today.replace(hour=23, minute=59, second=59, microsecond=999999)
        else:
            # Use the provided reference datetime
            start_time = ref_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
            end_time = ref_datetime.replace(hour=23, minute=59, second=59, microsecond=999999)

        conn = get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            query = """
                SELECT
                    COALESCE(c.conversation_via, 'Unknown') as channel,
                    COUNT(*) as count
                FROM conversation_overall_feedback f
                LEFT JOIN conversations c ON f.conversation_id = c.id
                WHERE f.chatbot_id = %s
                  AND f.deleted_at IS NULL
                  AND c.deleted_at IS NULL
                  AND f.created_at >= %s
                  AND f.created_at <= %s
                GROUP BY COALESCE(c.conversation_via, 'Unknown')
                ORDER BY count DESC
            """

            params = [chatbot_id, start_time, end_time]

            # Debug output for date range
            print(f"Date Range for chatbot {chatbot_id}:")
            print(f"  Start: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  End: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")

            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()

        conn.close()

        # Convert to expected format
        result = []
        for row in rows:
            result.append({
                "channel": row["channel"],
                "count": int(row["count"])
            })

        print(f"Feedback by channel result: {result}")
        return result

    except Exception as e:
        print(f"Error fetching feedback by channel for chatbot {chatbot_id}: {e}")
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




def get_feedback_stats_by_chatbot(chatbot_id: str, ref_datetime=None):
    """
    Fetch feedback stats for a chatbot from conversation_overall_feedback:

    - feedback_total: count of messages with a rating
    - feedback_pos: only 'love it' (case-insensitive)
    - feedback_neg: only 'bad' (case-insensitive)
    - feedback_avg: only 'decent' (case-insensitive)
    """

    try:
        start_time = ref_datetime - timedelta(days=1) if ref_datetime else None
        conn = get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            query = """
                SELECT
                    COUNT(*) AS feedback_total,
                    SUM(CASE WHEN LOWER(rating) = 'love it' THEN 1 ELSE 0 END) AS feedback_pos,
                    SUM(CASE WHEN LOWER(rating) = 'bad' THEN 1 ELSE 0 END) AS feedback_neg,
                    SUM(CASE WHEN LOWER(rating) = 'decent' THEN 1 ELSE 0 END) AS feedback_avg
                FROM conversation_overall_feedback
                WHERE chatbot_id = %s
                  AND deleted_at IS NULL
                  AND rating IS NOT NULL
            """

            params = [chatbot_id]

            if start_time:
                query += " AND created_at >= %s;"
                params.append(start_time)
            else:
                query += " AND created_at >= NOW() - INTERVAL '1 day';"

            cursor.execute(query, tuple(params))
            stats = cursor.fetchone()

        conn.close()

        return {
            "feedback_total": stats["feedback_total"] or 0,
            "feedback_pos": stats["feedback_pos"] or 0,
            "feedback_neg": stats["feedback_neg"] or 0,
            "feedback_avg": stats["feedback_avg"] or 0
        }

    except Exception:
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