#!/usr/bin/env python3
"""
Test script for TGTG reservation functionality.
Tests the reservation system with mock data.
"""

import os
import sys
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram_notify import notify_with_reservation_buttons, get_notifier

def test_reservation_buttons():
    """Test sending a notification with reservation buttons."""
    print("🧪 Testing TGTG Reservation Button Functionality\n")
    
    # Mock offer data
    mock_offer_message = (
        "🍽️ <b>Test Restaurant</b>\n"
        "📍 123 Test Street, Test City\n"
        "🛍️ <b>Surprise Bag</b>\n"
        "📦 <b>2</b> bags available\n"
        "📅 <b>Today</b>\n"
        "⏰ <b>Pickup:</b> 18:00 - 19:00 🔥 <b>Soon!</b>"
    )
    
    mock_item_id = "test_item_12345"
    mock_store_name = "Test Restaurant"
    
    print("📋 Test offer details:")
    print(f"   Store: {mock_store_name}")
    print(f"   Item ID: {mock_item_id}")
    print(f"   Message: {mock_offer_message[:50]}...")
    
    print("\n📤 Sending test notification with reservation buttons...")
    
    try:
        success = notify_with_reservation_buttons(
            mock_offer_message, 
            mock_item_id, 
            mock_store_name
        )
        
        if success:
            print("✅ Test notification sent successfully!")
            print("\n💡 Check your Telegram chat for:")
            print("   - The offer message")
            print("   - 'Reserve Bag' button")
            print("   - 'Cancel' button")
            print("\n⚠️  Note: The reservation will fail since this is test data,")
            print("   but you can test the button interface!")
        else:
            print("❌ Failed to send test notification")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

def test_simple_keyboard():
    """Test creating and sending a simple inline keyboard."""
    print("\n🧪 Testing Simple Inline Keyboard\n")
    
    try:
        notifier = get_notifier()
        
        # Create a simple keyboard
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Test Button 1", callback_data="test:1")],
            [InlineKeyboardButton("🔄 Test Button 2", callback_data="test:2")],
            [InlineKeyboardButton("❌ Cancel Test", callback_data="test:cancel")]
        ])
        
        test_message = (
            "🧪 <b>Keyboard Test</b>\n\n"
            "This is a test message with inline buttons.\n"
            "Click any button to test the callback system!"
        )
        
        success = notifier.send_message_sync(test_message, reply_markup=keyboard)
        
        if success:
            print("✅ Keyboard test sent successfully!")
            print("💡 Check your Telegram chat and try pressing the buttons.")
        else:
            print("❌ Failed to send keyboard test")
            
    except Exception as e:
        print(f"❌ Error during keyboard test: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Run the tests."""
    print("🚀 TGTG Reservation System Tests")
    print("=" * 40)
    
    # Check environment
    if not os.getenv('TELEGRAM_BOT_TOKEN'):
        print("❌ TELEGRAM_BOT_TOKEN not found in environment!")
        print("Make sure your .env file is configured properly.")
        sys.exit(1)
    
    if not os.getenv('TELEGRAM_CHAT_ID'):
        print("❌ TELEGRAM_CHAT_ID not found in environment!")
        print("Make sure your .env file is configured properly.")
        sys.exit(1)
    
    print("✅ Environment variables found")
    print()
    
    # Test 1: Simple keyboard test
    test_simple_keyboard()
    
    input("\n⏸️  Press Enter to continue to the reservation button test...")
    
    # Test 2: Reservation buttons test
    test_reservation_buttons()
    
    print("\n" + "=" * 40)
    print("🏁 Tests completed!")
    print()
    print("📝 Next steps:")
    print("1. Start the bot handler: python start_bot.py")
    print("2. Press the buttons in your Telegram chat")
    print("3. Check the bot logs for callback handling")
    print()
    print("⚠️  Remember: The actual reservation will fail with test data,")
    print("   but you can verify the button interface is working!")

if __name__ == "__main__":
    main()
