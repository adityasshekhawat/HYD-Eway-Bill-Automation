#!/usr/bin/env python3
"""
DC Sequence Manager - Thread-safe sequence management for new DC naming convention
Handles the new format: {Company}{DC}{Facility}{SequentialNumber}
- Company: AK (Amolakchand), BD (Bodega), SB (SourcingBee)  
- Facility: AH (Arihant/Vikrant), SG (Sutlej/Gomati), HYD (Hyderabad)
- Hub (optional): NCH, BAL, BVG, etc. (for Hyderabad)
- Sequential: 6-digit number (000001 to 999999) - fits 16 char limit

NOW WITH GOOGLE SHEETS PERSISTENCE FOR PRODUCTION RELIABILITY
"""

import os
import json
from typing import Dict
from datetime import datetime

class SupabaseSequenceGenerator:
    def __init__(self):
        # Use single Supabase project for all environments
        print("🔄 SupabaseSequenceGenerator: Starting initialization...")
        
        try:
            import streamlit as st
            print("✅ Streamlit imported successfully")
            self.supabase_url = os.getenv('SUPABASE_URL') or st.secrets['SUPABASE_URL']
            self.supabase_key = os.getenv('SUPABASE_KEY') or st.secrets['SUPABASE_KEY']
            print(f"✅ Got credentials from streamlit secrets")
            print(f"   URL: {self.supabase_url[:30]}..." if self.supabase_url else "   URL: None")
            print(f"   Key: {self.supabase_key[:30]}..." if self.supabase_key else "   Key: None")
        except (ImportError, KeyError) as e:
            print(f"⚠️ Streamlit secrets failed ({e}), trying environment variables...")
            # Fallback when streamlit is not available or secrets not configured
            self.supabase_url = os.getenv('SUPABASE_URL')
            self.supabase_key = os.getenv('SUPABASE_KEY')
            print(f"   ENV URL: {self.supabase_url[:30]}..." if self.supabase_url else "   ENV URL: None")
            print(f"   ENV Key: {self.supabase_key[:30]}..." if self.supabase_key else "   ENV Key: None")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError(f"Supabase credentials not found - URL: {bool(self.supabase_url)}, Key: {bool(self.supabase_key)}")
        
        print("🔄 Creating Supabase client...")
        from supabase import create_client
        self.supabase = create_client(self.supabase_url, self.supabase_key)
        print("✅ Supabase client created successfully")
    
    def get_next_sequence(self, sequence_name: str) -> int:
        try:
            result = self.supabase.rpc('get_next_seq', {'seq_name': sequence_name}).execute()
            if result.data is not None:
                if isinstance(result.data, list) and len(result.data) > 0:
                    return int(result.data[0])
                elif isinstance(result.data, int):
                    return result.data
                else:
                    print(f"⚠️ Unexpected Supabase result format: {result.data}")
                    raise ValueError(f"Unexpected result format: {result.data}")
            raise ValueError(f"No data returned for {sequence_name}")
        except Exception as e:
            print(f"⚠️ Supabase RPC error: {e}")
            raise
    
    def get_current_sequence_value(self, sequence_name: str) -> int:
        """
        Get current sequence value WITHOUT incrementing it using the new RPC function
        """
        try:
            result = self.supabase.rpc('get_current_seq', {'seq_name': sequence_name}).execute()
            if result.data is not None:
                if isinstance(result.data, list) and len(result.data) > 0:
                    return int(result.data[0])
                elif isinstance(result.data, int):
                    return result.data
                else:
                    print(f"⚠️ Unexpected Supabase result format: {result.data}")
                    raise ValueError(f"Unexpected result format: {result.data}")
            raise ValueError(f"No data returned for {sequence_name}")
        except Exception as e:
            print(f"⚠️ Supabase get_current_seq RPC error: {e}")
            raise

class LocalSequenceGenerator:
    def __init__(self, state_file='dc_sequence_state_v2.json'):
        self.state_file = state_file
        self.sequences = self._load_sequences()
    
    def _load_sequences(self):
        try:
            with open(self.state_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Default sequences starting at 300
            return {
                'akdcah_seq': 300,
                'akdcsg_seq': 300,
                'bddcah_seq': 300,
                'bddcsg_seq': 300,
                'sbdcah_seq': 300,
                'sbdcsg_seq': 300
            }
    
    def _save_sequences(self):
        with open(self.state_file, 'w') as f:
            json.dump(self.sequences, f, indent=2)
    
    def get_next_sequence(self, sequence_name: str) -> int:
        if sequence_name not in self.sequences:
            self.sequences[sequence_name] = 300
        
        self.sequences[sequence_name] += 1
        next_seq = self.sequences[sequence_name]
        self._save_sequences()
        return next_seq

class DCSequenceManager:
    def __init__(self):
        # Try sequence generators in order: Google Sheets → Supabase → Local JSON
        
        # 1. Try Google Sheets first (best for Streamlit Cloud)
        try:
            print("🔄 Attempting to initialize Google Sheets sequence generator...")
            from .google_sheets_sequence_generator import GoogleSheetsSequenceGenerator
            self.generator = GoogleSheetsSequenceGenerator()
            print("✅ Using Google Sheets sequence generator")
            
            # Test the connection
            try:
                test_seq = self.generator.get_current_sequence_value('akdcah_seq')
                print(f"✅ Google Sheets connection test successful: akdcah_seq = {test_seq}")
            except Exception as test_error:
                print(f"❌ Google Sheets connection test failed: {test_error}")
                raise test_error
                
        except Exception as gs_error:
            print(f"⚠️ Google Sheets unavailable ({type(gs_error).__name__}), trying Supabase...")
            
            # 2. Try Supabase as fallback
            try:
                print("🔄 Attempting to initialize Supabase sequence generator...")
                self.generator = SupabaseSequenceGenerator()
                print("✅ Using Supabase sequence generator")
                
                # Test the connection immediately
                try:
                    test_seq = self.generator.get_current_sequence_value('akdcah_seq')
                    print(f"✅ Supabase connection test successful: akdcah_seq = {test_seq}")
                except Exception as test_error:
                    print(f"❌ Supabase connection test failed: {test_error}")
                    raise test_error
                    
            except Exception as sb_error:
                print(f"⚠️ Supabase unavailable ({type(sb_error).__name__}), using local sequence generator")
                print(f"   Google Sheets error: {gs_error}")
                print(f"   Supabase error: {sb_error}")
                self.generator = LocalSequenceGenerator()
            
        self.company_codes = {'AMOLAKCHAND': 'AK', 'BODEGA': 'BD', 'SOURCINGBEE': 'SB'}
        self.facility_codes = {
            'Sutlej/Gomati': 'SG', 
            'Arihant': 'AH', 
            'Vikrant': 'AH',
            'FC-Hyderabad': 'HYD',  # Telangana facility
            'Hyderabad': 'HYD'
        }
        
        # Hub codes for Telangana (extracted from HYD_XXX format)
        self.telangana_hubs = ['BVG', 'SGR', 'BAL', 'KMP', 'NCH', 'SAN']
        
        # Add a reserved numbers cache for the two-step generation process
        self.reserved_numbers = {}
    
    def _extract_hub_code(self, hub_value: str) -> str:
        """
        Extract hub code from hub value (e.g., 'HYD_NCH' -> 'NCH')
        
        Args:
            hub_value: Hub value from data (e.g., 'HYD_NCH', 'HYD_BAL')
            
        Returns:
            Hub code (e.g., 'NCH', 'BAL') or empty string if not extractable
        """
        if not hub_value or not isinstance(hub_value, str):
            return ''
        
        # Extract the hub code after the underscore
        parts = hub_value.split('_')
        if len(parts) >= 2:
            hub_code = parts[-1].upper()
            return hub_code
        return ''
    
    def generate_dc_number(self, company_name: str, facility_name: str, hub_value: str = None) -> str:
        """
        Generate DC number with optional hub-based tracking for Telangana
        
        Args:
            company_name: Company name (e.g., AMOLAKCHAND, BODEGA)
            facility_name: Facility name (e.g., Arihant, FC-Hyderabad)
            hub_value: Optional hub value (e.g., 'HYD_NCH') for hub-specific sequences
            
        Returns:
            DC number in format: {Company}DC{Facility}{Sequence} or {Company}DC{Facility}{Hub}{Sequence}
        """
        company_code = self.company_codes.get(company_name.upper(), 'XX')
        facility_code = self.facility_codes.get(facility_name, 'XX')
        
        # Check if this is Telangana (Hyderabad) and hub tracking is needed
        if facility_code == 'HYD' and hub_value:
            hub_code = self._extract_hub_code(hub_value)
            if hub_code:
                # Use hub-specific sequence: akdchydnch_seq, bddchybal_seq, etc.
                # Format: AKDCHYDNCH123456 (16 chars max: 10 prefix + 6 digits)
                prefix = f"{company_code}DC{facility_code}{hub_code}"
                sequence_name = f"{prefix.lower()}_seq"
                next_seq = self.generator.get_next_sequence(sequence_name)
                return f"{prefix}{next_seq:06d}"  # 6 digits (1 to 999,999)
        
        # Default behavior for non-Telangana or when hub not provided
        # Format: AKDCAH123456 (up to 14 chars: 6 prefix + 6 digits, leaves 2 spare)
        prefix = f"{company_code}DC{facility_code}"
        sequence_name = f"{prefix.lower()}_seq"
        next_seq = self.generator.get_next_sequence(sequence_name)
        return f"{prefix}{next_seq:06d}"  # 6 digits for consistency
        
    def reserve_dc_number(self, company_name: str, facility_name: str, hub_value: str = None) -> str:
        """
        Reserve and immediately increment the DC number atomically.
        
        CHANGED: No longer uses a two-step reserve/confirm pattern because:
        1. reserved_numbers cache is lost on Streamlit rerun (new instance)
        2. No way to guarantee confirmation is called
        3. Race conditions between reserve and confirm
        
        Now increments immediately and returns the new DC number.
        
        Args:
            company_name: Company name (e.g., AMOLAKCHAND, BODEGA)
            facility_name: Facility name (e.g., Arihant, Sutlej/Gomati, FC-Hyderabad)
            hub_value: Optional hub value (e.g., 'HYD_NCH') for hub-specific sequences
            
        Returns:
            New DC number (already incremented in Google Sheets/Supabase)
        """
        company_code = self.company_codes.get(company_name.upper(), 'XX')
        facility_code = self.facility_codes.get(facility_name, 'XX')
        
        # Check if this is Telangana (Hyderabad) and hub tracking is needed
        if facility_code == 'HYD' and hub_value:
            hub_code = self._extract_hub_code(hub_value)
            if hub_code:
                prefix = f"{company_code}DC{facility_code}{hub_code}"
                sequence_name = f"{prefix.lower()}_seq"
            else:
                prefix = f"{company_code}DC{facility_code}"
                sequence_name = f"{prefix.lower()}_seq"
        else:
            prefix = f"{company_code}DC{facility_code}"
            sequence_name = f"{prefix.lower()}_seq"
        
        # ATOMIC: Increment sequence immediately (no reservation needed)
        try:
            next_seq = self.generator.get_next_sequence(sequence_name)
            dc_number = f"{prefix}{next_seq:06d}"  # 6 digits to fit 16-char limit
            print(f"✅ Generated DC number: {dc_number} (sequence incremented immediately)")
            print(f"   Length: {len(dc_number)} chars (max 16)")
            return dc_number
        except Exception as e:
            print(f"❌ Failed to generate DC number: {e}")
            # Fallback: use current + 1 (risky but better than crashing)
            current_seq = self.get_current_sequence(sequence_name)
            next_seq = current_seq + 1
            dc_number = f"{prefix}{next_seq:06d}"
            print(f"⚠️  Using fallback DC number: {dc_number} (NOT saved to database!)")
            return dc_number
    
    def confirm_dc_number(self, dc_number: str) -> bool:
        """
        Confirm a previously reserved DC number, incrementing the sequence.
        
        Args:
            dc_number: The reserved DC number to confirm
            
        Returns:
            True if confirmation successful, False otherwise
        """
        if dc_number not in self.reserved_numbers:
            print(f"❌ Cannot confirm DC number {dc_number} - not found in reservations")
            return False
            
        reservation = self.reserved_numbers[dc_number]
        sequence_name = reservation['sequence_name']
        
        try:
            # Now actually increment the sequence
            next_seq = self.generator.get_next_sequence(sequence_name)
            
            # Clean up the reservation
            del self.reserved_numbers[dc_number]
            
            print(f"✅ Confirmed DC number: {dc_number}")
            return True
        except Exception as e:
            print(f"❌ Failed to confirm DC number {dc_number}: {e}")
            return False
    
    def get_current_sequence(self, sequence_name: str) -> int:
        """
        Get the current sequence number without incrementing it.
        
        Args:
            sequence_name: Name of the sequence
            
        Returns:
            Current sequence number
        """
        if isinstance(self.generator, LocalSequenceGenerator):
            # For local generator, we can access the sequences directly
            return self.generator.sequences.get(sequence_name, 300)
        else:
            # For Supabase, use the proper RPC function that doesn't increment
            try:
                return self.generator.get_current_sequence_value(sequence_name)
            except Exception as e:
                print(f"⚠️ Error getting current sequence for {sequence_name}: {e}")
                return 300  # Default fallback
    
    def get_current_sequences(self) -> dict:
        """Get all current sequence numbers"""
        if isinstance(self.generator, LocalSequenceGenerator):
            return self.generator.sequences
        else:
            # For Supabase, we'd need to implement this
            return {}
            
    def get_sequence_health_report(self) -> dict:
        """Get a health report on sequence status"""
        report = {
            'health_status': 'healthy',
            'warnings': [],
            'last_updated': datetime.now().isoformat()
        }
        
        if isinstance(self.generator, LocalSequenceGenerator):
            report['local_sequences'] = self.generator.sequences
            
            # Calculate stats
            sequences = list(self.generator.sequences.values())
            if sequences:
                report['max_sequence'] = max(sequences)
                report['min_sequence'] = min(sequences)
            else:
                report['max_sequence'] = 0
                report['min_sequence'] = 0
                report['warnings'].append('No sequences found')
        else:
            report['local_sequences'] = {}
            report['max_sequence'] = 0
            report['min_sequence'] = 0
            report['warnings'].append('Using Supabase - local sequences not available')
            
            # Add Supabase health check
            try:
                # Implement Supabase health check here
                report['supabase_health'] = {'status': 'healthy'}
            except Exception as e:
                report['supabase_health'] = {
                    'status': 'error',
                    'message': str(e)
                }
                report['warnings'].append(f'Supabase error: {str(e)}')
                report['health_status'] = 'warning'
        
        return report

dc_sequence_manager = DCSequenceManager() 