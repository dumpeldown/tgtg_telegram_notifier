#!/usr/bin/env python3
"""
Test script to verify that user emails are properly saved to the database.
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multi_user.multi_user_db import get_multi_user_db

def test_email_update():
    """Test the email update functionality."""
    print("🧪 Testing email update functionality...")
    
    db = get_multi_user_db()
    
    # Test user registration without email
    chat_id = "test_chat_12345"
    result = db.register_user(chat_id)
    
    if result['success']:
        user_id = result['user_id']
        print(f"✅ Registered user with ID: {user_id}")
        
        # Check initial state (no email)
        user = db.get_user_by_chat_id(chat_id)
        print(f"📧 Initial email: {user.get('tgtg_email', 'Not set')}")
        
        # Update email
        test_email = "test@example.com"
        success = db.update_user_email(user_id, test_email)
        
        if success:
            print(f"✅ Updated email to: {test_email}")
            
            # Verify the email was saved
            updated_user = db.get_user_by_chat_id(chat_id)
            saved_email = updated_user.get('tgtg_email', 'Not set')
            
            if saved_email == test_email:
                print(f"✅ Email successfully verified: {saved_email}")
                return True
            else:
                print(f"❌ Email mismatch. Expected: {test_email}, Got: {saved_email}")
                return False
        else:
            print("❌ Failed to update email")
            return False
    else:
        print(f"❌ Failed to register user: {result.get('error', 'Unknown error')}")
        return False

if __name__ == "__main__":
    success = test_email_update()
    if success:
        print("🎉 All tests passed!")
    else:
        print("💥 Tests failed!")
