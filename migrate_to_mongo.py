#!/usr/bin/env python
"""
Data Migration Script: SQLite to MongoDB
Migrates all Django model data from SQLite to MongoDB collections.
"""

import os
import sys
import django
from datetime import datetime
from bson import ObjectId

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Dinesphere.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from pymongo import MongoClient
from django.conf import settings
from django.contrib.auth import get_user_model

# Import all models
from UsersHandling.models import User, FavouriteRestaurant
from Restaurants.models import (
    Restaurant, Table, TableSize, SeatingType, 
    RestaurantStaff, Review, Holiday
)
from Reservations.models import Booking

# MongoDB Connection
client = MongoClient(settings.MONGO_URI)
db = client[settings.MONGO_DB_NAME]


def migrate_users():
    """Migrate User model to MongoDB"""
    print("Migrating Users...")
    users_collection = db['users']
    users_collection.delete_many({})  # Clear existing
    
    count = 0
    for user in User.objects.all():
        doc = {
            '_id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_staff': user.is_staff,
            'is_active': user.is_active,
            'date_joined': user.date_joined,
            'last_login': user.last_login,
            'image': user.image.name if user.image else None,
            'role': user.role if hasattr(user, 'role') else 'customer',
        }
        users_collection.insert_one(doc)
        count += 1
    
    print(f"  ✓ Migrated {count} users")
    return count


def migrate_restaurants():
    """Migrate Restaurant model to MongoDB"""
    print("Migrating Restaurants...")
    restaurants_collection = db['restaurants']
    restaurants_collection.delete_many({})
    
    count = 0
    for restaurant in Restaurant.objects.all():
        doc = {
            '_id': restaurant.id,
            'name': restaurant.name,
            'address': restaurant.address,
            'city': restaurant.city,
            'cuisine_type': restaurant.cuisine_type,
            'description': restaurant.description,
            'phone': restaurant.phone,
            'email': restaurant.email,
            'website': restaurant.website,
            'rating': float(restaurant.rating) if restaurant.rating else 0.0,
            'is_approved': restaurant.is_approved,
            'owner_id': restaurant.owner_id,
            'image': restaurant.image.name if restaurant.image else None,
            'created_at': datetime.now(),
        }
        restaurants_collection.insert_one(doc)
        count += 1
    
    print(f"  ✓ Migrated {count} restaurants")
    return count


def migrate_tables():
    """Migrate Table model to MongoDB"""
    print("Migrating Tables...")
    tables_collection = db['tables']
    tables_collection.delete_many({})
    
    count = 0
    for table in Table.objects.all():
        doc = {
            '_id': table.id,
            'name': table.name,
            'restaurant_id': table.restaurant_id,
            'table_size_id': table.table_size_id,
            'seating_type_id': table.seating_type_id,
            'is_active': table.is_active,
        }
        tables_collection.insert_one(doc)
        count += 1
    
    print(f"  ✓ Migrated {count} tables")
    return count


def migrate_table_sizes():
    """Migrate TableSize model to MongoDB"""
    print("Migrating Table Sizes...")
    table_sizes_collection = db['table_sizes']
    table_sizes_collection.delete_many({})
    
    count = 0
    for size in TableSize.objects.all():
        doc = {
            '_id': size.id,
            'name': size.name,
            'capacity': size.capacity,
            'restaurant_id': size.restaurant_id,
        }
        table_sizes_collection.insert_one(doc)
        count += 1
    
    print(f"  ✓ Migrated {count} table sizes")
    return count


def migrate_seating_types():
    """Migrate SeatingType model to MongoDB"""
    print("Migrating Seating Types...")
    seating_types_collection = db['seating_types']
    seating_types_collection.delete_many({})
    
    count = 0
    for seating in SeatingType.objects.all():
        doc = {
            '_id': seating.id,
            'name': seating.name,
            'restaurant_id': seating.restaurant_id,
        }
        seating_types_collection.insert_one(doc)
        count += 1
    
    print(f"  ✓ Migrated {count} seating types")
    return count


def migrate_restaurant_staff():
    """Migrate RestaurantStaff model to MongoDB"""
    print("Migrating Restaurant Staff...")
    staff_collection = db['restaurant_staff']
    staff_collection.delete_many({})
    
    count = 0
    for staff in RestaurantStaff.objects.all():
        doc = {
            '_id': staff.id,
            'user_id': staff.user_id,
            'restaurant_id': staff.restaurant_id,
            'role': staff.role,
            'is_active': staff.is_active,
        }
        staff_collection.insert_one(doc)
        count += 1
    
    print(f"  ✓ Migrated {count} staff members")
    return count


def migrate_reviews():
    """Migrate Review model to MongoDB"""
    print("Migrating Reviews...")
    reviews_collection = db['reviews']
    reviews_collection.delete_many({})
    
    count = 0
    for review in Review.objects.all():
        doc = {
            '_id': review.id,
            'restaurant_id': review.restaurant_id,
            'user_id': review.user_id,
            'rating': review.rating,
            'comment': review.comment,
            'on_display': review.on_display,
            'created_at': review.created_at,
        }
        reviews_collection.insert_one(doc)
        count += 1
    
    print(f"  ✓ Migrated {count} reviews")
    return count


def migrate_holidays():
    """Migrate Holiday model to MongoDB"""
    print("Migrating Holidays...")
    holidays_collection = db['holidays']
    holidays_collection.delete_many({})
    
    count = 0
    for holiday in Holiday.objects.all():
        doc = {
            '_id': holiday.id,
            'name': holiday.name,
            'date': holiday.date,
            'restaurant_id': holiday.restaurant_id,
            'is_recurring': holiday.is_recurring,
        }
        holidays_collection.insert_one(doc)
        count += 1
    
    print(f"  ✓ Migrated {count} holidays")
    return count


def migrate_bookings():
    """Migrate Booking model to MongoDB"""
    print("Migrating Bookings...")
    bookings_collection = db['bookings']
    bookings_collection.delete_many({})
    
    count = 0
    for booking in Booking.objects.all():
        doc = {
            '_id': booking.id,
            'restaurant_id': booking.restaurant_id,
            'customer_id': booking.customer_id,
            'booking_start_datetime': booking.booking_start_datetime,
            'booking_end_datetime': booking.booking_end_datetime,
            'status': booking.status,
            'payment_status': booking.payment_status,
            'total_price': float(booking.total_price) if booking.total_price else 0.0,
            'created_at': booking.created_at,
            'table_ids': [t.id for t in booking.tables.all()],
        }
        bookings_collection.insert_one(doc)
        count += 1
    
    print(f"  ✓ Migrated {count} bookings")
    return count


def migrate_favourites():
    """Migrate FavouriteRestaurant model to MongoDB"""
    print("Migrating Favourites...")
    favourites_collection = db['favourites']
    favourites_collection.delete_many({})
    
    count = 0
    for fav in FavouriteRestaurant.objects.all():
        doc = {
            '_id': fav.id,
            'user_id': fav.user_id,
            'restaurant_id': fav.restaurant_id,
            'created_at': datetime.now(),
        }
        favourites_collection.insert_one(doc)
        count += 1
    
    print(f"  ✓ Migrated {count} favourites")
    return count


def create_indexes():
    """Create MongoDB indexes for performance"""
    print("Creating indexes...")
    
    # Users indexes
    db['users'].create_index('username', unique=True)
    db['users'].create_index('email', unique=True)
    
    # Restaurants indexes
    db['restaurants'].create_index('name')
    db['restaurants'].create_index('owner_id')
    db['restaurants'].create_index('city')
    db['restaurants'].create_index('is_approved')
    
    # Tables indexes
    db['tables'].create_index('restaurant_id')
    
    # Bookings indexes
    db['bookings'].create_index('restaurant_id')
    db['bookings'].create_index('customer_id')
    db['bookings'].create_index('status')
    db['bookings'].create_index('booking_start_datetime')
    
    # Reviews indexes
    db['reviews'].create_index('restaurant_id')
    db['reviews'].create_index('user_id')
    
    # Staff indexes
    db['restaurant_staff'].create_index('restaurant_id')
    db['restaurant_staff'].create_index('user_id')
    
    print("  ✓ Indexes created")


def main():
    """Run the migration"""
    print("=" * 60)
    print("MongoDB Data Migration")
    print("=" * 60)
    print()
    
    try:
        # Test connection
        client.admin.command('ping')
        print("✓ MongoDB connection successful")
        print()
        
        # Run migrations
        stats = {
            'users': migrate_users(),
            'restaurants': migrate_restaurants(),
            'tables': migrate_tables(),
            'table_sizes': migrate_table_sizes(),
            'seating_types': migrate_seating_types(),
            'restaurant_staff': migrate_restaurant_staff(),
            'reviews': migrate_reviews(),
            'holidays': migrate_holidays(),
            'bookings': migrate_bookings(),
            'favourites': migrate_favourites(),
        }
        
        # Create indexes
        create_indexes()
        
        print()
        print("=" * 60)
        print("Migration Summary")
        print("=" * 60)
        for collection, count in stats.items():
            print(f"  {collection}: {count} documents")
        print()
        print("✓ Migration completed successfully!")
        
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        client.close()


if __name__ == '__main__':
    main()
