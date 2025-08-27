#!/usr/bin/env python3
"""
Multi-User Database Management for TGTG Bot
Handles user registration, credentials, and per-user notification tracking.
"""

import os
import json
import sqlite3
import hashlib
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from contextlib import contextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultiUserDatabase:
    """Manages multi-user database for TGTG bot."""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Keep the database in the multi_user directory
            db_path = os.path.join(os.path.dirname(__file__), 'multi_user.db')
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize the multi-user database with required tables."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    telegram_chat_id TEXT UNIQUE NOT NULL,
                    tgtg_email TEXT,
                    tgtg_credentials TEXT,  -- JSON string of TGTG credentials
                    timezone TEXT DEFAULT 'Europe/Berlin',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            # User-specific offer notifications (separate from global database)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    store_id TEXT NOT NULL,
                    item_id TEXT NOT NULL,
                    pickup_start TEXT NOT NULL,
                    pickup_end TEXT NOT NULL,
                    offer_hash TEXT NOT NULL,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    UNIQUE(user_id, offer_hash)
                )
            ''')
            
            # User reservations tracking
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_reservations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    order_id TEXT NOT NULL,
                    item_id TEXT NOT NULL,
                    store_name TEXT NOT NULL,
                    reserved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    auto_cancel_at TIMESTAMP,
                    status TEXT DEFAULT 'active',  -- active, cancelled, expired
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            conn.commit()
            logger.info("✅ Multi-user database initialized")
    
    @contextmanager
    def _get_connection(self):
        """Get a database connection with proper error handling."""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def register_user(self, telegram_chat_id: str, tgtg_email: str = None) -> Dict[str, Any]:
        """
        Register or update a user in the database.
        
        Args:
            telegram_chat_id (str): User's Telegram chat ID
            tgtg_email (str): User's TGTG email (optional)
            
        Returns:
            Dict[str, Any]: User data or error info
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if user already exists
                cursor.execute(
                    'SELECT * FROM users WHERE telegram_chat_id = ?',
                    (telegram_chat_id,)
                )
                existing_user = cursor.fetchone()
                
                if existing_user:
                    # Update existing user
                    cursor.execute('''
                        UPDATE users 
                        SET tgtg_email = COALESCE(?, tgtg_email),
                            last_active = CURRENT_TIMESTAMP,
                            is_active = 1
                        WHERE telegram_chat_id = ?
                    ''', (tgtg_email, telegram_chat_id))
                    
                    user_id = existing_user['user_id']
                    logger.info(f"👤 Updated existing user: {telegram_chat_id}")
                else:
                    # Create new user
                    cursor.execute('''
                        INSERT INTO users (telegram_chat_id, tgtg_email)
                        VALUES (?, ?)
                    ''', (telegram_chat_id, tgtg_email))
                    
                    user_id = cursor.lastrowid
                    logger.info(f"👤 Registered new user: {telegram_chat_id}")
                
                conn.commit()
                
                # Return user data
                return {
                    'success': True,
                    'user_id': user_id,
                    'telegram_chat_id': telegram_chat_id,
                    'tgtg_email': tgtg_email,
                    'is_new': existing_user is None
                }
                
        except Exception as e:
            logger.error(f"Failed to register user {telegram_chat_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_user_by_chat_id(self, telegram_chat_id: str) -> Optional[Dict[str, Any]]:
        """Get user data by Telegram chat ID."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT * FROM users WHERE telegram_chat_id = ? AND is_active = 1',
                    (telegram_chat_id,)
                )
                row = cursor.fetchone()
                
                if row:
                    return dict(row)
                return None
                
        except Exception as e:
            logger.error(f"Failed to get user {telegram_chat_id}: {e}")
            return None
    
    def save_user_credentials(self, user_id: int, credentials: Dict[str, Any]) -> bool:
        """Save TGTG credentials for a user."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE users 
                    SET tgtg_credentials = ?,
                        last_active = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                ''', (json.dumps(credentials), user_id))
                
                conn.commit()
                logger.info(f"💾 Saved credentials for user {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to save credentials for user {user_id}: {e}")
            return False
    
    def update_user_email(self, user_id: int, email: str) -> bool:
        """Update user's TGTG email."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE users 
                    SET tgtg_email = ?,
                        last_active = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                ''', (email, user_id))
                
                conn.commit()
                logger.info(f"💾 Updated email for user {user_id}: {email}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to update email for user {user_id}: {e}")
            return False
    
    def get_user_credentials(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get TGTG credentials for a user."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT tgtg_credentials FROM users WHERE user_id = ? AND is_active = 1',
                    (user_id,)
                )
                row = cursor.fetchone()
                
                if row and row['tgtg_credentials']:
                    return json.loads(row['tgtg_credentials'])
                return None
                
        except Exception as e:
            logger.error(f"Failed to get credentials for user {user_id}: {e}")
            return None
    
    def is_offer_already_sent(self, user_id: int, store_id: str, item_id: str, 
                             pickup_start: str, pickup_end: str) -> bool:
        """Check if an offer was already sent to a specific user."""
        try:
            # Create hash for this specific offer
            offer_data = f"{store_id}:{item_id}:{pickup_start}:{pickup_end}"
            offer_hash = hashlib.md5(offer_data.encode()).hexdigest()
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT COUNT(*) as count FROM user_notifications 
                    WHERE user_id = ? AND offer_hash = ?
                ''', (user_id, offer_hash))
                
                result = cursor.fetchone()
                return result['count'] > 0
                
        except Exception as e:
            logger.error(f"Failed to check offer for user {user_id}: {e}")
            return False
    
    def record_sent_offer(self, user_id: int, offer: Dict[str, Any]) -> bool:
        """Record that an offer was sent to a specific user."""
        try:
            store_id = offer['store']['store_id']
            item_id = offer['item']['item_id']
            pickup_interval = offer.get('pickup_interval', {})
            pickup_start = pickup_interval.get('start', '')
            pickup_end = pickup_interval.get('end', '')
            
            # Create hash for this specific offer
            offer_data = f"{store_id}:{item_id}:{pickup_start}:{pickup_end}"
            offer_hash = hashlib.md5(offer_data.encode()).hexdigest()
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR IGNORE INTO user_notifications 
                    (user_id, store_id, item_id, pickup_start, pickup_end, offer_hash)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, store_id, item_id, pickup_start, pickup_end, offer_hash))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Failed to record offer for user {user_id}: {e}")
            return False
    
    def cleanup_old_offers(self, user_id: int, days_to_keep: int = 7) -> int:
        """Clean up old offer records for a specific user."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM user_notifications 
                    WHERE user_id = ? AND sent_at < ?
                ''', (user_id, cutoff_date))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                if deleted_count > 0:
                    logger.info(f"🧹 Cleaned up {deleted_count} old offers for user {user_id}")
                
                return deleted_count
                
        except Exception as e:
            logger.error(f"Failed to cleanup offers for user {user_id}: {e}")
            return 0
    
    def get_all_active_users(self) -> List[Dict[str, Any]]:
        """Get all active users."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM users 
                    WHERE is_active = 1 AND tgtg_credentials IS NOT NULL
                    ORDER BY last_active DESC
                ''')
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Failed to get active users: {e}")
            return []
    
    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Get statistics for a specific user."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Get notification count
                cursor.execute('''
                    SELECT COUNT(*) as notification_count 
                    FROM user_notifications 
                    WHERE user_id = ?
                ''', (user_id,))
                notification_count = cursor.fetchone()['notification_count']
                
                # Get reservation count
                cursor.execute('''
                    SELECT COUNT(*) as reservation_count 
                    FROM user_reservations 
                    WHERE user_id = ?
                ''', (user_id,))
                reservation_count = cursor.fetchone()['reservation_count']
                
                # Get user info
                cursor.execute('''
                    SELECT created_at, last_active 
                    FROM users 
                    WHERE user_id = ?
                ''', (user_id,))
                user_info = cursor.fetchone()
                
                return {
                    'user_id': user_id,
                    'notification_count': notification_count,
                    'reservation_count': reservation_count,
                    'created_at': user_info['created_at'] if user_info else None,
                    'last_active': user_info['last_active'] if user_info else None
                }
                
        except Exception as e:
            logger.error(f"Failed to get stats for user {user_id}: {e}")
            return {}

# Global database instance
_multi_user_db: Optional[MultiUserDatabase] = None

def get_multi_user_db() -> MultiUserDatabase:
    """Get or create the global MultiUserDatabase instance."""
    global _multi_user_db
    if _multi_user_db is None:
        _multi_user_db = MultiUserDatabase()
    return _multi_user_db

if __name__ == "__main__":
    # Test the multi-user database
    print("🧪 Testing Multi-User Database")
    
    db = MultiUserDatabase()
    
    # Test user registration
    result = db.register_user("123456789", "test@example.com")
    print(f"Registration result: {result}")
    
    # Test user lookup
    user = db.get_user_by_chat_id("123456789")
    print(f"User lookup: {user}")
    
    print("✅ Multi-user database test completed!")
