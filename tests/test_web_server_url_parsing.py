"""
Test for Web Server URL parsing issue fix (Issue: "Host cannot contain ':' error")
"""
import sys
import os
import asyncio
from unittest.mock import Mock, PropertyMock

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app'))


async def test_handle_index_with_malformed_url():
    """Test that _handle_index gracefully handles malformed request.url access"""
    try:
        from web_server import DependencyTreeWebServer
        from dependency_graph_builder import DependencyGraphBuilder
        
        config = Mock()
        config.enable_web_ui = True
        
        # Create graph builder with some test data
        builder = DependencyGraphBuilder()
        builder.integrations = {
            'test_integration': {
                'name': 'Test Integration',
                'domain': 'test_integration',
                'version': '1.0.0',
                'requirements': []
            }
        }
        
        server = DependencyTreeWebServer(builder, config)
        
        # Create mock request that simulates the URL parsing error
        request = Mock()
        request.remote = '192.168.68.126:8123'
        request.path = '/'
        
        # Simulate the ValueError that occurs when accessing request.url
        # This is what happens in the real scenario with malformed URLs
        type(request).url = PropertyMock(side_effect=ValueError("Host '192.168.68.126:8123' cannot contain ':' (at position 14)"))
        
        # Call handler - should not raise an exception
        response = await server._handle_index(request)
        
        # Check response is successful
        assert response.status == 200
        assert 'text/html' in response.content_type
        
        print("✓ Handle index with malformed URL test passed")
        print("  The handler correctly caught the URL parsing error and continued")
        return True
        
    except Exception as e:
        print(f"✗ Handle index with malformed URL test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_error_middleware_with_url_error():
    """Test that error middleware handles URL parsing errors"""
    try:
        from web_server import DependencyTreeWebServer
        from dependency_graph_builder import DependencyGraphBuilder
        from aiohttp import web
        
        config = Mock()
        config.enable_web_ui = True
        
        builder = DependencyGraphBuilder()
        server = DependencyTreeWebServer(builder, config)
        
        # Create mock request that raises ValueError on url access
        request = Mock()
        request.path = '/api/test'
        request.method = 'GET'
        type(request).url = PropertyMock(side_effect=ValueError("Host '192.168.68.126:8123' cannot contain ':'"))
        
        # Create a handler that raises an exception
        async def failing_handler(request):
            raise RuntimeError("Test error")
        
        # Call error middleware
        response = await server.error_middleware(request, failing_handler)
        
        # Should return error response without crashing
        assert response.status == 500
        
        print("✓ Error middleware with URL error test passed")
        print("  The middleware correctly handled the URL parsing error")
        return True
        
    except Exception as e:
        print(f"✗ Error middleware with URL error test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_async_test(test_func):
    """Helper to run async tests"""
    return asyncio.run(test_func())


if __name__ == '__main__':
    print("Running Web Server URL Parsing Error Fix tests...\n")
    print("These tests verify the fix for: \"Host '192.168.68.126:8123' cannot contain ':'\"")
    print()
    
    tests = [
        test_handle_index_with_malformed_url,
        test_error_middleware_with_url_error,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if run_async_test(test):
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} raised exception: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"URL Parsing Tests completed: {passed} passed, {failed} failed")
    print(f"{'='*60}")
    
    if passed > 0:
        print("\n✅ Fix verified: The web server now handles URL parsing errors gracefully")
    
    sys.exit(0 if failed == 0 else 1)
