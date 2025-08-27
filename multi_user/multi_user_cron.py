#!/usr/bin/env python3
"""
Multi-User TGTG Cron Job
Checks offers for all registered users and sends notifications.
"""

import sys
import os
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multi_user.multi_user_tgtg import check_all_users

def main():
    """Run multi-user TGTG check."""
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("🔍 Starting multi-user TGTG check...")
        results = check_all_users(send_summary=False)
        
        if 'error' in results:
            logger.error(f"❌ Multi-user check failed: {results['error']}")
            sys.exit(1)
        else:
            logger.info(f"✅ Multi-user check completed: {results}")
            
    except Exception as e:
        logger.error(f"❌ Multi-user check error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
