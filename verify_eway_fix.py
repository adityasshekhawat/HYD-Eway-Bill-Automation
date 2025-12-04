import sys
import os
import pandas as pd
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from core.config_loader import get_config_loader
from eway_bill.eway_bill_template_generator import EwayBillTemplateGenerator

def verify_fix():
    print("🚀 Starting verification...")
    
    # 1. Test Config Loader
    loader = get_config_loader()
    
    # Test with a known FC from the user's mapping
    company = "AMOLAKCHAND"
    fc_name = "FC-Patna" # Assuming this exists based on mapping
    
    print(f"\n🔍 Testing FC Address Lookup for {company} - {fc_name}")
    fc_info = loader.get_fc_address(company, fc_name)
    
    if fc_info:
        print(f"✅ Found FC Info:")
        print(f"   Address: {fc_info['address']}")
        print(f"   City: {fc_info['city']}")
        print(f"   State: {fc_info['state']}")
        print(f"   Pincode: {fc_info['pincode']}")
        
        if not fc_info['city']:
            print("❌ City is missing!")
        else:
            print("✅ City is populated.")
    else:
        print(f"⚠️ FC {fc_name} not found directly. Listing available FCs for {company}:")
        fcs = loader.get_company_fcs(company)
        print(f"   Available FCs: {fcs[:5]}...")
        if fcs:
            # Try with first available FC
            fc_name = fcs[0]
            print(f"   Retrying with {fc_name}...")
            fc_info = loader.get_fc_address(company, fc_name)
            if fc_info:
                print(f"   City: {fc_info['city']}")

    # 2. Test E-Way Bill Template Generation Logic
    print(f"\n🔍 Testing Template Generation Logic")
    generator = EwayBillTemplateGenerator()
    
    # Mock DC Data
    dc_data = {
        'dc_number': 'TEST_DC_001',
        'date': datetime.now(),
        'hub_type': 'AMOLAKCHAND',
        'facility_name': fc_name,
        'facility_address_line1': fc_info['address_line1'] if fc_info else 'Test Address Line 1',
        'facility_address_line2': fc_info['address_line2'] if fc_info else 'Test Address Line 2',
        'facility_pincode': fc_info['pincode'] if fc_info else '800001',
        'facility_city': fc_info['city'] if fc_info else 'Patna',
        'facility_state': fc_info['state'] if fc_info else 'Bihar',
        'hub_address': 'Test Hub Address, Some City, 560001',
        'hub_pincode': '560001',
        'hub_state': 'Karnataka',
        'products': []
    }
    
    # Extract common data (this is where the mapping happens)
    common_data = generator._extract_common_data(dc_data)
    
    print("\n📊 Extracted Common Data (Supplier Dispatch Fields):")
    print(f"   Supplier Dispatch Name: {common_data.get('Supplier Dispatch Name')}")
    print(f"   Supplier Dispatch Address 1: {common_data.get('Supplier Dispatch Address 1')}")
    print(f"   Supplier Dispatch Address 2: {common_data.get('Supplier Dispatch Address 2')}")
    print(f"   Supplier Dispatch Place: {common_data.get('Supplier Dispatch Place')}")
    print(f"   Supplier Dispatch PinCode: {common_data.get('Supplier Dispatch PinCode')}")
    print(f"   Supplier Dispatch State Code: {common_data.get('Supplier Dispatch State Code')}")
    
    # Validation
    if common_data.get('Supplier Dispatch Place') and common_data.get('Supplier Dispatch State Code'):
        print("\n✅ Verification SUCCESS: Supplier Dispatch fields are populated.")
    else:
        print("\n❌ Verification FAILED: Supplier Dispatch fields are missing.")

if __name__ == "__main__":
    verify_fix()
