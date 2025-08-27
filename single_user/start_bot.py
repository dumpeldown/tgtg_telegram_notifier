#!/usr/bin/env python3
"""
Start the TGTG Telegram Bot Handler
This script starts the bot that handles reservation button presses.
"""

import sys
import os
import logging
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from single_user.telegram_bot_handler import TGTGBotHandler

def main():
    """Start the bot handler."""

    # Log the PID to bot_monitor.log when started manually
    pid = os.getpid()
    with open('bot_monitor.log', 'a') as f:
        f.write(f"{datetime.now().strftime('%a %b %d %H:%M:%S %Y')}: Bot handler started manually with PID: {pid}\n")
    
    # Log startup info to bot_handler.log instead of printing to console
    logger = logging.getLogger(__name__)
    logger.info(f"🤖 Starting TGTG Telegram Bot Handler with PID: {pid}")
    logger.info("This bot handles reservation button presses from notifications.")
    
    try:
        bot_handler = TGTGBotHandler()
        bot_handler.run_polling()
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Bot error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
