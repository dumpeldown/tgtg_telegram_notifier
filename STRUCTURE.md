# Project Structure

This document describes the reorganized structure of the TGTG Telegram Notifier project.

## 📁 Directory Structure

```
tgtg_notify/                    # Project root
├── .env                        # Environment variables (user-specific)
├── .env.example               # Environment template
├── .gitignore                 # Git ignore rules
├── README.md                  # Main project documentation
├── INSTALLATION.md            # Setup instructions
├── tgtg_credentials.json      # TGTG API credentials (shared)
│
├── common/                    # Shared components
│   ├── __init__.py           # Package initialization
│   ├── telegram_notify.py    # Core Telegram functionality
│   ├── tgtg_exceptions.py    # TGTG API error handling
│   ├── tgtg_reservation.py   # Reservation management
│   ├── setup_tgtg.py         # TGTG setup utilities
│   ├── setup_server.sh       # Server setup script
│   └── debug_offer_structure.py # Debugging tools
│
├── single_user/              # Single-user version
│   ├── __init__.py          # Package initialization
│   ├── main.py              # Main entry point
│   ├── tgtg_check.py        # TGTG checking logic
│   ├── offer_database.py    # Simple offer tracking
│   ├── db_manage.py         # Database management
│   ├── telegram_bot_handler.py # Basic bot interface
│   ├── start_bot.py         # Bot startup script
│   ├── tgtg_offers.db       # Single-user database
│   └── crontab-with-bot.txt # Single-user crontab
│
├── multi_user/              # Multi-user version
│   ├── __init__.py         # Package initialization
│   ├── multi_user_bot_handler.py # Advanced bot interface
│   ├── multi_user_tgtg.py  # Multi-user TGTG logic
│   ├── multi_user_db.py    # Multi-user database management
│   ├── multi_user_db_manage.py # Database admin tools
│   ├── multi_user_cron.py  # Scheduled checker
│   ├── start_multi_user_bot.py # Bot startup script
│   ├── multi_user.db       # Multi-user database
│   ├── crontab-multi-user.txt # Multi-user crontab
│   └── README_MULTI_USER.md # Multi-user documentation
│
└── tests/                   # Test suite
    ├── __init__.py         # Test package initialization
    ├── test_multi_user.py  # Multi-user functionality tests
    ├── test_credentials.py # Credential handling tests
    ├── test_email_update.py # Email update tests
    ├── test_manual_check.py # Manual checking tests
    ├── test_duplicate_prevention.py # Duplicate prevention tests
    ├── test_reservation_buttons.py # Reservation button tests
    ├── test_time_format.py # Time formatting tests
    ├── test_db.db         # Test database files
    └── test_offers.db     # Test offer database
```

## 🔧 Import Structure

### Multi-User Imports
```python
from multi_user.multi_user_db import get_multi_user_db
from multi_user.multi_user_tgtg import MultiUserTGTGChecker
from multi_user.multi_user_bot_handler import MultiUserTGTGBotHandler
```

### Single-User Imports
```python
from single_user.tgtg_check import TGTGChecker
from single_user.offer_database import OfferDatabase
from single_user.telegram_bot_handler import TGTGBotHandler
```

### Common Imports
```python
from common.telegram_notify import notify, get_notifier
from common.tgtg_exceptions import safe_tgtg_call, TGTGCaptchaException
from common.tgtg_reservation import get_reservation_manager
```

## 🚀 Running the Applications

### Single-User Version
```bash
# From project root
python3 single_user/main.py
python3 single_user/start_bot.py

# From single_user directory
cd single_user
python3 main.py
python3 start_bot.py
```

### Multi-User Version
```bash
# From project root
python3 multi_user/start_multi_user_bot.py
python3 multi_user/multi_user_cron.py

# From multi_user directory
cd multi_user
python3 start_multi_user_bot.py
python3 multi_user_cron.py
```

### Running Tests
```bash
# From project root
python3 tests/test_multi_user.py
python3 tests/test_credentials.py
```

## 📊 Database Locations

- **Single-User Database**: `single_user/tgtg_offers.db`
- **Multi-User Database**: `multi_user/multi_user.db`
- **Test Databases**: `tests/test_*.db`
- **Shared Credentials**: `tgtg_credentials.json` (root level)

## 🔄 Migration Notes

This reorganization:
1. ✅ Separates single-user and multi-user functionality
2. ✅ Creates a common library for shared components
3. ✅ Organizes all test files in dedicated directory
4. ✅ Moves database files to appropriate locations
5. ✅ Updates all import statements and references
6. ✅ Maintains backward compatibility for configuration files
