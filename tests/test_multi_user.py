#!/usr/bin/env python3
"""
Test script for Multi-User TGTG functionality.
Tests user registration, database operations, and notification system.
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multi_user.multi_user_db import MultiUserDatabase
from multi_user.multi_user_tgtg import MultiUserTGTGChecker
from common.telegram_notify import notify_to_chat

def test_database():
    """Test the multi-user database functionality."""
    print("🧪 Testing Multi-User Database")
    print("-" * 40)
    
    db = MultiUserDatabase()
    
    # Test user registration
    print("1. Testing user registration...")
    result1 = db.register_user("123456789", "test1@example.com")
    result2 = db.register_user("987654321", "test2@example.com")
    
    print(f"   User 1 registration: {'✅' if result1['success'] else '❌'}")
    print(f"   User 2 registration: {'✅' if result2['success'] else '❌'}")
    
    # Test user lookup
    print("\n2. Testing user lookup...")
    user1 = db.get_user_by_chat_id("123456789")
    user2 = db.get_user_by_chat_id("987654321")
    
    print(f"   User 1 lookup: {'✅' if user1 else '❌'}")
    print(f"   User 2 lookup: {'✅' if user2 else '❌'}")
    
    if user1:
        print(f"   User 1 ID: {user1['user_id']}, Email: {user1.get('tgtg_email')}")
    if user2:
        print(f"   User 2 ID: {user2['user_id']}, Email: {user2.get('tgtg_email')}")
    
    # Test offer tracking
    print("\n3. Testing offer tracking...")
    if user1:
        mock_offer = {
            'store': {'store_id': 'test_store_123'},
            'item_id': 'test_item_456',
            'pickup_interval': {
                'start': '2025-08-18T18:00:00Z',
                'end': '2025-08-18T19:00:00Z'
            }
        }
        
        # Check if offer already sent (should be False)
        already_sent_before = db.is_offer_already_sent(
            user1['user_id'], 'test_store_123', 'test_item_456',
            '2025-08-18T18:00:00Z', '2025-08-18T19:00:00Z'
        )
        
        # Record the offer
        record_success = db.record_sent_offer(user1['user_id'], mock_offer)
        
        # Check if offer already sent (should be True now)
        already_sent_after = db.is_offer_already_sent(
            user1['user_id'], 'test_store_123', 'test_item_456',
            '2025-08-18T18:00:00Z', '2025-08-18T19:00:00Z'
        )
        
        print(f"   Before recording: {'✅' if not already_sent_before else '❌'}")
        print(f"   Recording offer: {'✅' if record_success else '❌'}")
        print(f"   After recording: {'✅' if already_sent_after else '❌'}")
    
    # Test stats
    print("\n4. Testing user stats...")
    if user1:
        stats = db.get_user_stats(user1['user_id'])
        print(f"   User 1 stats: {stats}")
    
    print("\n✅ Database tests completed!")
    return db

def test_notifications():
    """Test the notification system."""
    print("\n🧪 Testing Multi-User Notifications")
    print("-" * 40)
    
    # Check environment variables
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN not found - skipping notification tests")
        return
    
    print("✅ Environment variables found")
    
    # Test notification to different chat IDs
    test_message = (
        f"🧪 <b>Multi-User Test Notification</b>\n\n"
        f"This is a test of the multi-user notification system.\n"
        f"Each user should only receive notifications for their own offers."
    )
    
    # Get the main chat ID from environment for testing
    main_chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if main_chat_id:
        print(f"📤 Sending test notification to {main_chat_id}...")
        success = notify_to_chat(test_message, main_chat_id)
        print(f"   Result: {'✅' if success else '❌'}")
    else:
        print("⚠️  No TELEGRAM_CHAT_ID found for notification testing")
    
    print("\n✅ Notification tests completed!")

def test_tgtg_checker():
    """Test the multi-user TGTG checker."""
    print("\n🧪 Testing Multi-User TGTG Checker")
    print("-" * 40)
    
    try:
        checker = MultiUserTGTGChecker()
        print("✅ Multi-user checker initialized")
        
        # Test getting all users
        active_users = checker.db.get_all_active_users()
        print(f"📊 Found {len(active_users)} active users")
        
        for user in active_users[:3]:  # Show first 3 users
            print(f"   User {user['user_id']}: {user.get('tgtg_email', 'No email')} ({user['telegram_chat_id']})")
        
        if active_users:
            print("\n⚠️  Note: To test actual TGTG checking, users need valid credentials")
            print("   Use the bot to register and authenticate users first")
        
    except Exception as e:
        print(f"❌ TGTG checker test failed: {e}")
    
    print("\n✅ TGTG checker tests completed!")

def test_message_formatting():
    """Test message formatting for different users."""
    print("\n🧪 Testing Message Formatting")
    print("-" * 40)
    
    from multi_user.multi_user_tgtg import MultiUserTGTGChecker
    
    checker = MultiUserTGTGChecker()
    
    # Mock offer data
    mock_offer = {
        'store': {
            'store_name': 'Test Restaurant',
            'branch': 'Downtown',
            'address': {
                'address_line': '123 Test Street',
                'city': 'Test City'
            }
        },
        'display_name': 'Surprise Bag',
        'item_id': 'test_item_123',
        'items_available': 2,
        'pickup_interval': {
            'start': '2025-08-18T18:00:00Z',
            'end': '2025-08-18T19:00:00Z'
        }
    }
    
    # Test different timezones
    timezones = ['Europe/Berlin', 'Europe/London', 'US/Eastern']
    
    for tz in timezones:
        print(f"\n📍 Timezone: {tz}")
        message = checker.format_offer_message(mock_offer, tz)
        print(f"   Message preview: {message[:100]}...")
    
    print("\n✅ Message formatting tests completed!")

def main():
    """Run all multi-user tests."""
    print("🚀 Multi-User TGTG System Tests")
    print("=" * 50)
    
    try:
        # Test 1: Database functionality
        db = test_database()
        
        # Test 2: Notification system
        test_notifications()
        
        # Test 3: TGTG checker
        test_tgtg_checker()
        
        # Test 4: Message formatting
        test_message_formatting()
        
        print("\n" + "=" * 50)
        print("🎉 All tests completed!")
        print("\n📋 Next steps:")
        print("1. Start the multi-user bot: python3 start_multi_user_bot.py")
        print("2. Register users by messaging the bot with /start")
        print("3. Test with: python3 multi_user_cron.py")
        print("4. Install crontab: crontab crontab-multi-user.txt")
        
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
