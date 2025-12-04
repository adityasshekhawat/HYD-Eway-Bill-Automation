#!/usr/bin/env python3
"""
Configuration Loader Module
Loads configuration from CSV files to replace hardcoded values
"""

import pandas as pd
import os
from typing import Dict, Optional, Tuple, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfigurationLoader:
    """
    Loads and manages configuration from CSV files:
    - Org_Names.csv: Organization name lookups
    - final_address.csv: FC and Hub addresses, GSTINs, states
    - TaxMasterGstDump: Tax data
    """
    
    def __init__(self, data_dir: str = "data"):
        """
        Initialize configuration loader
        
        Args:
            data_dir: Directory containing CSV files
        """
        self.data_dir = data_dir
        self.org_names = None
        self.final_address = None
        self.tax_master = None
        
        # Cached lookups
        self._gstin_cache = {}
        self._fc_address_cache = {}
        self._hub_address_cache = {}
        self._state_code_cache = {}
        
    def load_all(self):
        """Load all configuration files"""
        logger.info("Loading configuration files...")
        self._load_org_names()
        self._load_final_address()
        self._load_tax_master()
        self._build_caches()
        logger.info("✅ Configuration loaded successfully")
        
    def _load_org_names(self):
        """Load Org_Names.csv"""
        file_path = os.path.join(self.data_dir, "Org_Names.csv")
        try:
            self.org_names = pd.read_csv(file_path)
            logger.info(f"✅ Loaded {len(self.org_names)} organizations from Org_Names.csv")
        except Exception as e:
            logger.error(f"❌ Failed to load Org_Names.csv: {e}")
            raise
            
    def _load_final_address(self):
        """Load final_address.csv"""
        file_path = os.path.join(self.data_dir, "final_address.csv")
        try:
            self.final_address = pd.read_csv(file_path)
            logger.info(f"✅ Loaded {len(self.final_address)} address records from final_address.csv")
        except Exception as e:
            logger.error(f"❌ Failed to load final_address.csv: {e}")
            raise
            
    def _load_tax_master(self):
        """Load TaxMasterGstDump CSV"""
        # Try the specific file first
        file_path = os.path.join(self.data_dir, "TaxMasterGstDump-20-06-2025-19-09-57.csv")
        if not os.path.exists(file_path):
            # Fallback to TaxMaster.csv
            file_path = os.path.join(self.data_dir, "TaxMaster.csv")
        
        try:
            self.tax_master = pd.read_csv(file_path)
            logger.info(f"✅ Loaded {len(self.tax_master)} tax records from {os.path.basename(file_path)}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to load tax master: {e}")
            self.tax_master = None
            
    def _build_caches(self):
        """Build lookup caches for fast access"""
        if self.final_address is not None:
            self._build_gstin_cache()
            self._build_fc_address_cache()
            self._build_hub_address_cache()
            self._build_state_code_cache()
            
    def _build_gstin_cache(self):
        """Build GSTIN lookup cache: (company, state) -> GSTIN"""
        for _, row in self.final_address.iterrows():
            company = self._normalize_company_name(row.get('Entity name', ''))
            state = row.get('State', '')
            gstin = row.get('GST No', '')
            
            if company and state and gstin:
                key = (company, state)
                self._gstin_cache[key] = gstin
                
        logger.info(f"✅ Built GSTIN cache with {len(self._gstin_cache)} entries")
        
    def _build_fc_address_cache(self):
        """Build FC address cache: (company, fc_name) -> address info"""
        for _, row in self.final_address.iterrows():
            company = self._normalize_company_name(row.get('Entity name', ''))
            fc_name = row.get('FC Name', '')
            
            if company and fc_name:
                print(f"DEBUG: Processing FC '{fc_name}' for company '{company}'")
                address_line1 = row.get('FC Seller Address 1', '')
                address_line2 = row.get('FC Seller Address 1.1', '')
                pincode = str(row.get('Seller Pin code', '')).strip()
                state = row.get('State', '')
                fssai = str(row.get('Fssai', '')).strip()
                
                # Combine address lines
                full_address = f"{address_line1}, {address_line2}".strip(', ')
                
                # Extract city from FC Name or Address
                city = ''
                
                # 1. Try to extract from FC Name (e.g., FC-Hyderabad -> Hyderabad)
                if '-' in fc_name:
                    parts = fc_name.split('-')
                    if len(parts) > 1:
                        potential_city = parts[1].strip()
                        # Validate it's likely a city (no numbers, reasonable length)
                        if potential_city.isalpha() and len(potential_city) > 2:
                            city = potential_city
                            print(f"DEBUG: Extracted city '{city}' from FC Name '{fc_name}'")
                            
                # 2. If not found, look in address
                if not city:
                    address_lower = full_address.lower()
                    # Expanded list of cities
                    cities_to_check = [
                        'hyderabad', 'bengaluru', 'bangalore', 'delhi', 'pune', 'mumbai', 
                        'chennai', 'kolkata', 'patna', 'lucknow', 'ranchi', 'jaipur', 
                        'ahmedabad', 'guwahati', 'bhubaneswar', 'vijayawada', 'visakhapatnam',
                        'kochi', 'thiruvananthapuram', 'indore', 'bhopal', 'raipur', 'chandigarh',
                        'ludhiana', 'amritsar', 'jalandhar', 'gurgaon', 'gurugram', 'noida',
                        'ghaziabad', 'faridabad', 'mysore', 'mysuru', 'mangalore', 'mangaluru',
                        'hubli', 'dharwad', 'belgaum', 'belagavi', 'gulbarga', 'kalaburagi',
                        'davangere', 'shimoga', 'shivamogga', 'tumkur', 'tumakuru', 'hassan',
                        'bidar', 'hospet', 'hosapete', 'udupi', 'gadag', 'betageri', 'raichur',
                        'bagalkot', 'haveri', 'chitradurga', 'kolar', 'mandya', 'chikmagalur',
                        'chikkamagaluru', 'gangavathi', 'karwar', 'gokak', 'ranibennur', 'sira',
                        'puttur', 'chintamani', 'chamrajnagar', 'chamarajanagar', 'dandeli',
                        'hiriyur', 'shahabad', 'bhatkal', 'haliyal', 'ankola', 'kumta', 'sirsi',
                        'siddapur', 'yellapur', 'mundgod', 'honnavar', 'karwar'
                    ]
                    
                    for city_name in cities_to_check:
                        if city_name in address_lower:
                            city = city_name.title()
                            # Handle special cases
                            if city.lower() == 'bangalore': city = 'Bengaluru'
                            if city.lower() == 'gurgaon': city = 'Gurugram'
                            if city.lower() == 'mysore': city = 'Mysuru'
                            if city.lower() == 'mangalore': city = 'Mangaluru'
                            if city.lower() == 'belgaum': city = 'Belagavi'
                            if city.lower() == 'gulbarga': city = 'Kalaburagi'
                            if city.lower() == 'shimoga': city = 'Shivamogga'
                            if city.lower() == 'tumkur': city = 'Tumakuru'
                            if city.lower() == 'hospet': city = 'Hosapete'
                            if city.lower() == 'chikmagalur': city = 'Chikkamagaluru'
                            break
                            
                # 3. Fallback: Use FC Name itself if it looks like a city (no numbers/special chars)
                if not city and fc_name.isalpha() and len(fc_name) > 2:
                    city = fc_name.strip()
                
                key = (company, fc_name)
                self._fc_address_cache[key] = {
                    'address': full_address,
                    'address_line1': address_line1,
                    'address_line2': address_line2,
                    'pincode': pincode,
                    'city': city,  # Added city
                    'state': state,
                    'fssai': fssai
                }
                
        logger.info(f"✅ Built FC address cache with {len(self._fc_address_cache)} entries")
        
    def _build_hub_address_cache(self):
        """Build Hub address cache: (company, hub_name) -> address info"""
        for _, row in self.final_address.iterrows():
            company = self._normalize_company_name(row.get('Entity name', ''))
            hub_name = row.get('Hub Name', '')
            
            if company and hub_name:
                address_line1 = row.get('HUB Buyers Address 1', '')
                address_line2 = row.get('HUB Buyers Address 1.1', '')
                pincode = str(row.get('HUB Buyers Pin code', '')).strip()
                
                # Combine address lines
                full_address = f"{address_line1}, {address_line2}".strip(', ')
                
                key = (company, hub_name)
                self._hub_address_cache[key] = {
                    'address': full_address,
                    'address_line1': address_line1,
                    'address_line2': address_line2,
                    'pincode': pincode
                }
                
        logger.info(f"✅ Built Hub address cache with {len(self._hub_address_cache)} entries")
        
    def _build_state_code_cache(self):
        """Build state code cache from GSTIN prefixes"""
        for _, row in self.final_address.iterrows():
            state = row.get('State', '')
            gstin = row.get('GST No', '')
            
            if state and gstin and len(gstin) >= 2:
                # Extract state code from GSTIN (first 2 digits)
                state_code = gstin[:2]
                if state not in self._state_code_cache:
                    self._state_code_cache[state] = state_code
                    
        logger.info(f"✅ Built state code cache with {len(self._state_code_cache)} entries")
        
    def _normalize_company_name(self, company: str) -> str:
        """
        Normalize company name for consistent lookups
        
        Args:
            company: Company name from data
            
        Returns:
            Normalized company name
        """
        company = company.upper().strip()
        
        # Map variations to standard names
        if 'SOURCINGBEE' in company or 'SOURCING BEE' in company:
            return 'SOURCINGBEE'
        elif 'AMOLAKCHAND' in company:
            return 'AMOLAKCHAND'
        elif 'BODEGA' in company:
            return 'BODEGA'
        elif 'TAILHUB' in company:
            return 'TAILHUB'
            
        return company
        
    # ========== Public API Methods ==========
    
    def get_organization_name(self, org_profile_id: str) -> Optional[str]:
        """
        Get organization name from profile ID
        
        Args:
            org_profile_id: Organization profile ID
            
        Returns:
            Organization name or None
        """
        if self.org_names is None:
            return None
            
        match = self.org_names[self.org_names['org_profile_id'] == org_profile_id]
        if not match.empty:
            return match.iloc[0]['org_name']
        return None
        
    def get_gstin(self, company: str, state: str) -> Optional[str]:
        """
        Get GSTIN for company and state
        
        Args:
            company: Company name (SOURCINGBEE, AMOLAKCHAND, BODEGA)
            state: State name
            
        Returns:
            GSTIN or None
        """
        company = self._normalize_company_name(company)
        key = (company, state)
        return self._gstin_cache.get(key)
        
    def get_fc_address(self, company: str, fc_name: str) -> Optional[Dict]:
        """
        Get FC address information
        
        Args:
            company: Company name
            fc_name: FC name
            
        Returns:
            Dictionary with address, pincode, state, fssai or None
        """
        company = self._normalize_company_name(company)
        key = (company, fc_name)
        return self._fc_address_cache.get(key)
        
    def get_hub_address(self, company: str, hub_name: str) -> Optional[Dict]:
        """
        Get Hub address information
        
        Args:
            company: Company name
            hub_name: Hub name
            
        Returns:
            Dictionary with address, pincode or None
        """
        company = self._normalize_company_name(company)
        key = (company, hub_name)
        return self._hub_address_cache.get(key)
        
    def get_state_code(self, state: str) -> Optional[str]:
        """
        Get state code for state name
        
        Args:
            state: State name
            
        Returns:
            State code (2 digits) or None
        """
        return self._state_code_cache.get(state)
        
    def get_all_states(self) -> List[str]:
        """Get list of all available states"""
        return list(self._state_code_cache.keys())
        
    def get_all_companies(self) -> List[str]:
        """Get list of all companies"""
        companies = set()
        for (company, _) in self._gstin_cache.keys():
            companies.add(company)
        return sorted(list(companies))
        
    def get_company_states(self, company: str) -> List[str]:
        """
        Get all states where company operates
        
        Args:
            company: Company name
            
        Returns:
            List of state names
        """
        company = self._normalize_company_name(company)
        states = set()
        for (comp, state) in self._gstin_cache.keys():
            if comp == company:
                states.add(state)
        return sorted(list(states))
        
    def get_company_fcs(self, company: str) -> List[str]:
        """
        Get all FCs for company
        
        Args:
            company: Company name
            
        Returns:
            List of FC names
        """
        company = self._normalize_company_name(company)
        fcs = set()
        for (comp, fc) in self._fc_address_cache.keys():
            if comp == company:
                fcs.add(fc)
        return sorted(list(fcs))
        
    def get_company_hubs(self, company: str) -> List[str]:
        """
        Get all hubs for company
        
        Args:
            company: Company name
            
        Returns:
            List of hub names
        """
        company = self._normalize_company_name(company)
        hubs = set()
        for (comp, hub) in self._hub_address_cache.keys():
            if comp == company:
                hubs.add(hub)
        return sorted(list(hubs))
    
    def is_company_available_in_state(self, company: str, state: str) -> bool:
        """
        Check if a company has facilities/hubs in the given state
        
        Args:
            company: Company name (SOURCINGBEE, AMOLAKCHAND, BODEGA)
            state: State name
            
        Returns:
            True if company operates in state, False otherwise
        """
        company = self._normalize_company_name(company)
        
        # Check in GSTIN cache (fastest)
        key = (company, state)
        if key in self._gstin_cache:
            return True
        
        # Double-check in final_address data
        if self.final_address is not None:
            matching_rows = self.final_address[
                (self.final_address['Entity name'].str.contains(company, case=False, na=False)) &
                (self.final_address['State'] == state)
            ]
            return len(matching_rows) > 0
        
        return False
    
    def get_available_companies_for_state(self, state: str) -> List[str]:
        """
        Get list of companies that operate in the given state
        
        Args:
            state: State name
            
        Returns:
            List of company names (SOURCINGBEE, AMOLAKCHAND, BODEGA)
        """
        available_companies = []
        
        for company in ['SOURCINGBEE', 'AMOLAKCHAND', 'BODEGA']:
            if self.is_company_available_in_state(company, state):
                available_companies.append(company)
        
        return available_companies
    
    def get_company_info_for_state(self, company: str, state: str) -> Optional[Dict]:
        """
        Get comprehensive company information for a specific state
        
        Args:
            company: Company name
            state: State name
            
        Returns:
            Dictionary with GSTIN, FCs, hubs, or None if not available
        """
        if not self.is_company_available_in_state(company, state):
            return None
        
        company = self._normalize_company_name(company)
        
        # Get GSTIN
        gstin = self.get_gstin(company, state)
        
        # Get FCs in this state
        fcs = []
        if self.final_address is not None:
            fc_rows = self.final_address[
                (self.final_address['Entity name'].str.contains(company, case=False, na=False)) &
                (self.final_address['State'] == state)
            ]
            fcs = fc_rows['FC Name'].unique().tolist()
        
        # Get hubs in this state
        hubs = []
        if self.final_address is not None:
            hub_rows = self.final_address[
                (self.final_address['Entity name'].str.contains(company, case=False, na=False)) &
                (self.final_address['State'] == state)
            ]
            hubs = hub_rows['Hub Name'].unique().tolist()
        
        return {
            'company': company,
            'state': state,
            'gstin': gstin,
            'fcs': fcs,
            'hubs': hubs,
            'available': True
        }


# Singleton instance
_config_loader = None


def get_config_loader(data_dir: str = "data") -> ConfigurationLoader:
    """
    Get singleton configuration loader instance
    
    Args:
        data_dir: Directory containing CSV files
        
    Returns:
        ConfigurationLoader instance
    """
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigurationLoader(data_dir)
        _config_loader.load_all()
    return _config_loader


if __name__ == "__main__":
    # Test the configuration loader
    print("Testing Configuration Loader...")
    print("=" * 60)
    
    loader = get_config_loader()
    
    print("\n📊 Summary:")
    print(f"  Companies: {loader.get_all_companies()}")
    print(f"  States: {loader.get_all_states()}")
    
    print("\n🔍 Testing GSTIN lookup:")
    for company in ['SOURCINGBEE', 'AMOLAKCHAND', 'BODEGA']:
        states = loader.get_company_states(company)
        print(f"\n  {company}:")
        for state in states[:3]:  # Show first 3 states
            gstin = loader.get_gstin(company, state)
            print(f"    {state}: {gstin}")
            
    print("\n🏢 Testing FC address lookup:")
    for company in ['SOURCINGBEE', 'AMOLAKCHAND']:
        fcs = loader.get_company_fcs(company)
        if fcs:
            fc = fcs[0]
            fc_info = loader.get_fc_address(company, fc)
            print(f"\n  {company} - {fc}:")
            if fc_info:
                print(f"    Address: {fc_info['address'][:60]}...")
                print(f"    Pincode: {fc_info['pincode']}")
                print(f"    State: {fc_info['state']}")
                
    print("\n✅ Configuration loader test complete!")
