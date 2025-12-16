#!/usr/bin/env python3

sql = """
            INSERT INTO chatbot_metrics (
                chatbot_id, name, profile_url, bot_created_at,
                languages, total_coversation, coversation_diff, leads, leads_diff, platform,
                ai_resolved, human_resolved, ai_resolved_diff, human_resolved_diff,
                feedback_total, feedback_pos, feedback_neg, feedback_avg, ai_csat, human_csat,
                alerts, fb_geo, fb_channel, trends, net_impact, net_impact_graph, perform_by_geo,
                active_status, ongoing_calls, in_queue, unresolved
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

# Extract the VALUES part
values_line = sql.split('VALUES')[1].strip()
print("VALUES line:", values_line)
print("\nCount of %s:", values_line.count('%s'))