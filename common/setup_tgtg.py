#!/usr/bin/env python3
"""
TGTG Authentication Setup Script
Run this script to authenticate your TooGoodToGo account for the first time.
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from single_user.tgtg_check import TGTGChecker
from common.telegram_notify import notify

def setup_tgtg_authentication():
    """Interactive setup for TGTG authentication."""
    
    print("🍽️ TooGoodToGo Authentication Setup")
    print("=" * 40)
    print()
    
    # Get email from user
    email = input("Enter your TooGoodToGo email address: ").strip()
    
    if not email:
        print("❌ Email address is required!")
        return False
    
    # Validate email format (basic check)
    if '@' not in email or '.' not in email:
        print("❌ Please enter a valid email address!")
        return False
    
    print(f"\n🔄 Starting authentication for: {email}")
    print("📧 Please check your email for a login link from TooGoodToGo...")
    print("⏳ This script will wait until you click the link in the email.")
    
    # Create checker and authenticate
    checker = TGTGChecker()
    success = checker.authenticate(email)
    
    if success:
        print("\n✅ Authentication successful!")
        print("🎉 Your TGTG account is now connected!")
        
        # Send success notification
        notify(
            "✅ <b>TGTG Authentication Complete!</b>\n\n"
            "Your TooGoodToGo account is now connected and ready to check for offers! 🍽️"
        )
        
        # Test by checking favorites
        print("\n🔍 Testing by checking your favorites...")
        offers = checker.get_favorites_with_offers()
        
        if offers:
            print(f"🎉 Great! Found {len(offers)} favorite(s) with offers available!")
            notify(f"🎉 Found {len(offers)} favorite(s) with offers right now!")
        else:
            print("📝 No offers found right now, but the system is working!")
            notify("📝 TGTG system is working! No offers found at the moment, but we'll keep checking!")
        
        return True
    
    else:
        print("\n❌ Authentication failed!")
        print("Please check your email and try again.")
        
        notify(
            "❌ <b>TGTG Authentication Failed</b>\n\n"
            "Please check your email and try the authentication process again."
        )
        
        return False

def main():
    """Main function."""
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help', 'help']:
        print("TGTG Authentication Setup")
        print()
        print("This script helps you authenticate your TooGoodToGo account.")
        print("You'll need to:")
        print("1. Enter your TGTG email address")
        print("2. Check your email for a login link")
        print("3. Click the link to complete authentication")
        print()
        print("After authentication, credentials will be saved for future use.")
        return
    
    # Check if already authenticated
    checker = TGTGChecker()
    if checker.client:
        print("✅ TGTG account is already authenticated!")
        
        # Test the connection
        print("🔍 Testing connection by checking favorites...")
        try:
            offers = checker.get_favorites_with_offers()
            print(f"📝 Found {len(offers)} favorite(s) with offers available")
            
            if offers:
                print("\nOffers found:")
                for offer in offers:
                    store_name = offer['store']['store_name']
                    items = offer['items_available']
                    print(f"  🍽️ {store_name}: {items} bag(s) available")
            
            notify(f"🔍 TGTG check complete: {len(offers)} offer(s) found!")
            
        except Exception as e:
            print(f"❌ Error testing connection: {e}")
            print("You may need to re-authenticate.")
        
        return
    
    # Run authentication setup
    print("🔑 TGTG authentication required.")
    success = setup_tgtg_authentication()
    
    if success:
        print("\n🎉 Setup complete! You can now run the main script.")
        print("Run: python main.py")
    else:
        print("\n❌ Setup failed. Please try again.")

if __name__ == "__main__":
    main()
