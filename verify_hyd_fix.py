
import sys
import os
import pandas as pd
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.abspath('src'))

from core.vehicle_data_manager import VehicleDataManager
from core.config_loader import get_config_loader

def verify_hyd_fix():
    print("🔍 Verifying Hyderabad Facility Fixes...")
    print("=" * 60)
    
    # Initialize manager
    vdm = VehicleDataManager()
    
    # Test 1: Direct Facility Address Lookup
    print("\n1. Testing get_facility_address with 'FC-Hyderabad'...")
    
    # Test with exact name from CSV
    facility_name = "FC-Hyderabad"
    company = "AMOLAKCHAND"
    
    address_info = vdm.get_facility_address(facility_name, company=company)
    
    print(f"   Facility: {facility_name}")
    print(f"   Company: {company}")
    print(f"   Address: {address_info.get('address', '')[:50]}...")
    print(f"   City: {address_info.get('city', 'MISSING')}")
    print(f"   State: {address_info.get('state', 'MISSING')}")
    print(f"   Pincode: {address_info.get('pincode', 'MISSING')}")
    
    # Verification
    if address_info.get('city') == 'Hyderabad' and address_info.get('state') == 'Telangana':
        print("   ✅ SUCCESS: Correctly identified Hyderabad/Telangana")
    else:
        print(f"   ❌ FAILURE: Expected Hyderabad/Telangana, got {address_info.get('city')}/{address_info.get('state')}")
        
    # Test 2: Fuzzy Lookup
    print("\n2. Testing Fuzzy Lookup with 'FC Hyderabad' (no hyphen)...")
    fuzzy_name = "FC Hyderabad"
    address_info_fuzzy = vdm.get_facility_address(fuzzy_name, company=company)
    
    if address_info_fuzzy.get('city') == 'Hyderabad':
        print("   ✅ SUCCESS: Fuzzy lookup worked")
    else:
        print("   ❌ FAILURE: Fuzzy lookup failed")

    # Test 3: DC Data Creation (Mock)
    print("\n3. Testing _create_vehicle_dc_data population...")
    
    # Mock data
    mock_data = pd.DataFrame([{
        'trip_ref_number': 'TRIP123',
        'hub': 'HYD_SAN',
        'name': 'FC-Hyderabad',
        'title': 'Test Product',
        'taxable_amount': 1000,
        'planned_quantity': 10,
        'hsn_code': '1234',
        'gst_rate': 18,
        'cess': 0
    }])
    
    # Mock org data needed for _determine_hub_type
    vdm.org_data = pd.DataFrame([
        {'org_profile_id': 'SENDER1', 'org_name': 'AMOLAKCHAND'}
    ])
    
    # Create DC
    try:
        dcs = vdm._create_vehicle_dc_data(mock_data, 'SENDER1', 'KA01AB1234', ['TRIP123'])
        
        if dcs and len(dcs) > 0:
            dc = dcs[0]
            print(f"   Generated DC for {dc['vehicle_number']}")
            print(f"   Supplier Place: {dc.get('facility_city')}")
            print(f"   Supplier State: {dc.get('facility_state')}")
            print(f"   Supplier Pincode: {dc.get('facility_pincode')}")
            
            if (dc.get('facility_city') == 'Hyderabad' and 
                dc.get('facility_state') == 'Telangana' and 
                dc.get('facility_pincode') == '500078'):
                print("   ✅ SUCCESS: DC data correctly populated with Hyderabad details")
            else:
                print("   ❌ FAILURE: DC data has incorrect details")
                print(f"   Expected: Hyderabad, Telangana, 500078")
                print(f"   Got: {dc.get('facility_city')}, {dc.get('facility_state')}, {dc.get('facility_pincode')}")
        else:
            print("   ❌ FAILURE: No DC generated")
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_hyd_fix()
