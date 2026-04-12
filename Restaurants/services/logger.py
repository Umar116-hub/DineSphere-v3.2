from .mongo import logs_collection
from datetime import datetime
from django.conf import settings

def log_event(event, data=None):
    if not getattr(settings, 'USE_MONGO', False):
        return

    try:
        logs_collection.insert_one({
            "event": event,
            "data": data or {},
            "timestamp": datetime.utcnow()
        })
    except Exception:
        pass  # Fail silently for logging