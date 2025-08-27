#!/usr/bin/env python3
"""
TGTG Reservation Handler
Handles the reservation and cancellation of TGTG bags via the API.
"""

import os
import sys
import json
import time
import threading
import logging
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from tgtg import TgtgClient

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.telegram_notify import notify
from common.tgtg_exceptions import (
    safe_tgtg_call, handle_tgtg_exception, get_user_friendly_error_message,
    TGTGCaptchaException, TGTGServiceException
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TGTGReservationManager:
    """Manages TGTG bag reservations and auto-cancellations."""
    
    def __init__(self):
        self.client = self._setup_client()
        self.active_reservations: Dict[str, Dict[str, Any]] = {}
        self.reservation_timers: Dict[str, threading.Timer] = {}
        
    def _setup_client(self) -> TgtgClient:
        """Set up TGTG client with stored credentials."""
        creds_file = os.path.join(os.path.dirname(__file__), 'tgtg_credentials.json')
        
        if not os.path.exists(creds_file):
            raise FileNotFoundError(f"TGTG credentials file not found: {creds_file}")
        
        with open(creds_file, 'r') as f:
            credentials = json.load(f)
        
        client = TgtgClient(
            access_token=credentials.get('access_token'),
            refresh_token=credentials.get('refresh_token'), 
            cookie=credentials.get('cookie')
        )
        
        return client
    
    def reserve_bag(self, item_id: str, store_name: str, auto_cancel_minutes: int = 10) -> Dict[str, Any]:
        """
        Reserve a TGTG bag and set up auto-cancellation.
        
        Args:
            item_id (str): The TGTG item/product ID
            store_name (str): Name of the store (for notifications)
            auto_cancel_minutes (int): Minutes after which to auto-cancel (default: 10)
            
        Returns:
            Dict[str, Any]: Reservation result with order info or error
        """
        try:
            logger.info(f"🛒 Attempting to reserve bag from {store_name} (item: {item_id})")
            
            # Create the order/reservation
            order = safe_tgtg_call(
                self.client.create_order,
                operation=f"reserve bag from {store_name}",
                item_id=item_id,
                item_count=1
            )
            order_id = order.get('id')
            
            if not order_id:
                error_msg = f"❌ Failed to reserve bag from {store_name}: No order ID returned"
                logger.error(error_msg)
                notify(error_msg)
                return {'success': False, 'error': 'No order ID returned', 'order': order}
            
            # Store reservation details
            self.active_reservations[order_id] = {
                'item_id': item_id,
                'store_name': store_name,
                'order_id': order_id,
                'reserved_at': datetime.now(),
                'auto_cancel_at': datetime.now() + timedelta(minutes=auto_cancel_minutes)
            }
            
            # Set up auto-cancellation timer
            cancel_timer = threading.Timer(
                auto_cancel_minutes * 60,  # Convert to seconds
                self._auto_cancel_reservation,
                args=[order_id]
            )
            cancel_timer.start()
            self.reservation_timers[order_id] = cancel_timer
            
            # Send success notification
            success_msg = (
                f"✅ <b>Bag Reserved Successfully!</b>\n\n"
                f"🏪 <b>Store:</b> {store_name}\n"
                f"🆔 <b>Order ID:</b> <code>{order_id}</code>\n"
                f"⏰ <b>Reserved at:</b> {datetime.now().strftime('%H:%M:%S')}\n"
                f"🚨 <b>Auto-cancel in:</b> {auto_cancel_minutes} minutes\n\n"
                f"💡 <b>Next Steps:</b>\n"
                f"1. Open the TGTG app quickly\n"
                f"2. Find this order in your orders\n"
                f"3. Complete the payment before auto-cancel\n"
                f"4. Or manually cancel if you don't want it\n\n"
                f"⚠️ <i>The reservation will be automatically cancelled in {auto_cancel_minutes} minutes to free up the bag for others.</i>"
            )
            
            notify(success_msg)
            logger.info(f"✅ Successfully reserved bag from {store_name}, order ID: {order_id}")
            
            return {
                'success': True,
                'order_id': order_id,
                'order': order,
                'auto_cancel_at': self.active_reservations[order_id]['auto_cancel_at']
            }
            
        except (TGTGCaptchaException, TGTGServiceException) as tgtg_error:
            error_msg = (
                f"🚫 <b>Reservation Blocked</b>\n\n"
                f"🏪 <b>Store:</b> {store_name}\n"
                f"TGTG has temporarily blocked reservations due to high usage.\n\n"
                f"🔄 <b>Try again in 15-30 minutes</b>"
            )
            logger.warning(f"TGTG service blocked reservation for {store_name}: {tgtg_error}")
            notify(error_msg)
            return {'success': False, 'error': str(tgtg_error), 'service_blocked': True}
        except Exception as e:
            error_msg = f"❌ <b>Reservation Failed</b>\n\n🏪 <b>Store:</b> {store_name}\n🚨 <b>Error:</b> {str(e)}"
            logger.error(f"Failed to reserve bag from {store_name}: {e}")
            notify(error_msg)
            return {'success': False, 'error': str(e)}
    
    def cancel_reservation(self, order_id: str, manual: bool = True) -> bool:
        """
        Cancel a reservation.
        
        Args:
            order_id (str): The order ID to cancel
            manual (bool): Whether this is a manual cancellation (for notification)
            
        Returns:
            bool: True if cancellation was successful
        """
        try:
            # Cancel the auto-cancellation timer if it exists
            if order_id in self.reservation_timers:
                self.reservation_timers[order_id].cancel()
                del self.reservation_timers[order_id]
            
            # Get reservation details before cancelling
            reservation = self.active_reservations.get(order_id, {})
            store_name = reservation.get('store_name', 'Unknown Store')
            
            # Cancel the order via API
            safe_tgtg_call(
                self.client.abort_order,
                operation=f"cancel reservation {order_id}",
                order_id=order_id
            )
            
            # Remove from active reservations
            if order_id in self.active_reservations:
                del self.active_reservations[order_id]
            
            # Send notification
            cancel_type = "Manual" if manual else "Automatic"
            cancel_msg = (
                f"🚫 <b>Reservation Cancelled</b>\n\n"
                f"🏪 <b>Store:</b> {store_name}\n"
                f"🆔 <b>Order ID:</b> <code>{order_id}</code>\n"
                f"🔄 <b>Type:</b> {cancel_type} cancellation\n"
                f"⏰ <b>Cancelled at:</b> {datetime.now().strftime('%H:%M:%S')}\n\n"
                f"✅ The bag is now available for other customers."
            )
            
            notify(cancel_msg)
            logger.info(f"✅ Successfully cancelled reservation {order_id} for {store_name}")
            return True
            
        except (TGTGCaptchaException, TGTGServiceException) as tgtg_error:
            error_msg = (
                f"🚫 <b>Cancellation Blocked</b>\n\n"
                f"🆔 <b>Order ID:</b> <code>{order_id}</code>\n"
                f"TGTG has temporarily blocked API access.\n\n"
                f"🔄 <b>Try cancelling in the TGTG app directly</b>\n"
                f"Or wait 15-30 minutes and try again here."
            )
            logger.warning(f"TGTG service blocked cancellation for {order_id}: {tgtg_error}")
            notify(error_msg)
            return False
        except Exception as e:
            error_msg = f"❌ <b>Cancellation Failed</b>\n\n🆔 <b>Order ID:</b> <code>{order_id}</code>\n🚨 <b>Error:</b> {str(e)}"
            logger.error(f"Failed to cancel reservation {order_id}: {e}")
            notify(error_msg)
            return False
    
    def _auto_cancel_reservation(self, order_id: str):
        """Auto-cancel a reservation after timeout."""
        logger.info(f"⏰ Auto-cancelling reservation {order_id}")
        self.cancel_reservation(order_id, manual=False)
    
    def get_active_reservations(self) -> Dict[str, Dict[str, Any]]:
        """Get all active reservations."""
        return self.active_reservations.copy()
    
    def get_reservation_status(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a specific reservation.
        
        Args:
            order_id (str): The order ID to check
            
        Returns:
            Optional[Dict[str, Any]]: Order status or None if not found
        """
        try:
            status = self.client.get_order_status(order_id)
            return status
        except Exception as e:
            logger.error(f"Failed to get status for order {order_id}: {e}")
            return None
    
    def cleanup_expired_timers(self):
        """Clean up any expired or invalid timers."""
        current_time = datetime.now()
        expired_orders = []
        
        for order_id, reservation in self.active_reservations.items():
            if current_time > reservation['auto_cancel_at']:
                expired_orders.append(order_id)
        
        for order_id in expired_orders:
            logger.info(f"🧹 Cleaning up expired reservation: {order_id}")
            if order_id in self.reservation_timers:
                self.reservation_timers[order_id].cancel()
                del self.reservation_timers[order_id]
            if order_id in self.active_reservations:
                del self.active_reservations[order_id]

# Global reservation manager instance
_reservation_manager: Optional[TGTGReservationManager] = None

def get_reservation_manager() -> TGTGReservationManager:
    """Get or create the global TGTGReservationManager instance."""
    global _reservation_manager
    if _reservation_manager is None:
        _reservation_manager = TGTGReservationManager()
    return _reservation_manager

def reserve_bag(item_id: str, store_name: str, auto_cancel_minutes: int = 10) -> Dict[str, Any]:
    """
    Reserve a TGTG bag.
    
    Args:
        item_id (str): The TGTG item ID
        store_name (str): Store name for notifications
        auto_cancel_minutes (int): Minutes after which to auto-cancel
        
    Returns:
        Dict[str, Any]: Reservation result
    """
    manager = get_reservation_manager()
    return manager.reserve_bag(item_id, store_name, auto_cancel_minutes)

def cancel_reservation(order_id: str) -> bool:
    """
    Cancel a reservation.
    
    Args:
        order_id (str): The order ID to cancel
        
    Returns:
        bool: True if successful
    """
    manager = get_reservation_manager()
    return manager.cancel_reservation(order_id)

if __name__ == "__main__":
    # Test the reservation system
    print("🧪 TGTG Reservation Manager Test")
    print("This would require valid credentials and available offers to test properly.")
    
    try:
        manager = TGTGReservationManager()
        print("✅ Reservation manager initialized successfully!")
        
        active = manager.get_active_reservations()
        print(f"📊 Active reservations: {len(active)}")
        
    except Exception as e:
        print(f"❌ Failed to initialize reservation manager: {e}")
