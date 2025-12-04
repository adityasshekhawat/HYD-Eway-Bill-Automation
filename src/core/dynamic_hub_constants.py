#!/usr/bin/env python3
"""
Dynamic Hub Constants Generator
Replaces hardcoded HUB_CONSTANTS with data-driven configuration
"""

import sys
import os
from typing import Dict, Optional

# Handle both module import and standalone execution
try:
    from .config_loader import get_config_loader
except ImportError:
    # Add parent directory to path for standalone execution
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core.config_loader import get_config_loader


class DynamicHubConstants:
    """
    Generates HUB_CONSTANTS dynamically from configuration files
    Replaces hardcoded Bangalore-specific values
    """
    
    def __init__(self):
        """Initialize with configuration loader"""
        self.config = get_config_loader()
        self._constants_cache = {}
        
    def get_hub_constants(self, company: str, state: Optional[str] = None, fc_name: Optional[str] = None) -> Dict:
        """
        Get hub constants for a company, optionally filtered by state and FC
        
        Args:
            company: Company name (SOURCINGBEE, AMOLAKCHAND, BODEGA)
            state: Optional state filter
            fc_name: Optional FC name filter
            
        Returns:
            Dictionary with hub constants (compatible with old HUB_CONSTANTS format)
        """
        # Normalize company name
        company = company.upper().strip()
        if 'SOURCINGBEE' in company or 'SOURCING BEE' in company:
            company = 'SOURCINGBEE'
        elif 'AMOLAKCHAND' in company:
            company = 'AMOLAKCHAND'
        elif 'BODEGA' in company:
            company = 'BODEGA'
            
        # Check cache
        cache_key = (company, state, fc_name)
        if cache_key in self._constants_cache:
            return self._constants_cache[cache_key]
            
        # Get company states
        states = self.config.get_company_states(company)
        if not states:
            return self._get_fallback_constants(company)
            
        # Use provided state or first available state
        target_state = state if state else states[0]
        
        # Get company FCs
        fcs = self.config.get_company_fcs(company)
        if not fcs:
            return self._get_fallback_constants(company)
            
        # Use provided FC or first available FC
        target_fc = fc_name if fc_name else fcs[0]
        
        # Build constants
        constants = self._build_constants(company, target_state, target_fc)
        
        # Cache and return
        self._constants_cache[cache_key] = constants
        return constants
        
    def _build_constants(self, company: str, state: str, fc_name: str) -> Dict:
        """Build hub constants from configuration data"""
        # Get GSTIN
        gstin = self.config.get_gstin(company, state)
        
        # Get FC address
        fc_info = self.config.get_fc_address(company, fc_name)
        
        # Get state code
        state_code = self.config.get_state_code(state)
        
        # Determine company display name
        company_names = {
            'SOURCINGBEE': 'SourcingBee Private Limited',
            'AMOLAKCHAND': 'Amolakchand Ankur Kothari Enterprises Private Limited',
            'BODEGA': 'Bodega Retail Private Limited'
        }
        company_name = company_names.get(company, company)
        
        # Determine DC prefix (legacy format)
        dc_prefixes = {
            'SOURCINGBEE': 'SBDCMYR',
            'AMOLAKCHAND': 'AKVHDCMYR',
            'BODEGA': 'BDVHDCMYR'
        }
        dc_prefix = dc_prefixes.get(company, f'{company[:2]}DCMYR')
        
        # Determine company code (new format)
        company_codes = {
            'SOURCINGBEE': 'SB',
            'AMOLAKCHAND': 'AK',
            'BODEGA': 'BD'
        }
        company_code = company_codes.get(company, company[:2])
        
        # Extract city from FC info or state
        city = fc_info.get('state', state) if fc_info else state
        
        # Build constants dictionary
        constants = {
            'company_name': company_name,
            'sender_name': company_name,
            'sender_address': fc_info['address'] if fc_info else '',
            'sender_gstin': gstin or '',
            'state': state,
            'state_code': state_code or '',
            'place_of_supply': city,
            'dc_prefix': dc_prefix,
            'new_company_code': company_code,
            'fssai': fc_info.get('fssai', '') if fc_info else '',
            'pincode': fc_info.get('pincode', '') if fc_info else ''
        }
        
        return constants
        
    def _get_fallback_constants(self, company: str) -> Dict:
        """Get fallback constants when no data available"""
        company_names = {
            'SOURCINGBEE': 'SourcingBee Private Limited',
            'AMOLAKCHAND': 'Amolakchand Ankur Kothari Enterprises Private Limited',
            'BODEGA': 'Bodega Retail Private Limited'
        }
        
        return {
            'company_name': company_names.get(company, company),
            'sender_name': company_names.get(company, company),
            'sender_address': '',
            'sender_gstin': '',
            'state': '',
            'state_code': '',
            'place_of_supply': '',
            'dc_prefix': f'{company[:2]}DCMYR',
            'new_company_code': company[:2],
            'fssai': '',
            'pincode': ''
        }
        
    def get_all_hub_constants(self) -> Dict[str, Dict]:
        """
        Get all hub constants for all companies
        Returns dictionary compatible with old HUB_CONSTANTS format
        """
        all_constants = {}
        
        for company in self.config.get_all_companies():
            # Get first state and FC for each company as default
            states = self.config.get_company_states(company)
            fcs = self.config.get_company_fcs(company)
            
            if states and fcs:
                constants = self.get_hub_constants(company, states[0], fcs[0])
                all_constants[company] = constants
                
        return all_constants
        
    def get_facility_address_mapping(self) -> Dict[str, Dict]:
        """
        Get facility address mapping for all FCs
        Returns dictionary compatible with old FACILITY_ADDRESS_MAPPING format
        """
        mapping = {}
        
        for company in self.config.get_all_companies():
            fcs = self.config.get_company_fcs(company)
            
            for fc in fcs:
                fc_info = self.config.get_fc_address(company, fc)
                if fc_info:
                    # Determine facility code from FC name
                    facility_code = self._get_facility_code(fc)
                    
                    mapping[fc] = {
                        'address': fc_info['address'],
                        'pincode': fc_info['pincode'],
                        'facility_code': facility_code,
                        'state': fc_info.get('state', '')
                    }
                    
        return mapping
        
    def _get_facility_code(self, fc_name: str) -> str:
        """Extract facility code from FC name"""
        # Common patterns
        if 'Arihant' in fc_name or 'Vikrant' in fc_name:
            return 'AH'
        elif 'Sutlej' in fc_name or 'Gomati' in fc_name:
            return 'SG'
        elif 'Patna' in fc_name:
            return 'PTN'
        elif 'Ranchi' in fc_name:
            return 'RNC'
        elif 'Lucknow' in fc_name:
            return 'LKO'
        elif 'Hyderabad' in fc_name:
            return 'HYD'
        elif 'Pune' in fc_name:
            return 'PUN'
        elif 'Ahmedabad' in fc_name:
            return 'AMD'
        elif 'Bhubaneswar' in fc_name:
            return 'BHU'
        else:
            # Default: use first 2-3 chars
            return fc_name[:3].upper()


# Singleton instance
_dynamic_hub_constants = None


def get_dynamic_hub_constants() -> DynamicHubConstants:
    """Get singleton instance of dynamic hub constants"""
    global _dynamic_hub_constants
    if _dynamic_hub_constants is None:
        _dynamic_hub_constants = DynamicHubConstants()
    return _dynamic_hub_constants


# Backward compatibility: Generate HUB_CONSTANTS on import
def generate_hub_constants() -> Dict[str, Dict]:
    """
    Generate HUB_CONSTANTS dictionary for backward compatibility
    This can be used as a drop-in replacement for the old hardcoded HUB_CONSTANTS
    """
    dhc = get_dynamic_hub_constants()
    return dhc.get_all_hub_constants()


# Backward compatibility: Generate FACILITY_ADDRESS_MAPPING on import
def generate_facility_mapping() -> Dict[str, Dict]:
    """
    Generate FACILITY_ADDRESS_MAPPING dictionary for backward compatibility
    This can be used as a drop-in replacement for the old hardcoded FACILITY_ADDRESS_MAPPING
    """
    dhc = get_dynamic_hub_constants()
    return dhc.get_facility_address_mapping()


if __name__ == "__main__":
    # Test dynamic hub constants
    print("Testing Dynamic Hub Constants...")
    print("=" * 60)
    
    dhc = get_dynamic_hub_constants()
    
    print("\n📊 All Hub Constants:")
    all_constants = dhc.get_all_hub_constants()
    for company, constants in all_constants.items():
        print(f"\n{company}:")
        print(f"  Company Name: {constants['company_name']}")
        print(f"  GSTIN: {constants['sender_gstin']}")
        print(f"  State: {constants['state']} ({constants['state_code']})")
        print(f"  Address: {constants['sender_address'][:60]}...")
        print(f"  Pincode: {constants['pincode']}")
        
    print("\n\n🏢 Facility Address Mapping:")
    facility_mapping = dhc.get_facility_address_mapping()
    for fc_name, fc_info in list(facility_mapping.items())[:5]:  # Show first 5
        print(f"\n{fc_name}:")
        print(f"  Code: {fc_info['facility_code']}")
        print(f"  Address: {fc_info['address'][:60]}...")
        print(f"  Pincode: {fc_info['pincode']}")
        print(f"  State: {fc_info['state']}")
        
    print("\n\n🔍 Testing specific lookups:")
    # Test Hyderabad
    print("\nAMOLAKCHAND in Telangana:")
    hyd_constants = dhc.get_hub_constants('AMOLAKCHAND', 'Telangana')
    print(f"  GSTIN: {hyd_constants['sender_gstin']}")
    print(f"  State Code: {hyd_constants['state_code']}")
    print(f"  Place of Supply: {hyd_constants['place_of_supply']}")
    
    print("\n✅ Dynamic hub constants test complete!")
