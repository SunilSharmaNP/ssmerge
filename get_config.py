#!/usr/bin/env python3
"""
Improved Config Fetcher with better error handling and security
"""

import os
import sys
import subprocess
import requests
from pathlib import Path
from dotenv import load_dotenv
from __init__ import LOGGER

class ConfigFetcher:
    """Enhanced configuration fetcher with better error handling"""
    
    def __init__(self):
        self.config_file = Path("config.env")
        self.timeout = 30  # Request timeout
        
    def fetch_remote_config(self, url: str) -> bool:
        """
        Fetch configuration from remote URL with proper error handling
        """
        try:
            if not url or len(url.strip()) == 0:
                LOGGER.warning("No CONFIG_FILE_URL provided, skipping remote config fetch")
                return False
                
            LOGGER.info(f"🔄 Fetching config from: {url[:50]}...")
            
            # Validate URL format
            if not url.startswith(('http://', 'https://')):
                raise ValueError("Invalid URL format. Must start with http:// or https://")
            
            # Make request with timeout and proper headers
            headers = {
                'User-Agent': 'MergeBot-ConfigFetcher/1.0',
                'Accept': 'text/plain',
            }
            
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()  # Raise exception for bad status codes
            
            # Validate content
            if not response.content:
                raise ValueError("Empty response from config URL")
            
            # Write config file
            with open(self.config_file, 'wb') as f:
                f.write(response.content)
                
            # Validate config file
            if not self._validate_config_file():
                raise ValueError("Downloaded config file is invalid")
                
            LOGGER.info("✅ Config fetched and validated successfully")
            return True
            
        except requests.exceptions.RequestException as e:
            LOGGER.error(f"❌ Network error fetching config: {e}")
            return False
        except ValueError as e:
            LOGGER.error(f"❌ Config validation error: {e}")
            return False
        except Exception as e:
            LOGGER.error(f"❌ Unexpected error fetching config: {e}")
            return False
    
    def _validate_config_file(self) -> bool:
        """
        Validate the config file contains required variables
        """
        try:
            if not self.config_file.exists():
                return False
                
            # Load and check for required variables
            load_dotenv(self.config_file, override=True)
            
            required_vars = ['API_HASH', 'BOT_TOKEN', 'TELEGRAM_API', 'OWNER']
            missing_vars = []
            
            for var in required_vars:
                if not os.getenv(var):
                    missing_vars.append(var)
            
            if missing_vars:
                LOGGER.error(f"❌ Missing required variables in config: {missing_vars}")
                return False
                
            LOGGER.info("✅ Config file validation passed")
            return True
            
        except Exception as e:
            LOGGER.error(f"❌ Config file validation failed: {e}")
            return False
    
    def update_from_upstream(self, repo_url: str, branch: str = "master") -> bool:
        """
        Update bot from upstream repository with better error handling
        """
        try:
            if not repo_url or len(repo_url.strip()) == 0:
                LOGGER.info("No UPSTREAM_REPO provided, skipping update")
                return False
                
            LOGGER.info(f"🔄 Updating from upstream: {repo_url}")
            
            # Remove existing git directory
            if os.path.exists('.git'):
                subprocess.run(['rm', '-rf', '.git'], check=True)
            
            # Git commands
            git_commands = [
                f"git init -q",
                f"git config --global user.email 'bot@mergebot.local'",
                f"git config --global user.name 'mergebot'", 
                f"git add .",
                f"git commit -sm 'update' -q",
                f"git remote add origin {repo_url}",
                f"git fetch origin -q",
                f"git reset --hard origin/{branch} -q"
            ]
            
            # Execute git update
            update_command = " && ".join(git_commands)
            result = subprocess.run(update_command, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                LOGGER.info("✅ Successfully updated from upstream repository")
                return True
            else:
                LOGGER.error(f"❌ Git update failed: {result.stderr}")
                return False
                
        except subprocess.CalledProcessError as e:
            LOGGER.error(f"❌ Command execution failed: {e}")
            return False
        except Exception as e:
            LOGGER.error(f"❌ Unexpected error during update: {e}")
            return False

def main():
    """Main function"""
    try:
        config_fetcher = ConfigFetcher()
        
        # Fetch remote config if URL is provided
        config_url = os.getenv('CONFIG_FILE_URL')
        if config_url:
            if not config_fetcher.fetch_remote_config(config_url):
                LOGGER.warning("⚠️ Failed to fetch remote config, using local config")
        
        # Load config
        load_dotenv("config.env", override=True)
        
        # Update from upstream if configured
        upstream_repo = os.getenv('UPSTREAM_REPO')
        upstream_branch = os.getenv('UPSTREAM_BRANCH', 'master')
        
        if upstream_repo:
            if not config_fetcher.update_from_upstream(upstream_repo, upstream_branch):
                LOGGER.warning("⚠️ Failed to update from upstream, continuing with current version")
        
        LOGGER.info("🎯 Configuration setup completed")
        return True
        
    except Exception as e:
        LOGGER.error(f"❌ Configuration setup failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
