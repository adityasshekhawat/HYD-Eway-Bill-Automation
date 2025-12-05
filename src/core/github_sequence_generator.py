#!/usr/bin/env python3
"""
GitHub Sequence Generator - Use GitHub repository as sequence database
BEST ALTERNATIVE FOR STREAMLIT CLOUD - No quota limits, version controlled
"""

import os
import json
import base64
import requests
import time
from typing import Dict
from datetime import datetime

class GitHubSequenceGenerator:
    """
    Sequence generator using GitHub repository as backend
    
    Features:
    - Free and unlimited (no quota issues like Google Drive)
    - Version controlled (audit trail built-in)
    - Works perfectly on Streamlit Cloud
    - No external service dependencies
    - Automatic conflict resolution with retry logic
    """
    
    def __init__(self):
        """Initialize GitHub sequence generator"""
        print("🔄 GitHubSequenceGenerator: Starting initialization...")
        
        # Get GitHub credentials
        self.github_token = self._get_github_token()
        self.github_repo = self._get_github_repo()
        self.github_branch = os.getenv('GITHUB_BRANCH', 'main')
        self.sequence_file_path = 'sequence_data.json'
        
        # GitHub API configuration
        self.api_base = 'https://api.github.com'
        self.headers = {
            'Authorization': f'Bearer {self.github_token}',
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json'
        }
        
        # Initialize or verify sequence file exists
        self._initialize_sequence_file()
        
        print("✅ GitHub sequence generator initialized successfully")
        print(f"   Repository: {self.github_repo}")
        print(f"   Branch: {self.github_branch}")
        print(f"   File: {self.sequence_file_path}")
    
    def _get_github_token(self) -> str:
        """Get GitHub token from environment or Streamlit secrets"""
        # Try environment variable first
        token = os.getenv('GITHUB_TOKEN')
        if token:
            print("✅ Using GitHub token from environment variable")
            return token
        
        # Try Streamlit secrets
        try:
            import streamlit as st
            if 'GITHUB_TOKEN' in st.secrets:
                print("✅ Using GitHub token from Streamlit secrets")
                return st.secrets['GITHUB_TOKEN']
        except (ImportError, KeyError, FileNotFoundError):
            pass
        
        raise ValueError(
            "GitHub token not found. Please set GITHUB_TOKEN in environment or Streamlit secrets. "
            "Get token from: https://github.com/settings/tokens"
        )
    
    def _get_github_repo(self) -> str:
        """Get GitHub repository from environment or Streamlit secrets"""
        # Try environment variable first
        repo = os.getenv('GITHUB_REPO')
        if repo:
            print(f"✅ Using GitHub repo from environment: {repo}")
            return repo
        
        # Try Streamlit secrets
        try:
            import streamlit as st
            if 'GITHUB_REPO' in st.secrets:
                repo = st.secrets['GITHUB_REPO']
                print(f"✅ Using GitHub repo from Streamlit secrets: {repo}")
                return repo
        except (ImportError, KeyError, FileNotFoundError):
            pass
        
        raise ValueError(
            "GitHub repository not found. Please set GITHUB_REPO (format: 'username/repo-name') "
            "in environment or Streamlit secrets."
        )
    
    def _get_file_from_github(self) -> tuple:
        """Get sequence file content and SHA from GitHub"""
        try:
            url = f"{self.api_base}/repos/{self.github_repo}/contents/{self.sequence_file_path}"
            params = {'ref': self.github_branch}
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                content = base64.b64decode(data['content']).decode('utf-8')
                return json.loads(content), data['sha']
            elif response.status_code == 404:
                # File doesn't exist yet
                return None, None
            else:
                raise Exception(f"GitHub API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Error getting file from GitHub: {e}")
            raise
    
    def _commit_file_to_github(self, content: dict, sha: str = None, message: str = None) -> bool:
        """Commit updated sequence file to GitHub"""
        try:
            # Prepare content
            file_content = json.dumps(content, indent=2)
            content_encoded = base64.b64encode(file_content.encode()).decode()
            
            # Prepare commit message
            if not message:
                message = f"Update sequences: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # Prepare request data
            commit_data = {
                'message': message,
                'content': content_encoded,
                'branch': self.github_branch
            }
            
            # Include SHA if updating existing file
            if sha:
                commit_data['sha'] = sha
            
            # Make API request
            url = f"{self.api_base}/repos/{self.github_repo}/contents/{self.sequence_file_path}"
            response = requests.put(url, headers=self.headers, json=commit_data)
            
            if response.status_code in [200, 201]:
                print(f"✅ Successfully committed to GitHub: {message}")
                return True
            else:
                print(f"❌ Failed to commit to GitHub: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error committing to GitHub: {e}")
            return False
    
    def _initialize_sequence_file(self):
        """Initialize sequence file if it doesn't exist"""
        try:
            content, sha = self._get_file_from_github()
            if content is None:
                # File doesn't exist, create it
                print("📝 Creating initial sequence file in GitHub...")
                initial_content = {
                    'sequences': {
                        'akdcah_seq': 300,
                        'akdcsg_seq': 300,
                        'akdchydnch_seq': 300,
                        'akdchydbal_seq': 300,
                        'akdchydbvg_seq': 300,
                        'bddcah_seq': 300,
                        'bddcsg_seq': 300,
                        'sbdcah_seq': 300,
                        'sbdcsg_seq': 300
                    },
                    'last_updated': datetime.now().isoformat(),
                    'version': '1.0'
                }
                self._commit_file_to_github(initial_content, message="Initialize DC sequence file")
                print("✅ Sequence file initialized in GitHub")
            else:
                print("✅ Sequence file exists in GitHub")
        except Exception as e:
            print(f"❌ Error initializing sequence file: {e}")
            raise
    
    def get_next_sequence(self, sequence_name: str, retry_count: int = 5) -> int:
        """
        Get next sequence value (increments atomically with retry logic)
        
        Args:
            sequence_name: Name of sequence (e.g., 'akdcah_seq')
            retry_count: Number of retries on conflict
            
        Returns:
            Next sequence number
        """
        for attempt in range(retry_count):
            try:
                # Get current file
                content, sha = self._get_file_from_github()
                
                if content is None:
                    raise Exception("Sequence file not found in GitHub")
                
                # Get current sequence value
                sequences = content.get('sequences', {})
                current_value = sequences.get(sequence_name, 300)
                
                # Calculate next value
                next_value = current_value + 1
                
                # Update content
                sequences[sequence_name] = next_value
                content['sequences'] = sequences
                content['last_updated'] = datetime.now().isoformat()
                content[f'{sequence_name}_history'] = content.get(f'{sequence_name}_history', [])
                content[f'{sequence_name}_history'].append({
                    'value': next_value,
                    'timestamp': datetime.now().isoformat()
                })
                # Keep only last 10 history entries
                content[f'{sequence_name}_history'] = content[f'{sequence_name}_history'][-10:]
                
                # Commit to GitHub
                message = f"Increment {sequence_name}: {current_value} → {next_value}"
                success = self._commit_file_to_github(content, sha, message)
                
                if success:
                    print(f"✅ Incremented {sequence_name}: {current_value} → {next_value}")
                    return next_value
                else:
                    raise Exception("Failed to commit to GitHub")
                    
            except Exception as e:
                if attempt < retry_count - 1:
                    wait_time = (attempt + 1) * 0.5  # Exponential backoff
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
            content, _ = self._get_file_from_github()
            
            if content is None:
                return 300  # Default value
            
            sequences = content.get('sequences', {})
            return sequences.get(sequence_name, 300)
            
        except Exception as e:
            print(f"⚠️ Error getting current sequence for {sequence_name}: {e}")
            return 300
    
    def get_all_sequences(self) -> Dict[str, int]:
        """Get all sequences as a dictionary"""
        try:
            content, _ = self._get_file_from_github()
            
            if content is None:
                return {}
            
            return content.get('sequences', {})
            
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
            content, sha = self._get_file_from_github()
            
            if content is None:
                content = {'sequences': {}, 'version': '1.0'}
                sha = None
            
            # Update sequence
            sequences = content.get('sequences', {})
            sequences[sequence_name] = value
            content['sequences'] = sequences
            content['last_updated'] = datetime.now().isoformat()
            
            # Commit
            message = f"Set {sequence_name} = {value} (manual update)"
            success = self._commit_file_to_github(content, sha, message)
            
            if success:
                print(f"✅ Set {sequence_name} = {value}")
                return True
            else:
                return False
                
        except Exception as e:
            print(f"❌ Error setting sequence: {e}")
            return False

