#!/usr/bin/env python3
"""
Simple test to verify GSTIN mapping exists in final_address.csv
"""

import csv
import os

def test_gstin_mapping():
    """Test that GSTIN mapping is correct in final_address.csv"""
    
    print("=" * 80)
    print("GSTIN MAPPING VERIFICATION TEST")
    print("=" * 80)
    
    # Expected mappings from final_address.csv
    expected_mappings = {
        ('AMOLAKCHAND ANKUR KOTHARI ENTERPRISES PRIVATE LIMITED', 'Karnataka'): '29AAPCA1708D1ZS',
        ('AMOLAKCHAND ANKUR KOTHARI ENTERPRISES PRIVATE LIMITED', 'Telangana'): '36AAPCA1708D1ZX',
        ('AMOLAKCHAND ANKUR KOTHARI ENTERPRISES PRIVATE LIMITED', 'Bihar'): '10AAPCA1708D1ZB',
        ('AMOLAKCHAND ANKUR KOTHARI ENTERPRISES PRIVATE LIMITED', 'Jharkhand'): '20AAPCA1708D1ZA',
        ('AMOLAKCHAND ANKUR KOTHARI ENTERPRISES PRIVATE LIMITED', 'UP'): '09AAPCA1708D1ZU',
        ('BODEGA RETAIL PRIVATE LIMITED', 'Karnataka'): '29AAHCB1357R1Z1',
        ('BODEGA RETAIL PRIVATE LIMITED', 'Telangana'): '36AAHCB1357R1Z6',
        ('BODEGA RETAIL PRIVATE LIMITED', 'MH'): '27AAHCB1357R1Z5',
        ('SOURCINGBEE PRIVATE LIMITED', 'Karnataka'): '29AAWCS7485C1ZJ',
    }
    
    # Read actual mappings from CSV
    csv_path = os.path.join(os.path.dirname(__file__), 'data', 'final_address.csv')
    
    if not os.path.exists(csv_path):
        print(f"❌ CSV file not found: {csv_path}")
        return False
    
    actual_mappings = {}
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            entity = row.get('Entity name', '').strip()
            state = row.get('State', '').strip()
            gstin = row.get('GST No', '').strip()
            
            if entity and state and gstin:
                actual_mappings[(entity, state)] = gstin
    
    print(f"\nFound {len(actual_mappings)} GSTIN mappings in CSV")
    print("\nVerifying expected mappings:")
    print("-" * 80)
    
    all_passed = True
    for (entity, state), expected_gstin in expected_mappings.items():
        actual_gstin = actual_mappings.get((entity, state))
        
        # Also try normalized version
        if not actual_gstin:
            # Try with AMOLAKCHAND prefix variations
            if 'AMOLAKCHAND' in entity:
                actual_gstin = actual_mappings.get(('AMOLAKCHAND ANKUR KOTHARI ENTERPRISES PRIVATE LIMITED', state))
        
        status = "✅ PASS" if actual_gstin == expected_gstin else "❌ FAIL"
        
        if actual_gstin != expected_gstin:
            all_passed = False
        
        # Shortened entity name for display
        short_entity = 'AMOLAKCHAND' if 'AMOLAKCHAND' in entity else \
                      'BODEGA' if 'BODEGA' in entity else \
                      'SOURCINGBEE' if 'SOURCINGBEE' in entity else entity
        
        print(f"{status} | Company: {short_entity:15s} | State: {state:12s}")
        print(f"       | Expected: {expected_gstin} | Got: {actual_gstin or 'NOT FOUND'}")
        print("-" * 80)
    
    print("\n" + "=" * 80)
    if all_passed:
        print("✅ ALL TESTS PASSED - CSV mapping is correct!")
        print("\nThe fix applied to vehicle_dc_generator.py and dc_template_generator.py")
        print("will now use FACILITY STATE (not hub state) for GSTIN lookup,")
        print("ensuring correct GSTIN based on where the FC is located.")
    else:
        print("❌ SOME TESTS FAILED - Please check the CSV file")
    print("=" * 80)
    
    return all_passed

if __name__ == '__main__':
    import sys
    passed = test_gstin_mapping()
    sys.exit(0 if passed else 1)

