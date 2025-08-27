# Multi-User TGTG Telegram Notifier

A multi-user Telegram bot that monitors Too Good To Go (TGTG) offers and enables instant bag reservations for multiple users with individual accounts.

## 🌟 Features

### **Multi-User Support**
- ✅ **Individual user accounts** - Each user has their own TGTG credentials
- ✅ **Separate notifications** - Users only receive notifications for their favorites
- ✅ **Personal authentication** - Secure TGTG login per user via Telegram
- ✅ **User-specific tracking** - No duplicate notifications per user

### **Smart Reservation System**
- ✅ **One-click reservations** - Reserve bags directly from Telegram
- ✅ **Instant notifications** - Get notified immediately when offers appear  
- ✅ **Auto-cancellation** - Reservations auto-cancel to free bags for others
- ✅ **Manual control** - Cancel reservations manually anytime

### **Automated Monitoring**
- ✅ **Continuous checking** - Monitors all users every 15 minutes
- ✅ **Timezone support** - Pickup times shown in user's local timezone
- ✅ **Smart filtering** - No duplicate notifications
- ✅ **Database cleanup** - Automatic maintenance

## 🚀 Quick Start

### **For Bot Administrators**

1. **Setup the server**:
```bash
git clone <your-repo> tgtg_telegram_notifier
cd tgtg_telegram_notifier
python3 -m pip install python-telegram-bot tgtg pytz python-dotenv requests
```

2. **Configure bot token**:
```bash
# Create .env file with your bot token
echo "TELEGRAM_BOT_TOKEN=your_bot_token_here" > .env
```

3. **Start the bot**:
```bash
python3 start_multi_user_bot.py
```

4. **Install automated checks** (optional):
```bash
crontab crontab-multi-user.txt
```

### **For Users**

1. **Start conversation** with the bot:
   ```
   /start
   ```

2. **Enter your TGTG email** when prompted

3. **Click verification link** in email from TGTG

4. **Done!** You'll now receive notifications with reservation buttons

## 📱 User Commands

| Command | Description |
|---------|-------------|
| `/start` | Register and authenticate with TGTG |
| `/status` | Show your account status and settings |
| `/check` | Manually check for new offers |
| `/stats` | Show your notification statistics |
| `/help` | Show help and usage information |

## 🏗️ Architecture

### **Database Structure**
```sql
users                    -- User accounts and credentials
├── user_id             -- Primary key
├── telegram_chat_id    -- User's Telegram chat ID  
├── tgtg_email         -- User's TGTG email
├── tgtg_credentials   -- Encrypted TGTG tokens (JSON)
└── timezone           -- User's timezone preference

user_notifications      -- Per-user notification tracking
├── user_id            -- Foreign key to users
├── offer_hash         -- Unique offer identifier
└── sent_at           -- When notification was sent

user_reservations       -- Per-user reservation history
├── user_id           -- Foreign key to users  
├── order_id          -- TGTG order ID
└── status           -- Reservation status
```

### **Components**

| File | Purpose |
|------|---------|
| `multi_user_bot_handler.py` | Main bot interface and user commands |
| `multi_user_db.py` | Database management and user data |
| `multi_user_tgtg.py` | TGTG API integration for all users |
| `multi_user_cron.py` | Automated checking script |
| `telegram_notify.py` | Enhanced notifications with buttons |

## 🔧 Configuration

### **Environment Variables**
```bash
# Required
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Optional  
DEFAULT_TIMEZONE=Europe/Berlin
```

### **Per-User Settings**
- **TGTG Email**: Set during registration
- **Timezone**: Defaults to Europe/Berlin, customizable per user
- **Credentials**: Automatically managed and refreshed

## 📊 Monitoring

### **Bot Status**
```bash
# Check if bot is running
pgrep -f "start_multi_user_bot.py"

# View bot logs
tail -f multi_user_bot.log
```

### **User Management**
```bash
# Test the system
python3 tests/test_multi_user.py

# Check database
python3 -c "from multi_user_db import get_multi_user_db; db = get_multi_user_db(); print(f'Users: {len(db.get_all_active_users())}')"
```

### **Cron Jobs**
```bash
# View active cron jobs
crontab -l

# Check cron logs
tail -f multi_user_cron.log
```

## 🔐 Security & Privacy

### **Data Protection**
- ✅ **Encrypted credentials** - TGTG tokens stored securely in SQLite
- ✅ **User isolation** - Each user's data is completely separate
- ✅ **No password storage** - Only API tokens, refreshed automatically
- ✅ **Local database** - All data stays on your server

### **API Usage**
- ✅ **Rate limiting** - Respects TGTG API limits with delays
- ✅ **Token refresh** - Automatically renews expired credentials  
- ✅ **Error handling** - Graceful failure without data loss
- ✅ **Fair usage** - Auto-cancels reservations to share with others

## 🛠️ Development

### **Testing**
```bash
# Test database functionality
python3 tests/test_multi_user.py

# Test individual components
python3 multi_user_db.py
python3 multi_user_tgtg.py
```

### **Debugging**
```bash
# Enable debug logging
export PYTHONUNBUFFERED=1

# Run with verbose output
python3 start_multi_user_bot.py
```

### **Database Management**
```bash
# View database schema
sqlite3 multi_user.db ".schema"

# Check user count
sqlite3 multi_user.db "SELECT COUNT(*) FROM users WHERE is_active = 1;"

# Clean up test data
sqlite3 multi_user.db "DELETE FROM users WHERE tgtg_email LIKE '%test%';"
```

## 📈 Scaling

### **Performance Considerations**
- **Users**: Handles hundreds of users efficiently
- **Memory**: ~10-50MB per 100 users
- **Storage**: ~1KB per user + ~1KB per notification
- **Network**: Minimal usage, only necessary API calls

### **Optimization Options**
- **Database indexing**: Automatic via SQLite
- **Parallel checking**: Users checked sequentially with delays
- **Credential caching**: TGTG clients cached per user
- **Log rotation**: Automatic via system logrotate

## 🚨 Troubleshooting

### **Common Issues**

1. **Bot not responding**:
   ```bash
   # Check if bot process is running
   pgrep -f "start_multi_user_bot.py"
   
   # Restart if needed
   pkill -f "start_multi_user_bot.py"
   python3 start_multi_user_bot.py
   ```

2. **User authentication fails**:
   - Check email address is correct
   - Verify user clicked email verification link
   - Try again with `/start` command

3. **No notifications received**:
   - Verify user has favorites in TGTG app
   - Check if offers are actually available
   - Run manual check with `/check` command

4. **Database errors**:
   ```bash
   # Check database integrity
   sqlite3 multi_user.db "PRAGMA integrity_check;"
   
   # Rebuild if corrupted
   sqlite3 multi_user.db "VACUUM;"
   ```

### **Log Analysis**
```bash
# Check for errors
grep -i error multi_user_*.log

# Check user registrations  
grep -i "registered\|authenticated" multi_user_bot.log

# Check offer notifications
grep -i "notification\|offer" multi_user_cron.log
```

## 🔄 Migration from Single-User

If migrating from the single-user version:

1. **Backup existing data**:
   ```bash
   cp tgtg_credentials.json tgtg_credentials_backup.json
   cp offers.db offers_backup.db
   ```

2. **Run migration script** (create if needed):
   ```bash
   # Convert single-user data to multi-user format
   python3 migrate_to_multi_user.py
   ```

3. **Test new system**:
   ```bash
   python3 tests/test_multi_user.py
   ```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📝 License

This project is open source. Please use responsibly and respect TGTG's terms of service.

## 🙋‍♀️ Support

- **Issues**: Use GitHub Issues
- **Questions**: Check existing issues or create new one
- **Features**: Suggest via GitHub Issues with enhancement label

---

**Happy TGTG hunting with multi-user support!** 🍕👥📱
