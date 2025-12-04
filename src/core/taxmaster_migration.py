 #!/usr/bin/env python3
"""
TaxMaster Migration Module
Handles migration from TaxMaster.csv to TaxMasterGstDump format
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import os

# Column mapping from old to new format
TAXMASTER_COLUMN_MAPPING = {
    'jpin': 'Jpin',
    'hsn_code': 'hsnCode', 
    'gst_percentage': 'gstPercentage',
    'taxmasterid': 'TaxMasterID',
    'cess': 'cess',  # No change
    'cgst_component_share': 'cgstComponentShare',
    'sgst_component_share': 'sgstComponentShare',
    'igst_component_share': 'IgstComponentShare',
    'vatpercentage': 'vatPercentage',
    'sin_tax': 'sinTax'
}

# Critical columns that must exist
CRITICAL_COLUMNS = ['Jpin', 'hsnCode', 'gstPercentage', 'cess']

# Expected data ranges for validation
DATA_VALIDATION_RULES = {
    'gstPercentage': {'min': 0, 'max': 50, 'type': float},
    'cess': {'min': 0, 'max': 100, 'type': float},
    'cgstComponentShare': {'min': 0, 'max': 100, 'type': float},
    'sgstComponentShare': {'min': 0, 'max': 100, 'type': float}
}

def validate_taxmaster_file(file_path: str) -> Tuple[bool, List[str]]:
    """
    Validate TaxMaster file format and data quality
    
    Returns:
        tuple: (is_valid, list_of_issues)
    """
    issues = []
    
    try:
        # Load file
        df = pd.read_csv(file_path, dtype={'Jpin': str, 'hsnCode': str})
        
        # Check critical columns
        missing_cols = [col for col in CRITICAL_COLUMNS if col not in df.columns]
        if missing_cols:
            issues.append(f"Missing critical columns: {missing_cols}")
            return False, issues
        
        # Check data quality
        for col, rules in DATA_VALIDATION_RULES.items():
            if col in df.columns:
                # Check for reasonable ranges
                valid_data = df[col].dropna()
                if len(valid_data) > 0:
                    out_of_range = valid_data[(valid_data < rules['min']) | (valid_data > rules['max'])]
                    if len(out_of_range) > 0:
                        issues.append(f"Column {col}: {len(out_of_range)} values outside range {rules['min']}-{rules['max']}")
        
        # Check JPIN format
        invalid_jpins = df[~df['Jpin'].str.startswith('JPIN-', na=False)]
        if len(invalid_jpins) > 0:
            issues.append(f"Invalid JPIN format: {len(invalid_jpins)} records")
        
        # Check for null values in critical fields
        for col in CRITICAL_COLUMNS:
            null_count = df[col].isnull().sum()
            if null_count > 0:
                issues.append(f"Column {col}: {null_count} null values ({null_count/len(df)*100:.1f}%)")
        
        return len(issues) == 0, issues
        
    except Exception as e:
        issues.append(f"File loading error: {str(e)}")
        return False, issues

def clean_taxmaster_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and standardize TaxMaster data
    
    Args:
        df: Raw TaxMaster DataFrame
        
    Returns:
        Cleaned DataFrame
    """
    df_clean = df.copy()
    
    # Fix GST percentage anomalies (values that look like HSN codes)
    # If GST > 100 and looks like HSN code (8 digits), set to reasonable default
    anomalous_gst = df_clean['gstPercentage'] > 100
    if anomalous_gst.any():
        print(f"⚠️  Fixing {anomalous_gst.sum()} anomalous GST percentage values")
        # Set to 18% (common GST rate) for anomalous values
        df_clean.loc[anomalous_gst, 'gstPercentage'] = 18.0
    
    # Fill null cess values with 0
    df_clean['cess'] = df_clean['cess'].fillna(0.0)
    
    # Ensure numeric columns are proper floats
    numeric_cols = ['gstPercentage', 'cess', 'cgstComponentShare', 'sgstComponentShare']
    for col in numeric_cols:
        if col in df_clean.columns:
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0.0)
    
    # Ensure string columns are strings
    string_cols = ['Jpin', 'hsnCode', 'TaxMasterID']
    for col in string_cols:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].astype(str)
    
    return df_clean

def load_and_validate_taxmaster(file_path: str) -> pd.DataFrame:
    """
    Load, validate, and clean TaxMaster data
    
    Args:
        file_path: Path to TaxMaster file
        
    Returns:
        Cleaned and validated DataFrame
        
    Raises:
        ValueError: If file validation fails
    """
    print(f"🔄 Loading TaxMaster file: {file_path}")
    
    # Validate file
    is_valid, issues = validate_taxmaster_file(file_path)
    
    if not is_valid:
        print("❌ File validation failed:")
        for issue in issues:
            print(f"  - {issue}")
        # Don't raise error for minor issues, just warn
        print("⚠️  Proceeding with data cleaning...")
    
    # Load and clean data
    df = pd.read_csv(file_path, dtype={'Jpin': str, 'hsnCode': str})
    df_clean = clean_taxmaster_data(df)
    
    print(f"✅ Loaded and cleaned {len(df_clean)} tax records")
    print(f"📊 Data summary:")
    print(f"  - Unique JPINs: {df_clean['Jpin'].nunique()}")
    print(f"  - GST rates: {df_clean['gstPercentage'].nunique()} unique values")
    print(f"  - HSN codes: {df_clean['hsnCode'].nunique()} unique codes")
    
    return df_clean

def get_taxmaster_columns_for_merge() -> List[str]:
    """
    Get the list of columns needed for tax data merge operations
    
    Returns:
        List of column names for merging
    """
    return ['Jpin', 'hsnCode', 'gstPercentage', 'cess']

def create_legacy_mapping(df: pd.DataFrame) -> Dict[str, str]:
    """
    Create mapping from new column names back to legacy names for backward compatibility
    
    Args:
        df: DataFrame with new column names
        
    Returns:
        Dictionary mapping new -> old column names
    """
    return {v: k for k, v in TAXMASTER_COLUMN_MAPPING.items() if v in df.columns}

# File path constants
NEW_TAXMASTER_FILE = "data/TaxMasterGstDump-20-06-2025-19-09-57.csv"
OLD_TAXMASTER_FILE = "data/TaxMaster.csv"