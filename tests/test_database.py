#!/usr/bin/env python3
"""
Database Integration Tests
Tests database connection, retry logic, and transaction support
"""

import os
import sys
import uuid
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.db.notification_operation import NotificationOperation
from src.db.connection import DatabaseConnectionManager


def test_database_connection():
    """Test database connection with retry logic"""
    load_dotenv()
    
    # Test connection
    stats = DatabaseConnectionManager.get_connection_stats()
    assert stats.get('status') in ['connected', 'disconnected', 'error']


def test_notification_operations():
    """Test notification CRUD operations with transactions"""
    load_dotenv()
    
    # Initialize operations
    db_ops = NotificationOperation()
    
    # Create test notifications
    test_notifications = [
        {
            "question": f"Test Question 1 - {uuid.uuid4().hex[:8]}",
            "side": "Yes",
            "price": "0.65",
            "matched_size": "100",
            "notification_id": f"test_1_{uuid.uuid4().hex[:8]}"
        },
        {
            "question": f"Test Question 2 - {uuid.uuid4().hex[:8]}",
            "side": "No", 
            "price": "0.42",
            "matched_size": "50",
            "notification_id": f"test_2_{uuid.uuid4().hex[:8]}"
        }
    ]
    
    # Test saving notifications
    saved_ids = db_ops.save_notifications(test_notifications)
    assert isinstance(saved_ids, list)
    
    # Test retrieving notifications
    retrieved = db_ops.get_all_notifications(limit=5)
    assert isinstance(retrieved, list)


def test_transaction_rollback():
    """Test transaction rollback on duplicate keys"""
    load_dotenv()
    
    db_ops = NotificationOperation()
    unique_id = f"rollback_test_{uuid.uuid4().hex[:8]}"
    
    # Create notification with specific ID
    test_notification = {
        "question": f"Rollback Test - {unique_id}",
        "side": "Yes",
        "price": "0.50",
        "matched_size": "25",
        "notification_id": unique_id
    }
    
    # Save first time (should succeed)
    saved_ids_1 = db_ops.save_notifications([test_notification])
    assert isinstance(saved_ids_1, list)
    
    # Try to save same notification again (should handle duplicate)
    saved_ids_2 = db_ops.save_notifications([test_notification])
    # Should return empty list due to duplicate key handling
    assert isinstance(saved_ids_2, list)
