#!/usr/bin/env python3
"""
Test script to verify GSTIN is correctly looked up based on company and facility state
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.config_loader import ConfigLoader

def test_gstin_lookup():
    """Test GSTIN lookup for different company-state combinations"""
    
    print("=" * 80)
    print("GSTIN LOOKUP TEST")
    print("=" * 80)
    
    # Initialize config loader
    config = ConfigLoader()
    
    # Test cases from final_address.csv
    test_cases = [
        ('AMOLAKCHAND', 'Karnataka', '29AAPCA1708D1ZS'),
        ('AMOLAKCHAND', 'Telangana', '36AAPCA1708D1ZX'),
        ('AMOLAKCHAND', 'Bihar', '10AAPCA1708D1ZB'),
        ('AMOLAKCHAND', 'Jharkhand', '20AAPCA1708D1ZA'),
        ('AMOLAKCHAND', 'UP', '09AAPCA1708D1ZU'),
        ('BODEGA', 'Karnataka', '29AAHCB1357R1Z1'),
        ('BODEGA', 'Telangana', '36AAHCB1357R1Z6'),
        ('BODEGA', 'MH', '27AAHCB1357R1Z5'),
        ('SOURCINGBEE', 'Karnataka', '29AAWCS7485C1ZJ'),
    ]
    
    print("\nTesting GSTIN lookups:")
    print("-" * 80)
    
    all_passed = True
    for company, state, expected_gstin in test_cases:
        actual_gstin = config.get_gstin(company, state)
        status = "✅ PASS" if actual_gstin == expected_gstin else "❌ FAIL"
        
        if actual_gstin != expected_gstin:
            all_passed = False
        
        print(f"{status} | Company: {company:20s} | State: {state:12s}")
        print(f"       | Expected: {expected_gstin} | Got: {actual_gstin or 'None'}")
        print("-" * 80)
    
    print("\n" + "=" * 80)
    if all_passed:
        print("✅ ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED!")
    print("=" * 80)
    
    return all_passed

def test_dynamic_hub_constants():
    """Test that dynamic hub constants return correct GSTIN"""
    from core.dynamic_hub_constants import get_dynamic_hub_constants
    
    print("\n" + "=" * 80)
    print("DYNAMIC HUB CONSTANTS TEST")
    print("=" * 80)
    
    dhc = get_dynamic_hub_constants()
    
    # Test cases: (company, state, fc_name, expected_gstin)
    test_cases = [
        ('AMOLAKCHAND', 'Karnataka', 'Arihant', '29AAPCA1708D1ZS'),
        ('AMOLAKCHAND', 'Telangana', 'FC-Hyderabad', '36AAPCA1708D1ZX'),
        ('BODEGA', 'Karnataka', 'Arihant', '29AAHCB1357R1Z1'),
        ('BODEGA', 'Telangana', 'FC-Hyderabad', '36AAHCB1357R1Z6'),
    ]
    
    print("\nTesting dynamic hub constants:")
    print("-" * 80)
    
    all_passed = True
    for company, state, fc_name, expected_gstin in test_cases:
        hub_constants = dhc.get_hub_constants(company, state=state, fc_name=fc_name)
        actual_gstin = hub_constants.get('sender_gstin', '')
        status = "✅ PASS" if actual_gstin == expected_gstin else "❌ FAIL"
        
        if actual_gstin != expected_gstin:
            all_passed = False
        
        print(f"{status} | Company: {company:15s} | State: {state:12s} | FC: {fc_name:15s}")
        print(f"       | Expected: {expected_gstin} | Got: {actual_gstin or 'None'}")
        print("-" * 80)
    
    print("\n" + "=" * 80)
    if all_passed:
        print("✅ ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED!")
    print("=" * 80)
    
    return all_passed

if __name__ == '__main__':
    passed1 = test_gstin_lookup()
    passed2 = test_dynamic_hub_constants()
    
    print("\n" + "=" * 80)
    print("FINAL RESULT")
    print("=" * 80)
    if passed1 and passed2:
        print("✅ ALL TESTS PASSED - GSTIN lookup is working correctly!")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED - Please review the output above")
        sys.exit(1)

