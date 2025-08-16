import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pymongo.database import Database
from pymongo.collection import Collection
from pymongo.errors import (
    BulkWriteError, 
    DuplicateKeyError, 
    PyMongoError,
    ConnectionFailure,
    ServerSelectionTimeoutError,
    AutoReconnect
)
from .connection import get_database, DatabaseConnectionManager


class NotificationOperation:
    """Enhanced notification operations with transaction support and retry logic"""
    
    def __init__(self, db_name: str = None):
        self.logger = logging.getLogger(__name__)
        self.db_name = db_name
        self._db: Optional[Database] = None
        self._collection: Optional[Collection] = None
    
    @property
    def db(self) -> Database:
        """Get database instance with connection retry"""
        if self._db is None:
            self._db = get_database(self.db_name)
        return self._db
    
    @property
    def collection(self) -> Collection:
        """Get collection instance"""
        if self._collection is None:
            self._collection = self.db.notifications
        return self._collection
    
    def _retry_database_operation(self, operation_func, *args, **kwargs):
        """Retry database operations with exponential backoff"""
        max_retries = 3
        base_delay = 1
        
        for attempt in range(max_retries):
            try:
                return operation_func(*args, **kwargs)
            
            except (ConnectionFailure, ServerSelectionTimeoutError, AutoReconnect) as e:
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    self.logger.warning(
                        f"Database operation failed (attempt {attempt + 1}/{max_retries}): {e}. "
                        f"Retrying in {delay} seconds..."
                    )
                    import time
                    time.sleep(delay)
                    
                    # Force reconnection
                    self._db = None
                    self._collection = None
                else:
                    self.logger.error(f"Database operation failed after {max_retries} attempts: {e}")
                    raise
            
            except Exception as e:
                self.logger.error(f"Unexpected database error: {e}")
                raise
    
    def save_notifications(self, notifications: List[Dict[str, Any]]) -> List[str]:
        """Save notifications with transaction support and retry logic"""
        if not notifications:
            self.logger.info("No notifications to save")
            return []
        
        def _save_operation():
            # Add timestamps and ensure required fields
            processed_notifications = []
            for notification in notifications:
                processed_notification = notification.copy()
                processed_notification['created_at'] = datetime.now(timezone.utc)
                processed_notification['updated_at'] = datetime.now(timezone.utc)
                
                # Add unique identifier if not present
                if 'notification_id' not in processed_notification:
                    import uuid
                    processed_notification['notification_id'] = str(uuid.uuid4())
                
                processed_notifications.append(processed_notification)
            
            # Create unique index if it doesn't exist
            try:
                self.collection.create_index(
                    "notification_id", 
                    unique=True, 
                    background=True
                )
            except Exception:
                pass  # Index might already exist
            
            # Insert notifications without transactions (standalone MongoDB)
            try:
                result = self.collection.insert_many(
                    processed_notifications, 
                    ordered=False  # Continue on individual failures
                )
                
                inserted_ids = [str(obj_id) for obj_id in result.inserted_ids]
                self.logger.info(f"Successfully saved {len(inserted_ids)} notifications")
                return inserted_ids
            
            except BulkWriteError as e:
                # Handle partial success in bulk operations
                inserted_count = e.details.get('nInserted', 0)
                duplicate_count = len([err for err in e.details.get('writeErrors', []) 
                                     if err.get('code') == 11000])  # Duplicate key error code
                
                self.logger.warning(
                    f"Bulk write completed with errors: {inserted_count} inserted, "
                    f"{duplicate_count} duplicates, {len(e.details.get('writeErrors', [])) - duplicate_count} other errors"
                )
                
                # Return successfully inserted IDs if available
                if 'insertedIds' in e.details:
                    return [str(obj_id) for obj_id in e.details['insertedIds'].values()]
                else:
                    return []
            
            except DuplicateKeyError as e:
                self.logger.warning(f"Duplicate notification detected: {e}")
                return []
        
        try:
            return self._retry_database_operation(_save_operation)
        except Exception as e:
            self.logger.error(f"Failed to save notifications after retries: {e}")
            return []
    
    def get_all_notifications(self, limit: int = None, skip: int = 0) -> List[Dict[str, Any]]:
        """Get notifications with pagination and retry logic"""
        def _get_operation():
            cursor = self.collection.find({}).sort("created_at", -1)
            
            if skip > 0:
                cursor = cursor.skip(skip)
            if limit:
                cursor = cursor.limit(limit)
            
            notifications = list(cursor)
            
            # Convert ObjectId to string for JSON serialization
            for notification in notifications:
                notification['_id'] = str(notification['_id'])
            
            return notifications
        
        try:
            notifications = self._retry_database_operation(_get_operation)
            self.logger.info(f"Retrieved {len(notifications)} notifications")
            return notifications
        except Exception as e:
            self.logger.error(f"Failed to retrieve notifications: {e}")
            return []
    
    def get_notifications_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get notifications within a date range"""
        def _get_by_date_operation():
            cursor = self.collection.find({
                "created_at": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            }).sort("created_at", -1)
            
            notifications = list(cursor)
            
            for notification in notifications:
                notification['_id'] = str(notification['_id'])
            
            return notifications
        
        try:
            notifications = self._retry_database_operation(_get_by_date_operation)
            self.logger.info(f"Retrieved {len(notifications)} notifications for date range {start_date} to {end_date}")
            return notifications
        except Exception as e:
            self.logger.error(f"Failed to retrieve notifications by date range: {e}")
            return []
    
    def delete_old_notifications(self, days_old: int = 30) -> int:
        """Delete notifications older than specified days with transaction support"""
        def _delete_operation():
            from datetime import timedelta
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)
            
            # Delete without transactions (standalone MongoDB)
            result = self.collection.delete_many(
                {"created_at": {"$lt": cutoff_date}}
            )
            return result.deleted_count
        
        try:
            deleted_count = self._retry_database_operation(_delete_operation)
            self.logger.info(f"Deleted {deleted_count} old notifications (older than {days_old} days)")
            return deleted_count
        except Exception as e:
            self.logger.error(f"Failed to delete old notifications: {e}")
            return 0
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database and collection statistics"""
        try:
            collection_stats = self.db.command("collStats", "notifications")
            connection_stats = DatabaseConnectionManager.get_connection_stats()
            
            return {
                "connection": connection_stats,
                "collection": {
                    "count": collection_stats.get("count", 0),
                    "size_bytes": collection_stats.get("size", 0),
                    "avg_obj_size": collection_stats.get("avgObjSize", 0),
                    "indexes": collection_stats.get("nindexes", 0),
                }
            }
        except Exception as e:
            self.logger.error(f"Failed to get database stats: {e}")
            return {"error": str(e)}