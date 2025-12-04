#!/usr/bin/env python3
"""
Local Data Manager - Handles all data operations without Google Sheets dependency
"""

import pandas as pd
import os
import json
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Dict, List
import sys
from .dc_template_generator import HUB_CONSTANTS

# Import migration module for TaxMaster handling
from .taxmaster_migration import (
    load_and_validate_taxmaster,
    get_taxmaster_columns_for_merge,
    NEW_TAXMASTER_FILE,
    TAXMASTER_COLUMN_MAPPING
)

# Constants
DATA_DIR = "data"
INPUT_DIR = "input_data"
MASTER_DATA_DIR = "master_data"
OUTPUT_DIR = "generated_dcs"

# Define which columns are absolutely required vs. optional
# Optional columns are present in Raw_DC but may not be in other inputs.
# Type `object` signals that we shouldn't enforce a type on them during initial validation.
REQUIRED_COLUMNS = {
    'jpin': str,
    'taxable_amount': float,
    'planned_quantity': float,
    'title': str,
    'hub': str,
    'trip_ref_number': str,
    'delivery_date': str,
    # Optional columns from Raw_DC
    'name': object, 
    'sender': object,
    'receiver': object
}

# These are the columns that MUST be present in any input file.
STRICTLY_REQUIRED = {'jpin', 'taxable_amount', 'planned_quantity', 'title', 'hub', 'trip_ref_number', 'delivery_date'}

class DataValidator:
    """Validates input data format and structure"""
    
    @staticmethod
    def validate_columns(df: pd.DataFrame) -> tuple[bool, List[str]]:
        """
        Validate that strictly required columns are present.
        
        Returns:
            tuple: (is_valid, list of missing columns)
        """
        missing_columns = []
        
        # Check only strictly required columns
        for col in STRICTLY_REQUIRED:
            if col not in df.columns:
                missing_columns.append(f"Missing required column: {col}")
        
        return len(missing_columns) == 0, missing_columns
        
    @staticmethod
    def validate_against_raw_data(df: pd.DataFrame) -> tuple[bool, List[str]]:
        """
        Validate input data against Raw_DC.csv reference data
        
        Returns:
            tuple: (is_valid, list of validation messages)
        """
        validation_messages = []
        try:
            # Read reference data
            raw_df = pd.read_csv(os.path.join(DATA_DIR, 'Raw_DC.csv'))
            raw_df.columns = [col.strip().lower() for col in raw_df.columns]
            
            # Clean numeric columns in raw data
            numeric_cols = ['planned_quantity', 'taxable_amount']
            for col in numeric_cols:
                if col in raw_df.columns:
                    raw_df[col] = pd.to_numeric(raw_df[col].astype(str).str.replace(',', ''), errors='coerce')
            
            # Create a set of unique JPINs in raw data
            raw_jpins = set(raw_df['jpin'].astype(str))
            
            # Check if all JPINs in input exist in raw data
            input_jpins = set(df['jpin'].astype(str))
            unknown_jpins = input_jpins - raw_jpins
            if unknown_jpins:
                validation_messages.append(f"Found {len(unknown_jpins)} unknown JPINs not in reference data")
            
            # For matching JPINs, validate quantities and amounts are within expected ranges
            for jpin in input_jpins & raw_jpins:
                raw_rows = raw_df[raw_df['jpin'].astype(str) == jpin]
                input_rows = df[df['jpin'].astype(str) == jpin]
                
                # Check quantity range
                raw_qty_range = (raw_rows['planned_quantity'].min(), raw_rows['planned_quantity'].max())
                input_qty = input_rows['planned_quantity'].iloc[0]
                if input_qty < raw_qty_range[0] or input_qty > raw_qty_range[1]:
                    validation_messages.append(
                        f"JPIN {jpin}: Quantity {input_qty} outside expected range {raw_qty_range}"
                    )
                
                # Check amount range with 10% tolerance
                raw_amt_range = (
                    raw_rows['taxable_amount'].min() * 0.9,
                    raw_rows['taxable_amount'].max() * 1.1
                )
                input_amt = input_rows['taxable_amount'].iloc[0]
                if input_amt < raw_amt_range[0] or input_amt > raw_amt_range[1]:
                    validation_messages.append(
                        f"JPIN {jpin}: Amount {input_amt} outside expected range {raw_amt_range}"
                    )
            
            print("✅ Validated against Raw_DC.csv reference data")
            return len(validation_messages) == 0, validation_messages
            
        except FileNotFoundError:
            print("⚠️ Raw_DC.csv not found. Skipping reference validation.")
            return True, ["Reference validation skipped - Raw_DC.csv not found"]
        except Exception as e:
            print(f"❌ Error during reference validation: {str(e)}")
            return False, [f"Reference validation failed: {str(e)}"]

class DataManager:
    """Manages data loading, validation, and processing"""
    
    def __init__(self, input_dir: str = INPUT_DIR, master_dir: str = MASTER_DATA_DIR):
        self.input_dir = input_dir
        self.master_dir = master_dir
        self.ensure_directories()
    
    def ensure_directories(self):
        """Ensure required directories exist"""
        for directory in [self.input_dir, self.master_dir, OUTPUT_DIR]:
            if not os.path.exists(directory):
                os.makedirs(directory)
                print(f"✅ Created directory: {directory}")
    
    def load_data(self, file_path: str) -> Optional[pd.DataFrame]:
        """
        Load and validate input data
        
        Args:
            file_path: Path to the input CSV file
            
        Returns:
            DataFrame if valid, None if invalid
        """
        try:
            # Read the CSV file
            df = pd.read_csv(file_path)
            
            # Clean column names
            df.columns = [col.strip().lower() for col in df.columns]
            
            # Clean numeric data first
            for col in df.columns:
                if col in REQUIRED_COLUMNS:
                    expected_type = REQUIRED_COLUMNS[col]
                    if expected_type in [float, int]:
                        df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')
            
            # Then validate columns
            is_valid, issues = DataValidator.validate_columns(df)
            if not is_valid:
                print("❌ Data validation failed:")
                for issue in issues:
                    print(f"  - {issue}")
                return None
                
            # Validate against reference data
            is_valid, messages = DataValidator.validate_against_raw_data(df)
            if not is_valid:
                print("❌ Reference validation failed:")
                for msg in messages:
                    print(f"  - {msg}")
                return None
            elif messages:
                print("⚠️ Reference validation warnings:")
                for msg in messages:
                    print(f"  - {msg}")
            
            print(f"✅ Successfully loaded and validated {len(df)} rows from {file_path}")
            return df
            
        except Exception as e:
            print(f"❌ Error loading data: {str(e)}")
            return None
    
    def process_data(self, df: pd.DataFrame, tax_map: Dict) -> pd.DataFrame:
        """
        Process input data and calculate tax values for template generation
        
        Args:
            df: Input DataFrame
            tax_map: Dictionary mapping JPINs to tax details (supports both old and new format)
            
        Returns:
            DataFrame with calculated values
        """
        from tax_calculator import calculate_all_taxes
        
        print("🔄 Processing data...")
        
        # Create output DataFrame
        result_df = df.copy()
        
        # Ensure required columns exist with default values
        for col in ['cess', 'cgst', 'sgst', 'total_amount']:
            if col not in result_df.columns:
                result_df[col] = 0.0
            else:
                result_df[col] = result_df[col].astype(float)
        
        # Calculate tax values for each row
        for idx, row in df.iterrows():
            try:
                # Get tax details from tax_map
                jpin = row['jpin']
                tax_details = tax_map.get(jpin, {'hsn_code': 'N/A', 'gst_percentage': 0, 'cess': 0})
                
                # Handle both old and new format tax details
                # New format uses 'hsnCode' and 'gstPercentage', old uses 'hsn_code' and 'gst_percentage'
                hsn_code = tax_details.get('hsnCode', tax_details.get('hsn_code', 'N/A'))
                gst_percentage = tax_details.get('gstPercentage', tax_details.get('gst_percentage', 0))
                
                # Get input values
                taxable_value = Decimal(str(row['taxable_amount']))
                gst_rate = Decimal(str(gst_percentage)) if pd.notna(gst_percentage) else Decimal('0')
                cess_rate = Decimal(str(tax_details.get('cess', 0))) if pd.notna(tax_details.get('cess')) else Decimal('0')
                
                # Calculate taxes
                tax_values = calculate_all_taxes(taxable_value, gst_rate, cess_rate)
                
                # Update row with calculated values
                result_df.at[idx, 'cgst'] = float(tax_values['cgst_amount'])
                result_df.at[idx, 'sgst'] = float(tax_values['sgst_amount'])
                result_df.at[idx, 'cess'] = float(tax_values['cess_amount'])
                result_df.at[idx, 'total_amount'] = float(tax_values['total_amount'])
                result_df.at[idx, 'hsn_code'] = str(hsn_code)
                
                # Progress indicator every 100 rows
                if (idx + 1) % 100 == 0:
                    print(f"⏳ Processed {idx + 1}/{len(df)} rows...")
                
            except Exception as e:
                print(f"❌ Error processing row {idx} (JPIN: {row.get('jpin', 'unknown')}): {str(e)}")
        
        print("✅ Data processing complete!")
        return result_df

def load_taxmaster_data():
    """Load TaxMaster data with automatic format detection and migration"""
    try:
        # Try new format first
        if os.path.exists(NEW_TAXMASTER_FILE):
            print("🔄 Loading new TaxMaster format...")
            return load_and_validate_taxmaster(NEW_TAXMASTER_FILE)
        else:
            # Fallback to old format
            old_file = os.path.join(DATA_DIR, 'TaxMaster.csv')
            if os.path.exists(old_file):
                print("⚠️  Loading old TaxMaster format...")
                tax_df = pd.read_csv(old_file, dtype={'jpin': str})
                # Convert to new format
                tax_df = tax_df.rename(columns=TAXMASTER_COLUMN_MAPPING)
                print(f"✅ Converted {len(tax_df)} tax records to new format")
                return tax_df
            else:
                raise FileNotFoundError("Neither new nor old TaxMaster file found")
                
    except Exception as e:
        print(f"❌ Error loading TaxMaster data: {str(e)}")
        return None

def read_master_data(filename):
    """Read master data from CSV file"""
    try:
        filepath = os.path.join(MASTER_DATA_DIR, filename)
        df = pd.read_csv(filepath)
        print(f"✅ Read master data from: {filename}")
        return df
    except Exception as e:
        print(f"❌ Error reading master data: {str(e)}")
        return None

def get_dc_data(input_file):
    """Get DC data from input file and enrich with master data"""
    try:
        print(f"🔄 Loading data from: {input_file}")
        
        # Determine if we're using Raw_DC as the base
        is_raw_dc_input = 'Raw_DC.csv' in os.path.basename(input_file)
        
        # Initialize DataManager
        manager = DataManager()
        
        # Read input data
        df = manager.load_data(input_file)
        if df is None:
            return None
            
        # Read master data files using migration-aware loading
        tax_df = load_taxmaster_data()
        if tax_df is None:
            print("❌ Failed to load TaxMaster data")
            return None
            
        tax_df = tax_df.drop_duplicates(subset='Jpin', keep='last')  # Use new column name
        
        # Read hub addresses
        hub_address_df = pd.read_csv(os.path.join(DATA_DIR, 'HubAddresses.csv'))
        hub_address_map = pd.Series(hub_address_df['Location Address'].values, index=hub_address_df['Location Name']).to_dict()

        # Read org names
        org_names_df = pd.read_csv(os.path.join(DATA_DIR, 'Org_Names.csv'), dtype={'org_profile_id': str})
        org_names_map = org_names_df.set_index('org_profile_id')['org_name'].to_dict()

        # --- Data Enrichment ---
        
        # 1. Merge Tax data using new format
        merge_columns = get_taxmaster_columns_for_merge()
        df = pd.merge(
            df, 
            tax_df[merge_columns], 
            left_on='jpin',  # Raw data uses 'jpin'
            right_on='Jpin',  # Tax data uses 'Jpin'
            how='left'
        )
        
        # Rename columns to match expected names and drop duplicate
        df = df.rename(columns={'hsnCode': 'hsn_code', 'gstPercentage': 'gst'})
        if 'Jpin' in df.columns:
            df = df.drop('Jpin', axis=1)
            
        df['hsn_code'].fillna('N/A', inplace=True)
        df['cess'].fillna(0, inplace=True)
        df['gst'].fillna(0, inplace=True)

        # 2. Map Hub Addresses
        df['hub_address'] = df['hub'].map(hub_address_map)
        df['hub_address'].fillna('Address not found', inplace=True)

        # 3. Map Sender and Receiver Names
        # Ensure sender/receiver columns exist, even if empty, to prevent errors
        if 'sender' not in df.columns:
            df['sender'] = ''
        if 'receiver' not in df.columns:
            df['receiver'] = ''
            
        df['sender_name'] = df['sender'].map(org_names_map).fillna(df['sender'])
        df['receiver_name'] = df['receiver'].map(org_names_map).fillna(df['receiver'])

        print("✅ Data enrichment complete.")

        # Group data by trip_ref_number AND sender to create one DC per trip per sender
        grouped = df.groupby(['trip_ref_number', 'sender'])
        
        dc_data_list = []
        
        for (trip_ref_number, sender), group in grouped:
            first_row = group.iloc[0]
            
            # --- Determine Hub Type (Sender Entity) ---
            # This logic might need to be more robust based on actual business rules
            sender_name = first_row.get('sender_name', '').lower()
            if 'sourcingbee' in sender_name:
                hub_type = 'SOURCINGBEE'
            elif 'amolakchand' in sender_name:
                hub_type = 'AMOLAKCHAND'
            elif 'bodega' in sender_name:
                hub_type = 'BODEGA'
            else:
                # Default based on hub name if sender is unclear
                hub_name = first_row['hub']
                if 'SB' in hub_name:
                    hub_type = 'SOURCINGBEE'
                elif 'AK' in hub_name:
                    hub_type = 'AMOLAKCHAND'
                else:
                    hub_type = 'BODEGA' # Default

            # Get hub constants
            hub_constants = HUB_CONSTANTS.get(hub_type, {})
            
            # Prepare product list for the template
            products = []
            for _, row in group.iterrows():
                products.append({
                    'Description': row['title'],
                    'HSN': row['hsn_code'],
                    'Quantity': Decimal(str(row['planned_quantity'])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                    'Value': Decimal(str(row['taxable_amount'])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                    'GST Rate': Decimal(str(row['gst'])),
                    'Cess': Decimal(str(row['cess'])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                })

            # Create the final dictionary for this DC
            dc_data_list.append({
                'trip_ref_number': trip_ref_number,
                'date': datetime.strptime(first_row['delivery_date'], '%B %d, %Y') if isinstance(first_row['delivery_date'], str) else first_row['delivery_date'],
                'hub_type': hub_type,
                'sender_name': hub_constants.get('sender_name', 'N/A'),
                'receiver_name': hub_constants.get('sender_name', 'N/A'),  # Use same company name for intrastate transfer
                'hub_address': first_row.get('hub_address', 'N/A'),
                'products': products
            })
            
        print(f"Grouped data into {len(dc_data_list)} DCs to be generated.")
        return dc_data_list
        
    except Exception as e:
        print(f"Error in get_dc_data: {str(e)}")
        import traceback
        traceback.print_exc()
        return None 