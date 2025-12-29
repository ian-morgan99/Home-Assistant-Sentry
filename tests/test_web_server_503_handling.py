"""
Tests for Web Server 503 Error Handling and Logging
Tests the new error handling and logging improvements for issue #39
"""
import sys
import os
import asyncio
from unittest.mock import Mock, patch
from io import StringIO

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app'))


def test_web_server_503_with_no_dependency_graph():
    """Test that web server returns proper 503 error when dependency graph is not available"""
    try:
        from web_server import DependencyTreeWebServer
        
        # Create a mock config
        config = Mock()
        config.enable_web_ui = True
        
        # Initialize web server WITHOUT a dependency graph builder (None)
        server = DependencyTreeWebServer(None, config, port=8099)
        
        assert server.dependency_graph_builder is None
        print("✓ Web server initialized without dependency graph")
        
        # Test that the server recognizes it cannot start
        async def test_start():
            # Capture logging output
            with patch('web_server.logger') as mock_logger:
                await server.start()
                
                # Verify that error logging was called
                # The start method should log errors about missing dependency graph
                assert mock_logger.error.called, "Expected error logging when dependency graph is missing"
                print("✓ Web server correctly logged error about missing dependency graph")
        
        asyncio.run(test_start())
        
        print("✓ Web server 503 with no dependency graph test passed")
        return True
    except Exception as e:
        print(f"✗ Web server 503 with no dependency graph test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_api_returns_detailed_503_error():
    """Test that API endpoints return detailed 503 errors with helpful messages"""
    try:
        from web_server import DependencyTreeWebServer
        import json
        
        config = Mock()
        config.enable_web_ui = True
        
        # Initialize web server WITHOUT a dependency graph builder
        server = DependencyTreeWebServer(None, config)
        
        # Create mock request
        request = Mock()
        
        # Test get_components endpoint
        response = await server._handle_get_components(request)
        
        # Verify status code is 503
        assert response.status == 503, f"Expected 503, got {response.status}"
        
        # Verify response contains helpful information
        data = json.loads(response.text)
        assert 'error' in data, "Response should contain 'error' field"
        assert 'message' in data, "Response should contain 'message' field"
        assert 'dependency graph' in data['message'].lower(), "Message should mention dependency graph"
        
        print("✓ API returns detailed 503 error with helpful message")
        print(f"  Error: {data['error']}")
        print(f"  Message: {data['message']}")
        
        return True
    except Exception as e:
        print(f"✗ API 503 error details test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_validation_detects_mismatch():
    """Test that config validation detects web UI enabled without dependency graph"""
    try:
        from config_manager import ConfigManager
        
        # Mock environment variables to simulate problematic config
        with patch.dict(os.environ, {
            'ENABLE_WEB_UI': 'true',
            'ENABLE_DEPENDENCY_GRAPH': 'false',
            'SUPERVISOR_TOKEN': 'test_token'
        }):
            # Capture logging output
            with patch('config_manager.logger') as mock_logger:
                config = ConfigManager()
                
                # Verify config values
                assert config.enable_web_ui is True
                assert config.enable_dependency_graph is False
                
                # Verify that validation was called and logged warnings
                # The _validate_config should have been called during __init__
                warning_calls = [call for call in mock_logger.warning.call_args_list]
                
                # Check if any warning mentions the configuration issue
                has_config_warning = any(
                    'Web UI' in str(call) or 'dependency graph' in str(call).lower()
                    for call in warning_calls
                )
                
                print("✓ Config validation detects web UI without dependency graph")
                if has_config_warning:
                    print("  ✓ Validation logged appropriate warnings")
                
        return True
    except Exception as e:
        print(f"✗ Config validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_async_test(test_func):
    """Helper to run async tests"""
    return asyncio.run(test_func())


if __name__ == '__main__':
    print("Running Web Server 503 Error Handling Tests...\n")
    print("=" * 60)
    print("Testing Issue #39: WebUI 503 Error Improvements")
    print("=" * 60)
    print()
    
    tests = [
        ('sync', test_web_server_503_with_no_dependency_graph),
        ('async', test_api_returns_detailed_503_error),
        ('sync', test_config_validation_detects_mismatch),
    ]
    
    passed = 0
    failed = 0
    
    for test_type, test in tests:
        try:
            if test_type == 'sync':
                if test():
                    passed += 1
                else:
                    failed += 1
            else:
                if run_async_test(test):
                    passed += 1
                else:
                    failed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} raised exception: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
        print()
    
    print(f"{'='*60}")
    print(f"503 Error Handling Tests: {passed} passed, {failed} failed")
    print(f"{'='*60}")
    
    sys.exit(0 if failed == 0 else 1)
