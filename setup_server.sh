#!/bin/bash

# TGTG Telegram Notifier - Server Setup Script
# This script helps set up the TGTG notification system on a new server

set -e  # Exit on any error

echo "🚀 TGTG Telegram Notifier - Server Setup"
echo "========================================"

# Get current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

echo "📁 Project directory: $PROJECT_DIR"

# Update system packages
echo "📦 Updating system packages..."
if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update
    sudo apt-get install -y python3 python3-pip python3-venv git curl
elif command -v yum >/dev/null 2>&1; then
    sudo yum update -y
    sudo yum install -y python3 python3-pip git curl
elif command -v pacman >/dev/null 2>&1; then
    sudo pacman -Sy python python-pip git curl
else
    echo "⚠️  Unknown package manager. Please install python3, python3-pip, and git manually."
fi

# Create virtual environment (optional but recommended)
echo "🐍 Setting up Python virtual environment..."
if [ ! -d "$PROJECT_DIR/venv" ]; then
    python3 -m venv "$PROJECT_DIR/venv"
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
source "$PROJECT_DIR/venv/bin/activate"

# Install Python dependencies
echo "📚 Installing Python dependencies..."
pip install --upgrade pip
pip install python-telegram-bot tgtg pytz python-dotenv requests

echo "✅ Dependencies installed successfully!"

# Check for required files
echo "🔍 Checking for required configuration files..."

if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo "⚠️  .env file not found!"
    echo "Creating template .env file..."
    cat > "$PROJECT_DIR/.env" << 'EOF'
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Optional: Set your timezone (default is Europe/Berlin)
# DEFAULT_TIMEZONE=Europe/Berlin
EOF
    echo "📝 Please edit .env file with your Telegram bot token and chat ID"
    echo "   File location: $PROJECT_DIR/.env"
fi

if [ ! -f "$PROJECT_DIR/tgtg_credentials.json" ]; then
    echo "⚠️  TGTG credentials not found!"
    echo "Please run the TGTG setup script to authenticate:"
    echo "   python3 setup_tgtg.py"
fi

# Test the installation
echo "🧪 Testing installation..."
cd "$PROJECT_DIR"

# Test Python imports
python3 -c "
try:
    import telegram
    import tgtg
    import pytz
    import dotenv
    import requests
    print('✅ All Python packages imported successfully!')
except ImportError as e:
    print(f'❌ Import error: {e}')
    exit(1)
"

# Test configuration files
if [ -f ".env" ] && [ -f "tgtg_credentials.json" ]; then
    echo "🔧 Testing TGTG checker..."
    python3 -c "
try:
    from tgtg_check import TGTGChecker
    checker = TGTGChecker()
    print('✅ TGTG checker initialized successfully!')
except Exception as e:
    print(f'⚠️  TGTG checker test failed: {e}')
    print('This is normal if you haven\\'t set up credentials yet.')
"
fi

# Update crontab with correct paths
echo "📅 Setting up crontab..."
CRONTAB_FILE="$PROJECT_DIR/tgtg-15min-notify-crontab.txt"

if [ -f "$CRONTAB_FILE" ]; then
    # Replace placeholder paths with actual paths
    sed -i "s|/home/username/tgtg_telegram_notifier|$PROJECT_DIR|g" "$CRONTAB_FILE"
    sed -i "s|PROJECT_DIR=/home/username/tgtg_telegram_notifier|PROJECT_DIR=$PROJECT_DIR|g" "$CRONTAB_FILE"
    
    echo "✅ Crontab file updated with correct paths"
    echo "📋 To install the crontab, run:"
    echo "   crontab $CRONTAB_FILE"
    echo ""
    echo "📋 To view current crontab:"
    echo "   crontab -l"
    echo ""
    echo "📋 To edit crontab manually:"
    echo "   crontab -e"
else
    echo "⚠️  Crontab file not found: $CRONTAB_FILE"
fi

# Create log directory
mkdir -p "$PROJECT_DIR/logs"
echo "📄 Created logs directory: $PROJECT_DIR/logs"

# Set up log rotation (optional)
echo "🔄 Setting up log rotation..."
sudo tee "/etc/logrotate.d/tgtg-notifier" > /dev/null << EOF
$PROJECT_DIR/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    create 0644 $(whoami) $(whoami)
}
EOF

echo ""
echo "🎉 Setup completed successfully!"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your Telegram bot credentials"
echo "2. Run 'python3 setup_tgtg.py' to set up TGTG authentication"
echo "3. Test the system with 'python3 -c \"from tgtg_check import TGTGChecker; TGTGChecker().check_and_notify()\"'"
echo "4. Install the crontab with 'crontab $CRONTAB_FILE'"
echo ""
echo "Files to configure:"
echo "- .env (Telegram credentials)"
echo "- tgtg_credentials.json (will be created by setup_tgtg.py)"
echo ""
echo "Logs will be stored in:"
echo "- $PROJECT_DIR/cron_*.log"
echo ""
echo "Happy TGTG hunting! 🍕📱"
