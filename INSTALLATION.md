# TGTG Telegram Notifier - Server Installation Guide

This guide helps you set up the TGTG notification system on a new server with all required dependencies and cron jobs.

## 🚀 Quick Installation

### Option 1: Automated Setup (Recommended)
```bash
# 1. Clone/copy your project to the server
git clone <your-repo-url> tgtg_telegram_notifier
cd tgtg_telegram_notifier

# 2. Run the automated setup script
chmod +x setup_server.sh
./setup_server.sh

# 3. Follow the prompts to configure your credentials
```

### Option 2: Manual Setup

#### Step 1: System Requirements
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv git

# CentOS/RHEL
sudo yum update
sudo yum install python3 python3-pip git

# Arch Linux
sudo pacman -Sy python python-pip git
```

#### Step 2: Python Dependencies
```bash
# Install required Python packages
pip3 install --user python-telegram-bot tgtg pytz python-dotenv requests

# Or use virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate
pip install python-telegram-bot tgtg pytz python-dotenv requests
```

#### Step 3: Configuration Files

Create `.env` file:
```bash
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Optional: Set your timezone
DEFAULT_TIMEZONE=Europe/Berlin
```

Set up TGTG credentials:
```bash
python3 setup_tgtg.py
```

#### Step 4: Install Cron Jobs
```bash
# Edit the crontab file to update paths if needed
nano tgtg-15min-notify-crontab.txt

# Install the crontab
crontab tgtg-15min-notify-crontab.txt
```

## 📋 Cron Job Schedule

The crontab includes several automated tasks:

| Job | Schedule | Description |
|-----|----------|-------------|
| **Main Notifications** | Every 15 minutes | Checks for new TGTG offers and sends notifications |
| **Dependency Check** | Daily at 6:00 AM | Ensures all Python packages are installed |
| **Health Check** | Every hour | Verifies configuration files exist |
| **Weekly Summary** | Sundays at 6:00 PM | Sends database statistics |
| **Monthly Cleanup** | 1st of month at 2:00 AM | Cleans old notification records |
| **Boot Setup** | At system startup | Installs dependencies after reboot |

## 🔧 Configuration

### Required Files
- `.env` - Telegram bot credentials
- `tgtg_credentials.json` - TGTG authentication (created by setup_tgtg.py)

### Directory Structure
```
tgtg_telegram_notifier/
├── .env                           # Telegram configuration
├── tgtg_credentials.json          # TGTG authentication
├── main.py                        # Main script
├── tgtg_check.py                  # TGTG checking logic
├── telegram_notify.py             # Telegram notifications
├── offer_database.py              # SQLite database management
├── db_manage.py                   # Database tools
├── setup_tgtg.py                  # TGTG authentication setup
├── setup_server.sh                # Server setup script
├── tgtg-15min-notify-crontab.txt  # Cron configuration
└── logs/                          # Log files (created automatically)
    ├── cron_tgtg.log             # Main notification logs
    ├── cron_setup.log            # Setup/installation logs
    ├── cron_health_check.log     # Health check logs
    └── cron_cleanup.log          # Cleanup operation logs
```

## 🛠️ Testing

Test the installation:
```bash
# Test TGTG checker
python3 -c "from tgtg_check import TGTGChecker; TGTGChecker().check_and_notify()"

# Test database
python3 db_manage.py stats

# Test credential persistence
python3 tests/test_credentials.py
```

## 📊 Monitoring

### View Logs
```bash
# Main notification logs
tail -f cron_tgtg.log

# All logs
tail -f cron_*.log
```

### Cron Management
```bash
# View current crontab
crontab -l

# Edit crontab
crontab -e

# Remove crontab
crontab -r
```

### Database Management
```bash
# View statistics
python3 db_manage.py stats

# View recent notifications
python3 db_manage.py recent

# Clean old records
python3 db_manage.py cleanup

# Reset database
python3 db_manage.py reset
```

## 🔍 Troubleshooting

### Common Issues

1. **"Module not found" errors**
   - Run the dependency check: `python3 -c "import telegram, tgtg, pytz, dotenv, requests"`
   - Reinstall packages: `pip3 install --user python-telegram-bot tgtg pytz python-dotenv requests`

2. **"Credentials not found" errors**
   - Ensure `.env` file exists with correct tokens
   - Run `python3 setup_tgtg.py` to create TGTG credentials

3. **Cron jobs not running**
   - Check cron service: `sudo systemctl status cron`
   - View cron logs: `grep CRON /var/log/syslog`
   - Verify crontab: `crontab -l`

4. **Token expiration issues**
   - The system automatically refreshes TGTG tokens
   - Check logs for authentication errors: `grep -i "auth\|token\|credential" cron_*.log`

### Log Locations
- Cron logs: `cron_*.log` files in project directory
- System cron logs: `/var/log/syslog` or `/var/log/cron`

## 🔄 Updates

To update the system:
```bash
# Pull latest code
git pull

# Update dependencies
pip3 install --upgrade python-telegram-bot tgtg pytz python-dotenv requests

# Restart cron service if needed
sudo systemctl restart cron
```

## ⚡ Performance

- **Memory usage**: ~50-100MB per check
- **Network usage**: Minimal (a few KB per API call)
- **Storage**: SQLite database grows ~1KB per notification
- **CPU usage**: Very low (only during 15-minute checks)

## 📧 Support

If you encounter issues:
1. Check the logs in `cron_*.log` files
2. Run manual tests to isolate the problem
3. Verify all configuration files are present and correct
4. Check system resources and cron service status

The system is designed to be robust and will continue working even if individual checks fail. Token refresh is automatic, and the database prevents duplicate notifications.
