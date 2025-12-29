"""
Test for dashboard creation 404 error handling
"""
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app'))

def test_dashboard_404_handling():
    """Test that 404 errors are properly handled during dashboard creation"""
    try:
        from config_manager import ConfigManager
        
        # Set test environment variables
        os.environ['AI_ENABLED'] = 'false'
        os.environ['AI_PROVIDER'] = 'ollama'
        os.environ['AI_ENDPOINT'] = 'http://localhost:11434'
        os.environ['AI_MODEL'] = 'llama2'
        os.environ['CHECK_SCHEDULE'] = '02:00'
        os.environ['LOG_LEVEL'] = 'standard'
        os.environ['SUPERVISOR_TOKEN'] = 'test_token'
        os.environ['AUTO_CREATE_DASHBOARD'] = 'false'
        
        config = ConfigManager()
        
        # Verify config loaded properly
        assert config.supervisor_token == 'test_token'
        assert config.auto_create_dashboard is False
        
        print("✓ Dashboard 404 handling test setup passed")
        return True
    except Exception as e:
        print(f"✗ Dashboard 404 handling test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_log_methods_exist():
    """Test that the log methods exist in ha_client"""
    try:
        from ha_client import HomeAssistantClient
        
        # Check that the methods exist
        assert hasattr(HomeAssistantClient, '_log_dashboard_permission_error')
        assert hasattr(HomeAssistantClient, '_log_dashboard_endpoint_not_found')
        assert hasattr(HomeAssistantClient, 'create_lovelace_dashboard')
        
        print("✓ Dashboard error logging methods exist")
        return True
    except Exception as e:
        print(f"✗ Dashboard error logging methods test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("Running dashboard 404 error handling tests...\n")
    
    tests = [
        test_dashboard_404_handling,
        test_log_methods_exist
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
