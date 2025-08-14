import os
import asyncio
import logging
import requests
import json
from typing import Optional, Dict, List, Any
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TelegramNotifier:
    """A class to handle Telegram notifications."""
    
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if not self.bot_token or not self.chat_id:
            raise ValueError(
                "TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set in environment variables. "
                "Check your .env file or system environment variables."
            )
        
        self.bot = Bot(token=self.bot_token)
    
    async def send_message_async(self, message: str, reply_markup=None) -> bool:
        """
        Send a message asynchronously via Telegram Bot API.
        
        Args:
            message (str): The message to send
            reply_markup: Optional inline keyboard markup
            
        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML',  # Allows basic HTML formatting
                reply_markup=reply_markup
            )
            logger.info(f"Message sent successfully to chat {self.chat_id}")
            return True
        except TelegramError as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while sending message: {e}")
            return False
    
    def send_message_sync(self, message: str, reply_markup=None) -> bool:
        """
        Send a message synchronously via Telegram Bot API using requests.
        
        Args:
            message (str): The message to send
            reply_markup: Optional inline keyboard markup
            
        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        try:
            # Use requests for a more reliable synchronous approach
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            if reply_markup:
                data['reply_markup'] = json.dumps(reply_markup.to_dict() if hasattr(reply_markup, 'to_dict') else reply_markup)
            
            response = requests.post(url, data=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok', False):
                    logger.info(f"Message sent successfully to chat {self.chat_id}")
                    return True
                else:
                    logger.error(f"Telegram API error: {result.get('description', 'Unknown error')}")
                    return False
            else:
                logger.error(f"HTTP error {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error("Request timeout while sending Telegram message")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error while sending Telegram message: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in synchronous message sending: {e}")
            return False

    def create_reservation_keyboard(self, item_id: str, store_name: str) -> InlineKeyboardMarkup:
        """
        Create an inline keyboard for reservation actions.
        
        Args:
            item_id (str): The TGTG item ID
            store_name (str): Name of the store for display
            
        Returns:
            InlineKeyboardMarkup: The inline keyboard markup
        """
        keyboard = [
            [
                InlineKeyboardButton(
                    "🛒 Reserve Bag", 
                    callback_data=f"reserve:{item_id}"
                ),
                InlineKeyboardButton(
                    "❌ Cancel", 
                    callback_data=f"cancel_reserve:{item_id}"
                )
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    def send_offer_with_buttons(self, message: str, item_id: str, store_name: str) -> bool:
        """
        Send an offer message with reservation buttons.
        
        Args:
            message (str): The offer message
            item_id (str): The TGTG item ID
            store_name (str): Name of the store
            
        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        keyboard = self.create_reservation_keyboard(item_id, store_name)
        return self.send_message_sync(message, reply_markup=keyboard)

    def update_message_text(self, message_id: int, new_text: str, reply_markup=None) -> bool:
        """
        Update an existing message text.
        
        Args:
            message_id (int): The message ID to update
            new_text (str): New text for the message
            reply_markup: Optional new keyboard markup
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/editMessageText"
            
            data = {
                'chat_id': self.chat_id,
                'message_id': message_id,
                'text': new_text,
                'parse_mode': 'HTML'
            }
            
            if reply_markup:
                data['reply_markup'] = json.dumps(reply_markup.to_dict() if hasattr(reply_markup, 'to_dict') else reply_markup)
            
            response = requests.post(url, data=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok', False):
                    logger.info(f"Message {message_id} updated successfully")
                    return True
                else:
                    logger.error(f"Telegram API error updating message: {result.get('description', 'Unknown error')}")
                    return False
            else:
                logger.error(f"HTTP error {response.status_code} updating message: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating message: {e}")
            return False

# Global notifier instance
_notifier: Optional[TelegramNotifier] = None

def get_notifier() -> TelegramNotifier:
    """Get or create the global TelegramNotifier instance."""
    global _notifier
    if _notifier is None:
        _notifier = TelegramNotifier()
    return _notifier

def notify(message: str, use_async: bool = False, reply_markup=None) -> bool:
    """
    Send a notification message via Telegram.
    
    This is the main function you should call to send notifications.
    
    Args:
        message (str): The message to send
        use_async (bool): Whether to use async method (default: False for compatibility)
        reply_markup: Optional inline keyboard markup
        
    Returns:
        bool: True if message was sent successfully, False otherwise
        
    Example:
        from telegram import notify
        
        # Simple notification
        notify("Hello from your Python script!")
        
        # With HTML formatting
        notify("<b>Alert:</b> Something important happened!")
        
        # With inline keyboard
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Click me", callback_data="test")]])
        notify("Message with button", reply_markup=keyboard)
    """
    try:
        notifier = get_notifier()
        if use_async:
            # For async usage, you'd typically call this from an async context
            return asyncio.run(notifier.send_message_async(message, reply_markup))
        else:
            return notifier.send_message_sync(message, reply_markup)
    except Exception as e:
        logger.error(f"Failed to initialize or send notification: {e}")
        return False

def notify_with_reservation_buttons(message: str, item_id: str, store_name: str) -> bool:
    """
    Send a notification with reservation buttons for a TGTG offer.
    
    Args:
        message (str): The offer message
        item_id (str): The TGTG item ID
        store_name (str): Name of the store
        
    Returns:
        bool: True if message was sent successfully, False otherwise
    """
    try:
        notifier = get_notifier()
        return notifier.send_offer_with_buttons(message, item_id, store_name)
    except Exception as e:
        logger.error(f"Failed to send offer with buttons: {e}")
        return False

# For backward compatibility and convenience
send_notification = notify

if __name__ == "__main__":
    # Test the notification system
    test_message = "🔔 Test notification from tgtg_notify script!"
    success = notify(test_message)
    if success:
        print("✅ Test notification sent successfully!")
    else:
        print("❌ Failed to send test notification. Check your configuration.")