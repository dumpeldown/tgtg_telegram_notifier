#!/usr/bin/env python3
"""
Multi-User TGTG Checker
Handles TGTG checking and notifications for multiple users.
"""

import os
import sys
import json
import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pytz
from tgtg import TgtgClient
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multi_user.multi_user_db import get_multi_user_db
from common.telegram_notify import notify_to_chat, notify_with_reservation_buttons_to_chat
from common.tgtg_exceptions import (
    safe_tgtg_call, handle_tgtg_exception, get_user_friendly_error_message,
    TGTGCaptchaException, TGTGServiceException
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultiUserTGTGChecker:
    """Handles TGTG checking for multiple users."""
    
    def __init__(self):
        self.db = get_multi_user_db()
        self.user_clients: Dict[int, TgtgClient] = {}  # Cache TGTG clients per user
    
    def _get_user_client(self, user_id: int) -> Optional[TgtgClient]:
        """Get or create TGTG client for a specific user."""
        try:
            # Check if we already have a client for this user
            if user_id in self.user_clients:
                return self.user_clients[user_id]
            
            # Get user credentials
            credentials = self.db.get_user_credentials(user_id)
            if not credentials:
                logger.warning(f"No credentials found for user {user_id}")
                return None
            
            # Create TGTG client
            client = TgtgClient(
                access_token=credentials.get('access_token'),
                refresh_token=credentials.get('refresh_token'),
                cookie=credentials.get('cookie')
            )
            
            # Cache the client
            self.user_clients[user_id] = client
            logger.info(f"✅ Created TGTG client for user {user_id}")
            
            return client
            
        except Exception as e:
            logger.error(f"Failed to create TGTG client for user {user_id}: {e}")
            return None
    
    def _update_user_credentials_if_changed(self, user_id: int, client: TgtgClient):
        """Update user credentials if they were refreshed."""
        try:
            current_credentials = self.db.get_user_credentials(user_id)
            if not current_credentials:
                return
            
            # Check if refresh token has changed
            original_refresh_token = current_credentials.get('refresh_token')
            current_refresh_token = client.refresh_token
            
            if original_refresh_token != current_refresh_token:
                logger.info(f"🔄 Tokens were refreshed for user {user_id}, updating credentials...")
                
                new_credentials = {
                    'access_token': client.access_token,
                    'refresh_token': client.refresh_token,
                    'user_id': current_credentials.get('user_id'),  # Keep original user_id
                    'cookie': client.cookie
                }
                
                self.db.save_user_credentials(user_id, new_credentials)
                logger.info(f"✅ Credentials updated successfully for user {user_id}")
                
        except Exception as e:
            logger.warning(f"Failed to update credentials for user {user_id}: {e}")
    
    def get_user_favorites_with_offers(self, user_id: int) -> List[Dict[str, Any]]:
        """Get favorites with offers for a specific user."""
        try:
            client = self._get_user_client(user_id)
            if not client:
                return []
            
            logger.info(f"🔍 Checking favorites for user {user_id}...")
            
            # Use safe TGTG call with exception handling
            favorites = safe_tgtg_call(
                client.get_favorites,
                operation=f"get_favorites for user {user_id}"
            )
            
            # Update credentials if they were refreshed
            self._update_user_credentials_if_changed(user_id, client)
            
            # Filter favorites with offers
            offers = []
            for favorite in favorites:
                if favorite.get('items_available', 0) > 0:
                    offers.append(favorite)
                    logger.info(f"  📦 Found offer: {favorite['store']['store_name']} - {favorite['items_available']} items")
            
            logger.info(f"📊 Found {len(offers)} offers for user {user_id}")
            return offers
            
        except (TGTGCaptchaException, TGTGServiceException) as e:
            logger.warning(f"TGTG service issue for user {user_id}: {e}")
            return []  # Return empty list, don't crash the whole system
        except Exception as e:
            logger.error(f"Failed to get favorites for user {user_id}: {e}")
            return []
    
    def format_offer_message(self, offer: Dict, timezone: str = 'Europe/Berlin') -> str:
        """Format an offer into a nice Telegram message."""
        try:
            # Debug logging to understand the structure
            logger.debug(f"Formatting offer with keys: {list(offer.keys())}")
            if 'store' in offer:
                logger.debug(f"Store keys: {list(offer['store'].keys())}")
            
            store_name = offer.get('store', {}).get('store_name', 'Unknown Store')
            branch = offer.get('store', {}).get('branch', '')
            display_name = offer.get('display_name', 'Food items')
            items_available = offer.get('items_available', 0)
            
            # Location - handle missing location gracefully
            location = "Location not available"
            if store := offer.get('store'):
                if store_location := store.get('store_location'):
                    address_line = store_location.get('address', {}).get('address_line', '')
                    city = store_location.get('address', {}).get('city', '')
                    if address_line and city:
                        location = f"{address_line}, {city}"
                    elif address_line:
                        location = address_line
                    elif city:
                        location = city
                    elif 'latitude' in store_location and 'longitude' in store_location:
                        # If we only have coordinates, show them as fallback
                        lat = store_location.get('latitude', 0)
                        lng = store_location.get('longitude', 0)
                        location = f"📍 {lat:.4f}, {lng:.4f}"
            
            # Pickup time and date handling
            pickup_info = ""
            date_info = ""
            
            if pickup_interval := offer.get('pickup_interval'):
                start_time = pickup_interval.get('start', '')
                end_time = pickup_interval.get('end', '')
                
                if start_time and end_time:
                    try:
                        # Parse the ISO datetime strings
                        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                        end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                        
                        # Convert to local timezone
                        local_tz = pytz.timezone(timezone)
                        start_local = start_dt.astimezone(local_tz)
                        end_local = end_dt.astimezone(local_tz)
                        
                        # Get current time in the same timezone
                        now_local = datetime.now(local_tz)
                        today = now_local.date()
                        pickup_date = start_local.date()
                        
                        # Determine if pickup is today, tomorrow, or another day
                        if pickup_date == today:
                            date_info = "📅 <b>Today</b>"
                        elif pickup_date == today + timedelta(days=1):
                            date_info = "📅 <b>Tomorrow</b>"
                        elif pickup_date == today + timedelta(days=2):
                            date_info = "📅 <b>Day after tomorrow</b>"
                        else:
                            # Calculate days difference
                            days_diff = (pickup_date - today).days
                            if days_diff > 0:
                                if days_diff <= 7:
                                    day_name = pickup_date.strftime('%A')
                                    date_info = f"📅 <b>{day_name}</b> ({days_diff} days)"
                                else:
                                    date_info = f"📅 <b>{pickup_date.strftime('%d.%m.%Y')}</b> ({days_diff} days)"
                            else:
                                date_info = f"📅 <b>{pickup_date.strftime('%d.%m.%Y')}</b>"
                        
                        pickup_info = f"\n⏰ <b>Pickup:</b> {start_local.strftime('%H:%M')} - {end_local.strftime('%H:%M')}"
                        
                        # Add urgency indicator if pickup is soon
                        time_until_pickup = start_local - now_local
                        if time_until_pickup.total_seconds() > 0:
                            hours_until = time_until_pickup.total_seconds() / 3600
                            if hours_until < 2:
                                pickup_info += " 🔥 <b>Soon!</b>"
                            elif hours_until < 6:
                                pickup_info += " ⚡ <b>Today</b>"
                        
                    except Exception as e:
                        logger.warning(f"Failed to parse pickup time: {e}")
                        pickup_info = f"\n⏰ <b>Pickup:</b> {start_time} - {end_time}"
                        date_info = ""
            
            # Build the message
            message_parts = [
                f"🍽️ <b>{store_name}</b>",
                f"📍 {location}",
                f"🛍️ <b>{display_name}</b>",
                f"📦 <b>{items_available}</b> bag{'s' if items_available != 1 else ''} available"
            ]
            
            if date_info:
                message_parts.append(date_info)
            
            if pickup_info:
                message_parts.append(pickup_info.lstrip('\n'))
            
            message = '\n'.join(message_parts)
            return message
            
        except Exception as e:
            logger.error(f"Failed to format offer message: {e}")
            # Create a safe fallback message
            store_name = "Unknown Store"
            items_available = 0
            try:
                if store := offer.get('store'):
                    store_name = store.get('store_name', 'Unknown Store')
                items_available = offer.get('items_available', 0)
            except Exception:
                pass
            
            return f"🍽️ New offer available at {store_name}" + (f" - {items_available} items" if items_available > 0 else "")
    
    def manual_check_user_offers(self, user_id: int, telegram_chat_id: str) -> bool:
        """Manual check that shows ALL current offers, regardless of notification history."""
        try:
            user = self.db.get_user_by_chat_id(telegram_chat_id)
            if not user:
                logger.warning(f"User not found: {telegram_chat_id}")
                return False
            
            offers = self.get_user_favorites_with_offers(user_id)
            
            if offers:
                user_timezone = user.get('timezone', 'Europe/Berlin')
                
                # Send ALL offers with reservation buttons (no filtering)
                for i, offer in enumerate(offers):
                    message = self.format_offer_message(offer, user_timezone)
                    store_name = offer['store']['store_name']
                    item_id = offer['item']['item_id']
                    
                    # Send offer with reservation buttons
                    success = notify_with_reservation_buttons_to_chat(
                        message, item_id, store_name, telegram_chat_id
                    )
                    
                    if success:
                        logger.info(f"✅ Manual check: Sent offer to user {user_id} for {store_name}")
                    else:
                        logger.error(f"❌ Manual check: Failed to send offer to user {user_id} for {store_name}")
                    
                    # Add delay between messages to avoid flooding
                    if i < len(offers) - 1:
                        time.sleep(1)
                
                # Send summary
                summary_message = (
                    f"🔍 <b>Manual Check Complete</b>\n\n"
                    f"Found <b>{len(offers)}</b> offer{'s' if len(offers) != 1 else ''} "
                    f"in your favorites right now!\n\n"
                    f"📦 Check the messages above for details.\n\n"
                    f"💡 <i>This shows ALL current offers, including ones you've seen before.</i>"
                )
                
                success = notify_to_chat(summary_message, telegram_chat_id)
                return success
                
            else:
                # No offers found
                no_offers_message = (
                    f"🔍 <b>Manual Check Complete</b>\n\n"
                    f"📭 No offers found in your favorites right now.\n\n"
                    f"💡 <i>Try again later or add more favorites in the TGTG app!</i>"
                )
                
                success = notify_to_chat(no_offers_message, telegram_chat_id)
                return success
                
        except (TGTGCaptchaException, TGTGServiceException) as e:
            logger.warning(f"TGTG service issue during manual check for user {user_id}: {e}")
            error_message = get_user_friendly_error_message(e)
            notify_to_chat(error_message, telegram_chat_id)
            return False
        except Exception as e:
            logger.error(f"Failed manual check for user {user_id}: {e}")
            error_message = (
                f"❌ <b>Manual Check Failed</b>\n\n"
                f"Error checking offers: {str(e)}\n\n"
                f"💡 <i>Try:</i> /status /help"
            )
            notify_to_chat(error_message, telegram_chat_id)
            return False
    
    def check_and_notify_user(self, user_id: int, telegram_chat_id: str, send_summary: bool = True) -> Dict[str, Any]:
        """Check offers and send notifications for a specific user.
        
        Returns:
            Dict with keys: 'success' (bool), 'had_offers' (bool), 'new_offers_count' (int)
        """
        try:
            user = self.db.get_user_by_chat_id(telegram_chat_id)
            if not user:
                logger.warning(f"User not found: {telegram_chat_id}")
                return False
            
            offers = self.get_user_favorites_with_offers(user_id)
            
            if offers:
                new_offers = []
                skipped_offers = []
                
                # Filter out offers we've already notified this user about
                for offer in offers:
                    store_id = offer['store']['store_id']
                    item_id = offer['item']['item_id']  # Raw favorites structure
                    pickup_interval = offer.get('pickup_interval', {})
                    pickup_start = pickup_interval.get('start', '')
                    pickup_end = pickup_interval.get('end', '')
                    
                    # Check if we've already sent a notification for this exact offer to this user
                    if self.db.is_offer_already_sent(user_id, store_id, item_id, pickup_start, pickup_end):
                        skipped_offers.append(offer)
                        logger.info(f"⏭️ Skipping already notified offer for user {user_id}: {offer['store']['store_name']}")
                    else:
                        new_offers.append(offer)
                
                logger.info(f"📊 User {user_id}: {len(offers)} total offers, {len(new_offers)} new, {len(skipped_offers)} already notified")
                
                # Send notifications for new offers only
                if new_offers:
                    user_timezone = user.get('timezone', 'Europe/Berlin')
                    
                    for i, offer in enumerate(new_offers):
                        message = self.format_offer_message(offer, user_timezone)
                        store_name = offer['store']['store_name']
                        item_id = offer['item']['item_id']  # Fix: use correct structure
                        
                        # Send notification with reservation buttons to this specific user
                        success = notify_with_reservation_buttons_to_chat(
                            message, item_id, store_name, telegram_chat_id
                        )
                        
                        if success:
                            # Record the successful notification for this user
                            self.db.record_sent_offer(user_id, offer)
                            logger.info(f"✅ Sent notification to user {user_id} for {store_name}")
                        else:
                            logger.error(f"❌ Failed to send notification to user {user_id} for {store_name}")
                        
                        # Add a small delay between messages to avoid issues
                        if i < len(new_offers) - 1:
                            time.sleep(1)
                    
                    # Send summary for new offers
                    if send_summary and len(new_offers) > 1:
                        summary = (
                            f"🎉 <b>TGTG Summary</b>\n\n"
                            f"Found <b>{len(new_offers)}</b> new favorite{'s' if len(new_offers) != 1 else ''} "
                            f"with offers available!\n\n"
                        )
                        if skipped_offers:
                            summary += f"(Skipped {len(skipped_offers)} already notified offer{'s' if len(skipped_offers) != 1 else ''})\n\n"
                        
                        summary += f"Check the messages above for details. 🚀"
                        notify_to_chat(summary, telegram_chat_id)
                
                # Clean up old database entries for this user (keep last 7 days)
                self.db.cleanup_old_offers(user_id, days_to_keep=7)
                
                return {
                    'success': True,
                    'had_offers': True,
                    'new_offers_count': len(new_offers),
                    'total_offers_count': len(offers)
                }
            
            else:
                if send_summary:
                    message = (
                        f"🔍 <b>TGTG Check Complete</b>\n\n"
                        f"No offers found in your favorites right now.\n"
                        f"Keep checking back! 🤞"
                    )
                    notify_to_chat(message, telegram_chat_id)
                
                logger.info(f"No offers found for user {user_id}")
                return {
                    'success': True,
                    'had_offers': False,
                    'new_offers_count': 0,
                    'total_offers_count': 0
                }
                
                
        except (TGTGCaptchaException, TGTGServiceException) as e:
            logger.warning(f"TGTG service issue for user {user_id}: {e}")
            error_message = get_user_friendly_error_message(e)
            notify_to_chat(error_message, telegram_chat_id)
            return {
                'success': False,
                'had_offers': False,
                'new_offers_count': 0,
                'total_offers_count': 0,
                'service_unavailable': True
            }
        except Exception as e:
            logger.error(f"Failed to check and notify user {user_id}: {e}")
            error_message = (
                f"❌ <b>TGTG Check Failed</b>\n\n"
                f"There was an error checking for offers:\n"
                f"<code>{str(e)}</code>"
            )
            notify_to_chat(error_message, telegram_chat_id)
            return {
                'success': False,
                'had_offers': False,
                'new_offers_count': 0,
                'total_offers_count': 0
            }
    
    def check_and_notify_all_users(self, send_summary: bool = False) -> Dict[str, Any]:
        """Check and notify all active users."""
        try:
            active_users = self.db.get_all_active_users()
            logger.info(f"🔍 Checking {len(active_users)} active users...")
            
            results = {
                'total_users': len(active_users),
                'successful_checks': 0,
                'failed_checks': 0,
                'users_with_offers': 0
            }
            
            for user in active_users:
                try:
                    user_id = user['user_id']
                    telegram_chat_id = user['telegram_chat_id']
                    
                    logger.info(f"📱 Checking user {user_id} ({telegram_chat_id})...")
                    
                    result = self.check_and_notify_user(user_id, telegram_chat_id, send_summary)
                    
                    if result['success']:
                        results['successful_checks'] += 1
                        if result['had_offers']:
                            results['users_with_offers'] += 1
                    else:
                        results['failed_checks'] += 1
                    
                    # Small delay between users
                    time.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Failed to check user {user.get('user_id', 'unknown')}: {e}")
                    results['failed_checks'] += 1
            
            logger.info(f"📊 Multi-user check complete: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to check all users: {e}")
            return {'error': str(e)}

# Global multi-user checker instance
_multi_user_checker: Optional[MultiUserTGTGChecker] = None

def get_multi_user_checker() -> MultiUserTGTGChecker:
    """Get or create the global MultiUserTGTGChecker instance."""
    global _multi_user_checker
    if _multi_user_checker is None:
        _multi_user_checker = MultiUserTGTGChecker()
    return _multi_user_checker

def check_all_users(send_summary: bool = False) -> Dict[str, Any]:
    """Check and notify all users - convenience function."""
    checker = get_multi_user_checker()
    return checker.check_and_notify_all_users(send_summary)

if __name__ == "__main__":
    # Test the multi-user checker
    print("🧪 Testing Multi-User TGTG Checker")
    
    checker = MultiUserTGTGChecker()
    results = checker.check_and_notify_all_users(send_summary=True)
    
    print(f"Check results: {results}")
    print("✅ Multi-user checker test completed!")
