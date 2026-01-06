"""
Test WebUI API URL resolution for different access scenarios
This tests the getApiUrl() JavaScript function logic in Python
"""
import sys
import os
from urllib.parse import urlparse, urljoin

def get_api_url_python(path, window_location_pathname='/', window_location_origin='http://localhost:8099'):
    """
    Python implementation of the JavaScript getApiUrl() function
    to test the logic without needing a browser
    """
    # Sanitize path
    raw_path = path or ''
    sanitized_path = raw_path.lstrip('/').replace('//', '/')
    
    # Get base path from window location
    pathname = window_location_pathname or '/'
    base_path = pathname if pathname.endswith('/') else pathname + '/'
    base = window_location_origin + base_path
    
    # Use urljoin to combine
    return urljoin(base, sanitized_path)

def test_direct_access():
    """Test API URL resolution when accessing directly on port 8099"""
    print("\n=== Test 1: Direct Access (localhost:8099) ===")
    
    # Scenario: User accesses http://localhost:8099/
    # Expected: API calls should go to http://localhost:8099/api/status
    
    result = get_api_url_python(
        'api/status',
        window_location_pathname='/',
        window_location_origin='http://localhost:8099'
    )
    expected = 'http://localhost:8099/api/status'
    
    print(f"  Input: api/status")
    print(f"  Window pathname: /")
    print(f"  Window origin: http://localhost:8099")
    print(f"  Result: {result}")
    print(f"  Expected: {expected}")
    
    assert result == expected, f"Expected {expected}, got {result}"
    print("  ✓ PASS")
    return True

def test_ingress_access():
    """Test API URL resolution when accessing through HA ingress"""
    print("\n=== Test 2: Ingress Access (/api/hassio_ingress/ha_sentry/) ===")
    
    # Scenario: User accesses http://homeassistant.local:8123/api/hassio_ingress/ha_sentry/
    # Expected: API calls should go to http://homeassistant.local:8123/api/hassio_ingress/ha_sentry/api/status
    
    result = get_api_url_python(
        'api/status',
        window_location_pathname='/api/hassio_ingress/ha_sentry/',
        window_location_origin='http://homeassistant.local:8123'
    )
    expected = 'http://homeassistant.local:8123/api/hassio_ingress/ha_sentry/api/status'
    
    print(f"  Input: api/status")
    print(f"  Window pathname: /api/hassio_ingress/ha_sentry/")
    print(f"  Window origin: http://homeassistant.local:8123")
    print(f"  Result: {result}")
    print(f"  Expected: {expected}")
    
    assert result == expected, f"Expected {expected}, got {result}"
    print("  ✓ PASS")
    return True

def test_ingress_access_no_trailing_slash():
    """Test API URL resolution when pathname doesn't have trailing slash"""
    print("\n=== Test 3: Ingress Access (no trailing slash) ===")
    
    # Scenario: pathname might not have trailing slash
    # Expected: Function should add it and resolve correctly
    
    result = get_api_url_python(
        'api/status',
        window_location_pathname='/api/hassio_ingress/ha_sentry',
        window_location_origin='http://homeassistant.local:8123'
    )
    expected = 'http://homeassistant.local:8123/api/hassio_ingress/ha_sentry/api/status'
    
    print(f"  Input: api/status")
    print(f"  Window pathname: /api/hassio_ingress/ha_sentry")
    print(f"  Window origin: http://homeassistant.local:8123")
    print(f"  Result: {result}")
    print(f"  Expected: {expected}")
    
    assert result == expected, f"Expected {expected}, got {result}"
    print("  ✓ PASS")
    return True

def test_component_endpoint():
    """Test API URL for component list endpoint"""
    print("\n=== Test 4: Components Endpoint (ingress) ===")
    
    result = get_api_url_python(
        'api/components',
        window_location_pathname='/api/hassio_ingress/ha_sentry/',
        window_location_origin='http://homeassistant.local:8123'
    )
    expected = 'http://homeassistant.local:8123/api/hassio_ingress/ha_sentry/api/components'
    
    print(f"  Input: api/components")
    print(f"  Result: {result}")
    print(f"  Expected: {expected}")
    
    assert result == expected, f"Expected {expected}, got {result}"
    print("  ✓ PASS")
    return True

def test_root_path_case():
    """Test what happens if window.location.pathname is truly just /"""
    print("\n=== Test 5: Root Path (/) - Direct Access ===")
    
    # This is the case when accessing add-on directly via port
    result = get_api_url_python(
        'api/status',
        window_location_pathname='/',
        window_location_origin='http://localhost:8099'
    )
    expected = 'http://localhost:8099/api/status'
    
    print(f"  Input: api/status")
    print(f"  Window pathname: /")
    print(f"  Result: {result}")
    print(f"  Expected: {expected}")
    
    assert result == expected, f"Expected {expected}, got {result}"
    print("  ✓ PASS")
    return True

def test_api_with_leading_slash():
    """Test handling of API path with leading slash"""
    print("\n=== Test 6: API Path with Leading Slash ===")
    
    # User might call getApiUrl('/api/status') instead of 'api/status'
    result = get_api_url_python(
        '/api/status',  # Note: leading slash
        window_location_pathname='/api/hassio_ingress/ha_sentry/',
        window_location_origin='http://homeassistant.local:8123'
    )
    expected = 'http://homeassistant.local:8123/api/hassio_ingress/ha_sentry/api/status'
    
    print(f"  Input: /api/status (with leading slash)")
    print(f"  Result: {result}")
    print(f"  Expected: {expected}")
    
    assert result == expected, f"Expected {expected}, got {result}"
    print("  ✓ PASS")
    return True

def run_all_tests():
    """Run all test cases"""
    print("=" * 70)
    print("Testing WebUI getApiUrl() Function - Python Implementation")
    print("=" * 70)
    
    tests = [
        test_direct_access,
        test_ingress_access,
        test_ingress_access_no_trailing_slash,
        test_component_endpoint,
        test_root_path_case,
        test_api_with_leading_slash
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except AssertionError as e:
            print(f"  ✗ FAIL: {e}")
            failed += 1
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 70)
    
    return failed == 0

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
