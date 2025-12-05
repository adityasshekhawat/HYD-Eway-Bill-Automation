#!/usr/bin/env python3
"""
Debug script to check which sequence generator is actually being used
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def check_sequence_generator():
    print("=" * 70)
    print("DEBUGGING SEQUENCE GENERATOR")
    print("=" * 70)
    
    print("\n1️⃣  Checking which generator is being used...")
    from core.dc_sequence_manager import DCSequenceManager
    
    manager = DCSequenceManager()
    
    generator_type = type(manager.generator).__name__
    print(f"\n✅ Current generator: {generator_type}")
    
    if generator_type == "LocalSequenceGenerator":
        print("\n⚠️  WARNING: Using LOCAL JSON file (NOT Google Sheets!)")
        print("   This means:")
        print("   - Sequences incrementing locally in dc_sequence_state_v2.json")
        print("   - NOT saving to Google Sheets")
        print("   - Google Sheets initialization must have failed")
        print("\nℹ️  Check Streamlit logs for Google Sheets initialization errors")
        
    elif generator_type == "SupabaseSequenceGenerator":
        print("\n⚠️  Using Supabase (NOT Google Sheets)")
        print("   Google Sheets initialization must have failed")
        
    elif generator_type == "GoogleSheetsSequenceGenerator":
        print("\n✅ Using Google Sheets!")
        print("   Sequences SHOULD be saving to Google Sheets")
        print("\nℹ️  If sequences are incrementing but not in Google Sheets:")
        print("   1. Check if worksheet.update() is failing silently")
        print("   2. Check Google Sheets API permissions")
        print("   3. Check if spreadsheet exists and is accessible")
        
        # Try to get current sequences
        try:
            print("\n2️⃣  Testing Google Sheets read...")
            all_seqs = manager.generator.get_all_sequences()
            if all_seqs:
                print(f"✅ Found {len(all_seqs)} sequences in Google Sheets:")
                for seq_name, seq_val in list(all_seqs.items())[:5]:
                    print(f"   - {seq_name}: {seq_val}")
            else:
                print("⚠️  No sequences found in Google Sheets (might be empty)")
        except Exception as e:
            print(f"❌ Read test failed: {e}")
        
        # Test write operation
        print("\n3️⃣  Testing Google Sheets write...")
        print("   This will attempt to increment akdcah_seq")
        print("   Type 'yes' to proceed: ", end="")
        response = input().strip().lower()
        
        if response == 'yes':
            try:
                print("\n   🔄 Calling get_next_sequence('akdcah_seq')...")
                next_val = manager.generator.get_next_sequence('akdcah_seq')
                print(f"   ✅ Returned value: {next_val}")
                
                print("\n   🔄 Verifying in Google Sheets...")
                current_val = manager.generator.get_current_sequence_value('akdcah_seq')
                print(f"   ✅ Current value in Google Sheets: {current_val}")
                
                if current_val == next_val:
                    print("\n✅✅✅ WRITE SUCCESSFUL - Google Sheets is working! ✅✅✅")
                else:
                    print(f"\n❌ WRITE FAILED - Expected {next_val}, got {current_val}")
                    print("   The write operation is not persisting to Google Sheets")
                    
            except Exception as e:
                print(f"\n❌ Write test failed: {e}")
                import traceback
                traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("DEBUG COMPLETE")
    print("=" * 70)

if __name__ == '__main__':
    try:
        check_sequence_generator()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

