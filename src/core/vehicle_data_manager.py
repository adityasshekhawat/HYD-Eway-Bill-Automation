#!/usr/bin/env python3
"""
Vehicle Data Manager - Handles vehicle-based DC data grouping
Separate from trip-based system to maintain existing functionality
"""

import pandas as pd
import os
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
import json
import decimal
import re
import numpy as np
from .hub_metadata_service import hub_metadata

# Import migration module for TaxMaster handling
from .taxmaster_migration import (
    load_and_validate_taxmaster, 
    get_taxmaster_columns_for_merge,
    NEW_TAXMASTER_FILE
)

# Import HUB_CONSTANTS for company name mapping
from .dc_template_generator import HUB_CONSTANTS, FACILITY_ADDRESS_MAPPING

# Import dynamic configuration loader
try:
    from .config_loader import get_config_loader
except ImportError:
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core.config_loader import get_config_loader

# Data directory
DATA_DIR = "data"

class VehicleDataManager:
    def __init__(self):
        """Initialize the VehicleDataManager"""
        self.raw_data = None
        self.tax_data = None
        self.org_data = None
        self.hub_address_data = None
        self.routes_cache = None
        
        # Use the centralized hub metadata service
        self.hub_metadata = hub_metadata
        
        # ✅ CITY-AGNOSTIC: Load configuration dynamically
        self.config_loader = get_config_loader()
        
        # ✅ CITY-AGNOSTIC: Use dynamic facility addresses from configuration
        # This replaces hardcoded Bangalore-specific addresses
        self.facility_addresses = FACILITY_ADDRESS_MAPPING
        
        # ✅ CITY-AGNOSTIC: No hardcoded default - will use config loader fallback
        self.default_facility_address = {
            'address': '',
            'address_line1': '',
            'address_line2': '',
            'pincode': '000000',
            'city': '',
            'state': ''
        }
        
        self.hub_addresses = self._load_hub_addresses()
        
        # Create hub_address_data DataFrame for compatibility with _enrich_with_hub_addresses
        if self.hub_addresses:
            hub_data = []
            for location_name, address_info in self.hub_addresses.items():
                hub_data.append({
                    'Location Name': location_name,
                    'Location Address': address_info['address']
                })
            self.hub_address_data = pd.DataFrame(hub_data)
        else:
            self.hub_address_data = pd.DataFrame(columns=['Location Name', 'Location Address'])
        
    def _load_hub_addresses(self):
        """Load hub addresses from CSV and extract pincodes - flexible filename support"""
        try:
            # List of possible hub address files to try (in order of preference)
            possible_files = [
                'HubAddresses.csv',           # Default/legacy name
                'Hub Addresses.csv',          # Common variation
                'New Hub adress.csv',         # User's current file
                'hub_addresses.csv',          # Lowercase variation
                'Hub_Addresses.csv'           # Underscore variation
            ]
            
            # Also scan for any CSV file with correct format
            import glob
            csv_files = glob.glob(os.path.join(DATA_DIR, '*.csv'))
            
            hub_addresses = {}
            file_found = False
            
            # First, try the known possible files
            for filename in possible_files:
                file_path = os.path.join(DATA_DIR, filename)
                if os.path.exists(file_path):
                    try:
                        hub_df = pd.read_csv(file_path)
                        
                        # Check if it has the required columns
                        required_columns = ['Location Name', 'Location Address']
                        if all(col in hub_df.columns for col in required_columns):
                            print(f"✅ Found hub addresses file: {filename}")
                            file_found = True
                            break
                        else:
                            print(f"⚠️ Skipping {filename} - missing required columns: {required_columns}")
                            continue
                            
                    except Exception as e:
                        print(f"⚠️ Error reading {filename}: {e}")
                        continue
            
            # If no known file found, scan all CSV files for the correct format
            if not file_found:
                print("🔍 Scanning all CSV files for hub address format...")
                
                for csv_file in csv_files:
                    try:
                        # Skip other known files (Raw_DC, TaxMaster, etc.)
                        filename = os.path.basename(csv_file).lower()
                        if any(skip in filename for skip in ['raw_dc', 'taxmaster', 'org_names']):
                            continue
                            
                        hub_df = pd.read_csv(csv_file)
                        
                        # Check if it has the required columns for hub addresses
                        required_columns = ['Location Name', 'Location Address']
                        if all(col in hub_df.columns for col in required_columns):
                            print(f"✅ Auto-detected hub addresses file: {os.path.basename(csv_file)}")
                            file_found = True
                            break
                        else:
                            print(f"⚠️ Skipping {os.path.basename(csv_file)} - not hub address format")
                            
                    except Exception as e:
                        print(f"⚠️ Error scanning {os.path.basename(csv_file)}: {e}")
                        continue
            
            if not file_found:
                print("❌ No hub addresses file found with correct format (Location Name, Location Address)")
                return {}
            
            # Process the found file
            for _, row in hub_df.iterrows():
                location_name = row['Location Name']
                address = row['Location Address']
                
                # Handle NaN/float values in address
                if pd.isna(address) or not isinstance(address, str):
                    print(f"⚠️ Skipping hub {location_name} - invalid address: {address}")
                    continue
                
                # Extract pincode from address using regex
                pincode_match = re.search(r'(\d{6})', address)
                pincode = pincode_match.group(1) if pincode_match else '000000'  # ✅ CITY-AGNOSTIC: Changed from 562123
                
                hub_addresses[location_name] = {
                    'address': address,
                    'pincode': pincode
                }
                
            print(f"🏢 Loaded {len(hub_addresses)} hub addresses with pincodes")
            return hub_addresses
            
        except Exception as e:
            print(f"⚠️ Error loading hub addresses: {e}")
            return {}

    def get_hub_pincode(self, hub_name):
        """Get pincode for a specific hub using metadata service"""
        hub_info = self.hub_metadata.get_hub_info(hub_name)
        if hub_info:
            return hub_info['pincode']
        
        print(f"⚠️ Hub {hub_name} not found, using fallback pincode 000000")
        return '000000'  # ✅ CITY-AGNOSTIC: Changed from hardcoded 562123

    def get_hub_address_with_pincode(self, hub_name):
        """Get full address for a specific hub using metadata service"""
        hub_info = self.hub_metadata.get_hub_info(hub_name)
        if hub_info:
            return hub_info['full_address']
        
        print(f"⚠️ Hub {hub_name} not found, using fallback address")
        return f"Unknown Location, 000000"  # ✅ CITY-AGNOSTIC: Changed from hardcoded Bengaluru
    
    def get_hub_distance(self, from_hub, to_hub):
        """Get distance between two hubs using metadata service"""
        return self.hub_metadata.get_distance(from_hub, to_hub)
    
    def get_hub_state_info(self, hub_name):
        """Get state and state code for a hub using metadata service"""
        return self.hub_metadata.get_state_info(hub_name)
    
    def get_hub_place_of_supply(self, hub_name):
        """Get place of supply for a hub using metadata service"""
        return self.hub_metadata.get_place_of_supply(hub_name)
        
    def load_data_from_uploads(self, uploaded_files):
        """Load data from uploaded files instead of local directory"""
        try:
            # Load raw DC data from uploaded file
            if 'raw_dc' not in uploaded_files:
                print("❌ Raw_DC.csv file not uploaded")
                return False
                
            self.raw_data = pd.read_csv(uploaded_files['raw_dc'])
            print(f"✅ Loaded {len(self.raw_data)} rows from uploaded Raw_DC.csv")
            
            # Load tax master from uploaded file with new format handling
            if 'tax_master' not in uploaded_files:
                print("❌ TaxMaster.csv file not uploaded")
                return False
                
            # Use migration module to handle new TaxMaster format
            try:
                # Try to load as new format first - FIXED: Specify dtypes to avoid mixed type warnings
                dtype_spec = {
                    'Jpin': str,  # Ensure Jpin is always string
                    'hsnCode': str,  # HSN codes should be strings
                    'gstPercentage': 'float64',  # GST percentage as float
                    'cess': 'float64'  # CESS as float
                }
                self.tax_data = pd.read_csv(uploaded_files['tax_master'], dtype=dtype_spec, low_memory=False)
                
                # Check if it's the new format
                if 'Jpin' in self.tax_data.columns:
                    print(f"✅ Detected new TaxMaster format")
                    # Validate and clean the data
                    from .taxmaster_migration import clean_taxmaster_data
                    self.tax_data = clean_taxmaster_data(self.tax_data)
                    print(f"✅ Loaded and cleaned {len(self.tax_data)} tax records from new format")
                else:
                    # Old format - convert column names
                    print(f"⚠️  Detected old TaxMaster format - converting...")
                    from .taxmaster_migration import TAXMASTER_COLUMN_MAPPING
                    self.tax_data = self.tax_data.rename(columns=TAXMASTER_COLUMN_MAPPING)
                    print(f"✅ Converted and loaded {len(self.tax_data)} tax records from old format")
                    
            except Exception as e:
                print(f"❌ Error processing TaxMaster file: {str(e)}")
                return False
            
            # Load organization data from uploaded file
            if 'org_names' not in uploaded_files:
                print("❌ Org_Names.csv file not uploaded")
                return False
                
            self.org_data = pd.read_csv(uploaded_files['org_names'])
            print(f"✅ Loaded {len(self.org_data)} organization records from uploaded Org_Names.csv")
            
            # Load hub addresses from uploaded file
            if 'hub_addresses' not in uploaded_files:
                print("❌ HubAddresses.csv file not uploaded")
                return False
                
            self.hub_address_data = pd.read_csv(uploaded_files['hub_addresses'])
            print(f"✅ Loaded {len(self.hub_address_data)} hub addresses from uploaded HubAddresses.csv")
            
            # Clear routes cache to force refresh
            self.routes_cache = None
            
            return True
            
        except Exception as e:
            print(f"❌ Error loading data from uploads: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def load_data(self):
        """Load all required data files (legacy method for backward compatibility)"""
        try:
            # Load raw DC data
            raw_file = os.path.join(DATA_DIR, 'Raw_DC.csv')
            self.raw_data = pd.read_csv(raw_file)
            print(f"✅ Loaded {len(self.raw_data)} rows from Raw_DC.csv")
            
            # Load tax master using migration module
            try:
                # Try new format first
                if os.path.exists(NEW_TAXMASTER_FILE):
                    print("🔄 Loading new TaxMaster format...")
                    self.tax_data = load_and_validate_taxmaster(NEW_TAXMASTER_FILE)
                else:
                    # Fallback to old format
                    old_file = os.path.join(DATA_DIR, 'TaxMaster.csv')
                    print("⚠️  Loading old TaxMaster format...")
                    self.tax_data = pd.read_csv(old_file, dtype={'jpin': str})
                    # Convert to new format
                    from .taxmaster_migration import TAXMASTER_COLUMN_MAPPING
                    self.tax_data = self.tax_data.rename(columns=TAXMASTER_COLUMN_MAPPING)
                    print(f"✅ Converted {len(self.tax_data)} tax records to new format")
            except Exception as e:
                print(f"❌ Error loading tax data: {str(e)}")
                return False
            
            # Load organization data
            org_file = os.path.join(DATA_DIR, 'Org_Names.csv')
            self.org_data = pd.read_csv(org_file)
            print(f"✅ Loaded {len(self.org_data)} organization records")
            
            # Load hub addresses with flexible file detection
            # Use the same logic as _load_hub_addresses but store in self.hub_address_data
            hub_addresses_dict = self._load_hub_addresses()
            if hub_addresses_dict:
                # Convert the dictionary to DataFrame format expected by _enrich_with_hub_addresses
                hub_data = []
                for location_name, address_info in hub_addresses_dict.items():
                    hub_data.append({
                        'Location Name': location_name,
                        'Location Address': address_info['address']
                    })
                self.hub_address_data = pd.DataFrame(hub_data)
                print(f"✅ Loaded {len(self.hub_address_data)} hub addresses (flexible detection)")
            else:
                print("⚠️ No hub addresses loaded - using empty DataFrame")
                self.hub_address_data = pd.DataFrame(columns=['Location Name', 'Location Address'])
            
            return True
            
        except Exception as e:
            print(f"❌ Error loading data: {str(e)}")
            return False
    
    def get_available_routes(self):
        """Get all unique From-To route combinations"""
        if self.raw_data is None:
            return []
            
        if self.routes_cache is not None:
            return self.routes_cache
            
        try:
            # Group by origin (name) and destination (hub)
            routes = self.raw_data.groupby(['name', 'hub']).size().reset_index(name='trip_count')
            routes_list = []
            
            for _, row in routes.iterrows():
                routes_list.append({
                    'from': row['name'],
                    'to': row['hub'], 
                    'trip_count': row['trip_count']
                })
            
            self.routes_cache = routes_list
            return routes_list
            
        except Exception as e:
            print(f"❌ Error getting routes: {str(e)}")
            return []
    
    def get_trips_for_route(self, from_location, to_location):
        """Get all trips for a specific route (single facility)"""
        if self.raw_data is None:
            return []
            
        try:
            # Filter data for the specific route
            route_data = self.raw_data[
                (self.raw_data['name'] == from_location) & 
                (self.raw_data['hub'] == to_location)
            ]
            
            # Use the same composite key format as multiple facilities for consistency
            # Group by composite key (trip_ref_number, hub, name) to maintain unified format
            trip_summary = []
            # Create composite unique identifier: trip_ref_number + hub + name combination (most specific)
            composite_keys = route_data[['trip_ref_number', 'hub', 'name']].drop_duplicates()
            
            for _, key_row in composite_keys.iterrows():
                trip_ref_number = key_row['trip_ref_number']
                hub = key_row['hub']
                facility_name = key_row['name']
                
                # Get all rows for this specific (trip_ref_number, hub, name) combination
                trip_rows = route_data[
                    (route_data['trip_ref_number'] == trip_ref_number) & 
                    (route_data['hub'] == hub) &
                    (route_data['name'] == facility_name)
                ]
                
                # Calculate totals - using correct column names
                total_qty = trip_rows['planned_quantity'].sum()
                # Handle taxable_amount as string with commas
                taxable_amounts = trip_rows['taxable_amount'].astype(str).str.replace(',', '').astype(float)
                total_value = taxable_amounts.sum()
                product_count = len(trip_rows)
                delivery_date = trip_rows['delivery_date'].iloc[0]
                
                # Count sellers
                sellers = trip_rows['sender'].nunique()
                
                # Create composite trip identifier for UI - use same format as multiple facilities
                composite_trip_id = f"{trip_ref_number}@{hub}@{facility_name}"
                
                trip_summary.append({
                    'trip_ref_number': trip_ref_number,  # Keep original for backward compatibility
                    'composite_trip_id': composite_trip_id,  # New composite identifier (unified format)
                    'hub': hub,  # Include hub for clarity
                    'delivery_date': delivery_date,
                    'total_qty': total_qty,
                    'total_value': float(total_value),
                    'product_count': product_count,
                    'seller_count': sellers,
                    'from': facility_name,  # Include the specific facility for this trip
                    'to': to_location
                })
            
            return trip_summary
            
        except Exception as e:
            print(f"❌ Error getting trips for route: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_trips_for_multiple_facilities(self, from_locations, to_location):
        """Get all trips for multiple facilities to a single destination"""
        if self.raw_data is None:
            return []
            
        try:
            # Filter data for the specific routes (multiple origins, one destination)
            route_data = self.raw_data[
                (self.raw_data['name'].isin(from_locations)) & 
                (self.raw_data['hub'] == to_location)
            ]
            
            if route_data.empty:
                print(f"❌ No data found for routes from {from_locations} to {to_location}")
                return []
                
            print(f"✅ Found {len(route_data)} rows for routes from {from_locations} to {to_location}")
            
            # Group by composite key (trip_ref_number, hub, name) to handle multiple facilities per trip_ref_number
            trip_summary = []
            # Create composite unique identifier: trip_ref_number + hub + name combination
            composite_keys = route_data[['trip_ref_number', 'hub', 'name']].drop_duplicates()
            
            for _, key_row in composite_keys.iterrows():
                trip_ref_number = key_row['trip_ref_number']
                hub = key_row['hub']
                from_location = key_row['name']
                
                # Get all rows for this specific (trip_ref_number, hub, name) combination
                trip_rows = route_data[
                    (route_data['trip_ref_number'] == trip_ref_number) & 
                    (route_data['hub'] == hub) &
                    (route_data['name'] == from_location)
                ]
                
                # Calculate totals - using correct column names
                total_qty = trip_rows['planned_quantity'].sum()
                # Handle taxable_amount as string with commas
                taxable_amounts = trip_rows['taxable_amount'].astype(str).str.replace(',', '').astype(float)
                total_value = taxable_amounts.sum()
                product_count = len(trip_rows)
                delivery_date = trip_rows['delivery_date'].iloc[0]
                
                # Count sellers
                sellers = trip_rows['sender'].nunique()
                
                # Create composite trip identifier for UI
                composite_trip_id = f"{trip_ref_number}@{hub}@{from_location}"
                
                trip_summary.append({
                    'trip_ref_number': trip_ref_number,  # Keep original for backward compatibility
                    'composite_trip_id': composite_trip_id,  # New composite identifier
                    'hub': hub,  # Include hub for clarity
                    'delivery_date': delivery_date,
                    'total_qty': total_qty,
                    'total_value': float(total_value),
                    'product_count': product_count,
                    'seller_count': sellers,
                    'from': from_location,  # Include the specific facility for this trip
                    'to': to_location
                })
            
            return trip_summary
            
        except Exception as e:
            print(f"❌ Error getting trips for multiple facilities: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_facility_address(self, facility_name, company=None):
        """
        Get facility-specific address information with robust lookup
        
        Args:
            facility_name: Name of the facility
            company: Optional company name for better lookup
            
        Returns:
            Dictionary with address information
        """
        # 1. Try exact match in static mapping (fastest)
        if facility_name in self.facility_addresses:
            return self.facility_addresses[facility_name]
            
        # 2. If company provided, try config loader
        if company and self.config_loader:
            # Try exact match
            fc_info = self.config_loader.get_fc_address(company, facility_name)
            if fc_info:
                return fc_info
                
            # Try fuzzy match within company FCs
            fcs = self.config_loader.get_company_fcs(company)
            if fcs:
                # Normalize facility name (remove spaces, lowercase)
                norm_name = facility_name.lower().replace(' ', '').replace('-', '').replace('_', '')
                
                for fc in fcs:
                    norm_fc = fc.lower().replace(' ', '').replace('-', '').replace('_', '')
                    if norm_name in norm_fc or norm_fc in norm_name:
                        print(f"🔄 Fuzzy matched facility '{facility_name}' to '{fc}'")
                        return self.config_loader.get_fc_address(company, fc)
        
        # 3. Fallback: Search all facility addresses in mapping
        norm_name = facility_name.lower().replace(' ', '').replace('-', '').replace('_', '')
        for name, addr in self.facility_addresses.items():
            norm_addr_name = name.lower().replace(' ', '').replace('-', '').replace('_', '')
            if norm_name in norm_addr_name or norm_addr_name in norm_name:
                print(f"🔄 Fuzzy matched facility '{facility_name}' to '{name}' (global search)")
                return addr
                
        return self.default_facility_address
    
    def get_vehicle_dc_data(self, assigned_trips, vehicle_number):
        """Generate DC data grouped by vehicle and seller"""
        if self.raw_data is None or self.tax_data is None:
            return None
            
        try:
            # Handle both old format (trip_ref_number) and new format (composite_trip_id)
            actual_trip_refs = []
            hub_filters = []
            name_filters = []
            
            for trip_id in assigned_trips:
                if '@' in str(trip_id):
                    # New composite format: trip_ref_number@hub or trip_ref_number@hub@name
                    parts = str(trip_id).split('@')
                    trip_ref = parts[0]
                    hub = parts[1] if len(parts) > 1 else None
                    name = parts[2] if len(parts) > 2 else None
                    
                    actual_trip_refs.append(trip_ref)
                    if hub:
                        hub_filters.append((trip_ref, hub))
                    if name:
                        name_filters.append((trip_ref, hub, name))
                else:
                    # Old format: just trip_ref_number
                    actual_trip_refs.append(str(trip_id))
            
            # Filter raw data for selected trips
            if name_filters:
                # Use most specific filter: trip_ref_number + hub + name
                filter_conditions = []
                for trip_ref, hub, name in name_filters:
                    condition = (
                        (self.raw_data['trip_ref_number'] == trip_ref) &
                        (self.raw_data['hub'] == hub) &
                        (self.raw_data['name'] == name)
                    )
                    filter_conditions.append(condition)
                
                # Combine all conditions with OR
                combined_condition = filter_conditions[0]
                for condition in filter_conditions[1:]:
                    combined_condition = combined_condition | condition
                    
                vehicle_data = self.raw_data[combined_condition]
                
            elif hub_filters:
                # Use hub filter: trip_ref_number + hub
                filter_conditions = []
                for trip_ref, hub in hub_filters:
                    condition = (
                        (self.raw_data['trip_ref_number'] == trip_ref) &
                        (self.raw_data['hub'] == hub)
                    )
                    filter_conditions.append(condition)
                
                # Combine all conditions with OR
                combined_condition = filter_conditions[0]
                for condition in filter_conditions[1:]:
                    combined_condition = combined_condition | condition
                    
                vehicle_data = self.raw_data[combined_condition]
            else:
                # Fallback to old method: just trip_ref_number
                vehicle_data = self.raw_data[self.raw_data['trip_ref_number'].isin(actual_trip_refs)]
            
            if vehicle_data.empty:
                print("❌ No data found for selected trips")
                print(f"🔍 DEBUG - Why no data found:")
                print(f"   Trip refs searched: {actual_trip_refs[:5]}")
                print(f"   Name filters: {name_filters[:3]}")
                print(f"   Available trip refs in data (sample): {self.raw_data['trip_ref_number'].unique()[:10].tolist()}")
                print(f"   Available hubs in data (sample): {self.raw_data['hub'].unique()[:10].tolist()}")
                print(f"   Available names in data (sample): {self.raw_data['name'].unique()[:10].tolist()}")
                print(f"   Trip ref data type: {self.raw_data['trip_ref_number'].dtype}")
                return None
            
            print(f"🔄 Processing {len(vehicle_data)} rows for vehicle {vehicle_number}")
            print(f"🔍 Selected trips breakdown:")
            for trip_id in assigned_trips:
                if '@' in str(trip_id):
                    parts = str(trip_id).split('@')
                    trip_ref = parts[0]
                    hub = parts[1] if len(parts) > 1 else 'N/A'
                    name = parts[2] if len(parts) > 2 else 'N/A'
                    print(f"   Trip: {trip_ref}, Hub: {hub}, Facility: {name}")
                else:
                    print(f"   Trip: {trip_id} (legacy format)")
            
            # Enrich with tax data
            enriched_data = self._enrich_with_tax_data(vehicle_data)
            
            # Enrich with hub addresses
            enriched_data = self._enrich_with_hub_addresses(enriched_data)
            
            # Group by seller (sender) to create separate DCs
            dc_data_list = []
            grouped = enriched_data.groupby('sender')
            
            for sender, group in grouped:
                dc_data = self._create_vehicle_dc_data(group, sender, vehicle_number, assigned_trips)
                if dc_data:
                    dc_data_list.append(dc_data)
            
            print(f"✅ Generated {len(dc_data_list)} DCs for vehicle {vehicle_number}")
            return dc_data_list
            
        except Exception as e:
            print(f"❌ Error generating vehicle DC data: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def _enrich_with_tax_data(self, df):
        """Enrich data with tax information using new TaxMaster format"""
        try:
            # Use new column names for merge
            merge_columns = get_taxmaster_columns_for_merge()
            
            # Print some diagnostics
            print(f"\n🔍 Tax Data Enrichment:")
            print(f"   Raw data rows: {len(df)}")
            print(f"   Tax data rows: {len(self.tax_data)}")
            print(f"   Raw data unique JPINs: {df['jpin'].nunique()}")
            print(f"   Tax data unique JPINs: {self.tax_data['Jpin'].nunique()}")
            
            # Sample some JPINs from raw data
            sample_jpins = df['jpin'].dropna().unique()[:3]
            print(f"\n📋 Sample JPINs from Raw Data:")
            for jpin in sample_jpins:
                print(f"   {jpin}")
                # Check if this JPIN exists in tax data
                matches = self.tax_data[self.tax_data['Jpin'] == jpin]
                if len(matches) > 0:
                    print(f"   ✅ Found in tax data: HSN={matches.iloc[0]['hsnCode']}, GST={matches.iloc[0]['gstPercentage']}%")
                else:
                    print(f"   ❌ Not found in tax data")
            
            # Merge with tax data on Jpin (new format)
            enriched = df.merge(
                self.tax_data[merge_columns],
                left_on='jpin',  # Raw data still uses 'jpin'
                right_on='Jpin',  # Tax data uses 'Jpin'
                how='left'
            )
            
            # Check merge results
            print(f"\n📊 Merge Results:")
            print(f"   Rows after merge: {len(enriched)}")
            print(f"   Null HSN codes: {enriched['hsnCode'].isnull().sum()} ({enriched['hsnCode'].isnull().sum()/len(enriched)*100:.1f}%)")
            print(f"   Null GST rates: {enriched['gstPercentage'].isnull().sum()} ({enriched['gstPercentage'].isnull().sum()/len(enriched)*100:.1f}%)")
            
            # Rename columns to match expected names in downstream processing
            column_renames = {
                'hsnCode': 'hsn_code',
                'gstPercentage': 'gst_rate'
            }
            enriched = enriched.rename(columns=column_renames)
            
            # Fill missing values - FIXED: Avoid chained assignment warnings
            enriched = enriched.assign(
                hsn_code=enriched['hsn_code'].fillna('N/A'),
                gst_rate=enriched['gst_rate'].fillna(0),
                cess=enriched['cess'].fillna(0)
            )
            
            # Drop the duplicate Jpin column from merge
            if 'Jpin' in enriched.columns:
                enriched = enriched.drop('Jpin', axis=1)
            
            # Sample some rows to verify enrichment
            print(f"\n📋 Sample Enriched Data (3 rows):")
            for _, row in enriched.head(3).iterrows():
                print(f"   Product: {row.get('title', 'N/A')[:30]}...")
                print(f"   JPIN: {row.get('jpin', 'N/A')}")
                print(f"   HSN: {row.get('hsn_code', 'N/A')}")
                print(f"   GST: {row.get('gst_rate', 'N/A')}%")
                print(f"   ---")
            
            return enriched
            
        except Exception as e:
            print(f"❌ Error enriching with tax data: {str(e)}")
            import traceback
            traceback.print_exc()
            return df
    
    def _enrich_with_hub_addresses(self, df):
        """Enrich data with full hub addresses"""
        try:
            if self.hub_address_data is not None:
                # Create mapping from hub address data
                hub_address_map = pd.Series(
                    self.hub_address_data['Location Address'].values,
                    index=self.hub_address_data['Location Name']
                ).to_dict()
                
                # Map hub names to full addresses
                df['hub_address'] = df['hub'].map(hub_address_map)
                # FIXED: Avoid chained assignment warning
                df = df.assign(hub_address=df['hub_address'].fillna('Address not found'))
            else:
                df['hub_address'] = df['hub']  # Fallback to hub name
            
            return df
            
        except Exception as e:
            print(f"❌ Error enriching with hub addresses: {str(e)}")
            df['hub_address'] = df['hub']  # Fallback to hub name
            return df
    
    def _create_vehicle_dc_data(self, group_data, sender, vehicle_number, trip_refs):
        """Create DC data structure for a specific seller in a vehicle"""
        try:
            first_row = group_data.iloc[0]
            
            # Determine hub type based on sender
            hub_type = self._determine_hub_type(sender)
            
            # Get hub address from the first row (destination)
            hub_name = first_row.get('hub', 'Unknown')
            hub_address = self.get_hub_address_with_pincode(hub_name)
            
            # Get hub pincode (CRITICAL FIX!)
            hub_pincode = self.get_hub_pincode(hub_name)
            print(f"🎯 EXTRACTED hub pincode for {hub_name}: {hub_pincode}")
            
            # Get facility name from the data (source facility) - NEW: Enhanced facility detection
            facility_name = first_row.get('name', 'Unknown')
            print(f"🏭 Detected facility from data: {facility_name}")
            
            # Get facility address information with debugging
            facility_address = self.get_facility_address(facility_name, company=hub_type)
            if isinstance(facility_address, dict) and 'address' in facility_address:
                print(f"   Facility address: {facility_address['address'][:50]}...")
                print(f"   Facility pincode: {facility_address.get('pincode', 'Not found')}")
            else:
                print(f"   ⚠️ Facility address lookup failed for: {facility_name}")
                print(f"   Facility address result: {facility_address}")
            
            # Calculate distance between source facility and destination hub
            distance = self.get_hub_distance(facility_name, hub_name)
            
            # Get destination hub state information
            hub_state, hub_state_code = self.get_hub_state_info(hub_name)
            hub_place_of_supply = self.get_hub_place_of_supply(hub_name)
            
            print(f"🔍 DEBUG - Enhanced DC data creation:")
            print(f"   Facility: {facility_name}")
            print(f"   Destination Hub: {hub_name}")
            print(f"   Hub Pincode: {hub_pincode}")  # Add debug for hub pincode
            print(f"   Distance: {distance}km")
            print(f"   Hub State: {hub_state} ({hub_state_code})")
            print(f"   Place of Supply: {hub_place_of_supply}")
            print(f"   Hub Address: {hub_address[:50]}...")
            
            # Process products
            products = []
            for _, row in group_data.iterrows():
                # Use correct column names from the raw data
                product_name = row.get('title', row.get('product_name', 'Unknown Product'))
                taxable_value = row.get('taxable_amount', row.get('value', 0))
                
                # Handle taxable_amount as string with commas
                if isinstance(taxable_value, str):
                    taxable_value = taxable_value.replace(',', '')
                
                try:
                    taxable_value = float(taxable_value)
                except (ValueError, TypeError):
                    taxable_value = 0.0
                
                quantity = row.get('planned_quantity', row.get('quantity', 0))
                
                try:
                    quantity = float(quantity)
                except (ValueError, TypeError):
                    quantity = 0.0
                
                # Get HSN and GST rate from tax data
                hsn_code = row.get('hsn_code', row.get('hsn', 'N/A'))  # Fixed: use hsn_code from enriched data
                gst_rate = row.get('gst_rate', 0)
                cess_rate = row.get('cess', 0)  # Fixed: use 'cess' from enriched data
                
                # Create product with correct field names expected by DC generator
                product = {
                    'Description': product_name,
                    'HSN': hsn_code,
                    'Quantity': quantity,
                    'Value': taxable_value,
                    'GST Rate': gst_rate,
                    'Cess': cess_rate
                }
                
                products.append(product)
            
            print(f"   Products processed: {len(products)}")
            
            # CRITICAL FIX: Get actual company name from HUB_CONSTANTS based on hub_type
            hub_constants = HUB_CONSTANTS.get(hub_type, {})
            company_name = hub_constants.get('company_name', hub_type)  # Fallback to hub_type if no company_name
            
            print(f"🏢 Using company name for DC: {company_name} (hub_type: {hub_type})")
            
            # Create DC data with enhanced metadata
            dc_data = {
                'date': datetime.now(),
                'sender_name': company_name,  # FIXED: Use actual company name instead of sender ID
                'receiver_name': company_name,  # FIXED: Use actual company name for stock transfer
                'hub_type': hub_type,
                'hub_address': hub_address,
                'hub_name': hub_name,
                'hub_pincode': hub_pincode,  # CRITICAL FIX: Add hub pincode!
                'hub_state': hub_state,
                'hub_state_code': hub_state_code,
                'place_of_supply': hub_place_of_supply,
                'vehicle_number': vehicle_number,
                'trip_ref_numbers': trip_refs,
                'products': products,
                'facility_name': facility_name,
                'facility_address': facility_address.get('address', ''),
                'facility_address_line1': facility_address.get('address_line1', ''),
                'facility_address_line2': facility_address.get('address_line2', ''),
                'facility_pincode': facility_address.get('pincode', ''),
                'facility_city': facility_address.get('city', ''),
                'facility_state': facility_address.get('state', ''),
                'distance': str(distance)  # Distance as string for compatibility
            }
            
            # Split products if needed (250 product limit) - UPDATED to pass facility_name
            dc_list = self._split_products_if_needed(
                products, sender, vehicle_number, trip_refs, 
                hub_type, hub_address, facility_address, facility_name, hub_pincode
            )
            
            # Update each DC with enhanced metadata
            for dc in dc_list:
                dc.update({
                    'hub_name': hub_name,
                    'hub_pincode': hub_pincode,  # CRITICAL FIX: Add hub pincode to each DC!
                    'hub_state': hub_state,
                    'hub_state_code': hub_state_code,
                    'place_of_supply': hub_place_of_supply,
                    'distance': str(distance),
                    # CRITICAL FIX: Ensure facility address fields are in all DCs
                    'facility_address': facility_address.get('address', ''),  # Add facility_address!
                    'facility_address_line1': facility_address.get('address_line1', ''),
                    'facility_address_line2': facility_address.get('address_line2', ''),
                    'facility_city': facility_address.get('city', ''),
                    'facility_state': facility_address.get('state', '')
                })
            
            return dc_list
            
        except Exception as e:
            print(f"❌ Error creating vehicle DC data: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def _determine_hub_type(self, sender):
        """Determine hub type based on sender organization"""
        try:
            # Get organization name from org_data
            org_row = self.org_data[self.org_data['org_profile_id'] == sender]
            if not org_row.empty:
                org_name = org_row.iloc[0]['org_name'].lower()
                
                if 'sourcingbee' in org_name:
                    return 'SOURCINGBEE'
                elif 'amolakchand' in org_name:
                    return 'AMOLAKCHAND'
                elif 'bodega' in org_name:
                    return 'BODEGA'
            
            # Fallback logic
            return 'SOURCINGBEE'  # Default
            
        except Exception as e:
            print(f"⚠️ Error determining hub type: {str(e)}")
            return 'SOURCINGBEE'
    
    def _split_products_if_needed(self, products, sender, vehicle_number, trip_refs, hub_type, hub_address, facility_address, facility_name=None, hub_pincode=''):
        """Split products into multiple DCs if needed (250 product limit)"""
        max_products_per_dc = 250
        dc_list = []
        
        # CRITICAL FIX: Get actual company name from HUB_CONSTANTS based on hub_type
        hub_constants = HUB_CONSTANTS.get(hub_type, {})
        company_name = hub_constants.get('company_name', hub_type)  # Fallback to hub_type if no company_name
        
        print(f"🏢 Split DC using company name: {company_name} (hub_type: {hub_type})")
        
        # Ensure facility_address is a dictionary with required keys
        if not isinstance(facility_address, dict):
            facility_address = self.default_facility_address
        
        # Safe access to facility address components with fallbacks
        facility_addr = facility_address.get('address', 'Unknown Address')
        facility_pin = facility_address.get('pincode', '')
        facility_line1 = facility_address.get('address_line1', '')
        facility_line2 = facility_address.get('address_line2', '')
        facility_city = facility_address.get('city', '')
        facility_state = facility_address.get('state', '')
        
        if len(products) <= max_products_per_dc:
            # Single DC
            dc_data = {
                'dc_number': self._generate_dc_number(sender, vehicle_number, facility_name),
                'vehicle_number': vehicle_number,
                'trip_refs': trip_refs,
                'sender': sender,
                'sender_name': company_name,  # FIXED: Use actual company name
                'receiver_name': company_name,  # FIXED: Use actual company name for stock transfer
                'hub_type': hub_type,
                'hub_address': hub_address,
                'hub_pincode': hub_pincode,  # CRITICAL FIX: Add hub pincode!
                'facility_address': facility_addr,
                'facility_address_line1': facility_line1,
                'facility_address_line2': facility_line2,
                'facility_pincode': facility_pin,
                'facility_city': facility_city,
                'facility_state': facility_state,
                'facility_name': facility_name or 'Unknown',  # Use parameter or default
                'products': products,
                'total_value': sum(product['Value'] for product in products),
                'total_quantity': sum(product['Quantity'] for product in products)
            }
            dc_list.append(dc_data)
            return dc_list  # CRITICAL FIX: Add missing return statement for single DC case
        else:
            # Multiple DCs
            for i in range(0, len(products), max_products_per_dc):
                chunk_products = products[i:i + max_products_per_dc]
                chunk_number = (i // max_products_per_dc) + 1
                
                dc_data = {
                    'dc_number': f"{self._generate_dc_number(sender, vehicle_number, facility_name)}_{chunk_number:02d}",
                    'vehicle_number': vehicle_number,
                    'trip_refs': trip_refs,
                    'sender': sender,
                    'sender_name': company_name,  # FIXED: Use actual company name
                    'receiver_name': company_name,  # FIXED: Use actual company name for stock transfer
                    'hub_type': hub_type,
                    'hub_address': hub_address,
                    'hub_pincode': hub_pincode,  # CRITICAL FIX: Add hub pincode!
                    'facility_address': facility_addr,
                    'facility_address_line1': facility_line1,
                    'facility_address_line2': facility_line2,
                    'facility_pincode': facility_pin,
                    'facility_city': facility_city,
                    'facility_state': facility_state,
                    'facility_name': facility_name or 'Unknown',  # Use parameter or default
                    'products': chunk_products,
                    'total_value': sum(product['Value'] for product in chunk_products),
                    'total_quantity': sum(product['Quantity'] for product in chunk_products)
                }
                dc_list.append(dc_data)
            
            return dc_list
    
    def _generate_dc_number(self, sender, vehicle_number, facility_name=None):
        """
        Generate a unique DC number using the new naming convention
        New format: {Company}{DC}{Facility}{SequentialNumber}
        
        Args:
            sender: Company/sender name (for backward compatibility)
            vehicle_number: Vehicle number (for backward compatibility)
            facility_name: Facility name for new format
            
        Returns:
            Placeholder DC number (actual generation happens in vehicle_dc_generator)
        """
        # FIXED: Remove duplicate DC number generation to prevent sequence skipping
        # The actual DC number generation now happens only in vehicle_dc_generator.py
        # This prevents double-incrementing of the sequence counter
        
        try:
            # Determine company name from sender (hub type detection logic)
            company_name = self._get_company_from_sender(sender)
            
            # Use provided facility_name or detect from available data
            if facility_name:
                detected_facility = facility_name
            else:
                detected_facility = self._detect_facility_from_context()
            
            # Return placeholder - actual generation happens in vehicle_dc_generator
            placeholder_dc = f"PENDING_{company_name}_{detected_facility}"
            
            print(f"🔢 Prepared DC generation params: Company={company_name}, Facility={detected_facility}")
            return placeholder_dc
            
        except Exception as e:
            print(f"⚠️ Error preparing DC generation: {e}")
            return f"PENDING_{sender}_{vehicle_number}"
    
    def _get_company_from_sender(self, sender):
        """
        Map sender to company name for new DC format
        
        Args:
            sender: Sender identifier/name
            
        Returns:
            Company name (AMOLAKCHAND, BODEGA, SOURCINGBEE)
        """
        try:
            # Get organization name from org_data if available
            if hasattr(self, 'org_data') and self.org_data is not None:
                org_row = self.org_data[self.org_data['org_profile_id'] == sender]
                if not org_row.empty:
                    org_name = org_row.iloc[0]['org_name'].lower()
                    
                    # Map organization names to standard company names
                    if 'amolakchand' in org_name or 'ankur' in org_name or 'kothari' in org_name:
                        return 'AMOLAKCHAND'
                    elif 'bodega' in org_name:
                        return 'BODEGA'
                    elif 'sourcingbee' in org_name:
                        return 'SOURCINGBEE'
            
            # Fallback mapping based on sender patterns
            sender_lower = str(sender).lower()
            if 'amolak' in sender_lower or 'kothari' in sender_lower:
                return 'AMOLAKCHAND'
            elif 'bodega' in sender_lower:
                return 'BODEGA'
            else:
                return 'SOURCINGBEE'  # Default fallback
                
        except Exception as e:
            print(f"⚠️ Error mapping sender to company: {e}")
            return 'SOURCINGBEE'  # Safe default
    
    def _detect_facility_from_context(self):
        """
        Detect facility from current processing context
        
        Returns:
            Facility name (defaults to 'Arihant' if not detectable)
        """
        # Default to Arihant if no specific facility detected
        # In future, this could be enhanced to detect from data context
        return 'Arihant'
    
    def create_audit_trail(self, vehicle_assignments):
        """Create audit trail for trip-to-vehicle mapping"""
        try:
            audit_data = []
            for assignment in vehicle_assignments:
                for trip_ref_number in assignment['trip_refs']:
                    audit_data.append({
                        'trip_ref_number': trip_ref_number,
                        'vehicle_number': assignment['vehicle_number'],
                        'assignment_date': datetime.now().isoformat(),
                        'from_location': assignment.get('from_location', 'N/A'),
                        'to_location': assignment.get('to_location', 'N/A'),
                        'dc_count': assignment.get('dc_count', 0)
                    })
            
            # Save to JSON file
            audit_file = f"vehicle_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(audit_file, 'w') as f:
                json.dump(audit_data, f, indent=2)
            
            print(f"✅ Audit trail saved to {audit_file}")
            return audit_file
            
        except Exception as e:
            print(f"❌ Error creating audit trail: {str(e)}")
            return None 