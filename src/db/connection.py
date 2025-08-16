import os
import time
import logging
from typing import Optional, Dict, Any
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import (
    ConnectionFailure, 
    ServerSelectionTimeoutError, 
    NetworkTimeout,
)
from ..config import get_config


class DatabaseConnectionManager:
    """Enhanced database connection manager with retry logic and connection pooling"""
    
    _client: Optional[MongoClient] = None
    _database: Optional[Database] = None
    _connection_attempts = 0
    _max_connection_attempts = 5
    _retry_delay_base = 2  # Base delay in seconds for exponential backoff
    
    @classmethod
    def _get_connection_config(cls) -> Dict[str, Any]:
        """Get MongoDB connection configuration with pooling settings"""
        config = get_config()
        
        return {
            'host': config.get("database.mongo_url", "mongodb://localhost:27017"),
            'serverSelectionTimeoutMS': 5000,  # 5 second timeout
            'connectTimeoutMS': 10000,  # 10 second connection timeout
            'socketTimeoutMS': 30000,   # 30 second socket timeout
            'maxPoolSize': 10,          # Maximum connections in pool
            'minPoolSize': 1,           # Minimum connections in pool
            'maxIdleTimeMS': 300000,    # 5 minutes max idle time
            'retryWrites': True,        # Enable retryable writes
            'retryReads': True,         # Enable retryable reads
            'w': 'majority',            # Write concern for durability
            'journal': True,            # Ensure writes are journaled
        }
    
    @classmethod
    def get_client(cls, force_reconnect: bool = False) -> MongoClient:
        """Get MongoDB client with retry logic and connection pooling"""
        logger = logging.getLogger(__name__)
        
        if cls._client is not None and not force_reconnect:
            try:
                # Test the connection
                cls._client.admin.command('ping')
                cls._connection_attempts = 0  # Reset on successful ping
                return cls._client
            except (ConnectionFailure, ServerSelectionTimeoutError) as e:
                logger.warning(f"Existing connection failed ping test: {e}")
                cls._close_client()
        
        # Attempt to create new connection with retry logic
        for attempt in range(cls._max_connection_attempts):
            try:
                logger.info(f"Attempting database connection (attempt {attempt + 1}/{cls._max_connection_attempts})")
                
                connection_config = cls._get_connection_config()
                cls._client = MongoClient(**connection_config)
                
                # Test the connection
                cls._client.admin.command('ping')
                
                logger.info("Database connection established successfully")
                cls._connection_attempts = 0
                return cls._client
                
            except (ConnectionFailure, ServerSelectionTimeoutError, NetworkTimeout) as e:
                cls._connection_attempts += 1
                
                if attempt < cls._max_connection_attempts - 1:
                    # Calculate exponential backoff delay
                    delay = cls._retry_delay_base ** (attempt + 1)
                    logger.warning(
                        f"Database connection attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {delay} seconds..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"All database connection attempts failed. Last error: {e}")
                    raise ConnectionFailure(f"Failed to connect to database after {cls._max_connection_attempts} attempts")
            
            except Exception as e:
                logger.error(f"Unexpected error during database connection: {e}")
                raise
        
        raise ConnectionFailure("Failed to establish database connection")
    
    @classmethod
    def get_database(cls, db_name: str = None, force_reconnect: bool = False) -> Database:
        """Get database instance with retry logic"""
        logger = logging.getLogger(__name__)
        
        try:
            client = cls.get_client(force_reconnect)
            
            if db_name is None:
                config = get_config()
                db_name = config.get("database.db_name", "polymarket_notifications")
            
            cls._database = client[db_name]
            
            # Test database access
            cls._database.command('ping')
            
            return cls._database
            
        except Exception as e:
            logger.error(f"Failed to get database instance: {e}")
            raise
    
    @classmethod
    def _close_client(cls):
        """Internal method to close client connection"""
        if cls._client:
            try:
                cls._client.close()
            except Exception:
                pass  # Ignore errors when closing
            finally:
                cls._client = None
                cls._database = None
    
    @classmethod
    def close_connection(cls):
        """Close database connection and cleanup resources"""
        logger = logging.getLogger(__name__)
        logger.info("Closing database connection")
        cls._close_client()
    
    @classmethod
    def get_connection_stats(cls) -> Dict[str, Any]:
        """Get connection pool statistics"""
        if cls._client is None:
            return {"status": "disconnected"}
        
        try:
            # Get server status
            server_status = cls._client.admin.command('serverStatus')
            
            return {
                "status": "connected",
                "connection_attempts": cls._connection_attempts,
                "server_version": server_status.get('version', 'unknown'),
                "uptime_seconds": server_status.get('uptime', 0),
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "connection_attempts": cls._connection_attempts
            }


# Backward compatibility
class DatabaseConnection(DatabaseConnectionManager):
    """Backward compatibility wrapper"""
    pass


def get_database(db_name: str = None) -> Database:
    """Get MongoDB database instance"""
    return DatabaseConnectionManager.get_database(db_name)
