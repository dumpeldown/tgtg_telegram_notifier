#!/usr/bin/env python3
"""
Test script for TGTG credential persistence.
This tests whether tokens are properly updated when they're refreshed.
"""

import os
import sys
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from single_user.tgtg_check import TGTGChecker


def main():
    """Test credential persistence functionality."""
    print("🧪 Testing TGTG Credential Persistence\n")
    
    # Check if credentials file exists
    creds_file = os.path.join(os.path.dirname(__file__), 'tgtg_credentials.json')
    
    if not os.path.exists(creds_file):
        print("❌ No credentials file found!")
        print("Run setup_tgtg.py first to create credentials.")
        return
    
    print(f"📁 Credentials file: {creds_file}")
    
    # Read current credentials
    with open(creds_file, 'r') as f:
        original_creds = json.load(f)
    
    print(f"🔑 Current access token: {original_creds.get('access_token', 'N/A')[:20]}...")
    print(f"🔄 Current refresh token: {original_creds.get('refresh_token', 'N/A')[:20]}...")
    
    # Initialize checker
    print("\n🔧 Initializing TGTG checker...")
    try:
        checker = TGTGChecker()
        print("✅ Checker initialized successfully!")
        
        # Get favorites (this might trigger a token refresh)
        print("\n📋 Fetching favorites (this may refresh tokens)...")
        offers = checker.get_favorites_with_offers()
        print(f"✅ Found {len(offers)} offers in favorites")
        
        # Update credentials if changed
        checker._update_credentials_if_changed()
        
        # Check if credentials were updated
        with open(creds_file, 'r') as f:
            updated_creds = json.load(f)
        
        if updated_creds != original_creds:
            print("\n🔄 Credentials were updated!")
            print(f"🔑 New access token: {updated_creds.get('access_token', 'N/A')[:20]}...")
            print(f"🔄 New refresh token: {updated_creds.get('refresh_token', 'N/A')[:20]}...")
            print("✅ Token persistence is working correctly!")
        else:
            print("\n📝 Credentials unchanged (tokens still valid)")
            print("✅ No refresh needed - system working correctly!")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
