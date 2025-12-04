#!/usr/bin/env python3
"""
GitHub Sequence Sync - Automatically sync sequence state changes back to GitHub
Only runs in cloud environments (Streamlit Cloud)
"""

import os
import json
import base64
import requests
from datetime import datetime
from typing import Dict, Optional

class GitHubSequenceSync:
    """Sync sequence state changes back to GitHub repository"""
    
    def __init__(self):
        # Detect cloud environment first
        self.is_cloud = self._detect_cloud_environment()
        
        # GitHub configuration from environment variables
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.github_repo = os.getenv('GITHUB_REPO')
        self.github_branch = os.getenv('GITHUB_BRANCH', 'main')
        self.sequence_file_path = 'dc_sequence_state_v2.json'
        
        # GitHub API endpoints
        self.api_base = 'https://api.github.com'
        self.headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json'
        } if self.github_token else {}
        
        # Enable/disable based on environment and configuration
        self.enabled = self.is_cloud and bool(self.github_token and self.github_repo)
        
        if self.is_cloud:
            if not self.github_token:
                print("⚠️ Cloud environment detected but GITHUB_TOKEN not set - sync disabled")
            elif not self.github_repo:
                print("⚠️ Cloud environment detected but GITHUB_REPO not set - sync disabled")
            else:
                print("✅ GitHub sync enabled for cloud environment")
        else:
            print("🏠 Local environment - GitHub sync disabled")
    
    def _detect_cloud_environment(self) -> bool:
        """Detect if we're running in a cloud environment"""
        # Streamlit Cloud indicators
        streamlit_cloud_indicators = [
            'STREAMLIT_CLOUD',
            'STREAMLIT_SHARING',
            'STREAMLIT_SERVER_PORT',
            'STREAMLIT_SERVER_ADDRESS'
        ]
        
        # Check for any Streamlit Cloud indicators
        for indicator in streamlit_cloud_indicators:
            if os.getenv(indicator):
                return True
        
        # Check for other cloud platforms
        other_cloud_indicators = [
            'HEROKU',
            'RENDER',
            'RAILWAY',
            'VERCEL',
            'NETLIFY'
        ]
        
        for indicator in other_cloud_indicators:
            if os.getenv(indicator):
                return True
        
        # Check if running on a remote server (not localhost)
        server_address = os.getenv('STREAMLIT_SERVER_ADDRESS', 'localhost')
        if server_address != 'localhost' and server_address != '127.0.0.1':
            return True
        
        return False
    
    def get_file_sha(self) -> Optional[str]:
        """Get the current SHA of the sequence file on GitHub"""
        try:
            url = f"{self.api_base}/repos/{self.github_repo}/contents/{self.sequence_file_path}"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                return response.json()['sha']
            else:
                print(f"⚠️ Could not get file SHA: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error getting file SHA: {e}")
            return None
    
    def commit_sequence_state(self, sequence_data: Dict, commit_message: str = None) -> bool:
        """
        Commit sequence state changes back to GitHub
        
        Args:
            sequence_data: The sequence state data to commit
            commit_message: Optional custom commit message
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False
            
        try:
            # Get current file SHA
            file_sha = self.get_file_sha()
            if not file_sha:
                print("❌ Could not get file SHA - cannot commit")
                return False
            
            # Prepare file content
            file_content = json.dumps(sequence_data, indent=4)
            content_encoded = base64.b64encode(file_content.encode()).decode()
            
            # Prepare commit message
            if not commit_message:
                total_sequences = sum(sequence_data.get('sequences', {}).values())
                sequences_summary = ", ".join([f"{k}:{v}" for k, v in sequence_data.get('sequences', {}).items()])
                commit_message = f"Auto-sync: Update DC sequences [{sequences_summary}]"
            
            # Prepare commit data
            commit_data = {
                'message': commit_message,
                'content': content_encoded,
                'sha': file_sha,
                'branch': self.github_branch
            }
            
            # Make API request
            url = f"{self.api_base}/repos/{self.github_repo}/contents/{self.sequence_file_path}"
            response = requests.put(url, headers=self.headers, json=commit_data)
            
            if response.status_code == 200:
                print(f"✅ Successfully synced sequence state to GitHub")
                print(f"   Commit: {commit_message}")
                return True
            else:
                print(f"❌ Failed to sync to GitHub: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error syncing to GitHub: {e}")
            return False
    
    def sync_if_cloud(self, sequence_data: Dict) -> bool:
        """
        Sync to GitHub only if in cloud environment
        
        Args:
            sequence_data: The sequence state data to sync
            
        Returns:
            True if sync attempted (regardless of success), False if skipped
        """
        if not self.enabled:
            return False
            
        print("🌐 Cloud environment - syncing sequence state to GitHub...")
        return self.commit_sequence_state(sequence_data)

# Global instance
github_sync = GitHubSequenceSync() 