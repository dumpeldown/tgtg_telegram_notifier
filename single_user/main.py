#!/usr/bin/env python3
"""
TGTG Notify - Complete TooGoodToGo favorites checker with Telegram notifications
"""

import sys
import os
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.telegram_notify import notify
from single_user.tgtg_check import TGTGChecker

def demo_notifications():
    """Demo function showing basic notification functionality."""
    print("� Testing Telegram notifications...")
    
    # Send a startup notification
    startup_msg = "🔔 <b>TGTG Notify</b> script started successfully!"
    if notify(startup_msg):
        print("✅ Startup notification sent!")
        return True
    else:
        print("❌ Failed to send startup notification")
        return False

def run_tgtg_check():
    """Run the TGTG favorites check."""
    print("🍽️ Starting TGTG favorites check...")
    
    checker = TGTGChecker()
    
    if not checker.client:
        print("❌ TGTG client not authenticated.")
        print("\n📧 To authenticate, run:")
        print('python -c "from tgtg_check import TGTGChecker; checker = TGTGChecker(); checker.authenticate(\'your-email@example.com\')"')
        
        # Send notification about authentication needed
        auth_msg = (
            "🔑 <b>TGTG Authentication Needed</b>\n\n"
            "Please authenticate your TGTG account to start checking for offers.\n"
            "Check the console for instructions."
        )
        notify(auth_msg)
        return False
    
    # Run the check and send notifications
    return checker.check_and_notify()

def main():
    """Main function demonstrating the complete system."""
    print("🚀 Starting TGTG Notify - Complete System Demo")
    print("=" * 50)
    
    # Test Telegram notifications first
    if not demo_notifications():
        return
    
    time.sleep(2)
    
    # Run TGTG check
    success = run_tgtg_check()
    
    # Send completion notification
    if success:
        final_msg = (
            "✅ <b>TGTG Notify Complete!</b>\n\n"
            "• 📱 Telegram integration: <b>Working</b>\n"
            "• 🍽️ TGTG favorites check: <b>Complete</b>\n"
            "• � Notifications: <b>Active</b>\n\n"
            "The system is ready to monitor your TGTG favorites! 🚀"
        )
        notify(final_msg)
        print("\n🎉 Complete system demo finished successfully!")
    else:
        error_msg = (
            "⚠️ <b>TGTG Notify Setup Incomplete</b>\n\n"
            "Telegram notifications are working, but TGTG authentication is needed.\n"
            "Please authenticate your TGTG account to complete the setup."
        )
        notify(error_msg)
        print("\n⚠️ System demo completed with authentication required.")

if __name__ == "__main__":
    main()