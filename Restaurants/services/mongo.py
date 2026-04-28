from pymongo import MongoClient
from django.conf import settings
from datetime import datetime

# ─── Lazy MongoDB Connection ──────────────────────────────────────
# Only establish a real connection when USE_MONGO is True.
# This prevents startup crashes when MongoDB isn't installed/running.

_client = None
_db = None


def _get_client():
    """Lazily create and cache the MongoClient."""
    global _client
    if _client is None:
        try:
            _client = MongoClient(
                settings.MONGO_URI,
                serverSelectionTimeoutMS=3000  # Fail fast if MongoDB is unreachable
            )
            # Optional: Test connection immediately
            _client.admin.command('ping')
        except Exception as e:
            if settings.DEBUG:
                print(f"MongoDB Connection Error: {e}")
            _client = None
            raise e
    return _client


def _get_db():
    """Lazily get and cache the MongoDB database."""
    global _db
    if _db is None:
        client = _get_client()
        if client:
            _db = client[settings.MONGO_DB_NAME]
    return _db


def _get_collection(name):
    """Get a MongoDB collection by name. Only works when USE_MONGO=True."""
    if not getattr(settings, 'USE_MONGO', False):
        return None
    try:
        db = _get_db()
        return db[name] if db is not None else None
    except Exception as e:
        if settings.DEBUG:
            print(f"MongoDB Collection Error ({name}): {e}")
        return None


# ─── Collection Accessors ─────────────────────────────────────────
# These are functions, NOT module-level variables, so they only
# trigger a connection when actually called.

def get_logs_collection():
    return _get_collection("logs")

def get_config_collection():
    return _get_collection("configurations")

def get_users_collection():
    return _get_collection("users")

def get_restaurants_collection():
    return _get_collection("restaurants")

def get_tables_collection():
    return _get_collection("tables")

def get_table_sizes_collection():
    return _get_collection("table_sizes")

def get_seating_types_collection():
    return _get_collection("seating_types")

def get_restaurant_staff_collection():
    return _get_collection("restaurant_staff")

def get_reviews_collection():
    return _get_collection("reviews")

def get_holidays_collection():
    return _get_collection("holidays")

def get_bookings_collection():
    return _get_collection("bookings")

def get_favourites_collection():
    return _get_collection("favourites")


# ─── Backward-Compatible Property Objects ─────────────────────────
# These let existing code like `from .mongo import logs_collection`
# keep working. They act as lazy proxies to the real collections.

class _LazyCollection:
    """A proxy that looks up the real collection on every attribute access."""
    def __init__(self, name):
        self._name = name

    def __getattr__(self, attr):
        collection = _get_collection(self._name)
        if collection is None:
            # Return a no-op for common operations when MongoDB is disabled
            if attr in ('insert_one', 'insert_many', 'update_one', 'update_many',
                        'delete_one', 'delete_many', 'create_index'):
                return lambda *a, **kw: None
            if attr == 'find':
                return lambda *a, **kw: []
            if attr == 'count_documents':
                return lambda *a, **kw: 0
            raise AttributeError(
                f"MongoDB is disabled (USE_MONGO=False). Cannot access '{attr}' on '{self._name}' collection."
            )
        return getattr(collection, attr)


# Module-level names for backward compatibility
logs_collection = _LazyCollection("logs")
config_collection = _LazyCollection("configurations")
users_collection = _LazyCollection("users")
restaurants_collection = _LazyCollection("restaurants")
tables_collection = _LazyCollection("tables")
table_sizes_collection = _LazyCollection("table_sizes")
seating_types_collection = _LazyCollection("seating_types")
restaurant_staff_collection = _LazyCollection("restaurant_staff")
reviews_collection = _LazyCollection("reviews")
holidays_collection = _LazyCollection("holidays")
bookings_collection = _LazyCollection("bookings")
favourites_collection = _LazyCollection("favourites")


# ─── Utility Functions ────────────────────────────────────────────

def is_mongo_available():
    """Check if MongoDB is available and USE_MONGO is enabled."""
    if not getattr(settings, 'USE_MONGO', False):
        return False
    try:
        client = _get_client()
        if client:
            client.admin.command('ping')
            return True
        return False
    except Exception:
        return False


def get_collection_stats():
    """Get document counts for all collections."""
    if not is_mongo_available():
        return {}

    return {
        "users": get_users_collection().count_documents({}),
        "restaurants": get_restaurants_collection().count_documents({}),
        "tables": get_tables_collection().count_documents({}),
        "table_sizes": get_table_sizes_collection().count_documents({}),
        "seating_types": get_seating_types_collection().count_documents({}),
        "restaurant_staff": get_restaurant_staff_collection().count_documents({}),
        "reviews": get_reviews_collection().count_documents({}),
        "holidays": get_holidays_collection().count_documents({}),
        "bookings": get_bookings_collection().count_documents({}),
        "favourites": get_favourites_collection().count_documents({}),
        "logs": get_logs_collection().count_documents({}),
    }