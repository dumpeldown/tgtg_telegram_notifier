# Virtual Environment Setup for Crontab

## 🐍 Virtual Environment in Cron Jobs

All crontab files have been updated to use the virtual environment activation pattern to ensure proper dependency management.

## 📋 Pattern Used

Each Python command in cron is wrapped with:
```bash
/bin/bash -c 'source $PROJECT_DIR/venv/bin/activate && python3 [command]'
```

## 🛠️ Setup Requirements

### 1. Create Virtual Environment
```bash
cd /path/to/your/project
python3 -m venv venv
```

### 2. Activate and Install Dependencies
```bash
source venv/bin/activate
pip install --upgrade python-telegram-bot tgtg pytz python-dotenv requests
```

### 3. Verify Structure
Your project should look like:
```
/home/pi/programming-fun/tgtg_telegram_notifier/
├── venv/
│   ├── bin/
│   │   ├── activate
│   │   └── python3
│   └── lib/
├── single_user/
├── multi_user/
├── common/
└── ...
```

## ⚙️ Why This Pattern?

### ❌ Without Virtual Environment:
```bash
# Uses system Python, may have missing/wrong versions
*/15 * * * * cd $PROJECT_DIR && python3 script.py
```

### ✅ With Virtual Environment:
```bash
# Uses project-specific Python with correct dependencies
*/15 * * * * cd $PROJECT_DIR && /bin/bash -c 'source $PROJECT_DIR/venv/bin/activate && python3 script.py'
```

## 🔧 Updated Files

All crontab files have been updated:

**Multi-User:**
- `multi_user/crontab-multi-user.txt`

**Single-User:**
- `single_user/crontab-simple.txt`
- `single_user/tgtg-15min-notify-crontab.txt`
- `single_user/crontab-with-bot.txt`

## 🧪 Testing

Test that virtual environment works in cron context:
```bash
# Test activation manually
cd /path/to/project
/bin/bash -c 'source venv/bin/activate && python3 -c "import tgtg; print(\"Success!\")"'
```

## 📝 Cron Installation

After setting up the virtual environment:
```bash
# Choose the appropriate crontab file for your setup
crontab single_user/crontab-simple.txt
# OR
crontab multi_user/crontab-multi-user.txt

# Verify installation
crontab -l
```

## 🚨 Troubleshooting

If cron jobs fail to run:

1. **Check virtual environment exists:**
   ```bash
   ls -la /path/to/project/venv/bin/activate
   ```

2. **Test activation manually:**
   ```bash
   /bin/bash -c 'source /path/to/project/venv/bin/activate && which python3'
   ```

3. **Check cron logs:**
   ```bash
   tail -f /path/to/project/*_cron.log
   ```

4. **Verify dependencies in venv:**
   ```bash
   source venv/bin/activate
   pip list | grep -E "(telegram|tgtg|pytz)"
   ```

This setup ensures that all scheduled tasks run with the correct Python environment and dependencies! 🎯
