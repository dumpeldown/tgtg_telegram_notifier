#!/usr/bin/env python3
"""
Multi-User Database Management Script for TGTG
Provides tools to inspect, manage, and analyze the multi-user TGTG system database.
"""

import sys
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multi_user.multi_user_db import get_multi_user_db
from common.telegram_notify import notify_to_chat

class MultiUserDBManager:
    """Manager for multi-user database operations."""
    
    def __init__(self):
        self.db = get_multi_user_db()
    
    def show_database_overview(self):
        """Show general database statistics and overview."""
        print("🗄️ Multi-User TGTG Database Overview")
        print("=" * 50)
        
        try:
            # Get database file info
            db_path = self.db.db_path
            if os.path.exists(db_path):
                db_size = os.path.getsize(db_path) / (1024 * 1024)  # MB
                print(f"📁 Database file: {db_path}")
                print(f"💾 Database size: {db_size:.2f} MB")
            else:
                print(f"❌ Database file not found: {db_path}")
                return
            
            # Get users count
            users = self.db.get_all_active_users()
            total_users = len(users)
            print(f"👥 Total active users: {total_users}")
            
            if total_users == 0:
                print("📭 No users registered in the system")
                return
            
            # Get total notifications and reservations
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                
                # Total notifications
                cursor.execute('SELECT COUNT(*) as count FROM user_notifications')
                total_notifications = cursor.fetchone()['count']
                
                # Total reservations
                cursor.execute('SELECT COUNT(*) as count FROM user_reservations')
                total_reservations = cursor.fetchone()['count']
                
                # Recent activity (last 24h)
                cursor.execute('''
                    SELECT COUNT(*) as count 
                    FROM user_notifications 
                    WHERE sent_at > datetime('now', '-24 hours')
                ''')
                notifications_24h = cursor.fetchone()['count']
                
                cursor.execute('''
                    SELECT COUNT(*) as count 
                    FROM user_reservations 
                    WHERE reserved_at > datetime('now', '-24 hours')
                ''')
                reservations_24h = cursor.fetchone()['count']
                
                print(f"📧 Total notifications sent: {total_notifications}")
                print(f"🛍️ Total reservations made: {total_reservations}")
                print(f"🕐 Notifications (last 24h): {notifications_24h}")
                print(f"🛒 Reservations (last 24h): {reservations_24h}")
                
        except Exception as e:
            print(f"❌ Error getting database overview: {e}")
    
    def show_users_list(self, show_credentials: bool = False):
        """Show list of all registered users."""
        print("👥 Registered Users")
        print("=" * 40)
        
        try:
            users = self.db.get_all_active_users()
            
            if not users:
                print("📭 No users registered")
                return
            
            for i, user in enumerate(users, 1):
                user_id = user['user_id']
                chat_id = user['telegram_chat_id']
                email = user.get('tgtg_email', 'Not set')
                created = user.get('created_at', 'Unknown')
                last_active = user.get('last_active', 'Unknown')
                timezone = user.get('timezone', 'Europe/Berlin')
                
                print(f"{i}. User ID: {user_id}")
                print(f"   📱 Chat ID: {chat_id}")
                print(f"   📧 Email: {email}")
                print(f"   🌍 Timezone: {timezone}")
                print(f"   📅 Registered: {created}")
                print(f"   🕐 Last active: {last_active}")
                
                if show_credentials:
                    credentials = self.db.get_user_credentials(user_id)
                    if credentials:
                        print(f"   🔑 Has credentials: ✅")
                        print(f"       Access token: {credentials.get('access_token', 'N/A')[:20]}...")
                        print(f"       Refresh token: {credentials.get('refresh_token', 'N/A')[:20]}...")
                    else:
                        print(f"   🔑 Has credentials: ❌")
                
                # Get user stats
                stats = self.db.get_user_stats(user_id)
                print(f"   📊 Notifications: {stats.get('notification_count', 0)}")
                print(f"   🛍️ Reservations: {stats.get('reservation_count', 0)}")
                print()
                
        except Exception as e:
            print(f"❌ Error getting users list: {e}")
    
    def show_user_details(self, user_identifier: str):
        """Show detailed information for a specific user."""
        print(f"🔍 User Details: {user_identifier}")
        print("=" * 40)
        
        try:
            # Try to find user by chat_id first, then by user_id
            user = None
            if user_identifier.isdigit() and len(user_identifier) < 10:
                # Looks like user_id
                users = self.db.get_all_active_users()
                user = next((u for u in users if u['user_id'] == int(user_identifier)), None)
            else:
                # Try chat_id
                user = self.db.get_user_by_chat_id(user_identifier)
            
            if not user:
                print(f"❌ User not found: {user_identifier}")
                return
            
            user_id = user['user_id']
            
            # Basic info
            print("📋 Basic Information:")
            print(f"   User ID: {user_id}")
            print(f"   📱 Chat ID: {user['telegram_chat_id']}")
            print(f"   📧 Email: {user.get('tgtg_email', 'Not set')}")
            print(f"   🌍 Timezone: {user.get('timezone', 'Europe/Berlin')}")
            print(f"   📅 Registered: {user.get('created_at', 'Unknown')}")
            print(f"   🕐 Last active: {user.get('last_active', 'Unknown')}")
            print(f"   ✅ Active: {user.get('is_active', False)}")
            print()
            
            # Credentials
            print("🔑 TGTG Credentials:")
            credentials = self.db.get_user_credentials(user_id)
            if credentials:
                print(f"   ✅ Has valid credentials")
                print(f"   Access token: {credentials.get('access_token', 'N/A')[:30]}...")
                print(f"   Refresh token: {credentials.get('refresh_token', 'N/A')[:30]}...")
                print(f"   User ID: {credentials.get('user_id', 'N/A')}")
                print(f"   Cookie: {'Present' if credentials.get('cookie') else 'Missing'}")
            else:
                print(f"   ❌ No credentials stored")
            print()
            
            # Statistics
            stats = self.db.get_user_stats(user_id)
            print("📊 Statistics:")
            print(f"   📧 Total notifications: {stats.get('notification_count', 0)}")
            print(f"   🛍️ Total reservations: {stats.get('reservation_count', 0)}")
            print()
            
            # Recent notifications
            self._show_user_notifications(user_id, hours=168)  # Last 7 days
            
            # Recent reservations
            self._show_user_reservations(user_id)
            
        except Exception as e:
            print(f"❌ Error getting user details: {e}")
    
    def _show_user_notifications(self, user_id: int, hours: int = 24):
        """Show recent notifications for a user."""
        print(f"📧 Recent Notifications (Last {hours} hours):")
        
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT store_id, item_id, pickup_start, pickup_end, sent_at, offer_hash
                    FROM user_notifications 
                    WHERE user_id = ? 
                      AND sent_at > datetime('now', '-{} hours')
                    ORDER BY sent_at DESC 
                    LIMIT 10
                '''.format(hours), (user_id,))
                
                notifications = cursor.fetchall()
                
                if notifications:
                    for notification in notifications:
                        sent_time = datetime.fromisoformat(notification['sent_at'].replace('Z', ''))
                        print(f"   🍽️ Store ID: {notification['store_id']}")
                        print(f"      Item ID: {notification['item_id']}")
                        print(f"      Pickup: {notification['pickup_start']} - {notification['pickup_end']}")
                        print(f"      Sent: {sent_time.strftime('%Y-%m-%d %H:%M:%S')}")
                        print(f"      Hash: {notification['offer_hash'][:16]}...")
                        print()
                else:
                    print(f"   📭 No notifications in the last {hours} hours")
                    
        except Exception as e:
            print(f"❌ Error getting notifications: {e}")
        print()
    
    def _show_user_reservations(self, user_id: int):
        """Show reservations for a user."""
        print("🛍️ Recent Reservations:")
        
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT order_id, item_id, store_name, reserved_at, auto_cancel_at, status
                    FROM user_reservations 
                    WHERE user_id = ?
                    ORDER BY reserved_at DESC 
                    LIMIT 10
                ''', (user_id,))
                
                reservations = cursor.fetchall()
                
                if reservations:
                    for reservation in reservations:
                        reserved_time = datetime.fromisoformat(reservation['reserved_at'].replace('Z', ''))
                        cancel_time = reservation['auto_cancel_at']
                        if cancel_time:
                            cancel_time = datetime.fromisoformat(cancel_time.replace('Z', ''))
                        
                        print(f"   🛒 Order ID: {reservation['order_id']}")
                        print(f"      Store: {reservation['store_name']}")
                        print(f"      Item ID: {reservation['item_id']}")
                        print(f"      Reserved: {reserved_time.strftime('%Y-%m-%d %H:%M:%S')}")
                        if cancel_time:
                            print(f"      Auto-cancel: {cancel_time.strftime('%Y-%m-%d %H:%M:%S')}")
                        print(f"      Status: {reservation['status']}")
                        print()
                else:
                    print("   📭 No reservations found")
                    
        except Exception as e:
            print(f"❌ Error getting reservations: {e}")
        print()
    
    def show_system_stats(self):
        """Show comprehensive system statistics."""
        print("📈 System Statistics")
        print("=" * 40)
        
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                
                # Users statistics
                cursor.execute('SELECT COUNT(*) as count FROM users WHERE is_active = 1')
                active_users = cursor.fetchone()['count']
                
                cursor.execute('SELECT COUNT(*) as count FROM users')
                total_users = cursor.fetchone()['count']
                
                print(f"👥 Active users: {active_users}/{total_users}")
                
                # Notifications by time period
                periods = [
                    ('Last hour', 1),
                    ('Last 24 hours', 24),
                    ('Last 7 days', 24*7),
                    ('Last 30 days', 24*30)
                ]
                
                print("\n📧 Notifications:")
                for period_name, hours in periods:
                    cursor.execute('''
                        SELECT COUNT(*) as count 
                        FROM user_notifications 
                        WHERE sent_at > datetime('now', '-{} hours')
                    '''.format(hours))
                    count = cursor.fetchone()['count']
                    print(f"   {period_name}: {count}")
                
                # Reservations by time period
                print("\n🛍️ Reservations:")
                for period_name, hours in periods:
                    cursor.execute('''
                        SELECT COUNT(*) as count 
                        FROM user_reservations 
                        WHERE reserved_at > datetime('now', '-{} hours')
                    '''.format(hours))
                    count = cursor.fetchone()['count']
                    print(f"   {period_name}: {count}")
                
                # Top stores by notifications
                print("\n🏪 Top Stores (by notifications):")
                cursor.execute('''
                    SELECT store_id, COUNT(*) as count
                    FROM user_notifications
                    GROUP BY store_id
                    ORDER BY count DESC
                    LIMIT 10
                ''')
                top_stores = cursor.fetchall()
                for i, store in enumerate(top_stores, 1):
                    print(f"   {i}. Store ID {store['store_id']}: {store['count']} notifications")
                
                # Reservation status distribution
                print("\n📊 Reservation Status:")
                cursor.execute('''
                    SELECT status, COUNT(*) as count
                    FROM user_reservations
                    GROUP BY status
                    ORDER BY count DESC
                ''')
                status_counts = cursor.fetchall()
                for status in status_counts:
                    print(f"   {status['status']}: {status['count']}")
                
        except Exception as e:
            print(f"❌ Error getting system stats: {e}")
    
    def cleanup_old_data(self, days_to_keep: int = 30):
        """Clean up old notifications and reservations."""
        print(f"🧹 Cleaning up data older than {days_to_keep} days...")
        
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                
                # Clean up old notifications
                cursor.execute('''
                    DELETE FROM user_notifications 
                    WHERE sent_at < datetime('now', '-{} days')
                '''.format(days_to_keep))
                notifications_deleted = cursor.rowcount
                
                # Clean up old completed/cancelled reservations
                cursor.execute('''
                    DELETE FROM user_reservations 
                    WHERE reserved_at < datetime('now', '-{} days')
                    AND status IN ('cancelled', 'expired')
                '''.format(days_to_keep))
                reservations_deleted = cursor.rowcount
                
                conn.commit()
                
                print(f"✅ Deleted {notifications_deleted} old notifications")
                print(f"✅ Deleted {reservations_deleted} old reservations")
                
                total_deleted = notifications_deleted + reservations_deleted
                if total_deleted > 0:
                    print(f"🎉 Total records cleaned up: {total_deleted}")
                else:
                    print("📭 No old records to clean up")
                
        except Exception as e:
            print(f"❌ Error during cleanup: {e}")
    
    def test_database(self):
        """Test database functionality."""
        print("🧪 Testing Multi-User Database")
        print("=" * 40)
        
        try:
            # Test database connection
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT 1')
                print("✅ Database connection: OK")
            
            # Test user registration
            test_chat_id = "test_999999"
            test_email = "test@example.com"
            
            # Clean up any existing test user
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM users WHERE telegram_chat_id = ?', (test_chat_id,))
                conn.commit()
            
            user = self.db.register_user(test_chat_id, test_email)
            print(f"✅ User registration: OK (ID: {user.get('user_id')})")
            
            # Test user retrieval
            retrieved_user = self.db.get_user_by_chat_id(test_chat_id)
            print(f"✅ User retrieval: {'OK' if retrieved_user else 'Failed'}")
            
            # Test credentials (mock)
            test_credentials = {
                'access_token': 'test_access_token',
                'refresh_token': 'test_refresh_token',
                'user_id': 12345,
                'cookie': 'test_cookie'
            }
            
            success = self.db.save_user_credentials(user['user_id'], test_credentials)
            print(f"✅ Credentials saving: {'OK' if success else 'Failed'}")
            
            # Test credentials retrieval
            retrieved_creds = self.db.get_user_credentials(user['user_id'])
            print(f"✅ Credentials retrieval: {'OK' if retrieved_creds else 'Failed'}")
            
            # Test stats
            stats = self.db.get_user_stats(user['user_id'])
            print(f"✅ User stats: {'OK' if stats else 'Failed'}")
            
            # Clean up test user
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM users WHERE telegram_chat_id = ?', (test_chat_id,))
                conn.commit()
            
            print("\n🎉 All database tests passed!")
            
        except Exception as e:
            print(f"❌ Database test failed: {e}")
    
    def export_user_data(self, user_identifier: str, output_file: str = None):
        """Export all data for a specific user."""
        print(f"📤 Exporting data for user: {user_identifier}")
        
        try:
            # Find user
            user = None
            if user_identifier.isdigit() and len(user_identifier) < 10:
                users = self.db.get_all_active_users()
                user = next((u for u in users if u['user_id'] == int(user_identifier)), None)
            else:
                user = self.db.get_user_by_chat_id(user_identifier)
            
            if not user:
                print(f"❌ User not found: {user_identifier}")
                return
            
            user_id = user['user_id']
            
            # Gather all user data
            export_data = {
                'user_info': user,
                'credentials': self.db.get_user_credentials(user_id),
                'stats': self.db.get_user_stats(user_id),
                'notifications': [],
                'reservations': []
            }
            
            # Get notifications
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM user_notifications WHERE user_id = ? ORDER BY sent_at DESC
                ''', (user_id,))
                export_data['notifications'] = [dict(row) for row in cursor.fetchall()]
                
                cursor.execute('''
                    SELECT * FROM user_reservations WHERE user_id = ? ORDER BY reserved_at DESC
                ''', (user_id,))
                export_data['reservations'] = [dict(row) for row in cursor.fetchall()]
            
            # Export to file
            if not output_file:
                output_file = f"user_data_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            print(f"✅ User data exported to: {output_file}")
            print(f"📊 Exported {len(export_data['notifications'])} notifications")
            print(f"📊 Exported {len(export_data['reservations'])} reservations")
            
        except Exception as e:
            print(f"❌ Error exporting user data: {e}")

def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("🗄️ Multi-User TGTG Database Management Tool")
        print("=" * 50)
        print("Usage: python multi_user_db_manage.py <command> [options]")
        print()
        print("Commands:")
        print("  overview              - Show database overview and statistics")
        print("  users                 - List all registered users")
        print("  users --credentials   - List users with credential status")
        print("  user <chat_id|user_id> - Show detailed user information")
        print("  stats                 - Show comprehensive system statistics")
        print("  cleanup [days]        - Clean up old data (default: 30 days)")
        print("  test                  - Test database functionality")
        print("  export <chat_id|user_id> [file] - Export user data to JSON")
        print()
        print("Examples:")
        print("  python multi_user_db_manage.py overview")
        print("  python multi_user_db_manage.py users")
        print("  python multi_user_db_manage.py user 123456789")
        print("  python multi_user_db_manage.py cleanup 14")
        print("  python multi_user_db_manage.py export 123456789")
        return
    
    manager = MultiUserDBManager()
    command = sys.argv[1].lower()
    
    if command == "overview":
        manager.show_database_overview()
        
    elif command == "users":
        show_creds = len(sys.argv) > 2 and sys.argv[2] == "--credentials"
        manager.show_users_list(show_credentials=show_creds)
        
    elif command == "user":
        if len(sys.argv) < 3:
            print("❌ Please provide a chat ID or user ID")
            return
        manager.show_user_details(sys.argv[2])
        
    elif command == "stats":
        manager.show_system_stats()
        
    elif command == "cleanup":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        manager.cleanup_old_data(days)
        
    elif command == "test":
        manager.test_database()
        
    elif command == "export":
        if len(sys.argv) < 3:
            print("❌ Please provide a chat ID or user ID")
            return
        output_file = sys.argv[3] if len(sys.argv) > 3 else None
        manager.export_user_data(sys.argv[2], output_file)
        
    else:
        print(f"❌ Unknown command: {command}")
        print("Run without arguments to see available commands")

if __name__ == "__main__":
    main()
