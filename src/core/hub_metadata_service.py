#!/usr/bin/env python3
"""
Hub Metadata Service - Centralized hub information management
Handles address parsing, distance mapping, and location-specific data
"""

import pandas as pd
import re
import os
from typing import Dict, Optional, Tuple

class HubMetadataService:
    """Centralized service for hub metadata management"""
    
    def __init__(self):
        self.hub_data = {}
        self.distance_matrix = {}
        self.state_codes = {
            'Karnataka': '29',
            'Tamil Nadu': '33',
            'Andhra Pradesh': '37',
            'Telangana': '36',
            'Kerala': '32',
            'Maharashtra': '27',
            'Gujarat': '24',
            'Rajasthan': '08',
            'Delhi': '07',
            'Haryana': '06',
            'Punjab': '03',
            'Uttar Pradesh': '09',
            'West Bengal': '19',
            'Odisha': '21',
            'Bihar': '10',
            'Jharkhand': '20',
            'Madhya Pradesh': '23',
            'Chhattisgarh': '22',
            'Assam': '18',
            'Goa': '30'
        }
        self._load_hub_data()
        self._setup_distance_matrix()
    
    def _load_hub_data(self):
        """Load and parse hub data from CSV - ✅ CITY-AGNOSTIC"""
        try:
            # ✅ Try final_address_updated.csv first (new format)
            try:
                hub_df = pd.read_csv('data/final_address_updated.csv')
                print("✅ Loading hub data from final_address_updated.csv")
                
                for _, row in hub_df.iterrows():
                    # Use Hub Name as location name
                    location_name = row.get('Hub Name', '')
                    if not location_name or pd.isna(location_name):
                        continue
                    
                    # Combine hub address fields
                    address_line1 = str(row.get('HUB Buyers Address 1', '')).strip()
                    address_line2 = str(row.get('HUB Buyers Address 1.1', '')).strip()
                    full_address = f"{address_line1}, {address_line2}".strip(', ')
                    
                    if not full_address:
                        print(f"⚠️ Skipping hub {location_name} - no address")
                        continue
                    
                    # Get pincode
                    pincode = str(row.get('HUB Buyers Pin code', '')).strip()
                    
                    # Get state
                    state = str(row.get('State', '')).strip()
                    
                    # Parse city from address or use state
                    parsed_data = self._parse_address(full_address)
                    city = parsed_data.get('city', state)
                    
                    self.hub_data[location_name] = {
                        'full_address': full_address,
                        'address_line1': address_line1,
                        'address_line2': address_line2,
                        'city': city,
                        'state': state,
                        'pincode': pincode,
                        'state_code': self.state_codes.get(state, '')
                    }
                    
                print(f"🏢 Loaded metadata for {len(self.hub_data)} hubs from final_address_updated.csv")
                return
                
            except FileNotFoundError:
                # Fallback to legacy HubAddresses.csv
                print("⚠️ final_address_updated.csv not found, trying HubAddresses.csv")
                hub_df = pd.read_csv('data/HubAddresses.csv')
                
                for _, row in hub_df.iterrows():
                    location_name = row['Location Name']
                    address = row['Location Address']
                    
                    # Skip invalid addresses
                    if pd.isna(address) or not isinstance(address, str):
                        print(f"⚠️ Skipping hub {location_name} - invalid address")
                        continue
                    
                    # Parse address components
                    parsed_data = self._parse_address(address)
                    
                    self.hub_data[location_name] = {
                        'full_address': address,
                        'address_line1': parsed_data['address_line1'],
                        'address_line2': parsed_data['address_line2'],
                        'city': parsed_data['city'],
                        'state': parsed_data['state'],
                        'pincode': parsed_data['pincode'],
                        'state_code': self.state_codes.get(parsed_data['state'], '')
                    }
                    
                print(f"🏢 Loaded metadata for {len(self.hub_data)} hubs from HubAddresses.csv")
            
        except Exception as e:
            print(f"⚠️ Error loading hub data: {e}")
            self.hub_data = {}
    
    def _parse_address(self, address: str) -> Dict[str, str]:
        """Parse address string into components - ✅ CITY-AGNOSTIC"""
        
        # Extract pincode (6 digits)
        pincode_match = re.search(r'(\d{6})', address)
        pincode = pincode_match.group(1) if pincode_match else '000000'  # ✅ No hardcoded value
        
        # Extract state (look for known state names)
        state = ''  # ✅ No default
        for state_name in self.state_codes.keys():
            if state_name.lower() in address.lower():
                state = state_name
                break
        
        # Extract city (common patterns)
        city_patterns = [
            r'(Hyderabad)',  # Hyderabad first
            r'(Mysore|Mysuru)',
            r'(Bengaluru|Bangalore)',
            r'(Mumbai|Bombay)',
            r'(Chennai|Madras)',
            r'(Pune)',
            r'(Kolar)',
            r'(Tumakuru)',
            r'(Ramanagar)',
            r'(Chikballapur)',
            r'(Tiptur)',
            r'(Patna)',
            r'(Ranchi)',
            r'(Lucknow)'
        ]
        
        city = ''  # ✅ No default
        for pattern in city_patterns:
            match = re.search(pattern, address, re.IGNORECASE)
            if match:
                city = match.group(1)
                break
        
        # Split address into lines (first part before first comma as line1)
        address_parts = [part.strip() for part in address.split(',')]
        
        if len(address_parts) >= 2:
            address_line1 = address_parts[0]
            # Take next 2-3 parts for line2, excluding state and pincode
            line2_parts = []
            for part in address_parts[1:]:
                if not re.search(r'\d{6}', part) and (not state or part.lower() != state.lower()):
                    line2_parts.append(part)
                if len(line2_parts) >= 2:
                    break
            address_line2 = ', '.join(line2_parts) if line2_parts else city
        else:
            address_line1 = address
            address_line2 = city
        
        return {
            'address_line1': address_line1,
            'address_line2': address_line2,
            'city': city,
            'state': state,
            'pincode': pincode
        }
    
    def _setup_distance_matrix(self):
        """Setup distance matrix for hub-to-hub distances"""
        # Default distance - FIXED: Changed to empty string for blank distance
        default_distance = ''  # Changed from 100 to '' for blank distance
        
        # Special distance mappings - REMOVED: No special distances needed for blank field
        # All distances should be blank as requested by user
        
        # Create distance matrix
        for hub_name in self.hub_data.keys():
            self.distance_matrix[hub_name] = {}
            
            for other_hub in self.hub_data.keys():
                if hub_name == other_hub:
                    distance = 0  # Same hub distance is 0
                else:
                    # FIXED: All inter-hub distances are blank (empty string)
                    distance = default_distance
                
                self.distance_matrix[hub_name][other_hub] = distance
    
    def get_hub_info(self, hub_name: str) -> Optional[Dict]:
        """Get complete hub information"""
        # Direct match
        if hub_name in self.hub_data:
            return self.hub_data[hub_name]
        
        # Partial match
        for hub_key in self.hub_data.keys():
            if hub_name.upper() in hub_key.upper() or hub_key.upper() in hub_name.upper():
                return self.hub_data[hub_key]
        
        print(f"⚠️ Hub {hub_name} not found in metadata")
        return None
    
    def get_distance(self, from_hub: str, to_hub: str) -> int:
        """Get distance between two hubs"""
        # Handle direct hub names
        if from_hub in self.distance_matrix and to_hub in self.distance_matrix[from_hub]:
            return self.distance_matrix[from_hub][to_hub]
        
        # Handle partial matches
        from_hub_key = self._find_hub_key(from_hub)
        to_hub_key = self._find_hub_key(to_hub)
        
        if from_hub_key and to_hub_key:
            return self.distance_matrix[from_hub_key][to_hub_key]
        
        # FIXED: Remove special case for Mysore - all distances should be blank
        # Default fallback - FIXED: Return empty string instead of 100
        return ''
    
    def _find_hub_key(self, hub_name: str) -> Optional[str]:
        """Find hub key by partial matching"""
        for hub_key in self.hub_data.keys():
            if hub_name.upper() in hub_key.upper() or hub_key.upper() in hub_name.upper():
                return hub_key
        return None
    
    def get_place_of_supply(self, hub_name: str) -> str:
        """Get place of supply for a hub - ✅ CITY-AGNOSTIC"""
        hub_info = self.get_hub_info(hub_name)
        if hub_info:
            return hub_info['city']
        return ''  # ✅ No fallback - let caller handle missing data
    
    def get_state_info(self, hub_name: str) -> Tuple[str, str]:
        """Get state name and state code for a hub - ✅ CITY-AGNOSTIC"""
        hub_info = self.get_hub_info(hub_name)
        if hub_info:
            return hub_info['state'], hub_info['state_code']
        return '', ''  # ✅ No fallback
    
    def get_customer_address_components(self, hub_name: str) -> Dict[str, str]:
        """Get customer address components for E-Way bill - ✅ CITY-AGNOSTIC"""
        hub_info = self.get_hub_info(hub_name)
        
        if hub_info:
            return {
                'address1': hub_info['address_line1'],
                'address2': hub_info['address_line2'],
                'city': hub_info['city'],
                'state': hub_info['state'],
                'pincode': hub_info['pincode'],
                'state_code': hub_info['state_code']
            }
        
        # ✅ No fallback - return empty values
        return {
            'address1': '',
            'address2': '',
            'city': '',
            'state': '',
            'pincode': '000000',
            'state_code': ''
        }
    
    def validate_hub_data(self) -> Dict[str, list]:
        """Validate hub data completeness"""
        issues = {
            'missing_pincode': [],
            'invalid_state': [],
            'missing_city': []
        }
        
        for hub_name, hub_info in self.hub_data.items():
            if not hub_info['pincode'] or hub_info['pincode'] == '562123':
                issues['missing_pincode'].append(hub_name)
            
            if hub_info['state'] not in self.state_codes:
                issues['invalid_state'].append(hub_name)
            
            if not hub_info['city'] or hub_info['city'] == 'Bengaluru':
                issues['missing_city'].append(hub_name)
        
        return issues
    
    def print_hub_summary(self):
        """Print summary of all hub data"""
        print(f"\n🏢 Hub Metadata Summary:")
        print(f"   Total Hubs: {len(self.hub_data)}")
        
        for hub_name, hub_info in self.hub_data.items():
            print(f"\n📍 {hub_name}:")
            print(f"   City: {hub_info['city']}")
            print(f"   State: {hub_info['state']} ({hub_info['state_code']})")
            print(f"   Pincode: {hub_info['pincode']}")
            print(f"   Address: {hub_info['address_line1']}")
        
        # Print distance matrix for Mysore
        print(f"\n🚗 Distance Matrix (sample - MYS_AGR):")
        if 'MYS_AGR' in self.distance_matrix:
            for dest, distance in list(self.distance_matrix['MYS_AGR'].items())[:5]:
                print(f"   MYS_AGR → {dest}: {distance}km")

# Global instance
hub_metadata = HubMetadataService() 