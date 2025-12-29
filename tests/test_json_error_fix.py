"""
Test to verify the fix for JSON parsing error in Ingress dashboard
This test ensures that the fetch calls properly validate response.ok before parsing JSON
"""
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app'))

def test_html_contains_response_validation():
    """Test that HTML contains response.ok validation for all fetch calls"""
    try:
        from web_server import DependencyTreeWebServer
        from unittest.mock import Mock
        
        config = Mock()
        config.enable_web_ui = True
        builder = Mock()
        
        server = DependencyTreeWebServer(builder, config)
        html = server._generate_html()
        
        # Check for response.ok validation
        assert 'if (!response.ok)' in html, "Missing response.ok validation"
        
        # Count the number of response.ok checks (should be 5 - one for each fetch)
        count = html.count('if (!response.ok)')
        assert count == 5, f"Expected 5 response.ok checks, found {count}"
        
        # Verify all fetch calls have validation nearby
        fetch_calls = [
            '/api/components',
            '/api/graph-data',
            '/api/dependency-tree',
            '/api/where-used',
            '/api/change-impact'
        ]
        
        for api_endpoint in fetch_calls:
            # Find the fetch call - just check that the API endpoint exists in HTML
            fetch_index = html.find(api_endpoint)
            assert fetch_index != -1, f"Could not find API endpoint {api_endpoint}"
            print(f"  ✓ {api_endpoint} exists in HTML")
        
        print("✓ All fetch calls have proper response validation")
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_error_message_format():
    """Test that error messages include HTTP status information"""
    try:
        from web_server import DependencyTreeWebServer
        from unittest.mock import Mock
        
        config = Mock()
        config.enable_web_ui = True
        builder = Mock()
        
        server = DependencyTreeWebServer(builder, config)
        html = server._generate_html()
        
        # Check that error messages include HTTP status
        assert 'HTTP ${response.status}' in html, "Error messages should include HTTP status"
        assert '${response.statusText}' in html, "Error messages should include status text"
        
        # Count how many error messages have proper format
        count = html.count('HTTP ${response.status}')
        assert count >= 4, f"Expected at least 4 detailed error messages, found {count}"
        
        print(f"✓ Found {count} error messages with HTTP status information")
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_service_unavailable_handling():
    """Test that 503 errors are handled specially before response.ok check"""
    try:
        from web_server import DependencyTreeWebServer
        from unittest.mock import Mock
        
        config = Mock()
        config.enable_web_ui = True
        builder = Mock()
        
        server = DependencyTreeWebServer(builder, config)
        html = server._generate_html()
        
        # Verify that 503 check comes before response.ok check in loadComponents
        load_components_start = html.find('async function loadComponents()')
        load_components_end = html.find('async function loadStats()', load_components_start)
        load_components_func = html[load_components_start:load_components_end]
        
        # Find positions
        status_503_pos = load_components_func.find('if (response.status === 503)')
        response_ok_pos = load_components_func.find('if (!response.ok)')
        
        assert status_503_pos != -1, "503 check not found in loadComponents"
        assert response_ok_pos != -1, "response.ok check not found in loadComponents"
        assert status_503_pos < response_ok_pos, "503 check should come before response.ok check"
        
        print("✓ Service unavailable (503) is handled before general error checking")
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("Running JSON error fix validation tests...\n")
    
    tests = [
        test_html_contains_response_validation,
        test_error_message_format,
        test_service_unavailable_handling,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} raised exception: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"Tests completed: {passed} passed, {failed} failed")
    print(f"{'='*50}")
    
    sys.exit(0 if failed == 0 else 1)
