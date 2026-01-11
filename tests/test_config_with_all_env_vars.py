"""Test that ConfigManager can read all environment variables properly"""
import os
import sys

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app'))


def test_config_manager_with_all_env_vars():
    """Test that ConfigManager properly reads all environment variables"""
    
    # Set all required environment variables
    test_env = {
        'AI_ENABLED': 'true',
        'AI_PROVIDER': 'ollama',
        'AI_ENDPOINT': 'http://localhost:11434',
        'AI_MODEL': 'llama2',
        'API_KEY': 'test-key',
        'CHECK_SCHEDULE': '02:00',
        'CREATE_DASHBOARD_ENTITIES': 'true',
        'CHECK_ALL_UPDATES': 'true',
        'CHECK_ADDONS': 'true',
        'CHECK_HACS': 'true',
        'SAFETY_THRESHOLD': '0.7',
        'LOG_LEVEL': 'standard',
        'OBFUSCATE_LOGS': 'true',
        'ENABLE_DEPENDENCY_GRAPH': 'true',
        'SAVE_REPORTS': 'true',
        'ENABLE_WEB_UI': 'true',
        'PORT': '8099',
        'CUSTOM_INTEGRATION_PATHS': '[]',
        'MONITOR_LOGS_AFTER_UPDATE': 'false',
        'LOG_CHECK_LOOKBACK_HOURS': '24',
        'SUPERVISOR_TOKEN': 'test-token'
    }
    
    # Save original environment
    original_env = {}
    for key in test_env:
        original_env[key] = os.environ.get(key)
    
    try:
        # Set test environment
        for key, value in test_env.items():
            os.environ[key] = value
        
        # Import and initialize ConfigManager
        from config_manager import ConfigManager
        config = ConfigManager()
        
        # Verify all values are correctly read
        assert config.ai_enabled == True, "ai_enabled should be True"
        assert config.ai_provider == 'ollama', "ai_provider should be 'ollama'"
        assert config.ai_endpoint == 'http://localhost:11434', "ai_endpoint mismatch"
        assert config.ai_model == 'llama2', "ai_model should be 'llama2'"
        assert config.api_key == 'test-key', "api_key mismatch"
        assert config.check_schedule == '02:00', "check_schedule should be '02:00'"
        assert config.create_dashboard_entities == True, "create_dashboard_entities should be True"
        assert config.check_all_updates == True, "check_all_updates should be True"
        assert config.check_addons == True, "check_addons should be True"
        assert config.check_hacs == True, "check_hacs should be True"
        assert config.safety_threshold == 0.7, "safety_threshold should be 0.7"
        assert config.log_level == 'standard', "log_level should be 'standard'"
        assert config.obfuscate_logs == True, "obfuscate_logs should be True"
        assert config.enable_dependency_graph == True, "enable_dependency_graph should be True"
        assert config.save_reports == True, "save_reports should be True"
        assert config.enable_web_ui == True, "enable_web_ui should be True"
        assert config.port == 8099, "port should be 8099"
        assert config.custom_integration_paths == [], "custom_integration_paths should be []"
        assert config.monitor_logs_after_update == False, "monitor_logs_after_update should be False"
        assert config.log_check_lookback_hours == 24, "log_check_lookback_hours should be 24"
        assert config.supervisor_token == 'test-token', "supervisor_token mismatch"
        
        print("✅ All ConfigManager properties correctly read from environment variables")
        
        # Test with web_ui disabled to ensure it doesn't cause issues
        os.environ['ENABLE_WEB_UI'] = 'false'
        config2 = ConfigManager()
        assert config2.enable_web_ui == False, "enable_web_ui should be False"
        print("✅ ConfigManager correctly handles enable_web_ui=false")
        
        # Test with obfuscate_logs disabled
        os.environ['OBFUSCATE_LOGS'] = 'false'
        config3 = ConfigManager()
        assert config3.obfuscate_logs == False, "obfuscate_logs should be False"
        print("✅ ConfigManager correctly handles obfuscate_logs=false")
        
        print("\n✅ All tests passed! ConfigManager properly reads all environment variables.")
        
    finally:
        # Restore original environment
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


if __name__ == "__main__":
    test_config_manager_with_all_env_vars()
