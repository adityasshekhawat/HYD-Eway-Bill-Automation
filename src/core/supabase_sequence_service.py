#!/usr/bin/env python3
"""
Supabase Sequence Service - Persistent sequence management using Supabase
"""

import os
from datetime import datetime
from typing import Dict, Optional, Tuple
import json

class SupabaseSequenceService:
    """Manages DC sequences using Supabase for persistence"""
    
    def __init__(self):
        # Try to get credentials from environment variables first
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        
        # If not found in environment, try Streamlit secrets
        if not self.supabase_url or not self.supabase_key:
            try:
                import streamlit as st
                # Use proper Streamlit secrets access for cloud environment
                try:
                    # First try direct access (works in cloud)
                    self.supabase_url = st.secrets['SUPABASE_URL']
                    self.supabase_key = st.secrets['SUPABASE_KEY']
                    print("✅ Loaded Supabase credentials from Streamlit secrets")
                except KeyError as e:
                    # If keys don't exist, try with get method
                    print(f"❌ Missing Streamlit secret key: {e}")
                    self.supabase_url = st.secrets.get('SUPABASE_URL')
                    self.supabase_key = st.secrets.get('SUPABASE_KEY')
                    if self.supabase_url and self.supabase_key:
                        print("✅ Loaded Supabase credentials from Streamlit secrets (fallback)")
                    else:
                        print("❌ Failed to load Supabase credentials from Streamlit secrets")
                except Exception as e:
                    print(f"❌ Error accessing Streamlit secrets: {e}")
                    self.supabase_url = None
                    self.supabase_key = None
            except ImportError:
                print("ℹ️ Streamlit not available (not in Streamlit environment)")
            except Exception as e:
                print(f"❌ Error importing Streamlit: {e}")
        
        self.enabled = bool(self.supabase_url and self.supabase_key)
        self.supabase = None
        
        if self.enabled:
            try:
                from supabase import create_client
                self.supabase = create_client(self.supabase_url, self.supabase_key)
                print("✅ Supabase sequence service initialized")
            except ImportError:
                print("❌ Supabase library not installed - run: pip install supabase")
                self.enabled = False
            except Exception as e:
                print(f"❌ Supabase connection failed: {e}")
                self.enabled = False
        else:
            print("⚠️ Supabase not configured - missing SUPABASE_URL or SUPABASE_KEY")
            # Add detailed debug info
            print(f"   URL available: {bool(self.supabase_url)}")
            print(f"   Key available: {bool(self.supabase_key)}")
    
    def get_next_sequence(self, prefix: str) -> Tuple[bool, int]:
        """
        Get next sequence number for a prefix
        
        Args:
            prefix: DC prefix (e.g., "AKDCAH")
            
        Returns:
            Tuple of (success, sequence_number)
        """
        if not self.enabled:
            print(f"❌ Supabase not enabled for sequence {prefix}")
            return False, 0
            
        try:
            # Use RPC function for atomic increment
            result = self.supabase.rpc('increment_sequence', {'seq_prefix': prefix}).execute()
            
            if result.data:
                sequence_num = result.data
                print(f"✅ Supabase: Got sequence {prefix}:{sequence_num:08d}")
                return True, sequence_num
            else:
                print(f"❌ Supabase: No sequence returned for {prefix}")
                return False, 0
                
        except Exception as e:
            print(f"❌ Supabase sequence error for {prefix}: {e}")
            return False, 0
    
    def get_current_sequences(self) -> Tuple[bool, Dict[str, int]]:
        """
        Get all current sequence numbers
        
        Returns:
            Tuple of (success, sequences_dict)
        """
        if not self.enabled:
            return False, {}
            
        try:
            result = self.supabase.table('dc_sequences').select('prefix,current_number').execute()
            
            if result.data:
                sequences = {row['prefix']: row['current_number'] for row in result.data}
                print(f"✅ Supabase: Retrieved {len(sequences)} sequences")
                return True, sequences
            else:
                print("❌ Supabase: No sequences found")
                return False, {}
                
        except Exception as e:
            print(f"❌ Supabase sequences fetch error: {e}")
            return False, {}
    
    def reset_sequence(self, prefix: str, value: int = 0) -> bool:
        """
        Reset a specific sequence to a value
        
        Args:
            prefix: DC prefix to reset
            value: Value to reset to (default: 0)
            
        Returns:
            True if successful
        """
        if not self.enabled:
            return False
            
        try:
            result = self.supabase.table('dc_sequences').update({
                'current_number': value,
                'last_updated': datetime.now().isoformat()
            }).eq('prefix', prefix).execute()
            
            if result.data:
                print(f"✅ Supabase: Reset {prefix} to {value}")
                return True
            else:
                print(f"❌ Supabase: Failed to reset {prefix}")
                return False
                
        except Exception as e:
            print(f"❌ Supabase reset error for {prefix}: {e}")
            return False
    
    def ensure_sequences_exist(self) -> bool:
        """
        Ensure all required sequence prefixes exist in database
        
        Returns:
            True if all sequences exist or were created
        """
        if not self.enabled:
            return False
            
        required_prefixes = ["AKDCAH", "AKDCSG", "BDDCAH", "BDDCSG", "SBDCAH", "SBDCSG"]
        
        try:
            # Get existing sequences
            success, existing = self.get_current_sequences()
            if not success:
                return False
            
            # Check for missing prefixes
            missing_prefixes = [p for p in required_prefixes if p not in existing]
            
            if missing_prefixes:
                print(f"🔧 Creating missing sequences: {missing_prefixes}")
                
                # Insert missing sequences
                for prefix in missing_prefixes:
                    result = self.supabase.table('dc_sequences').insert({
                        'prefix': prefix,
                        'current_number': 0,
                        'last_updated': datetime.now().isoformat()
                    }).execute()
                    
                    if result.data:
                        print(f"✅ Created sequence: {prefix}")
                    else:
                        print(f"❌ Failed to create sequence: {prefix}")
                        return False
            
            return True
            
        except Exception as e:
            print(f"❌ Error ensuring sequences exist: {e}")
            return False
    
    def health_check(self) -> Dict[str, any]:
        """
        Check Supabase connection health
        
        Returns:
            Health status dictionary
        """
        if not self.enabled:
            return {
                'status': 'disabled',
                'message': 'Supabase not configured',
                'sequences': {},
                'debug_info': {
                    'url_available': bool(self.supabase_url),
                    'key_available': bool(self.supabase_key)
                }
            }
        
        try:
            success, sequences = self.get_current_sequences()
            
            if success:
                return {
                    'status': 'healthy',
                    'message': 'Supabase connection working',
                    'sequences': sequences,
                    'total_sequences': sum(sequences.values())
                }
            else:
                return {
                    'status': 'error',
                    'message': 'Failed to fetch sequences',
                    'sequences': {}
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Health check failed: {e}',
                'sequences': {}
            }

# Global instance
supabase_sequence_service = SupabaseSequenceService() 