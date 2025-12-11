#!/usr/bin/env python3
"""
Verification script to test HYD_ATP hub data loading
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("=" * 70)
print("HYD_ATP Hub Verification Script")
print("=" * 70)

# Test 1: Check CSV file
print("\n1️⃣ Checking final_address_updated.csv:")
try:
    import pandas as pd
    df = pd.read_csv('data/final_address_updated.csv')
    atp_entries = df[df['Hub Name'] == 'HYD_ATP']
    print(f"   ✅ Found {len(atp_entries)} HYD_ATP entries")
    if len(atp_entries) > 0:
        row = atp_entries.iloc[0]
        print(f"   Company: {row['Entity name']}")
        print(f"   Address 1: {row['HUB Buyers Address 1'][:60]}...")
        print(f"   Address 2: {row['HUB Buyers Address 1.1'][:60]}...")
        print(f"   Pincode: {row['HUB Buyers Pin code']}")
        print(f"   State: {row['State']}")
except Exception as e:
    print(f"   ❌ Error reading CSV: {e}")

# Test 2: Check hub_metadata_service
print("\n2️⃣ Checking hub_metadata_service:")
try:
    # Force reimport to avoid caching issues
    if 'src.core.hub_metadata_service' in sys.modules:
        del sys.modules['src.core.hub_metadata_service']
    
    from src.core.hub_metadata_service import HubMetadataService
    
    # Create fresh instance
    hub_service = HubMetadataService()
    
    print(f"   Total hubs loaded: {len(hub_service.hub_data)}")
    
    # Check if HYD_ATP exists
    if 'HYD_ATP' in hub_service.hub_data:
        print(f"   ✅ HYD_ATP found in hub_data!")
        hub_info = hub_service.hub_data['HYD_ATP']
        print(f"   Full address: {hub_info['full_address'][:80]}...")
        print(f"   Address line 1: {hub_info['address_line1'][:60]}...")
        print(f"   Address line 2: {hub_info['address_line2'][:60]}...")
        print(f"   City: {hub_info['city']}")
        print(f"   State: {hub_info['state']}")
        print(f"   Pincode: {hub_info['pincode']}")
        print(f"   State code: {hub_info['state_code']}")
    else:
        print(f"   ❌ HYD_ATP NOT found in hub_data")
        print(f"   Available Hyderabad hubs:")
        for hub_name in hub_service.hub_data.keys():
            if 'HYD' in hub_name:
                print(f"      - {hub_name}")
    
    # Test get_customer_address_components method
    print("\n   Testing get_customer_address_components('HYD_ATP'):")
    components = hub_service.get_customer_address_components('HYD_ATP')
    if components:
        print(f"   ✅ Components retrieved successfully!")
        print(f"   Address1: {components.get('address1', 'N/A')[:60]}...")
        print(f"   Address2: {components.get('address2', 'N/A')[:60]}...")
        print(f"   City: {components.get('city', 'N/A')}")
        print(f"   Pincode: {components.get('pincode', 'N/A')}")
    else:
        print(f"   ❌ No components returned")
        
except Exception as e:
    print(f"   ❌ Error loading hub_metadata_service: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Check config_loader
print("\n3️⃣ Checking config_loader:")
try:
    if 'src.core.config_loader' in sys.modules:
        del sys.modules['src.core.config_loader']
    
    from src.core.config_loader import get_config_loader
    
    config = get_config_loader()
    
    # Check GSTIN for Telangana
    gstin_ak = config.get_gstin('AMOLAKCHAND', 'Telangana')
    gstin_bd = config.get_gstin('BODEGA', 'Telangana')
    
    print(f"   AMOLAKCHAND Telangana GSTIN: {gstin_ak}")
    print(f"   BODEGA Telangana GSTIN: {gstin_bd}")
    
    if gstin_ak and gstin_bd:
        print(f"   ✅ GSTIN lookups working")
    else:
        print(f"   ⚠️ Some GSTIN lookups failed")
        
except Exception as e:
    print(f"   ❌ Error loading config_loader: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("Verification complete!")
print("=" * 70)
print("\n💡 If HYD_ATP is not found, make sure:")
print("   1. data/final_address_updated.csv exists and has HYD_ATP entries")
print("   2. The app is restarted (for Streamlit, click 'Rerun' or 'Clear cache')")
print("   3. No caching issues with Python module imports")
