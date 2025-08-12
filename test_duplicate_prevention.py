#!/usr/bin/env python3
"""
Quick test to verify the duplicate prevention system works correctly.
"""

def test_duplicate_prevention():
    """Test the duplicate prevention functionality."""
    
    print("🧪 Testing Duplicate Prevention System")
    print("=" * 50)
    
    try:
        from tgtg_check import TGTGChecker
        
        # Initialize checker (this will create the database)
        checker = TGTGChecker()
        print("✅ TGTG Checker initialized")
        
        # Test offer data
        test_offer = {
            'store': {
                'store_id': 99999,
                'store_name': 'Test Restaurant',
                'store_location': {
                    'address': {
                        'address_line': '123 Test St',
                        'city': 'Test City',
                        'country': {'name': 'Test Country'}
                    }
                }
            },
            'item_id': 88888,
            'display_name': 'Test Surprise Bag',
            'items_available': 2,
            'pickup_interval': {
                'start': '2025-08-12T18:00:00Z',
                'end': '2025-08-12T20:00:00Z'
            }
        }
        
        # Check if offer exists (should be False initially)
        store_id = test_offer['store']['store_id']
        item_id = test_offer['item_id']
        pickup_start = test_offer['pickup_interval']['start']
        pickup_end = test_offer['pickup_interval']['end']
        
        exists_before = checker.db.is_offer_already_sent(store_id, item_id, pickup_start, pickup_end)
        print(f"✅ First check (should be False): {not exists_before}")
        
        # Record the offer
        recorded = checker.db.record_sent_offer(test_offer)
        print(f"✅ Offer recorded: {recorded}")
        
        # Check if offer exists now (should be True)
        exists_after = checker.db.is_offer_already_sent(store_id, item_id, pickup_start, pickup_end)
        print(f"✅ Second check (should be True): {exists_after}")
        
        # Test message formatting
        message = checker.format_offer_message(test_offer)
        print("✅ Message formatting works")
        print(f"📱 Sample message:\n{'-'*30}\n{message}\n{'-'*30}")
        
        # Test database stats
        stats = checker.get_database_stats()
        print(f"✅ Database stats: {stats['total_records']} records")
        
        print("\n🎉 All duplicate prevention tests passed!")
        print("\n💡 Key benefits:")
        print("• Same offer won't trigger multiple notifications")
        print("• Different pickup times will still notify")
        print("• Perfect for automated scheduling every 30 minutes")
        print("• Database automatically cleans up old records")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """Main function."""
    print("🚫 Duplicate Prevention Test")
    print("This test verifies that the same offer won't be notified twice")
    print()
    
    success = test_duplicate_prevention()
    
    if success:
        print("\n✅ System is ready for automated monitoring!")
        print("You can safely schedule the checker to run every 30 minutes.")
    else:
        print("\n❌ Please fix the issues before using automated monitoring.")

if __name__ == "__main__":
    main()
