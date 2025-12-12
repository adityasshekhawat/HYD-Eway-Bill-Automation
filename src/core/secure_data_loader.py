#!/usr/bin/env python3
"""
Secure Data Loader - Loads sensitive data from Streamlit Secrets or environment variables
This allows keeping sensitive data out of the public repository
"""

import os
import pandas as pd
import streamlit as st
from typing import Optional, Dict
import json

class SecureDataLoader:
    """
    Loads sensitive data from secure sources instead of committed files
    Priority: Streamlit Secrets > Environment Variables > Local Files (dev only)
    """
    
    def __init__(self):
        self.is_production = self._check_production_env()
        
    def _check_production_env(self) -> bool:
        """Check if running in production (Streamlit Cloud)"""
        return os.getenv('STREAMLIT_SHARING_MODE') is not None or \
               os.getenv('IS_STREAMLIT_CLOUD') == 'true'
    
    def load_final_address_csv(self) -> pd.DataFrame:
        """
        Load final_address_updated.csv from secure source
        
        Returns:
            DataFrame with address data
        """
        # Try Streamlit Secrets first (production)
        if self.is_production:
            try:
                # Option 1: Load from secrets as JSON
                if "final_address_data" in st.secrets:
                    data = st.secrets["final_address_data"]
                    return pd.DataFrame(json.loads(data))
                
                # Option 2: Load from secrets as CSV string
                if "final_address_csv" in st.secrets:
                    from io import StringIO
                    csv_string = st.secrets["final_address_csv"]
                    return pd.read_csv(StringIO(csv_string))
                    
            except Exception as e:
                print(f"⚠️ Failed to load from secrets: {e}")
        
        # Fallback to local file (development only)
        local_path = 'data/final_address_updated.csv'
        if os.path.exists(local_path):
            print(f"📁 Loading from local file: {local_path}")
            return pd.read_csv(local_path)
        
        raise FileNotFoundError(
            "Could not load final_address data. "
            "Please configure Streamlit Secrets or provide local file."
        )
    
    def load_hub_addresses(self) -> Dict:
        """Load hub addresses from secure source"""
        if self.is_production and "hub_addresses" in st.secrets:
            return dict(st.secrets["hub_addresses"])
        
        # Fallback to local file
        local_path = 'data/HubAddresses.csv'
        if os.path.exists(local_path):
            df = pd.read_csv(local_path)
            return pd.Series(
                df['Location Address'].values,
                index=df['Location Name']
            ).to_dict()
        
        return {}
    
    def load_org_names(self) -> Dict:
        """Load organization names from secure source"""
        if self.is_production and "org_names" in st.secrets:
            return dict(st.secrets["org_names"])
        
        # Fallback to local file
        local_path = 'data/Org_Names.csv'
        if os.path.exists(local_path):
            df = pd.read_csv(local_path, dtype={'org_profile_id': str})
            return df.set_index('org_profile_id')['org_name'].to_dict()
        
        return {}
    
    def load_taxmaster(self) -> pd.DataFrame:
        """Load tax master data from secure source"""
        if self.is_production and "taxmaster_data" in st.secrets:
            data = st.secrets["taxmaster_data"]
            return pd.DataFrame(json.loads(data))
        
        # Fallback to local file
        local_paths = [
            'master_data/TaxMaster_Updated.csv',
            'data/TaxMaster.csv'
        ]
        
        for path in local_paths:
            if os.path.exists(path):
                return pd.read_csv(path, dtype={'jpin': str})
        
        raise FileNotFoundError("Could not load TaxMaster data")


# Singleton instance
_secure_loader = None

def get_secure_data_loader() -> SecureDataLoader:
    """Get singleton instance of secure data loader"""
    global _secure_loader
    if _secure_loader is None:
        _secure_loader = SecureDataLoader()
    return _secure_loader


# Example usage in your existing code:
"""
# Instead of:
df = pd.read_csv('data/final_address_updated.csv')

# Use:
from src.core.secure_data_loader import get_secure_data_loader
loader = get_secure_data_loader()
df = loader.load_final_address_csv()
"""
