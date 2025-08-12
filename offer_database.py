import sqlite3
import logging
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
import os

logger = logging.getLogger(__name__)

class OfferDatabase:
    """SQLite database manager for tracking sent TGTG offer notifications."""
    
    def __init__(self, db_path: str = "tgtg_offers.db"):
        """
        Initialize the offer database.
        
        Args:
            db_path (str): Path to the SQLite database file
        """
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize the database and create tables if they don't exist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create offers table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sent_offers (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        store_id INTEGER NOT NULL,
                        store_name TEXT NOT NULL,
                        item_id INTEGER NOT NULL,
                        display_name TEXT NOT NULL,
                        items_available INTEGER NOT NULL,
                        pickup_start TEXT,
                        pickup_end TEXT,
                        notification_sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        offer_hash TEXT NOT NULL,
                        UNIQUE(store_id, item_id, pickup_start, pickup_end)
                    )
                ''')
                
                # Create index for faster lookups
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_store_item_pickup 
                    ON sent_offers(store_id, item_id, pickup_start, pickup_end)
                ''')
                
                # Create index for cleanup operations
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_notification_sent_at 
                    ON sent_offers(notification_sent_at)
                ''')
                
                conn.commit()
                logger.info("✅ Offer database initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize offer database: {e}")
            raise
    
    def _generate_offer_hash(self, store_id: int, item_id: int, pickup_start: str, pickup_end: str) -> str:
        """
        Generate a unique hash for an offer.
        
        Args:
            store_id (int): Store ID
            item_id (int): Item ID  
            pickup_start (str): Pickup start time
            pickup_end (str): Pickup end time
            
        Returns:
            str: Unique offer hash
        """
        import hashlib
        offer_string = f"{store_id}_{item_id}_{pickup_start}_{pickup_end}"
        return hashlib.md5(offer_string.encode()).hexdigest()
    
    def is_offer_already_sent(self, store_id: int, item_id: int, pickup_start: str, pickup_end: str) -> bool:
        """
        Check if a notification for this offer has already been sent.
        
        Args:
            store_id (int): Store ID
            item_id (int): Item ID
            pickup_start (str): Pickup start time
            pickup_end (str): Pickup end time
            
        Returns:
            bool: True if notification was already sent, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT COUNT(*) FROM sent_offers 
                    WHERE store_id = ? AND item_id = ? AND pickup_start = ? AND pickup_end = ?
                ''', (store_id, item_id, pickup_start, pickup_end))
                
                count = cursor.fetchone()[0]
                return count > 0
                
        except Exception as e:
            logger.error(f"Failed to check if offer was already sent: {e}")
            return False  # If in doubt, allow sending to avoid missing offers
    
    def record_sent_offer(self, offer: dict) -> bool:
        """
        Record that a notification has been sent for this offer.
        
        Args:
            offer (dict): Offer data dictionary
            
        Returns:
            bool: True if recorded successfully, False otherwise
        """
        try:
            store_id = offer['store']['store_id']
            store_name = offer['store']['store_name']
            item_id = offer['item_id']
            display_name = offer['display_name']
            items_available = offer['items_available']
            
            # Get pickup times
            pickup_interval = offer.get('pickup_interval', {})
            pickup_start = pickup_interval.get('start', '')
            pickup_end = pickup_interval.get('end', '')
            
            # Generate offer hash
            offer_hash = self._generate_offer_hash(store_id, item_id, pickup_start, pickup_end)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO sent_offers 
                    (store_id, store_name, item_id, display_name, items_available, 
                     pickup_start, pickup_end, offer_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (store_id, store_name, item_id, display_name, items_available,
                      pickup_start, pickup_end, offer_hash))
                
                conn.commit()
                logger.debug(f"✅ Recorded sent offer: {store_name} - {display_name}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to record sent offer: {e}")
            return False
    
    def cleanup_old_offers(self, days_to_keep: int = 7) -> int:
        """
        Clean up old offer records to keep database size manageable.
        
        Args:
            days_to_keep (int): Number of days to keep records for
            
        Returns:
            int: Number of records deleted
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    DELETE FROM sent_offers 
                    WHERE notification_sent_at < ?
                ''', (cutoff_date.isoformat(),))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                if deleted_count > 0:
                    logger.info(f"🧹 Cleaned up {deleted_count} old offer records (older than {days_to_keep} days)")
                
                return deleted_count
                
        except Exception as e:
            logger.error(f"Failed to cleanup old offers: {e}")
            return 0
    
    def get_recent_offers(self, hours: int = 24) -> List[Tuple]:
        """
        Get recently sent offers for debugging/monitoring.
        
        Args:
            hours (int): Number of hours to look back
            
        Returns:
            List[Tuple]: List of recent offer records
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT store_name, display_name, items_available, 
                           pickup_start, pickup_end, notification_sent_at
                    FROM sent_offers 
                    WHERE notification_sent_at > ?
                    ORDER BY notification_sent_at DESC
                ''', (cutoff_time.isoformat(),))
                
                return cursor.fetchall()
                
        except Exception as e:
            logger.error(f"Failed to get recent offers: {e}")
            return []
    
    def get_database_stats(self) -> dict:
        """
        Get database statistics for monitoring.
        
        Returns:
            dict: Database statistics
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total records
                cursor.execute('SELECT COUNT(*) FROM sent_offers')
                total_records = cursor.fetchone()[0]
                
                # Records from last 24 hours
                cutoff_24h = datetime.now() - timedelta(hours=24)
                cursor.execute('''
                    SELECT COUNT(*) FROM sent_offers 
                    WHERE notification_sent_at > ?
                ''', (cutoff_24h.isoformat(),))
                records_24h = cursor.fetchone()[0]
                
                # Records from last 7 days
                cutoff_7d = datetime.now() - timedelta(days=7)
                cursor.execute('''
                    SELECT COUNT(*) FROM sent_offers 
                    WHERE notification_sent_at > ?
                ''', (cutoff_7d.isoformat(),))
                records_7d = cursor.fetchone()[0]
                
                # Database file size
                db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
                
                return {
                    'total_records': total_records,
                    'records_24h': records_24h,
                    'records_7d': records_7d,
                    'db_size_mb': round(db_size / (1024 * 1024), 2),
                    'db_path': self.db_path
                }
                
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}

if __name__ == "__main__":
    """Test the offer database functionality."""
    
    print("🗄️ Testing Offer Database...")
    
    # Initialize database
    db = OfferDatabase("test_offers.db")
    
    # Test offer data
    test_offer = {
        'store': {'store_id': 12345, 'store_name': 'Test Restaurant'},
        'item_id': 67890,
        'display_name': 'Test Surprise Bag',
        'items_available': 2,
        'pickup_interval': {
            'start': '2025-08-12T18:00:00Z',
            'end': '2025-08-12T20:00:00Z'
        }
    }
    
    # Test checking if offer exists (should be False initially)
    exists = db.is_offer_already_sent(12345, 67890, '2025-08-12T18:00:00Z', '2025-08-12T20:00:00Z')
    print(f"✅ Offer exists check (should be False): {exists}")
    
    # Record the offer
    recorded = db.record_sent_offer(test_offer)
    print(f"✅ Offer recorded: {recorded}")
    
    # Test checking again (should be True now)
    exists = db.is_offer_already_sent(12345, 67890, '2025-08-12T18:00:00Z', '2025-08-12T20:00:00Z')
    print(f"✅ Offer exists check (should be True): {exists}")
    
    # Get stats
    stats = db.get_database_stats()
    print(f"✅ Database stats: {stats}")
    
    print("\n🎉 Database test completed!")
    
    # Clean up test database
    if os.path.exists("test_offers.db"):
        os.remove("test_offers.db")
        print("🧹 Test database cleaned up")
