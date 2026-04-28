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
        return (
            "No activity logs recorded for this user yet.\n\n"
            "Actions such as:\n"
            "- Registering a restaurant\n"
            "- Adding or updating tables\n"
            "- Managing staff\n"
            "- Adding holidays\n\n"
            "Will automatically appear here once performed."
        )

    lines = []
    lines.append("Dinesphere Activity Log Report")
    lines.append("=" * 50)
    lines.append("")

    for log in logs:
        timestamp = log.get("timestamp")
        data = log.get("data", {})

        # Try to format timestamp nicely if it's a datetime object
        try:
            time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        except AttributeError:
            time_str = str(timestamp)

        lines.append(f"[{time_str}]")
        
        # Display the action primary if available
        action = data.get("action", "General Event").replace("_", " ").title()
        lines.append(f"ACTION: {action}")

        for key, value in data.items():
            if key != "action":
                lines.append(f"  {key.capitalize():10}: {value}")

        lines.append("-" * 30)

    return "\n".join(lines)