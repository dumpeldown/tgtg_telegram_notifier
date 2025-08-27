#!/usr/bin/env python3
"""
Test script for manual check functionality.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multi_user.multi_user_tgtg import get_multi_user_checker
from multi_user.multi_user_db import get_multi_user_db

def test_manual_check():
    """Test the manual check functionality."""
    print("🧪 Testing Manual Check Functionality")
    print("=" * 40)
    
    try:
        # Get database and checker
        db = get_multi_user_db()
        checker = get_multi_user_checker()
        
        # Get all active users
        users = db.get_all_active_users()
        print(f"📊 Found {len(users)} active users")
        
        if not users:
            print("❌ No active users found. Please register a user first.")
            return
        
        # Test with first user
        user = users[0]
        user_id = user['user_id']
        chat_id = user['telegram_chat_id']
        
        print(f"\n🧪 Testing manual check for user {user_id} ({chat_id})")
        
        # Get offers first
        offers = checker.get_user_favorites_with_offers(user_id)
        print(f"📦 Found {len(offers)} current offers")
        
        if offers:
            print("✅ Offers available - manual check should show them all")
            
            # Test manual check
            success = checker.manual_check_user_offers(user_id, chat_id)
            print(f"📱 Manual check result: {'✅ Success' if success else '❌ Failed'}")
            
        else:
            print("📭 No offers available - manual check should show 'no offers' message")
            
            # Test manual check with no offers
            success = checker.manual_check_user_offers(user_id, chat_id)
            print(f"📱 Manual check result: {'✅ Success' if success else '❌ Failed'}")
        
        print("\n🎉 Manual check test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_manual_check()
