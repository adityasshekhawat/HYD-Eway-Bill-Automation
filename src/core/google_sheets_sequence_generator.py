#!/usr/bin/env python3
"""
Google Sheets Sequence Generator - Cloud-based sequence management
Works perfectly with Streamlit Cloud (no ephemeral filesystem issues)
"""

import os
import json
from typing import Dict
from datetime import datetime
import time

try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:
    gspread = None
    Credentials = None

class GoogleSheetsSequenceGenerator:
    """
    Sequence generator using Google Sheets as backend
    
    Features:
    - Cloud-based persistence (works on Streamlit Cloud)
    - Easy manual auditing via Google Sheets interface
    - Automatic conflict resolution
    - Thread-safe with retry logic
    """
    
    def __init__(self):
        """Initialize Google Sheets client"""
        print("🔄 GoogleSheetsSequenceGenerator: Starting initialization...")
        
        if gspread is None:
            raise ImportError(
                "gspread not installed. Run: pip install gspread google-auth"
            )
        
        # Get credentials from Streamlit secrets or environment
        self.credentials_json = self._get_credentials()
        
        # Set up Google Sheets API scopes
        SCOPES = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        # Authenticate
        creds = Credentials.from_service_account_info(
            self.credentials_json,
            scopes=SCOPES
        )
        self.client = gspread.authorize(creds)
        
        # Get or create the sequences spreadsheet
        self.spreadsheet_id = self._get_or_create_spreadsheet()
        self.worksheet = self._get_or_create_worksheet()
        
        print("✅ Google Sheets sequence generator initialized successfully")
    
    def _get_credentials(self) -> dict:
        """Get Google Sheets credentials from Streamlit secrets or environment"""
        try:
            import streamlit as st
            # Try Streamlit secrets first (for Streamlit Cloud)
            if 'GOOGLE_SHEETS_CREDENTIALS' in st.secrets:
                return json.loads(st.secrets['GOOGLE_SHEETS_CREDENTIALS'])
            elif 'gcp_service_account' in st.secrets:
                # Alternative format in secrets.toml
                return dict(st.secrets['gcp_service_account'])
        except (ImportError, KeyError):
            pass
        
        # Try environment variable
        creds_json = os.getenv('GOOGLE_SHEETS_CREDENTIALS')
        if creds_json:
            return json.loads(creds_json)
        
        # Try loading from file (local development)
        creds_file = os.path.join(
            os.path.dirname(__file__), 
            '..', '..', 
            'google_sheets_credentials.json'
        )
        if os.path.exists(creds_file):
            with open(creds_file, 'r') as f:
                return json.load(f)
        
        raise ValueError(
            "Google Sheets credentials not found. Please set up credentials. "
            "See setup guide: GOOGLE_SHEETS_SETUP.md"
        )
    
    def _get_or_create_spreadsheet(self) -> str:
        """Get existing spreadsheet or create new one"""
        spreadsheet_name = 'DC_Sequences_Database'
        
        try:
            # Try to open existing spreadsheet
            spreadsheet = self.client.open(spreadsheet_name)
            print(f"✅ Found existing spreadsheet: {spreadsheet_name}")
            return spreadsheet.id
        except gspread.SpreadsheetNotFound:
            # Create new spreadsheet
            print(f"📝 Creating new spreadsheet: {spreadsheet_name}")
            spreadsheet = self.client.create(spreadsheet_name)
            
            # Share with yourself (makes it visible in Google Drive)
            # Note: This requires the service account email to be known
            print(f"✅ Created spreadsheet: {spreadsheet.url}")
            return spreadsheet.id
    
    def _get_or_create_worksheet(self):
        """Get or create the sequences worksheet"""
        spreadsheet = self.client.open_by_key(self.spreadsheet_id)
        
        try:
            worksheet = spreadsheet.worksheet('Sequences')
            print("✅ Found existing 'Sequences' worksheet")
        except gspread.WorksheetNotFound:
            # Create new worksheet
            worksheet = spreadsheet.add_worksheet(
                title='Sequences',
                rows=100,
                cols=4
            )
            
            # Set up headers
            worksheet.update('A1:D1', [[
                'Sequence Name',
                'Current Value',
                'Last Updated',
                'Total Increments'
            ]])
            
            # Format header row
            worksheet.format('A1:D1', {
                'textFormat': {'bold': True},
                'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.8}
            })
            
            print("✅ Created new 'Sequences' worksheet with headers")
        
        return worksheet
    
    def get_next_sequence(self, sequence_name: str, retry_count: int = 3) -> int:
        """
        Get next sequence value (increments atomically)
        
        Args:
            sequence_name: Name of sequence (e.g., 'akdcah_seq')
            retry_count: Number of retries on conflict
            
        Returns:
            Next sequence number
        """
        for attempt in range(retry_count):
            try:
                # Find the row for this sequence
                all_values = self.worksheet.get_all_values()
                
                row_index = None
                current_value = 300  # Default starting value
                
                # Search for existing sequence
                for idx, row in enumerate(all_values[1:], start=2):  # Skip header
                    if row and row[0] == sequence_name:
                        row_index = idx
                        current_value = int(row[1]) if row[1] else 300
                        break
                
                # Calculate next value
                next_value = current_value + 1
                
                # Update or insert
                if row_index:
                    # Update existing row
                    self.worksheet.update(f'B{row_index}:D{row_index}', [[
                        next_value,
                        datetime.now().isoformat(),
                        int(all_values[row_index-1][3] or 0) + 1
                    ]])
                else:
                    # Insert new row
                    next_row = len(all_values) + 1
                    self.worksheet.update(f'A{next_row}:D{next_row}', [[
                        sequence_name,
                        next_value,
                        datetime.now().isoformat(),
                        1
                    ]])
                
                print(f"✅ Incremented {sequence_name}: {current_value} → {next_value}")
                return next_value
                
            except Exception as e:
                if attempt < retry_count - 1:
                    wait_time = 0.5 * (attempt + 1)
                    print(f"⚠️ Retry {attempt + 1}/{retry_count} after {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    print(f"❌ Failed after {retry_count} attempts: {e}")
                    raise
    
    def get_current_sequence_value(self, sequence_name: str) -> int:
        """
        Get current sequence value WITHOUT incrementing
        
        Args:
            sequence_name: Name of sequence
            
        Returns:
            Current sequence number
        """
        try:
            all_values = self.worksheet.get_all_values()
            
            # Search for existing sequence
            for row in all_values[1:]:  # Skip header
                if row and row[0] == sequence_name:
                    return int(row[1]) if row[1] else 300
            
            # Not found, return default
            return 300
            
        except Exception as e:
            print(f"⚠️ Error getting current sequence for {sequence_name}: {e}")
            return 300
    
    def get_all_sequences(self) -> Dict[str, int]:
        """Get all sequences as a dictionary"""
        try:
            all_values = self.worksheet.get_all_values()
            
            sequences = {}
            for row in all_values[1:]:  # Skip header
                if row and len(row) >= 2 and row[0]:
                    sequences[row[0]] = int(row[1]) if row[1] else 300
            
            return sequences
            
        except Exception as e:
            print(f"⚠️ Error getting all sequences: {e}")
            return {}
    
    def set_sequence_value(self, sequence_name: str, value: int) -> bool:
        """
        Manually set a sequence value (for initialization/correction)
        
        Args:
            sequence_name: Name of sequence
            value: Value to set
            
        Returns:
            True if successful
        """
        try:
            all_values = self.worksheet.get_all_values()
            
            row_index = None
            for idx, row in enumerate(all_values[1:], start=2):
                if row and row[0] == sequence_name:
                    row_index = idx
                    break
            
            if row_index:
                # Update existing
                self.worksheet.update(f'B{row_index}:D{row_index}', [[
                    value,
                    datetime.now().isoformat(),
                    '(manually set)'
                ]])
            else:
                # Insert new
                next_row = len(all_values) + 1
                self.worksheet.update(f'A{next_row}:D{next_row}', [[
                    sequence_name,
                    value,
                    datetime.now().isoformat(),
                    '(manually set)'
                ]])
            
            print(f"✅ Set {sequence_name} = {value}")
            return True
            
        except Exception as e:
            print(f"❌ Error setting sequence: {e}")
            return False


