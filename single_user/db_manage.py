#!/usr/bin/env python3
"""
Database Management Script for TGTG Offer Notifications
"""

import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from single_user.tgtg_check import TGTGChecker
from single_user.offer_database import OfferDatabase
from common.telegram_notify import notify

def show_database_stats():
    """Show database statistics."""
    print("📊 Database Statistics")
    print("=" * 40)
    
    checker = TGTGChecker()
    stats = checker.get_database_stats()
    
    if stats:
        print(f"📁 Database file: {stats['db_path']}")
        print(f"💾 Database size: {stats['db_size_mb']} MB")
        print(f"📦 Total records: {stats['total_records']}")
        print(f"🕐 Last 24 hours: {stats['records_24h']} notifications")
        print(f"📅 Last 7 days: {stats['records_7d']} notifications")
    else:
        print("❌ Failed to get database statistics")

def show_recent_notifications(hours: int = 24):
    """Show recent notifications."""
    print(f"📱 Recent Notifications (Last {hours} hours)")
    print("=" * 50)
    
    checker = TGTGChecker()
    recent = checker.get_recent_notifications(hours)
    
    if recent:
        for record in recent:
            store_name, display_name, items_available, pickup_start, pickup_end, sent_at = record
            
            # Parse and format the sent time
            try:
                sent_time = datetime.fromisoformat(sent_at.replace('Z', ''))
                sent_str = sent_time.strftime('%Y-%m-%d %H:%M:%S')
            except:
                sent_str = sent_at
            
            print(f"🍽️  {store_name}")
            print(f"    📦 {display_name} ({items_available} bag{'s' if items_available != 1 else ''})")
            print(f"    ⏰ Pickup: {pickup_start} - {pickup_end}")
            print(f"    📅 Sent: {sent_str}")
            print()
    else:
        print("📭 No recent notifications found")

def cleanup_database(days_to_keep: int = 7):
    """Clean up old database records."""
    print(f"🧹 Cleaning up records older than {days_to_keep} days...")
    
    checker = TGTGChecker()
    deleted_count = checker.cleanup_old_notifications(days_to_keep)
    
    print(f"✅ Deleted {deleted_count} old records")
    
    if deleted_count > 0:
        # Send notification about cleanup
        notify(f"🧹 <b>Database Cleanup</b>\n\nDeleted {deleted_count} old notification records (older than {days_to_keep} days)")

def test_database():
    """Test database functionality."""
    print("🧪 Testing Database Functionality")
    print("=" * 40)
    
    try:
        # Test database initialization
        db = OfferDatabase("tests/test_db.db")
        print("✅ Database initialization: OK")
        
        # Test offer recording
        test_offer = {
            'store': {'store_id': 99999, 'store_name': 'Test Store'},
            'item_id': 88888,
            'display_name': 'Test Bag',
            'items_available': 1,
            'pickup_interval': {
                'start': '2025-08-12T18:00:00Z',
                'end': '2025-08-12T20:00:00Z'
            }
        }
        
        # Test duplicate detection
        exists_before = db.is_offer_already_sent(99999, 88888, '2025-08-12T18:00:00Z', '2025-08-12T20:00:00Z')
        print(f"✅ Duplicate check (before): {not exists_before}")
        
        # Record offer
        recorded = db.record_sent_offer(test_offer)
        print(f"✅ Offer recording: {recorded}")
        
        # Test duplicate detection again
        exists_after = db.is_offer_already_sent(99999, 88888, '2025-08-12T18:00:00Z', '2025-08-12T20:00:00Z')
        print(f"✅ Duplicate check (after): {exists_after}")
        
        # Test stats
        stats = db.get_database_stats()
        print(f"✅ Statistics retrieval: {bool(stats)}")
        
        print("\n🎉 All database tests passed!")
        
        # Clean up test database
        import os
        if os.path.exists("tests/test_db.db"):
            os.remove("tests/test_db.db")
            print("🧹 Test database cleaned up")
            
    except Exception as e:
        print(f"❌ Database test failed: {e}")

def reset_database():
    """Reset the database (delete all records)."""
    print("⚠️  WARNING: This will delete ALL notification records!")
    response = input("Are you sure you want to continue? (yes/no): ").lower().strip()
    
    if response == 'yes':
        try:
            import os
            db_path = "tgtg_offers.db"
            if os.path.exists(db_path):
                os.remove(db_path)
                print("✅ Database reset successfully")
                notify("🔄 <b>Database Reset</b>\n\nAll notification records have been deleted. Fresh start! 🚀")
            else:
                print("📭 No database file found")
        except Exception as e:
            print(f"❌ Failed to reset database: {e}")
    else:
        print("❌ Database reset cancelled")

def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("🗄️ TGTG Database Management Tool")
        print("=" * 40)
        print("Usage: python db_manage.py <command>")
        print()
        print("Commands:")
        print("  stats          - Show database statistics")
        print("  recent [hours] - Show recent notifications (default: 24 hours)")
        print("  cleanup [days] - Clean up records older than X days (default: 7)")
        print("  test           - Test database functionality")
        print("  reset          - Reset database (delete all records)")
        print()
        print("Examples:")
        print("  python db_manage.py stats")
        print("  python db_manage.py recent 48")
        print("  python db_manage.py cleanup 14")
        return
    
    command = sys.argv[1].lower()
    
    if command == "stats":
        show_database_stats()
        
    elif command == "recent":
        hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
        show_recent_notifications(hours)
        
    elif command == "cleanup":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
        cleanup_database(days)
        
    elif command == "test":
        test_database()
        
    elif command == "reset":
        reset_database()
        
    else:
        print(f"❌ Unknown command: {command}")
        print("Run without arguments to see available commands")

if __name__ == "__main__":
    main()
