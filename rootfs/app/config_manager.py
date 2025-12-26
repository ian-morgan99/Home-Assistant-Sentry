"""
Configuration Manager for Home Assistant Sentry
"""
import os
import logging

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages add-on configuration from environment variables"""
    
    def __init__(self):
        """Initialize configuration from environment variables"""
        self.ai_enabled = self._get_bool_env('AI_ENABLED', True)
        self.ai_provider = os.getenv('AI_PROVIDER', 'openai')
        self.ai_endpoint = os.getenv('AI_ENDPOINT', 'http://localhost:11434')
        self.ai_model = os.getenv('AI_MODEL', 'gpt-3.5-turbo')
        self.api_key = os.getenv('API_KEY', '')
        self.check_schedule = os.getenv('CHECK_SCHEDULE', '02:00')
        self.create_dashboard_entities = self._get_bool_env('CREATE_DASHBOARD_ENTITIES', True)
        self.check_addons = self._get_bool_env('CHECK_ADDONS', True)
        self.check_hacs = self._get_bool_env('CHECK_HACS', True)
        self.safety_threshold = float(os.getenv('SAFETY_THRESHOLD', '0.7'))
        self.supervisor_token = os.getenv('SUPERVISOR_TOKEN', '')
        
        # Home Assistant API configuration
        self.ha_url = 'http://supervisor/core'
        self.supervisor_url = 'http://supervisor'
        
        logger.info(f"Configuration initialized: AI={self.ai_enabled}, Provider={self.ai_provider}")
    
    def _get_bool_env(self, key: str, default: bool) -> bool:
        """Get boolean value from environment variable"""
        value = os.getenv(key, str(default)).lower()
        return value in ('true', '1', 'yes', 'on')
    
    @property
    def headers(self):
        """Get API headers for Home Assistant"""
        return {
            'Authorization': f'Bearer {self.supervisor_token}',
            'Content-Type': 'application/json'
        }
