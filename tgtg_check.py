import os
import json
import logging
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import pytz
from tgtg import TgtgClient
from dotenv import load_dotenv
from telegram_notify import notify, notify_with_reservation_buttons
from offer_database import OfferDatabase

# Load environment variables
load_dotenv()

# Configuration
DEFAULT_TIMEZONE = 'Europe/Berlin'  # Change this to your local timezone
# Common timezones:
# 'Europe/Berlin' (Germany)
# 'Europe/Paris' (France)
# 'Europe/London' (UK)
# 'US/Eastern', 'US/Central', 'US/Mountain', 'US/Pacific' (USA)
# 'Europe/Amsterdam' (Netherlands)
# 'Europe/Zurich' (Switzerland)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TGTGChecker:
    """A class to check TooGoodToGo favorites for available offers."""
    
    def __init__(self):
        """Initialize the TGTG client."""
        self.client = None
        self.credentials_file = "tgtg_credentials.json"
        self.timezone = self._get_timezone()
        self.db = OfferDatabase()  # Initialize offer database
        self._setup_client()
    
    def _get_timezone(self) -> str:
        """Get timezone from environment variable or use default."""
        return os.getenv('TGTG_TIMEZONE', DEFAULT_TIMEZONE)
    
    def _setup_client(self):
        """Set up the TGTG client with credentials."""
        try:
            # Try to load existing credentials
            if os.path.exists(self.credentials_file):
                logger.info("Loading existing TGTG credentials...")
                with open(self.credentials_file, 'r') as f:
                    credentials = json.load(f)
                
                self.client = TgtgClient(
                    access_token=credentials['access_token'],
                    refresh_token=credentials['refresh_token'],
                    cookie=credentials['cookie']
                )
                
                # Store original refresh token to detect changes
                self._original_refresh_token = credentials['refresh_token']
                
                logger.info("✅ TGTG client initialized with saved credentials")
            else:
                logger.warning("❌ No saved credentials found. You need to authenticate first.")
                self.client = None
        except Exception as e:
            logger.error(f"Failed to initialize TGTG client: {e}")
            self.client = None
    
    def _update_credentials_if_changed(self):
        """Update credentials file if tokens have been refreshed."""
        if not self.client:
            return
            
        try:
            # Check if refresh token has changed (indicating token refresh occurred)
            current_refresh_token = self.client.refresh_token
            if hasattr(self, '_original_refresh_token') and current_refresh_token != self._original_refresh_token:
                logger.info("🔄 Tokens were refreshed, updating credentials file...")
                
                new_credentials = {
                    'access_token': self.client.access_token,
                    'refresh_token': self.client.refresh_token,
                    'cookie': self.client.cookie
                }
                
                with open(self.credentials_file, 'w') as f:
                    json.dump(new_credentials, f, indent=2)
                
                # Update our tracking variable
                self._original_refresh_token = current_refresh_token
                logger.info("✅ Credentials updated successfully")
                
        except Exception as e:
            logger.warning(f"Failed to update credentials: {e}")
            # Don't fail the whole operation if credential saving fails
    
    def authenticate(self, email: str) -> bool:
        """
        Authenticate with TGTG using email.
        
        Args:
            email (str): Your TGTG account email
            
        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            logger.info(f"Starting authentication for {email}")
            logger.info("📧 Please check your email and click the login link...")
            
            client = TgtgClient(email=email)
            credentials = client.get_credentials()
            
            # Save credentials for future use
            with open(self.credentials_file, 'w') as f:
                json.dump(credentials, f, indent=2)
            
            self.client = client
            logger.info("✅ Authentication successful! Credentials saved.")
            return True
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False
    
    def get_favorites_with_offers(self) -> List[Dict]:
        """
        Get all favorite stores that currently have offers available.
        
        Returns:
            List[Dict]: List of stores with available offers
        """
        if not self.client:
            logger.error("TGTG client not initialized. Run authenticate() first.")
            return []
        
        try:
            logger.info("🔍 Checking favorites for available offers...")
            
            # Get all favorites (items)
            items = self.client.get_items(favorites_only=True)
            
            # Filter items that have offers (items_available > 0)
            offers = []
            for item in items:
                if item.get('items_available', 0) > 0:
                    offers.append({
                        'item_id': item['item']['item_id'],
                        'display_name': item['display_name'],
                        'description': item.get('description', ''),
                        'items_available': item['items_available'],
                        #'price': item['item']['price_including_taxes'],
                        #'value': item['item']['value_including_taxes'],
                        'pickup_interval': item.get('pickup_interval', {}),
                        'store': {
                            'store_id': item['store']['store_id'],
                            'store_name': item['store']['store_name'],
                            'branch': item['store'].get('branch', ''),
                            'logo_picture': item['store'].get('logo_picture', {}).get('current_url', ''),
                            'address': {
                                'address_line': item['store']['store_location'].get('address', {}).get('address_line', ''),
                                'city': item['store']['store_location'].get('address', {}).get('city', ''),
                                'country': item['store']['store_location'].get('address', {}).get('country', {}).get('name', '')
                            }
                        }
                    })
            
            logger.info(f"Found {len(offers)} favorites with offers available")
            return offers
            
        except Exception as e:
            logger.error(f"Failed to get favorites: {e}")
            return []
    
    def format_offer_message(self, offer: Dict) -> str:
        """
        Format an offer into a nice Telegram message.
        
        Args:
            offer (Dict): Offer data
            
        Returns:
            str: Formatted message
        """
        try:
            store_name = offer['store']['store_name']
            branch = offer['store']['branch']
            display_name = offer['display_name']
            items_available = offer['items_available']
            
            # Address
            address = offer['store']['address']
            location = f"{address['address_line']}, {address['city']}"
            
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
                        local_tz = pytz.timezone(self.timezone)
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
            return f"🍽️ New offer available at {offer.get('store', {}).get('store_name', 'Unknown Store')}"
    
    def check_and_notify(self, send_summary: bool = True) -> bool:
        """
        Check for offers and send notifications.
        
        Args:
            send_summary (bool): Whether to send a summary even if no offers found
            
        Returns:
            bool: True if check was successful, False otherwise
        """
        try:
            offers = self.get_favorites_with_offers()
            
            # Update credentials if they were refreshed during the API call
            self._update_credentials_if_changed()
            
            if offers:
                new_offers = []
                skipped_offers = []
                
                # Filter out offers we've already notified about
                for offer in offers:
                    store_id = offer['store']['store_id']
                    item_id = offer['item_id']
                    pickup_interval = offer.get('pickup_interval', {})
                    pickup_start = pickup_interval.get('start', '')
                    pickup_end = pickup_interval.get('end', '')
                    
                    # Check if we've already sent a notification for this exact offer
                    if self.db.is_offer_already_sent(store_id, item_id, pickup_start, pickup_end):
                        skipped_offers.append(offer)
                        logger.info(f"⏭️ Skipping already notified offer: {offer['store']['store_name']} - {offer['display_name']}")
                    else:
                        new_offers.append(offer)
                
                logger.info(f"📊 Found {len(offers)} total offers: {len(new_offers)} new, {len(skipped_offers)} already notified")
                
                # Send notifications for new offers only
                if new_offers:
                    for i, offer in enumerate(new_offers):
                        message = self.format_offer_message(offer)
                        store_name = offer['store']['store_name']
                        item_id = offer['item_id']
                        
                        # Send notification with reservation buttons
                        success = notify_with_reservation_buttons(message, item_id, store_name)
                        
                        if success:
                            # Record the successful notification
                            self.db.record_sent_offer(offer)
                            logger.info(f"✅ Sent notification with buttons for {store_name}")
                        else:
                            logger.error(f"❌ Failed to send notification for {store_name}")
                        
                        # Add a small delay between messages to avoid issues
                        if i < len(new_offers) - 1:  # Don't delay after the last message
                            time.sleep(1)
                    
                    # Add delay before summary
                    time.sleep(2)
                    
                    # Send summary for new offers
                    if send_summary:
                        summary = (
                            f"🎉 <b>TGTG Summary</b>\n\n"
                            f"Found <b>{len(new_offers)}</b> new favorite{'s' if len(new_offers) != 1 else ''} "
                            f"with offers available!\n\n"
                        )
                        if skipped_offers:
                            summary += f"(Skipped {len(skipped_offers)} already notified offer{'s' if len(skipped_offers) != 1 else ''})\n\n"
                        
                        summary += f"Check the messages above for details. 🚀"
                        notify(summary)
                
                else:
                    # All offers were already notified about
                    if send_summary and skipped_offers:
                        summary = (
                            f"🔄 <b>TGTG Check Complete</b>\n\n"
                            f"Found {len(skipped_offers)} offer{'s' if len(skipped_offers) != 1 else ''} "
                            f"but you've already been notified about {'them' if len(skipped_offers) > 1 else 'it'}.\n\n"
                            f"Will notify you when new offers become available! 👀"
                        )
                        notify(summary)
                
                # Clean up old database entries (keep last 7 days)
                self.db.cleanup_old_offers(days_to_keep=7)
                
                return True
            
            else:
                if send_summary:
                    message = (
                        f"🔍 <b>TGTG Check Complete</b>\n\n"
                        f"No offers found in your favorites right now.\n"
                        f"Keep checking back! 🤞"
                    )
                    notify(message)
                
                logger.info("No offers found in favorites")
                return True
                
        except Exception as e:
            logger.error(f"Failed to check and notify: {e}")
            error_message = (
                f"❌ <b>TGTG Check Failed</b>\n\n"
                f"There was an error checking for offers:\n"
                f"<code>{str(e)}</code>"
            )
            notify(error_message)
            return False
    
    def get_database_stats(self) -> dict:
        """Get database statistics for monitoring."""
        return self.db.get_database_stats()
    
    def get_recent_notifications(self, hours: int = 24) -> List:
        """Get recent notifications for monitoring."""
        return self.db.get_recent_offers(hours)
    
    def cleanup_old_notifications(self, days_to_keep: int = 7) -> int:
        """Manually clean up old notification records."""
        return self.db.cleanup_old_offers(days_to_keep)

def main():
    """Main function for testing the TGTG checker."""
    checker = TGTGChecker()
    
    if not checker.client:
        print("❌ TGTG client not initialized.")
        print("You need to authenticate first. Example:")
        print('checker.authenticate("your-email@example.com")')
        return
    
    print("🚀 Starting TGTG favorites check...")
    success = checker.check_and_notify()
    
    if success:
        print("✅ TGTG check completed successfully!")
    else:
        print("❌ TGTG check failed!")

if __name__ == "__main__":
    main()