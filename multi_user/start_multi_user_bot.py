#!/usr/bin/env python3
"""
Start the Multi-User TGTG Telegram Bot Handler
This script starts the bot that handles multi-user registration and reservations.
"""

import sys
import os
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multi_user.multi_user_bot_handler import MultiUserTGTGBotHandler

def main():
    """Start the multi-user bot handler."""
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    
    print("🤖 Starting Multi-User TGTG Telegram Bot Handler...")
    print("This bot handles:")
    print("- User registration and TGTG authentication")
    print("- Multi-user offer notifications")
    print("- Reservation button presses")
    print("- Per-user notification tracking")
    print("Press Ctrl+C to stop.\n")
    
    try:
        bot_handler = MultiUserTGTGBotHandler()
        bot_handler.run_polling()
    except KeyboardInterrupt:
        print("\n🛑 Multi-user bot stopped by user")
    except Exception as e:
        print(f"❌ Multi-user bot error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
