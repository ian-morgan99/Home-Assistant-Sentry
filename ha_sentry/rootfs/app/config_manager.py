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
        self.check_all_updates = self._get_bool_env('CHECK_ALL_UPDATES', True)
        self.check_addons = self._get_bool_env('CHECK_ADDONS', True)
        self.check_hacs = self._get_bool_env('CHECK_HACS', True)
        self.safety_threshold = float(os.getenv('SAFETY_THRESHOLD', '0.7'))
        self.log_level = os.getenv('LOG_LEVEL', 'standard').lower()
        self.obfuscate_logs = self._get_bool_env('OBFUSCATE_LOGS', True)
        self.supervisor_token = os.getenv('SUPERVISOR_TOKEN', '')
        
        # New configuration options for dependency graph and reporting
        self.enable_dependency_graph = self._get_bool_env('ENABLE_DEPENDENCY_GRAPH', True)
        self.save_reports = self._get_bool_env('SAVE_REPORTS', True)
        self.custom_integration_paths = self._parse_custom_paths()
        
        # Web UI configuration for dependency visualization
        self.enable_web_ui = self._get_bool_env('ENABLE_WEB_UI', True)
        self.port = int(os.getenv('PORT', '8099'))
        
        # Log monitoring configuration
        self.monitor_logs_after_update = self._get_bool_env('MONITOR_LOGS_AFTER_UPDATE', False)
        self.log_check_lookback_hours = int(os.getenv('LOG_CHECK_LOOKBACK_HOURS', '24'))
        
        # Installation review configuration
        self.enable_installation_review = self._get_bool_env('ENABLE_INSTALLATION_REVIEW', False)
        self.installation_review_schedule = os.getenv('INSTALLATION_REVIEW_SCHEDULE', 'weekly').lower()
        self.installation_review_scope = os.getenv('INSTALLATION_REVIEW_SCOPE', 'full').lower()
        
        # Validate configuration consistency
        self._validate_config()
        
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
    
    def _validate_config(self):
        """Validate configuration for common issues and mismatches"""
        issues = []
        
        # Check for web UI without dependency graph
        if self.enable_web_ui and not self.enable_dependency_graph:
            issues.append({
                'severity': 'ERROR',
                'message': 'Web UI is enabled but dependency graph is disabled',
                'details': 'The web UI requires the dependency graph to function. You will get 503 errors when accessing the web UI.',
                'fix': 'Either enable "enable_dependency_graph: true" or disable "enable_web_ui: false"'
            })
        
        # Check if port matches expected ingress_port (8099)
        # The ingress_port in add-on metadata MUST match the actual server port
        # or Home Assistant ingress proxy will fail to connect
        if self.port != 8099:
            issues.append({
                'severity': 'WARNING',
                'message': f'Web UI port is set to {self.port} but ingress_port is hardcoded to 8099',
                'details': 'Home Assistant Supervisor expects the web server on port 8099 for ingress. Using a different port will break the ingress integration and sidebar panel access.',
                'fix': 'Set "port: 8099" in add-on configuration to match ingress_port'
            })
        
        # Log any configuration issues
        if issues:
            logger.warning("=" * 60)
            logger.warning("CONFIGURATION VALIDATION WARNINGS")
            logger.warning("=" * 60)
            for issue in issues:
                logger.warning(f"{issue['severity']}: {issue['message']}")
                logger.warning(f"  Details: {issue['details']}")
                logger.warning(f"  Fix: {issue['fix']}")
                logger.warning("")
            logger.warning("=" * 60)
        else:
            logger.debug("Configuration validation passed")
    
    def _get_bool_env(self, key: str, default: bool) -> bool:
        """Get boolean value from environment variable"""
        value = os.getenv(key, str(default)).lower()
        return value in ('true', '1', 'yes', 'on')
    
    def _parse_custom_paths(self) -> list:
        """Parse custom integration paths from environment variable"""
        paths_json = os.getenv('CUSTOM_INTEGRATION_PATHS', '[]')
        
        # Handle empty string explicitly - treat as empty array
        if not paths_json or paths_json.strip() == '':
            logger.debug("CUSTOM_INTEGRATION_PATHS is empty, using default paths")
            return []
        
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
