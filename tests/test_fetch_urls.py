"""
Test that fetch URLs in web_server.py use correct relative paths
This ensures the web UI works correctly when accessed via Home Assistant ingress
"""
import os
import re

def test_fetch_urls_are_relative():
    """Test that all fetch() calls use relative URLs that work with ingress"""
    # Read the web_server.py file
    web_server_path = os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app', 'web_server.py')
    with open(web_server_path, 'r') as f:
        content = f.read()
    
    # Find all fetch() calls in the JavaScript
    fetch_pattern = r"fetch\(['\"]([^'\"]+)['\"]"
    matches = re.findall(fetch_pattern, content)
    
    print(f"Found {len(matches)} fetch() calls")
    
    # Expected API endpoints
    expected_endpoints = [
        './api/components',
        './api/graph-data',
        # Note: dependency-tree, where-used, and change-impact use template literals
    ]
    
    # Check template literal patterns for remaining endpoints
    template_literal_pattern = r'fetch\(`([^`]+)`'
    template_matches = re.findall(template_literal_pattern, content)
    
    print(f"Found {len(template_matches)} fetch() calls with template literals")
    
    all_issues = []
    
    # Verify all fetch calls use ./api/ prefix for relative URLs
    for match in matches:
        if match.startswith('api/') and not match.startswith('./api/'):
            all_issues.append(f"Found fetch() call using 'api/' instead of './api/': {match}")
        else:
            print(f"  ✓ Static URL: {match}")
    
    for match in template_matches:
        # Extract the base path (before ${...})
        base_path = match.split('${')[0] if '${' in match else match
        if base_path.startswith('api/') and not base_path.startswith('./api/'):
            all_issues.append(f"Found fetch() call using 'api/' instead of './api/': {base_path}")
        else:
            print(f"  ✓ Template URL: {match}")
    
    if all_issues:
        print("\n❌ Issues found:")
        for issue in all_issues:
            print(f"  - {issue}")
        return False
    
    print("\n✅ All fetch() calls use correct relative URLs")
    return True

def test_api_endpoint_coverage():
    """Verify all API endpoints are using fetch with correct paths"""
    web_server_path = os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app', 'web_server.py')
    with open(web_server_path, 'r') as f:
        content = f.read()
    
    # Expected endpoints that should be fetched
    required_endpoints = [
        './api/components',
        './api/graph-data',
        './api/dependency-tree/',
        './api/where-used/',
        './api/change-impact',
    ]
    
    print("Checking for required API endpoints in fetch calls:")
    all_found = True
    
    for endpoint in required_endpoints:
        if endpoint in content:
            print(f"  ✓ Found: {endpoint}")
        else:
            print(f"  ✗ Missing: {endpoint}")
            all_found = False
    
    if all_found:
        print("\n✅ All required API endpoints are present")
        return True
    else:
        print("\n❌ Some API endpoints are missing")
        return False

def test_no_absolute_api_paths():
    """Ensure no fetch() calls use absolute paths that would break ingress"""
    web_server_path = os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app', 'web_server.py')
    with open(web_server_path, 'r') as f:
        content = f.read()
    
    # Find fetch calls with absolute paths starting with /api/
    absolute_pattern = r"fetch\(['\"][/]api/"
    matches = re.findall(absolute_pattern, content)
    
    if matches:
        print(f"❌ Found {len(matches)} fetch() calls with absolute paths:")
        for match in matches:
            print(f"  - {match}")
        print("\nAbsolute paths like '/api/...' may not work correctly with ingress!")
        return False
    
    print("✅ No fetch() calls use absolute paths")
    return True

if __name__ == '__main__':
    import sys
    
    print("\n" + "="*50)
    print("Testing Fetch URL Patterns in Web UI")
    print("="*50 + "\n")
    
    tests = [
        ("Fetch URLs Use Relative Paths", test_fetch_urls_are_relative),
        ("All API Endpoints Present", test_api_endpoint_coverage),
        ("No Absolute API Paths", test_no_absolute_api_paths),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\nRunning: {test_name}")
        print("-" * 50)
        try:
            if test_func():
                passed += 1
                print(f"✓ {test_name} PASSED\n")
            else:
                failed += 1
                print(f"✗ {test_name} FAILED\n")
        except Exception as e:
            failed += 1
            print(f"✗ {test_name} FAILED with error: {e}\n")
    
    print("="*50)
    print(f"Tests completed: {passed} passed, {failed} failed")
    print("="*50)
    
    sys.exit(0 if failed == 0 else 1)
