#!/usr/bin/env python3
"""
Multi-User Telegram Bot Handler for TGTG Reservations
Handles user registration, TGTG authentication, and reservations for multiple users.
"""

import os
import sys
import json
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CallbackQueryHandler, CommandHandler, 
    MessageHandler, ContextTypes, ConversationHandler, filters
)
from tgtg import TgtgClient

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multi_user.multi_user_db import get_multi_user_db
from common.tgtg_reservation import get_reservation_manager
from common.telegram_notify import notify_to_chat
from common.tgtg_exceptions import (
    safe_tgtg_call, handle_tgtg_exception, get_user_friendly_error_message,
    TGTGCaptchaException, TGTGServiceException
)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Conversation states
WAITING_FOR_EMAIL, WAITING_FOR_VERIFICATION = range(2)

class MultiUserTGTGBotHandler:
    """Handles multi-user Telegram bot interactions for TGTG reservations."""
    
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN must be set in environment variables")
        
        self.db = get_multi_user_db()
        self.reservation_manager = get_reservation_manager()
        self.application = Application.builder().token(self.bot_token).build()
        
        # Store pending authentications
        self.pending_auths: Dict[str, Dict] = {}
        
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up all bot command and callback handlers."""
        
        # Conversation handler for TGTG authentication
        auth_conversation = ConversationHandler(
            entry_points=[CommandHandler("start", self.handle_start_command)],
            states={
                WAITING_FOR_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_email_input)],
                WAITING_FOR_VERIFICATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_verification_check)],
            },
            fallbacks=[CommandHandler("cancel", self.handle_cancel_command)],
        )
        
        self.application.add_handler(auth_conversation)
        
        # Other command handlers
        self.application.add_handler(CommandHandler("status", self.handle_status_command))
        self.application.add_handler(CommandHandler("check", self.handle_check_command))
        self.application.add_handler(CommandHandler("reservations", self.handle_reservations_command))
        self.application.add_handler(CommandHandler("stats", self.handle_stats_command))
        self.application.add_handler(CommandHandler("help", self.handle_help_command))
        
        # Callback query handler for buttons
        self.application.add_handler(CallbackQueryHandler(self.handle_callback_query))
    
    def _update_user_email(self, user_id: int, email: str) -> bool:
        """Update user's TGTG email in the database."""
        return self.db.update_user_email(user_id, email)
    
    async def handle_start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle /start command and initiate user registration."""
        chat_id = str(update.effective_chat.id)
        
        # Check if user already exists
        user = self.db.get_user_by_chat_id(chat_id)
        
        if user and user.get('tgtg_credentials'):
            # User already registered and authenticated
            await update.message.reply_text(
                f"👋 <b>Welcome back!</b>\n\n"
                f"You're already registered and authenticated with TGTG.\n\n"
                f"Use /check to manually check for offers\n"
                f"Use /status to see your account info\n"
                f"Use /help for more commands",
                parse_mode='HTML'
            )
            return ConversationHandler.END
        
        elif user:
            # User exists but not authenticated with TGTG
            await update.message.reply_text(
                f"👋 <b>Welcome back!</b>\n\n"
                f"Your account is registered but not connected to TGTG yet.\n\n"
                f"📧 <b>Enter your Too Good To Go email:</b>\n\n"
                f"💡 <i>Or use</i> /cancel <i>to abort</i>",
                parse_mode='HTML'
            )
            return WAITING_FOR_EMAIL
        
        else:
            # New user
            # Register user in database
            result = self.db.register_user(chat_id)
            
            if result['success']:
                await update.message.reply_text(
                    f"🎉 <b>Welcome to TGTG Bot!</b>\n\n"
                    f"Get instant notifications when your favorite TGTG stores have deals available.\n"
                    f"Reserve bags directly from Telegram with one tap! 🚀\n\n"
                    f"<b>Quick Setup:</b>\n"
                    f"Just enter your TGTG email address and I'll handle the rest.\n\n"
                    f"📧 <b>Enter your Too Good To Go email:</b>\n\n"
                    f"💡 <i>Or use</i> /cancel <i>to abort</i>",
                    parse_mode='HTML'
                )
                return WAITING_FOR_EMAIL
            else:
                await update.message.reply_text(
                    f"❌ <b>Registration Failed</b>\n\n"
                    f"Sorry, there was an error: {result.get('error', 'Unknown error')}\n\n"
                    f"Please try again with /start",
                    parse_mode='HTML'
                )
                return ConversationHandler.END
    
    async def handle_email_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle email input and start TGTG authentication."""
        email = update.message.text.strip()
        chat_id = str(update.effective_chat.id)
        
        # Validate email format
        if '@' not in email or '.' not in email:
            await update.message.reply_text(
                f"❌ <b>Invalid Email</b>\n\n"
                f"Please enter a valid email address:\n\n"
                f"💡 <i>Or use</i> /cancel <i>to start over</i>",
                parse_mode='HTML'
            )
            return WAITING_FOR_EMAIL
        
        # Update user with email
        user = self.db.get_user_by_chat_id(chat_id)
        if not user:
            await update.message.reply_text(
                f"❌ <b>User Not Found</b>\n\n"
                f"Please restart with /start",
                parse_mode='HTML'
            )
            return ConversationHandler.END
        
        # Save the email to the database
        success = self._update_user_email(user['user_id'], email)
        if not success:
            await update.message.reply_text(
                f"❌ <b>Database Error</b>\n\n"
                f"Failed to save email. Please try again with /start",
                parse_mode='HTML'
            )
            return ConversationHandler.END
        
        # Start TGTG authentication process
        try:
            await update.message.reply_text(
                f"� <b>Sending Verification Email</b>\n\n"
                f"Email: <code>{email}</code>\n\n"
                f"Please wait while I send you a verification email...",
                parse_mode='HTML'
            )
            
            # Create TGTG client and immediately start email verification
            client = TgtgClient(email=email)
            
            # Send the verification email immediately (in background)
            credentials_task = asyncio.create_task(
                asyncio.to_thread(lambda: safe_tgtg_call(
                    client.get_credentials, 
                    operation="email verification"
                ))
            )
            
            # Store the task and user info for completion
            self.pending_auths[chat_id] = {
                'client': client,
                'credentials_task': credentials_task,
                'email': email,
                'user_id': user['user_id']
            }
            
            await update.message.reply_text(
                f"📧 <b>Email Sent!</b>\n\n"
                f"I've sent a verification email to:\n"
                f"<code>{email}</code>\n\n"
                f"<b>Please:</b>\n"
                f"1️⃣ Check your email (including spam folder)\n"
                f"2️⃣ Click the verification link from TGTG\n"
                f"3️⃣ Send me any message when done\n\n"
                f"⚡ <b>That's it!</b> Just one message after clicking the link.\n\n"
                f"⏱️ <i>Please be quick - the link expires in a few minutes.</i>\n\n"
                f"💡 <i>Use</i> /cancel <i>to abort</i>",
                parse_mode='HTML'
            )
            
            return WAITING_FOR_VERIFICATION
            
        except Exception as e:
            logger.error(f"TGTG authentication error for {chat_id}: {e}")
            await update.message.reply_text(
                f"❌ <b>Authentication Error</b>\n\n"
                f"Failed to start TGTG authentication: {str(e)}\n\n"
                f"Please check your email address.\n\n"
                f"💡 <i>Try again:</i> /start",
                parse_mode='HTML'
            )
            return ConversationHandler.END
    
    async def handle_verification_check(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle the user's response after clicking the verification link."""
        chat_id = str(update.effective_chat.id)
        
        if chat_id not in self.pending_auths:
            await update.message.reply_text(
                f"❌ <b>No Pending Authentication</b>\n\n"
                f"Please restart with /start",
                parse_mode='HTML'
            )
            return ConversationHandler.END
            
        auth_info = self.pending_auths[chat_id]
        client = auth_info['client']
        credentials_task = auth_info['credentials_task']
        email = auth_info['email']
        user_id = auth_info['user_id']
        
        try:
            await update.message.reply_text(
                f"🔄 <b>Checking Verification</b>\n\n"
                f"Please wait while I verify your authentication...",
                parse_mode='HTML'
            )
            
            # Check if the credentials are ready
            if credentials_task.done():
                try:
                    credentials = credentials_task.result()
                    
                    if credentials:
                        # Test the credentials by getting favorites
                        await update.message.reply_text("🔍 Testing connection...")
                        
                        favorites = safe_tgtg_call(
                            client.get_favorites,
                            operation="authentication test"
                        )
                        
                        if favorites:
                            # Save credentials to database
                            cred_data = {
                                'access_token': client.access_token,
                                'refresh_token': client.refresh_token,
                                'user_id': client.user_id,
                                'cookie': client.cookie
                            }
                            
                            success = self.db.save_user_credentials(user_id, cred_data)
                            
                            if success:
                                # Clean up pending authentication
                                del self.pending_auths[chat_id]
                                
                                await update.message.reply_text(
                                    f"🎉 <b>Setup Complete!</b>\n\n"
                                    f"✅ Connected to TGTG: <code>{email}</code>\n"
                                    f"✅ Found <b>{len(favorites)}</b> favorite stores\n"
                                    f"✅ Ready to receive notifications\n\n"
                                    f"🚀 <b>You're all set!</b> I'll notify you when deals are available.\n\n"
                                    f"💡 <b>Try these commands:</b>\n"
                                    f"/check - Check for offers now\n"
                                    f"/status - View your account\n"
                                    f"/help - Get help",
                                    parse_mode='HTML'
                                )
                                return ConversationHandler.END
                            else:
                                await update.message.reply_text(
                                    f"❌ <b>Setup Failed</b>\n\n"
                                    f"Authentication worked, but I couldn't save your credentials.\n\n"
                                    f"💡 <i>Try again:</i> /start",
                                    parse_mode='HTML'
                                )
                                return ConversationHandler.END
                        else:
                            await update.message.reply_text(
                                f"⚠️ <b>No Favorites Found</b>\n\n"
                                f"Authentication successful, but you have no favorite stores.\n"
                                f"Please add some favorites in the TGTG app first.\n\n"
                                f"💡 <i>Then try:</i> /start",
                                parse_mode='HTML'
                            )
                            return ConversationHandler.END
                    else:
                        await update.message.reply_text(
                            f"❌ <b>Verification Failed</b>\n\n"
                            f"The email verification wasn't completed successfully.\n\n"
                            f"💡 <i>Try again:</i> /start",
                            parse_mode='HTML'
                        )
                        return ConversationHandler.END
                        
                except (TGTGCaptchaException, TGTGServiceException) as tgtg_error:
                    logger.warning(f"TGTG service issue during verification for {chat_id}: {tgtg_error}")
                    error_message = get_user_friendly_error_message(tgtg_error)
                    await update.message.reply_text(
                        f"⚠️ <b>Service Temporarily Unavailable</b>\n\n"
                        f"TGTG authentication is temporarily blocked.\n"
                        f"This is a protective measure by TGTG.\n\n"
                        f"🔄 <b>Please try again in 15-30 minutes.</b>\n\n"
                        f"💡 <i>Use</i> /start <i>to try again later</i>",
                        parse_mode='HTML'
                    )
                    return ConversationHandler.END
                except Exception as cred_error:
                    logger.error(f"Credentials error for {chat_id}: {cred_error}")
                    await update.message.reply_text(
                        f"❌ <b>Authentication Error</b>\n\n"
                        f"Something went wrong: {str(cred_error)}\n\n"
                        f"💡 <i>Try again:</i> /start",
                        parse_mode='HTML'
                    )
                    return ConversationHandler.END
            else:
                # Credentials not ready yet - user probably hasn't clicked the link
                await update.message.reply_text(
                    f"⏳ <b>Still Waiting...</b>\n\n"
                    f"I haven't received confirmation yet.\n\n"
                    f"Please make sure you:\n"
                    f"✓ Check your email (and spam folder)\n"
                    f"✓ Click the TGTG verification link\n"
                    f"✓ Wait a moment for it to process\n\n"
                    f"Then send me another message.\n\n"
                    f"💡 <i>Use</i> /cancel <i>to start over</i>",
                    parse_mode='HTML'
                )
                return WAITING_FOR_VERIFICATION
                
        except Exception as e:
            logger.error(f"Verification error for {chat_id}: {e}")
            await update.message.reply_text(
                f"❌ <b>Verification Error</b>\n\n"
                f"Something went wrong: {str(e)}\n\n"
                f"💡 <i>Try again:</i> /start",
                parse_mode='HTML'
            )
            # Clean up on error
            if chat_id in self.pending_auths:
                if 'credentials_task' in self.pending_auths[chat_id]:
                    self.pending_auths[chat_id]['credentials_task'].cancel()
                del self.pending_auths[chat_id]
            return ConversationHandler.END
    
    async def handle_cancel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle /cancel command."""
        chat_id = str(update.effective_chat.id)
        
        # Clean up any pending authentication
        if chat_id in self.pending_auths:
            # Cancel the credentials task if it exists
            if 'credentials_task' in self.pending_auths[chat_id]:
                self.pending_auths[chat_id]['credentials_task'].cancel()
            del self.pending_auths[chat_id]
        
        await update.message.reply_text(
            f"🚫 <b>Registration Cancelled</b>\n\n"
            f"Setup process cancelled.\n\n"
            f"Start over anytime with /start",
            parse_mode='HTML'
        )
        return ConversationHandler.END
    
    async def handle_status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /status command."""
        chat_id = str(update.effective_chat.id)
        user = self.db.get_user_by_chat_id(chat_id)
        
        if not user:
            await update.message.reply_text(
                f"❌ <b>Not Registered</b>\n\n"
                f"You're not registered yet.\n\n"
                f"💡 <i>Use</i> /start <i>to get started!</i>",
                parse_mode='HTML'
            )
            return
        
        # Get user stats
        stats = self.db.get_user_stats(user['user_id'])
        
        status_message = f"👤 <b>Account Status</b>\n\n"
        status_message += f"📧 <b>TGTG Email:</b> {user.get('tgtg_email', 'Not set')}\n"
        status_message += f"🆔 <b>User ID:</b> {user['user_id']}\n"
        status_message += f"🌍 <b>Timezone:</b> {user.get('timezone', 'Europe/Berlin')}\n"
        status_message += f"📅 <b>Registered:</b> {user.get('created_at', 'Unknown')}\n"
        
        if user.get('tgtg_credentials'):
            status_message += f"✅ <b>TGTG Status:</b> Authenticated\n"
        else:
            status_message += f"❌ <b>TGTG Status:</b> Not authenticated\n"
            status_message += f"💡 <i>Use</i> /start <i>to authenticate</i>\n"
        
        status_message += f"\n📊 <b>Statistics:</b>\n"
        status_message += f"• Notifications sent: {stats.get('notification_count', 0)}\n"
        status_message += f"• Reservations made: {stats.get('reservation_count', 0)}\n"
        
        if user.get('tgtg_credentials'):
            status_message += f"\n💡 <i>Commands:</i> /check /help"
        
        await update.message.reply_text(status_message, parse_mode='HTML')
    
    async def handle_check_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /check command for manual offer checking."""
        chat_id = str(update.effective_chat.id)
        user = self.db.get_user_by_chat_id(chat_id)
        
        if not user or not user.get('tgtg_credentials'):
            await update.message.reply_text(
                f"❌ <b>Not Authenticated</b>\n\n"
                f"Please authenticate with TGTG first.\n\n"
                f"💡 <i>Use</i> /start <i>to authenticate</i>",
                parse_mode='HTML'
            )
            return
        
        await update.message.reply_text(
            f"🔍 <b>Checking for offers...</b>\n\n"
            f"Please wait while I check your TGTG favorites.",
            parse_mode='HTML'
        )
        
        # Import and use the multi-user checker for manual check (shows ALL offers)
        from multi_user_tgtg import get_multi_user_checker
        checker = get_multi_user_checker()
        
        success = checker.manual_check_user_offers(user['user_id'], chat_id)
        
        if not success:
            await update.message.reply_text(
                f"❌ <b>Check Failed</b>\n\n"
                f"There was an error checking your offers.\n\n"
                f"💡 <i>Try:</i> /status /help",
                parse_mode='HTML'
            )
    
    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle callback queries from inline keyboard buttons."""
        query = update.callback_query
        await query.answer()  # Acknowledge the callback query
        
        callback_data = query.data
        chat_id = str(query.message.chat_id)
        
        logger.info(f"📱 Received callback from {chat_id}: {callback_data}")
        
        # Check if user is authenticated
        user = self.db.get_user_by_chat_id(chat_id)
        if not user or not user.get('tgtg_credentials'):
            await query.edit_message_text(
                f"❌ <b>Not Authenticated</b>\n\n"
                f"Please authenticate with TGTG first.\n\n"
                f"💡 <i>Use</i> /start <i>to authenticate</i>",
                parse_mode='HTML'
            )
            return
        
        try:
            if callback_data.startswith("reserve:"):
                await self._handle_reserve_callback(query, callback_data, user)
            elif callback_data.startswith("cancel_reserve:") or callback_data.startswith("manual_cancel:"):
                await self._handle_cancel_callback(query, callback_data, user)
            else:
                await query.edit_message_text("❌ Unknown action. Please try again.")
        
        except Exception as e:
            logger.error(f"Error handling callback query: {e}")
            try:
                await query.edit_message_text(f"❌ <b>Error:</b> {str(e)}", parse_mode='HTML')
            except:
                pass  # Message might be too old to edit
    
    async def _handle_reserve_callback(self, query, callback_data: str, user: Dict) -> None:
        """Handle reservation button press."""
        try:
            # Extract item ID from callback data
            item_id = callback_data.split(":", 1)[1]
            
            # Get store name from the original message
            original_text = query.message.text
            store_name = "Unknown Store"
            
            # Try to extract store name from message
            lines = original_text.split('\n')
            for line in lines:
                if line.startswith('🍽️') and '<b>' in line:
                    store_name = line.replace('🍽️ <b>', '').replace('</b>', '').strip()
                    break
            
            # Update message to show reservation in progress
            await query.edit_message_text(
                f"⏳ <b>Reserving bag...</b>\n\n"
                f"🏪 <b>Store:</b> {store_name}\n"
                f"🆔 <b>Item ID:</b> <code>{item_id}</code>\n\n"
                f"Please wait while I reserve your bag...",
                parse_mode='HTML'
            )
            
            # Attempt reservation using the reservation manager
            # Note: We need to create a user-specific reservation manager
            from common.tgtg_reservation import TGTGReservationManager
            
            # Create a client with user's credentials
            credentials = self.db.get_user_credentials(user['user_id'])
            from tgtg import TgtgClient
            
            client = TgtgClient(
                access_token=credentials.get('access_token'),
                refresh_token=credentials.get('refresh_token'),
                cookie=credentials.get('cookie')
            )
            
            # Create order
            try:
                order = safe_tgtg_call(
                    client.create_order,
                    operation=f"reserve bag for {store_name}",
                    item_id=item_id,
                    item_count=1
                )
                order_id = order.get('id')
                
                if order_id:
                    success_text = (
                        f"✅ <b>Reservation Successful!</b>\n\n"
                        f"🏪 <b>Store:</b> {store_name}\n"
                        f"🆔 <b>Order ID:</b> <code>{order_id}</code>\n"
                        f"⏰ <b>Reserved at:</b> {datetime.now().strftime('%H:%M:%S')}\n\n"
                        f"💡 <b>Quick! Open the TGTG app and complete your payment!</b>\n\n"
                        f"⚠️ <i>Remember to complete the purchase in the app, or cancel the reservation to free it up for others.</i>"
                    )
                    
                    # Create cancel button
                    keyboard = [[InlineKeyboardButton("🚫 Cancel Reservation", callback_data=f"manual_cancel:{order_id}")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await query.edit_message_text(success_text, reply_markup=reply_markup, parse_mode='HTML')
                    
                    # Send notification to user's chat
                    notify_to_chat(
                        f"✅ <b>Bag Reserved!</b>\n\n"
                        f"Order ID: <code>{order_id}</code> for {store_name}\n"
                        f"Open the TGTG app quickly to complete payment!",
                        str(user['telegram_chat_id'])
                    )
                    
                else:
                    await query.edit_message_text(
                        f"❌ <b>Reservation Failed</b>\n\n"
                        f"🏪 <b>Store:</b> {store_name}\n"
                        f"The bag might already be taken or unavailable.",
                        parse_mode='HTML'
                    )
            
            except (TGTGCaptchaException, TGTGServiceException) as tgtg_error:
                logger.warning(f"TGTG service issue during reservation: {tgtg_error}")
                await query.edit_message_text(
                    f"🚫 <b>Reservation Blocked</b>\n\n"
                    f"🏪 <b>Store:</b> {store_name}\n"
                    f"TGTG has temporarily blocked reservations due to high usage.\n\n"
                    f"🔄 <b>Try again in 15-30 minutes</b>",
                    parse_mode='HTML'
                )
            except Exception as reserve_error:
                await query.edit_message_text(
                    f"❌ <b>Reservation Failed</b>\n\n"
                    f"🏪 <b>Store:</b> {store_name}\n"
                    f"🚨 <b>Error:</b> {str(reserve_error)}\n\n"
                    f"The bag might already be taken or unavailable.",
                    parse_mode='HTML'
                )
        
        except Exception as e:
            logger.error(f"Error in reserve callback: {e}")
            await query.edit_message_text(f"❌ <b>Reservation Error:</b> {str(e)}", parse_mode='HTML')
    
    async def _handle_cancel_callback(self, query, callback_data: str, user: Dict) -> None:
        """Handle cancellation button press."""
        try:
            if callback_data.startswith("manual_cancel:"):
                # Manual cancellation of active reservation
                order_id = callback_data.split(":", 1)[1]
                
                await query.edit_message_text("⏳ <b>Cancelling reservation...</b>", parse_mode='HTML')
                
                # Cancel the order using user's client
                credentials = self.db.get_user_credentials(user['user_id'])
                from tgtg import TgtgClient
                
                client = TgtgClient(
                    access_token=credentials.get('access_token'),
                    refresh_token=credentials.get('refresh_token'),
                    cookie=credentials.get('cookie')
                )
                
                try:
                    safe_tgtg_call(
                        client.abort_order,
                        operation=f"cancel reservation {order_id}",
                        order_id=order_id
                    )
                    
                    await query.edit_message_text(
                        f"✅ <b>Reservation Cancelled</b>\n\n"
                        f"🆔 <b>Order ID:</b> <code>{order_id}</code>\n"
                        f"🔄 <b>Status:</b> Successfully cancelled\n\n"
                        f"The bag is now available for other customers.",
                        parse_mode='HTML'
                    )
                except (TGTGCaptchaException, TGTGServiceException) as tgtg_error:
                    logger.warning(f"TGTG service issue during cancellation: {tgtg_error}")
                    await query.edit_message_text(
                        f"🚫 <b>Cancellation Blocked</b>\n\n"
                        f"🆔 <b>Order ID:</b> <code>{order_id}</code>\n"
                        f"TGTG has temporarily blocked API access.\n\n"
                        f"🔄 <b>Try cancelling in the TGTG app directly</b>\n"
                        f"Or wait 15-30 minutes and try again here.",
                        parse_mode='HTML'
                    )
                except Exception as cancel_error:
                    await query.edit_message_text(
                        f"❌ <b>Cancellation Failed</b>\n\n"
                        f"🆔 <b>Order ID:</b> <code>{order_id}</code>\n"
                        f"🚨 <b>Error:</b> {str(cancel_error)}\n\n"
                        f"The reservation might have already expired or been processed.",
                        parse_mode='HTML'
                    )
            else:
                # Simple cancel button - just dismiss the offer notification
                await query.edit_message_text(
                    f"🚫 <b>Offer Dismissed</b>\n\n"
                    f"You chose not to reserve this bag.\n"
                    f"You'll be notified of new offers as they become available.",
                    parse_mode='HTML'
                )
        
        except Exception as e:
            logger.error(f"Error in cancel callback: {e}")
            await query.edit_message_text(f"❌ <b>Cancel Error:</b> {str(e)}", parse_mode='HTML')
    
    async def handle_reservations_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /reservations command to show active reservations."""
        await update.message.reply_text(
            f"📋 <b>Active Reservations</b>\n\n"
            f"This feature shows reservations made through the automatic reservation system.\n"
            f"For manual reservations made through buttons, check your TGTG app directly.",
            parse_mode='HTML'
        )
    
    async def handle_stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /stats command."""
        chat_id = str(update.effective_chat.id)
        user = self.db.get_user_by_chat_id(chat_id)
        
        if not user:
            await update.message.reply_text(
                f"❌ <b>Not Registered</b>\n\n"
                f"You're not registered yet.\n\n"
                f"💡 <i>Use</i> /start <i>to get started!</i>",
                parse_mode='HTML'
            )
            return
        
        stats = self.db.get_user_stats(user['user_id'])
        
        stats_message = f"📊 <b>Your TGTG Stats</b>\n\n"
        stats_message += f"📧 Notifications received: {stats.get('notification_count', 0)}\n"
        stats_message += f"🛒 Reservations made: {stats.get('reservation_count', 0)}\n"
        stats_message += f"📅 Member since: {stats.get('created_at', 'Unknown')}\n"
        stats_message += f"⏰ Last active: {stats.get('last_active', 'Unknown')}\n"
        
        await update.message.reply_text(stats_message, parse_mode='HTML')
    
    async def handle_help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command."""
        help_text = f"""
🤖 <b>Multi-User TGTG Bot Help</b>

<b>🚀 Getting Started:</b>
/start - Register and authenticate with TGTG

<b>📱 Commands:</b>
/status - Show your account status
/check - Check for ALL current offers (manual check)
/stats - Show your statistics
/reservations - Show active reservations
/help - Show this help message

<b>🔧 How it works:</b>
1. Register with /start and enter your TGTG email
2. Click the verification link sent to your email
3. The bot will monitor your TGTG favorites automatically
4. Get notifications with "Reserve" buttons for NEW offers only
5. Use /check to see ALL current offers anytime
6. Click "Reserve" to instantly reserve bags
7. Complete payment in the TGTG app

<b>✨ Features:</b>
• Automatic offer monitoring every 15 minutes (new offers only)
• Manual checking shows ALL current offers
• Instant reservation via Telegram buttons
• No duplicate notifications for automatic monitoring

💡 <i>Click any command above to use it!</i>
        """
        
        await update.message.reply_text(help_text, parse_mode='HTML')
    
    def run_polling(self):
        """Run the bot with polling."""
        logger.info("🤖 Starting Multi-User TGTG Telegram Bot...")
        self.application.run_polling()
    
    async def run_webhook(self, webhook_url: str, port: int = 8443):
        """Run the bot with webhook (for production)."""
        logger.info(f"🌐 Starting Multi-User TGTG Telegram Bot with webhook: {webhook_url}")
        await self.application.run_webhook(
            listen="0.0.0.0",
            port=port,
            webhook_url=webhook_url
        )

def main():
    """Run the multi-user bot handler."""
    try:
        bot_handler = MultiUserTGTGBotHandler()
        bot_handler.run_polling()
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Bot error: {e}")

if __name__ == "__main__":
    main()
