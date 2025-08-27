#!/usr/bin/env python3
"""
Simple script to check if TGTG bot processes are running
"""

import subprocess
import sys
import os

def check_process_running():
    """Check if single-user and multi-user bots are running"""
    
    single_user_running = False
    multi_user_running = False
    
    try:
        # Use ps command to list Python processes
        if os.name == 'posix':  # Linux/Unix
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        else:  # Windows
            result = subprocess.run(['wmic', 'process', 'get', 'CommandLine,ProcessId'], capture_output=True, text=True)
        
        if result.returncode == 0:
            output = result.stdout
            
            # Check for single-user bot
            if 'start_bot.py' in output or 'telegram_bot_handler.py' in output:
                single_user_running = True
                print("✅ Single-user bot is running")
            
            # Check for multi-user bot  
            if 'start_multi_user_bot.py' in output or 'multi_user_bot_handler.py' in output:
                multi_user_running = True
                print("✅ Multi-user bot is running")
                
    except Exception as e:
        print(f"❌ Error checking processes: {e}")
        return
    
    # Report status
    print("\n=== TGTG Bot Status ===")
    print(f"Single-user bot: {'🟢 Running' if single_user_running else '🔴 Not running'}")
    print(f"Multi-user bot:  {'🟢 Running' if multi_user_running else '🔴 Not running'}")
    
    # Exit with error code if nothing is running
    if not single_user_running and not multi_user_running:
        print("\n⚠️  No TGTG bots are currently running!")
        sys.exit(1)
    
    print(f"\n✅ {sum([single_user_running, multi_user_running])} bot(s) active")

if __name__ == "__main__":
    try:
        check_process_running()
    except KeyboardInterrupt:
        print("\n❌ Interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error checking processes: {e}")
        sys.exit(1)
