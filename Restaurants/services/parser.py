from django.conf import settings


def get_user_logs(username):
    """
    Retrieve all log entries for a given username from MongoDB.
    Returns an empty list when MongoDB is disabled.
    """
    if not getattr(settings, 'USE_MONGO', False):
        return []

    try:
        from .mongo import get_logs_collection
        collection = get_logs_collection()
        if collection is None:
            return []

        logs = collection.find(
            {"event": username}
        ).sort("timestamp", -1)

        return list(logs)
    except Exception:
        return []


def format_logs_to_text(logs):
    """
    Format a list of MongoDB log documents into a human-readable text block.
    """
    if not logs:
        return "No logs found."

    lines = []

    for log in logs:
        timestamp = log.get("timestamp")
        data = log.get("data", {})

        lines.append("=" * 50)
        lines.append(f"Time      : {timestamp}")

        for key, value in data.items():
            lines.append(f"{key.capitalize():10}: {value}")

        lines.append("")  # spacing

    return "\n".join(lines)