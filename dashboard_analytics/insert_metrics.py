import json
import pycountry
from datetime import datetime, timezone
from .config_query import get_chatbots, get_record_by_id, get_settings, get_users, query_records
from .db_query import (
    get_conversation_summary,
    get_conversations,
    get_customers_by_chatbot,
    get_feedback_stats_by_chatbot,
    get_interactions_by_conversation,
    get_language_distribution,
    get_conversations_for_chatbot,
    get_customer_by_conversation,
)
from .db_connection import get_connection


def get_country_code(name):
    try:
        country = pycountry.countries.lookup(name)
        return country.alpha_2
    except Exception:
        return "XX"


def insert_metrics(ref_datetime=None):

    if ref_datetime is None:
        snapshot_time = datetime.now(timezone.utc)
    else:
        snapshot_time = ref_datetime
    # users = get_users()
    # account_ids = {u.get("account_id") for u in users if u.get("account_id")}
    # account_ids = list(account_ids)
    account_ids = ["86c3cb12-d1d1-5a0e-ab58-3230ec9fe11f"]

    # instead of get_chatbots()
    chatbots = []
    for acc_id in account_ids:
        chatbots.extend(query_records("chatbots", "account_id", acc_id))
    settings_list = get_settings()
    conversation_list = get_conversations()

    settings_map = {s.get("chatbot_id"): s for s in settings_list}
    conv_map = {c.get("chatbot_id"): c for c in conversation_list}

    conn = get_connection()
    cursor = conn.cursor()

    for cb in chatbots:
        chatbot_id = cb.get("id")
        name = cb.get("name")
        bot_created_at = cb.get("created_at")

        cb_settings = settings_map.get(chatbot_id, {})
        cb_conversation = conv_map.get(chatbot_id, {})

        profile_url = cb_settings.get("profile_image_url")
        languages = get_language_distribution(chatbot_id)

        total_coversation = cb_conversation.get("total_conversations", 0)
        ai_resolve = cb_conversation.get("total_conversations", 0)
        human_resolve = 0

        if total_coversation > 0:
            ai_resolved = ai_resolve 
            human_resolved = human_resolve 
        else:
            ai_resolved = 0
            human_resolved = 0

        cursor.execute(
            """
            SELECT ai_resolved, human_resolved, total_coversation
            FROM chatbot_metrics
            WHERE chatbot_id = %s
            AND snapshot_time <= %s
            ORDER BY snapshot_time DESC
            LIMIT 1
            """,
            (chatbot_id, snapshot_time),
        )
        prev = cursor.fetchone()

        prev_ai_resolved = prev[0] if prev else 0
        prev_human_resolved = prev[1] if prev else 0
        prev_total_conversation = prev[2] if prev else 0

        coversation_diff = total_coversation - prev_total_conversation
        ai_resolved_diff = ai_resolved - prev_ai_resolved
        human_resolved_diff = human_resolved - prev_human_resolved

        # leads for now
        leads = 0
        leads_diff = 0

        feedback_stats = get_feedback_stats_by_chatbot(chatbot_id)
        feedback_total = feedback_stats["feedback_total"]
        feedback_pos = feedback_stats["feedback_pos"]
        feedback_neg = feedback_stats["feedback_neg"]
        feedback_avg = feedback_stats["feedback_avg"]

        platform = cb_conversation.get("conversation_via", {})
        platform_json = json.dumps(platform)

        # cb_customer = get_customers_by_chatbot(chatbot_id)
        # conversation_ids = [
        #     str(cust.get("conversation_id"))
        #     for cust in cb_customer
        #     if cust.get("conversation_id") is not None
        # ]
        # interactions_map = get_interactions_by_conversation(conversation_ids)

        # dots = []
        # country_performance = {}

        # for cust in cb_customer:
        #     country = cust.get("country") or "Unknown"
        #     region = cust.get("region") or ""
        #     city = cust.get("city") or ""
        #     conv_id = cust.get("conversation_id")
        #     conv_id_key = str(conv_id) if conv_id is not None else None
        #     interactions = interactions_map.get(conv_id_key, 0)

        #     country_performance[country] = (
        #         country_performance.get(country, 0) + interactions
        #     )

        #     lat, lng = 0, 0
        #     code = get_country_code(country)

        #     dots.append(
        #         {
        #             "lat": lat,
        #             "lng": lng,
        #             "country": region or city or country,
        #             "code": code,
        #             "interactions": interactions,
        #         }
        #     )

        # perform_by_geo = {
        #     "dots": dots,
        #     "countryPerformance": [
        #         {"country": c, "interactions": count, "code": get_country_code(c)}
        #         for c, count in country_performance.items()
        #     ],
        # }

        # perform_by_geo_json = json.dumps(perform_by_geo)

        # Static data
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

        # STATIC_ALERTS = [
        #     {"time": "2 hr ago", "message": "High response time", "severity": "medium"}
        # ]

        # STATIC_TRENDS = [
        #     {"time": "2 hr ago", "message": "High response time", "severity": "medium"}
        # ]
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
            {"time": "5 min ago", "message": "XYZ Bot outage detected — unable to process requests", "severity": "critical"},
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
            {"time": "5 min ago", "message": "Sentiment recovery detected — 3% rise in positive chats", "severity": "low"},
        ]


        net_impact = 20
        STATIC_NET_IMPACT_GRAPH = {"ai": 14, "human": 12, "percentage": 30}

        fb_geo_json = json.dumps(STATIC_FB_GEO)
        fb_channel_json = json.dumps(STATIC_FB_CHANNEL)
        perform_by_geo_json = json.dumps(STATIC_PERFORM_BY_GEO)
        alerts_json = json.dumps(STATIC_ALERTS)
        trends_json = json.dumps(STATIC_TRENDS)
        net_impact_graph_json = json.dumps(STATIC_NET_IMPACT_GRAPH)

        sql = """
            INSERT INTO chatbot_metrics (
                snapshot_time, chatbot_id, name, profile_url, bot_created_at,
                languages, total_coversation, coversation_diff, leads, leads_diff, platform,
                ai_resolved, human_resolved, ai_resolved_diff, human_resolved_diff,
                feedback_total, feedback_pos, feedback_neg, feedback_avg, alerts, fb_geo, fb_channel,
                trends, net_impact, net_impact_graph, perform_by_geo
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            snapshot_time,
            chatbot_id,
            name,
            profile_url,
            bot_created_at,
            json.dumps(languages),
            total_coversation,
            coversation_diff,
            leads,
            leads_diff,
            platform_json,
            ai_resolved,
            human_resolved,
            ai_resolved_diff,
            human_resolved_diff,
            feedback_total,
            feedback_pos,
            feedback_neg,
            feedback_avg,
            alerts_json,
            fb_geo_json,
            fb_channel_json,
            trends_json,
            net_impact,
            net_impact_graph_json,
            perform_by_geo_json,
        )

        cursor.execute(sql, values)

    conn.commit()
    cursor.close()
    conn.close()
    print(f"Inserted metrics for {len(chatbots)} chatbots.")


def insert_chatbot_conversations(ref_datetime=None):
    """
    Insert all conversation data (with channel + customer info + language name + summary)
    for each chatbot into chatbot_conversation table.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # users = get_users()
    # account_ids = {u.get("account_id") for u in users if u.get("account_id")}
    # account_ids = list(account_ids)
    account_ids = ["86c3cb12-d1d1-5a0e-ab58-3230ec9fe11f"]


    # instead of get_chatbots()
    chatbots = []
    for acc_id in account_ids:
        chatbots.extend(query_records("chatbots", "account_id", acc_id))
    total_inserted = 0

    for cb in chatbots:
        chatbot_id = cb.get("id")
        chatbot_name = cb.get("name")

        conversations = get_conversations_for_chatbot(chatbot_id, ref_datetime)

        for conv in conversations:
            conversation_id = conv.get("id") or conv.get("conversation_id")

            summary_record = get_conversation_summary(
                    conversation_id, ref_datetime)
            query_summary = (summary_record or {}).get("title") or "AI interaction with z-assist"

            customer = get_customer_by_conversation(
                conversation_id, ref_datetime) if conversation_id else None
            customer_name = customer.get("customer_name") if customer else None
            contact = customer.get("contact") if customer else None
            city = customer.get("city") if customer else None
            region = customer.get("region") if customer else None

            channel = conv.get("conversation_via") or "Unknown"

            language_name = None
            language_id = conv.get("language_id")
            if language_id:
                language_record = get_record_by_id(
                    "languages", str(language_id))
                language_name = language_record.get("name")

            agent_value = json.dumps(
                [{
                    "name":"AI",
                    "profile_image":"https://zagentstoragedev94f5525a.blob.core.windows.net/data-connector-hub/welcome_avatar.svg?se=2045-10-19T07%3A53%3A48Z&sp=r&spr=https&sv=2025-11-05&sr=b&rscd=inline%3B%20filename%3Dwelcome_avatar.svg&rsct=image/svg%2Bxml&sig=ByHRzENC9L21IrmuEJ%2BhU4zbCfq%2Bqf4n8KTbOH3/a0Y%3D"
                 }]
                )

            sql = """
                INSERT INTO chatbot_conversation (
                    chatbot_id, query, customer_name, ticket_number, channel, status,
                    contact, city, region, agent, language_selected, last_updated, conversation_id
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            values = (
                chatbot_id,
                query_summary or "AI interaction with z-assist",
                customer_name,
                "TICKET-AI",
                channel,
                "success",
                contact,
                city,
                region,
                agent_value,  # JSON formatted
                language_name,
                conv.get("updated_at"),
                conversation_id,
            )

            cursor.execute(sql, values)
            total_inserted += 1

    conn.commit()
    cursor.close()
    conn.close()

    print(
        f"Inserted {total_inserted} conversation records across {len(chatbots)} chatbots.")
