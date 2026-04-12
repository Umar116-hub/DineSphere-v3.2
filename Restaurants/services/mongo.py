from pymongo import MongoClient
from django.conf import settings
from datetime import datetime

# MongoDB Client
client = MongoClient(settings.MONGO_URI)
db = client[settings.MONGO_DB_NAME]

# Collections
logs_collection = db["logs"]
config_collection = db["configurations"]

# Application collections
users_collection = db["users"]
restaurants_collection = db["restaurants"]
tables_collection = db["tables"]
table_sizes_collection = db["table_sizes"]
seating_types_collection = db["seating_types"]
restaurant_staff_collection = db["restaurant_staff"]
reviews_collection = db["reviews"]
holidays_collection = db["holidays"]
bookings_collection = db["bookings"]
favourites_collection = db["favourites"]


def is_mongo_available():
    """Check if MongoDB is available"""
    try:
        client.admin.command('ping')
        return True
    except Exception:
        return False


def log_event(user, data):
    """Log event to MongoDB"""
    try:
        logs_collection.insert_one({
            "user": user,
            "data": data,
            "timestamp": datetime.now()
        })
    except Exception:
        pass  # Fail silently for logging


def get_collection_stats():
    """Get document counts for all collections"""
    if not is_mongo_available():
        return {}
    
    return {
        "users": users_collection.count_documents({}),
        "restaurants": restaurants_collection.count_documents({}),
        "tables": tables_collection.count_documents({}),
        "table_sizes": table_sizes_collection.count_documents({}),
        "seating_types": seating_types_collection.count_documents({}),
        "restaurant_staff": restaurant_staff_collection.count_documents({}),
        "reviews": reviews_collection.count_documents({}),
        "holidays": holidays_collection.count_documents({}),
        "bookings": bookings_collection.count_documents({}),
        "favourites": favourites_collection.count_documents({}),
        "logs": logs_collection.count_documents({}),
    }