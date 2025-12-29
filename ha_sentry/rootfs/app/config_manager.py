"""
Configuration Manager for Home Assistant Sentry
"""
import json
import logging
import os

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
        self.auto_create_dashboard = self._get_bool_env('AUTO_CREATE_DASHBOARD', False)
        self.check_all_updates = self._get_bool_env('CHECK_ALL_UPDATES', True)
        self.check_addons = self._get_bool_env('CHECK_ADDONS', True)
        self.check_hacs = self._get_bool_env('CHECK_HACS', True)
        self.safety_threshold = float(os.getenv('SAFETY_THRESHOLD', '0.7'))
        self.log_level = os.getenv('LOG_LEVEL', 'standard').lower()
        self.supervisor_token = os.getenv('SUPERVISOR_TOKEN', '')
        
        # New configuration options for dependency graph and reporting
        self.enable_dependency_graph = self._get_bool_env('ENABLE_DEPENDENCY_GRAPH', True)
        self.save_reports = self._get_bool_env('SAVE_REPORTS', True)
        self.custom_integration_paths = self._parse_custom_paths()
        
        # Web UI configuration for dependency visualization
        self.enable_web_ui = self._get_bool_env('ENABLE_WEB_UI', True)
        
        # Home Assistant API configuration
        self.ha_url = 'http://supervisor/core'
        self.supervisor_url = 'http://supervisor'
        
        # Validate critical configuration
        if not self.supervisor_token:
            logger.warning("SUPERVISOR_TOKEN is not set! This will cause authentication failures.")
            logger.warning("The add-on requires 'homeassistant_api: true' in config.json to receive the token.")
        else:
            logger.debug(f"SUPERVISOR_TOKEN is set (length: {len(self.supervisor_token)})")
        
        logger.info(f"Configuration initialized: AI={self.ai_enabled}, Provider={self.ai_provider}, LogLevel={self.log_level}")
    
    def _get_bool_env(self, key: str, default: bool) -> bool:
        """Get boolean value from environment variable"""
        value = os.getenv(key, str(default)).lower()
        return value in ('true', '1', 'yes', 'on')
    
    def _parse_custom_paths(self) -> list:
        """Parse custom integration paths from environment variable"""
        paths_json = os.getenv('CUSTOM_INTEGRATION_PATHS', '[]')
        try:
            paths = json.loads(paths_json)
            if isinstance(paths, list):
                # Filter out empty strings and validate paths
                return [p for p in paths if p and isinstance(p, str)]
            return []
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse CUSTOM_INTEGRATION_PATHS: {paths_json}")
            return []
    
    def get_python_log_level(self) -> int:
        """Convert log_level string to Python logging level"""
        level_map = {
            'minimal': logging.ERROR,
            'standard': logging.INFO,
            'maximal': logging.DEBUG
        }
        return level_map.get(self.log_level, logging.INFO)
    
    @property
    def headers(self):
        """Get API headers for Home Assistant"""
        return {
            'Authorization': f'Bearer {self.supervisor_token}',
            'Content-Type': 'application/json'
        }
