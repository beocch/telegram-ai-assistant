import json
import os
from typing import Dict, Any, Optional
from pathlib import Path

from ..utils.logger import get_logger

logger = get_logger(__name__)

class UserSettingsService:
    """Service for managing user settings and API keys"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.settings_file = self.data_dir / "user_settings.json"
        self.settings = self._load_settings()
    
    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from file"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading settings: {str(e)}")
            return {}
    
    def _save_settings(self):
        """Save settings to file"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving settings: {str(e)}")
    
    def get_user_api_keys(self, user_id: int) -> Dict[str, str]:
        """Get user's API keys"""
        user_key = str(user_id)
        return self.settings.get(user_key, {}).get('api_keys', {})
    
    def set_user_api_key(self, user_id: int, provider: str, api_key: str):
        """Set user's API key for specific provider"""
        user_key = str(user_id)
        if user_key not in self.settings:
            self.settings[user_key] = {}
        if 'api_keys' not in self.settings[user_key]:
            self.settings[user_key]['api_keys'] = {}
        
        self.settings[user_key]['api_keys'][provider] = api_key
        self._save_settings()
        logger.info(f"API key set for user {user_id}, provider {provider}")
    
    def remove_user_api_key(self, user_id: int, provider: str):
        """Remove user's API key for specific provider"""
        user_key = str(user_id)
        if user_key in self.settings and 'api_keys' in self.settings[user_key]:
            self.settings[user_key]['api_keys'].pop(provider, None)
            self._save_settings()
            logger.info(f"API key removed for user {user_id}, provider {provider}")
    
    def get_user_preferences(self, user_id: int) -> Dict[str, Any]:
        """Get user's preferences"""
        user_key = str(user_id)
        return self.settings.get(user_key, {}).get('preferences', {})
    
    def set_user_preference(self, user_id: int, key: str, value: Any):
        """Set user's preference"""
        user_key = str(user_id)
        if user_key not in self.settings:
            self.settings[user_key] = {}
        if 'preferences' not in self.settings[user_key]:
            self.settings[user_key]['preferences'] = {}
        
        self.settings[user_key]['preferences'][key] = value
        self._save_settings()
        logger.info(f"Preference set for user {user_id}: {key} = {value}")
    
    def get_user_provider(self, user_id: int) -> Optional[str]:
        """Get user's preferred AI provider"""
        preferences = self.get_user_preferences(user_id)
        return preferences.get('provider')
    
    def get_user_model(self, user_id: int) -> Optional[str]:
        """Get user's preferred AI model"""
        preferences = self.get_user_preferences(user_id)
        return preferences.get('model')
    
    def set_user_provider(self, user_id: int, provider: str):
        """Set user's preferred AI provider"""
        self.set_user_preference(user_id, 'provider', provider)
    
    def set_user_model(self, user_id: int, model: str):
        """Set user's preferred AI model"""
        self.set_user_preference(user_id, 'model', model)
    
    def has_api_key(self, user_id: int, provider: str) -> bool:
        """Check if user has API key for provider"""
        api_keys = self.get_user_api_keys(user_id)
        return provider in api_keys and api_keys[provider]
    
    def get_all_users(self) -> list:
        """Get list of all user IDs"""
        return [int(uid) for uid in self.settings.keys() if uid.isdigit()]
    
    def delete_user_data(self, user_id: int):
        """Delete all data for user"""
        user_key = str(user_id)
        if user_key in self.settings:
            del self.settings[user_key]
            self._save_settings()
            logger.info(f"All data deleted for user {user_id}")
    
    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Get user's usage statistics"""
        user_key = str(user_id)
        return self.settings.get(user_key, {}).get('stats', {})
    
    def update_user_stats(self, user_id: int, stats: Dict[str, Any]):
        """Update user's usage statistics"""
        user_key = str(user_id)
        if user_key not in self.settings:
            self.settings[user_key] = {}
        if 'stats' not in self.settings[user_key]:
            self.settings[user_key]['stats'] = {}
        
        self.settings[user_key]['stats'].update(stats)
        self._save_settings() 