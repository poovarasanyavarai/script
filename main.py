from datetime import datetime, timedelta, timezone
from dashboard_analytics.insert_metrics import insert_metrics, insert_chatbot_conversations


def main(reference_date: str = "now"):
    """
    reference_date:
      - "now" → uses current UTC time
      - "yesterday" → uses current UTC time minus 1 day
      - "YYYY-MM-DD" → specific date in ISO format
    """
    now = datetime.now(timezone.utc)

    if reference_date.lower() == "now":
        ref_datetime = now
    elif reference_date.lower() == "yesterday":
        ref_datetime = now - timedelta(days=1)
    else:
        try:
            ref_datetime = datetime.fromisoformat(
                reference_date).replace(tzinfo=timezone.utc)
        except Exception:
            print(
                f"Invalid reference_date '{reference_date}', using now instead.")
            ref_datetime = now

    print(
        f"Starting chatbot metrics insertion for reference time: {ref_datetime}")
    insert_metrics(ref_datetime)
    print("Chatbot metrics insertion completed.")

    print("Starting chatbot conversation insertion...")
    insert_chatbot_conversations(ref_datetime)
    print("Chatbot conversation insertion completed.\n")


if __name__ == "__main__":
    main("now")
