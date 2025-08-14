#!/usr/bin/env python3
"""
Start the TGTG Telegram Bot Handler
This script starts the bot that handles reservation button presses.
"""

import sys
import logging
from telegram_bot_handler import TGTGBotHandler

def main():
    """Start the bot handler."""
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    
    print("🤖 Starting TGTG Telegram Bot Handler...")
    print("This bot handles reservation button presses from notifications.")
    print("Press Ctrl+C to stop.\n")
    
    try:
        bot_handler = TGTGBotHandler()
        bot_handler.run_polling()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Bot error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
