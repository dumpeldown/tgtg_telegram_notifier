# TGTG Notify - TooGoodToGo Favorites Monitor with Telegram Notifications

This project monitors your TooGoodToGo favorites for available offers and sends instant Telegram notifications when deals become available.

## 🚀 Features

- 🍽️ **TGTG Integration**: Automatically checks your TooGoodToGo favorites
- 📱 **Telegram Notifications**: Instant notifications when offers are found
- 🔄 **Automatic Monitoring**: Can be scheduled to run periodically
- 💰 **Detailed Offers**: Shows price, savings, pickup times, and location
- 🔒 **Secure**: Credentials stored locally and never shared

## 📋 Setup Instructions

### 1. Create a Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Start a conversation with BotFather by sending `/start`
3. Create a new bot by sending `/newbot`
4. Choose a name for your bot (e.g., "TGTG Notifier")
5. Choose a username for your bot (must end with "bot", e.g., "tgtg_notifier_bot")
6. BotFather will give you a **Bot Token** - save this for later

### 2. Get Your Chat ID

1. Search for `@userinfobot` on Telegram
2. Start a conversation and send `/start`
3. The bot will reply with your user information including your **Chat ID** - save this number

### 3. Configure Environment Variables

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file and replace the placeholder values:
   ```
   TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz1234567890
   TELEGRAM_CHAT_ID=123456789
   ```

### 4. Set Up TooGoodToGo Authentication

Run the setup script to authenticate your TGTG account:

```bash
python setup_tgtg.py
```

This will:
- Ask for your TGTG email address
- Send you an authentication email
- Wait for you to click the login link
- Save your credentials for future use

### 5. Test the Complete System

```bash
python main.py
```

This will test both Telegram notifications and TGTG integration.

## 📱 Usage Examples

### Basic Usage

```python
from tgtg_check import TGTGChecker
from telegram_notify import notify

# Create checker instance
checker = TGTGChecker()

# Check for offers and send notifications
checker.check_and_notify()
```

### Manual Checking

```python
from tgtg_check import TGTGChecker

checker = TGTGChecker()

# Get offers without sending notifications
offers = checker.get_favorites_with_offers()

for offer in offers:
    print(f"🍽️ {offer['store']['store_name']}: {offer['items_available']} bags available")
```

### Custom Notifications

```python
from telegram_notify import notify

# Send custom notification
notify("🔔 Custom TGTG notification!")

# Send with formatting
notify("<b>Alert:</b> New offer found! 🎉")
```

## 🔧 File Structure

```
tgtg_notify/
├── main.py                  # Main demo script
├── telegram_notify.py       # Telegram notification system
├── tgtg_check.py           # TooGoodToGo integration
├── setup_tgtg.py           # TGTG authentication setup
├── .env                    # Environment variables (create from .env.example)
├── .env.example            # Environment variables template
├── tgtg_credentials.json   # TGTG credentials (auto-generated)
├── README.md               # This file
└── .gitignore             # Git ignore rules
```

## 🤖 Automation

### Schedule Regular Checks

You can schedule the script to run periodically:

**Linux/macOS (cron):**
```bash
# Check every 30 minutes
*/30 * * * * cd /path/to/tgtg_notify && python -c "from tgtg_check import TGTGChecker; TGTGChecker().check_and_notify(send_summary=False)"
```

**Windows (Task Scheduler):**
- Create a new task
- Set it to run your Python script every 30 minutes
- Use the command: `python -c "from tgtg_check import TGTGChecker; TGTGChecker().check_and_notify(send_summary=False)"`

### Create a Service Script

```python
import time
from tgtg_check import TGTGChecker

def monitor_continuously(interval_minutes=30):
    """Monitor TGTG favorites continuously."""
    checker = TGTGChecker()
    
    while True:
        try:
            checker.check_and_notify(send_summary=False)
        except Exception as e:
            print(f"Error during check: {e}")
        
        time.sleep(interval_minutes * 60)

if __name__ == "__main__":
    monitor_continuously()
```

## 📧 Notification Examples

The system sends rich, formatted notifications:

```
🍽️ Pizza Palace
📍 123 Main Street, City
🛍️ Surprise Bag
📦 2 bags available
💰 4.99 EUR (was 15.00 EUR)
💚 Save 10.01 EUR!
⏰ Pickup: 18:00 - 20:00
```

## ❗ Troubleshooting

### TGTG Issues

1. **"TGTG client not authenticated"**: Run `python setup_tgtg.py` to authenticate
2. **"No favorites found"**: Make sure you have favorites set in your TGTG app
3. **Authentication fails**: Check your email and click the login link within the time limit

### Telegram Issues

1. **"Bot token not found"**: Make sure your `.env` file exists and contains the correct `TELEGRAM_BOT_TOKEN`
2. **"Chat not found"**: Verify your `TELEGRAM_CHAT_ID` is correct
3. **Bot doesn't respond**: Make sure you've started a conversation with your bot by sending `/start` to it

### General Issues

1. **Import errors**: Make sure all packages are installed: `pip install tgtg python-telegram-bot python-dotenv`
2. **Permission errors**: Ensure the script has write permissions for `tgtg_credentials.json`

## 🔒 Security Notes

- Never commit your `.env` file to version control
- Keep your bot token and TGTG credentials secret  
- The `tgtg_credentials.json` file is automatically excluded from git
- Credentials are stored locally and never transmitted except to the respective APIs

## 📄 License

This project is for personal use only. Respect TooGoodToGo's terms of service and rate limits.

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

---

**Happy deal hunting!** 🍽️💚
