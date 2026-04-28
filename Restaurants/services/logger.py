from datetime import datetime
from django.conf import settings


def log_event(event, data=None):
    """
    Log an event to MongoDB.
    
    Args:
        event: The username or event identifier (stored as 'event' field for querying)
        data: Optional dict with action details
    
    Only writes when USE_MONGO is True. 
    """
    if not getattr(settings, 'USE_MONGO', False):
        return

    try:
        from .mongo import get_logs_collection
        collection = get_logs_collection()
        if collection is not None:
            collection.insert_one({
                "event": event,
                "data": data or {},
                "timestamp": datetime.now()
            })
    except Exception as e:
        if settings.DEBUG:
            print(f"Logging Error: {e}")
        # In production, we still fail silently to avoid crashing the whole app 
        # for a non-critical logging failure.