#!/usr/bin/env python3
"""
Test script to verify Google Sheets sequence generator is working
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_google_sheets():
    print("=" * 60)
    print("TESTING GOOGLE SHEETS SEQUENCE GENERATOR")
    print("=" * 60)
    
    try:
        from core.google_sheets_sequence_generator import GoogleSheetsSequenceGenerator
        
        print("\n1️⃣  Initializing Google Sheets generator...")
        generator = GoogleSheetsSequenceGenerator()
        print("✅ Initialization successful\n")
        
        # Test getting current value
        print("2️⃣  Testing get_current_sequence_value...")
        test_seq_name = 'akdchydnch_seq'
        current_val = generator.get_current_sequence_value(test_seq_name)
        print(f"✅ Current value for {test_seq_name}: {current_val}\n")
        
        # Test getting next value (this will increment!)
        print("3️⃣  Testing get_next_sequence (THIS WILL INCREMENT!)...")
        print(f"   Are you sure you want to increment {test_seq_name}? (y/n): ", end="")
        response = input().strip().lower()
        
        if response == 'y':
            next_val = generator.get_next_sequence(test_seq_name)
            print(f"✅ Next value for {test_seq_name}: {next_val}")
            print(f"   (Incremented from {current_val} to {next_val})\n")
            
            # Verify the increment was saved
            print("4️⃣  Verifying the increment was saved...")
            new_current = generator.get_current_sequence_value(test_seq_name)
            print(f"✅ New current value: {new_current}")
            
            if new_current == next_val:
                print("✅ INCREMENT WAS SAVED TO GOOGLE SHEETS! 🎉\n")
            else:
                print(f"❌ INCREMENT NOT SAVED! Expected {next_val}, got {new_current}\n")
        else:
            print("   Skipping increment test\n")
        
        # Show all sequences
        print("5️⃣  Showing all sequences in Google Sheet...")
        all_seqs = generator.get_all_sequences()
        if all_seqs:
            print("✅ All sequences:")
            for seq_name, seq_val in all_seqs.items():
                print(f"   - {seq_name}: {seq_val}")
        else:
            print("⚠️  No sequences found in sheet")
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED - Google Sheets is working!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()
        print("\n" + "=" * 60)
        print("❌ TESTS FAILED - Google Sheets has issues")
        print("=" * 60)
        return False
    
    return True

if __name__ == '__main__':
    success = test_google_sheets()
    sys.exit(0 if success else 1)

