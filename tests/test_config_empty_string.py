"""
Test for handling empty string in CUSTOM_INTEGRATION_PATHS configuration
Addresses issue where empty string causes JSON parsing warning
"""
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app'))


def test_empty_string_custom_paths():
    """Test that empty string in CUSTOM_INTEGRATION_PATHS doesn't cause warning"""
    # Save original environment variable if it exists
    original_value = os.environ.get('CUSTOM_INTEGRATION_PATHS')
    
    try:
        from config_manager import ConfigManager
        
        # Test with empty string (should not log warning, should return empty list)
        os.environ['CUSTOM_INTEGRATION_PATHS'] = ''
        config = ConfigManager()
        
        assert hasattr(config, 'custom_integration_paths')
        assert isinstance(config.custom_integration_paths, list)
        assert config.custom_integration_paths == []
        
        # Test with whitespace-only string
        os.environ['CUSTOM_INTEGRATION_PATHS'] = '   '
        config2 = ConfigManager()
        assert config2.custom_integration_paths == []
        
        print("✓ Empty string custom paths test passed")
        return True
    except Exception as e:
        print(f"✗ Empty string custom paths test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Restore original environment variable or remove if it didn't exist
        if original_value is not None:
            os.environ['CUSTOM_INTEGRATION_PATHS'] = original_value
        elif 'CUSTOM_INTEGRATION_PATHS' in os.environ:
            del os.environ['CUSTOM_INTEGRATION_PATHS']


if __name__ == '__main__':
    print("Testing empty string handling in CUSTOM_INTEGRATION_PATHS...\n")
    
    if test_empty_string_custom_paths():
        print("\n" + "="*50)
        print("Test passed!")
        print("="*50)
        sys.exit(0)
    else:
        print("\n" + "="*50)
        print("Test failed!")
        print("="*50)
        sys.exit(1)
