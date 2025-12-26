"""
Basic tests for Home Assistant Sentry modules
"""
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'rootfs', 'app'))

def test_imports():
    """Test that all modules can be imported"""
    try:
        import config_manager
        import ha_client
        import ai_client
        import dashboard_manager
        import sentry_service
        print("✓ All modules imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

def test_config_manager():
    """Test ConfigManager initialization"""
    try:
        from config_manager import ConfigManager
        
        # Set test environment variables
        os.environ['AI_ENABLED'] = 'true'
        os.environ['AI_PROVIDER'] = 'ollama'
        os.environ['AI_ENDPOINT'] = 'http://localhost:11434'
        os.environ['AI_MODEL'] = 'llama2'
        os.environ['CHECK_SCHEDULE'] = '02:00'
        os.environ['SUPERVISOR_TOKEN'] = 'test_token'
        
        config = ConfigManager()
        
        assert config.ai_enabled is True
        assert config.ai_provider == 'ollama'
        assert config.ai_endpoint == 'http://localhost:11434'
        assert config.ai_model == 'llama2'
        assert config.check_schedule == '02:00'
        assert config.supervisor_token == 'test_token'
        
        print("✓ ConfigManager test passed")
        return True
    except Exception as e:
        print(f"✗ ConfigManager test failed: {e}")
        return False

def test_ai_client_init():
    """Test AIClient initialization"""
    try:
        from config_manager import ConfigManager
        from ai_client import AIClient
        
        config = ConfigManager()
        ai = AIClient(config)
        
        assert ai.config == config
        print("✓ AIClient initialization test passed")
        return True
    except Exception as e:
        print(f"✗ AIClient initialization test failed: {e}")
        return False

def test_fallback_analysis():
    """Test fallback analysis without AI"""
    try:
        from config_manager import ConfigManager
        from ai_client import AIClient
        
        # Set AI disabled
        os.environ['AI_ENABLED'] = 'false'
        config = ConfigManager()
        ai = AIClient(config)
        
        # Test with empty updates
        result = ai._fallback_analysis([], [])
        assert 'safe' in result
        assert 'confidence' in result
        assert 'issues' in result
        assert 'recommendations' in result
        assert 'summary' in result
        
        # Test with some updates
        addon_updates = [
            {'name': 'Test Addon', 'slug': 'test', 'current_version': '1.0', 'latest_version': '2.0'}
        ]
        result = ai._fallback_analysis(addon_updates, [])
        assert result['safe'] in (True, False)
        assert 0 <= result['confidence'] <= 1
        
        print("✓ Fallback analysis test passed")
        return True
    except Exception as e:
        print(f"✗ Fallback analysis test failed: {e}")
        return False

if __name__ == '__main__':
    print("Running Home Assistant Sentry tests...\n")
    
    tests = [
        test_imports,
        test_config_manager,
        test_ai_client_init,
        test_fallback_analysis
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        if test():
            passed += 1
        else:
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"Tests completed: {passed} passed, {failed} failed")
    print(f"{'='*50}")
    
    sys.exit(0 if failed == 0 else 1)
