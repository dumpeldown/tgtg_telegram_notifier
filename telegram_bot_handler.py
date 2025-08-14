#!/usr/bin/env python3
"""
Telegram Bot Handler for TGTG Reservations
Handles callback queries from inline keyboard buttons.
"""

import os
import json
import logging
from typing import Dict, Any
from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes
from telegram_notify import get_notifier
from tgtg_reservation import get_reservation_manager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class TGTGBotHandler:
    """Handles Telegram bot interactions for TGTG reservations."""
    
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN must be set in environment variables")
        
        self.reservation_manager = get_reservation_manager()
        self.application = Application.builder().token(self.bot_token).build()
        
        # Add handlers
        self.application.add_handler(CallbackQueryHandler(self.handle_callback_query))
        self.application.add_handler(CommandHandler("reservations", self.handle_reservations_command))
        self.application.add_handler(CommandHandler("cancel_all", self.handle_cancel_all_command))
    
    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle callback queries from inline keyboard buttons."""
        query = update.callback_query
        await query.answer()  # Acknowledge the callback query
        
        callback_data = query.data
        logger.info(f"📱 Received callback: {callback_data}")
        
        try:
            if callback_data.startswith("reserve:"):
                await self._handle_reserve_callback(query, callback_data)
            elif callback_data.startswith("cancel_reserve:"):
                await self._handle_cancel_callback(query, callback_data)
            elif callback_data.startswith("test"):
                await query.edit_message_text("✅ Test action received.")
            else:
                await query.edit_message_text("❌ Unknown action. Please try again.")
        except Exception as e:
            logger.error(f"Error handling callback query: {e}")
            try:
                await query.edit_message_text(f"❌ <b>Error:</b> {str(e)}")
            except:
                pass  # Message might be too old to edit
    
    async def _handle_reserve_callback(self, query, callback_data: str) -> None:
        """Handle reservation button press."""
        try:
            # Extract item ID from callback data
            item_id = callback_data.split(":", 1)[1]
            
            # Get store name from the original message (try to extract it)
            original_text = query.message.text
            store_name = "Unknown Store"
            
            # Try to extract store name from message
            lines = original_text.split('\n')
            for line in lines:
                if line.startswith('🏪') and 'Store:' in line:
                    store_name = line.split(':', 1)[1].strip()
                    break
            
            # Update message to show reservation in progress
            await query.edit_message_text(
                f"⏳ <b>Reserving bag...</b>\n\n"
                f"🏪 <b>Store:</b> {store_name}\n"
                f"🆔 <b>Item ID:</b> <code>{item_id}</code>\n\n"
                f"Please wait while we reserve your bag..."
            )
            
            # Attempt reservation
            result = self.reservation_manager.reserve_bag(item_id, store_name)
            
            if result['success']:
                order_id = result['order_id']
                auto_cancel_time = result['auto_cancel_at'].strftime('%H:%M:%S')
                
                # Update message with success
                success_text = (
                    f"✅ <b>Reservation Successful!</b>\n\n"
                    f"🏪 <b>Store:</b> {store_name}\n"
                    f"🆔 <b>Order ID:</b> <code>{order_id}</code>\n"
                    f"⏰ <b>Auto-cancel at:</b> {auto_cancel_time}\n\n"
                    f"💡 <b>Quick! Open the TGTG app and complete your payment!</b>\n\n"
                    f"⚠️ <i>This reservation will be automatically cancelled to free up the bag for others.</i>"
                )
                
                # Create cancel button for manual cancellation
                from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                keyboard = [[InlineKeyboardButton("🚫 Cancel Reservation", callback_data=f"manual_cancel:{order_id}")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(success_text, reply_markup=reply_markup)
                
            else:
                error_text = (
                    f"❌ <b>Reservation Failed</b>\n\n"
                    f"🏪 <b>Store:</b> {store_name}\n"
                    f"🚨 <b>Error:</b> {result.get('error', 'Unknown error')}\n\n"
                    f"The bag might already be taken or unavailable."
                )
                await query.edit_message_text(error_text)
        
        except Exception as e:
            logger.error(f"Error in reserve callback: {e}")
            await query.edit_message_text(f"❌ <b>Reservation Error:</b> {str(e)}")
    
    async def _handle_cancel_callback(self, query, callback_data: str) -> None:
        """Handle cancellation button press."""
        try:
            if callback_data.startswith("manual_cancel:"):
                # Manual cancellation of active reservation
                order_id = callback_data.split(":", 1)[1]
                
                await query.edit_message_text("⏳ <b>Cancelling reservation...</b>")
                
                success = self.reservation_manager.cancel_reservation(order_id, manual=True)
                
                if success:
                    await query.edit_message_text(
                        f"✅ <b>Reservation Cancelled</b>\n\n"
                        f"🆔 <b>Order ID:</b> <code>{order_id}</code>\n"
                        f"🔄 <b>Status:</b> Successfully cancelled\n\n"
                        f"The bag is now available for other customers."
                    )
                else:
                    await query.edit_message_text(
                        f"❌ <b>Cancellation Failed</b>\n\n"
                        f"🆔 <b>Order ID:</b> <code>{order_id}</code>\n\n"
                        f"The reservation might have already expired or been processed."
                    )
            else:
                # Simple cancel button - just dismiss the offer notification
                await query.edit_message_text(
                    f"🚫 <b>Offer Dismissed</b>\n\n"
                    f"You chose not to reserve this bag.\n"
                    f"You'll be notified of new offers as they become available."
                )
        
        except Exception as e:
            logger.error(f"Error in cancel callback: {e}")
            await query.edit_message_text(f"❌ <b>Cancel Error:</b> {str(e)}")
    
    async def handle_reservations_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /reservations command to show active reservations."""
        try:
            active_reservations = self.reservation_manager.get_active_reservations()
            
            if not active_reservations:
                await update.message.reply_text("📭 <b>No Active Reservations</b>\n\nYou don't have any active bag reservations right now.")
                return
            
            message_lines = ["📋 <b>Active Reservations</b>\n"]
            
            for order_id, reservation in active_reservations.items():
                store_name = reservation['store_name']
                reserved_at = reservation['reserved_at'].strftime('%H:%M:%S')
                auto_cancel_at = reservation['auto_cancel_at'].strftime('%H:%M:%S')
                
                message_lines.append(
                    f"🏪 <b>{store_name}</b>\n"
                    f"🆔 Order: <code>{order_id}</code>\n"
                    f"⏰ Reserved: {reserved_at}\n"
                    f"🚨 Auto-cancel: {auto_cancel_at}\n"
                )
            
            message_text = "\n".join(message_lines)
            await update.message.reply_text(message_text)
        
        except Exception as e:
            logger.error(f"Error in reservations command: {e}")
            await update.message.reply_text(f"❌ <b>Error:</b> {str(e)}")
    
    async def handle_cancel_all_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /cancel_all command to cancel all active reservations."""
        try:
            active_reservations = self.reservation_manager.get_active_reservations()
            
            if not active_reservations:
                await update.message.reply_text("📭 No active reservations to cancel.")
                return
            
            cancelled_count = 0
            for order_id in list(active_reservations.keys()):
                if self.reservation_manager.cancel_reservation(order_id, manual=True):
                    cancelled_count += 1
            
            await update.message.reply_text(
                f"✅ <b>Bulk Cancellation Complete</b>\n\n"
                f"Cancelled {cancelled_count} out of {len(active_reservations)} reservations."
            )
        
        except Exception as e:
            logger.error(f"Error in cancel_all command: {e}")
            await update.message.reply_text(f"❌ <b>Error:</b> {str(e)}")
    
    def run_polling(self):
        """Run the bot with polling."""
        logger.info("🤖 Starting TGTG Telegram Bot...")
        self.application.run_polling()
    
    async def run_webhook(self, webhook_url: str, port: int = 8443):
        """Run the bot with webhook (for production)."""
        logger.info(f"🌐 Starting TGTG Telegram Bot with webhook: {webhook_url}")
        await self.application.run_webhook(
            listen="0.0.0.0",
            port=port,
            webhook_url=webhook_url
        )

def main():
    """Run the bot handler."""
    try:
        bot_handler = TGTGBotHandler()
        bot_handler.run_polling()
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Bot error: {e}")

if __name__ == "__main__":
    main()
