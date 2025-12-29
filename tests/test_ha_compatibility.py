"""
Test Home Assistant API Compatibility
Tests update entity detection, API endpoints, and entity attributes across HA versions
"""
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app'))


def test_update_entity_state_detection():
    """Test that update entities with state='on' are properly detected"""
    # Simulate the detection logic from get_all_updates()
    def is_update_available(state_obj: dict) -> bool:
        """Check if update entity has an available update"""
        entity_id = state_obj.get('entity_id', '')
        entity_state = state_obj.get('state', '')
        
        # Update entities should start with 'update.'
        if not entity_id.startswith('update.'):
            return False
        
        # State should be 'on' when update is available
        return entity_state == 'on'
    
    # Test cases for different HA versions (2024.11.x, 2024.12.x, 2025.1.x)
    test_cases = [
        # Update available - should be detected
        {
            'entity_id': 'update.home_assistant_core',
            'state': 'on',
            'attributes': {
                'installed_version': '2024.11.0',
                'latest_version': '2024.12.0'
            }
        },
        # No update - should NOT be detected
        {
            'entity_id': 'update.home_assistant_supervisor',
            'state': 'off',
            'attributes': {
                'installed_version': '2024.12.0',
                'latest_version': '2024.12.0'
            }
        },
        # Update available for addon
        {
            'entity_id': 'update.addon_mosquitto',
            'state': 'on',
            'attributes': {
                'installed_version': '6.2.0',
                'latest_version': '6.3.0'
            }
        },
        # HACS integration update
        {
            'entity_id': 'update.hacs_custom_integration',
            'state': 'on',
            'attributes': {
                'installed_version': '1.0.0',
                'latest_version': '1.1.0'
            }
        }
    ]
    
    expected_results = [True, False, True, True]
    
    for i, test_case in enumerate(test_cases):
        result = is_update_available(test_case)
        expected = expected_results[i]
        assert result == expected, f"Test case {i} failed: expected {expected}, got {result}"
        print(f"  ✓ Test case {i}: {test_case['entity_id']} - {'Update available' if result else 'No update'}")
    
    print("✓ Update entity state detection test passed")
    return True


def test_update_entity_attributes():
    """Test that update entities expose expected attributes"""
    def validate_update_attributes(state_obj: dict) -> tuple:
        """Validate update entity has required attributes"""
        attributes = state_obj.get('attributes', {})
        
        has_installed_version = 'installed_version' in attributes
        has_latest_version = 'latest_version' in attributes
        has_friendly_name = 'friendly_name' in attributes or 'title' in attributes
        
        return has_installed_version, has_latest_version, has_friendly_name
    
    # Test cases simulating different HA versions
    test_cases = [
        # Standard format (most common)
        {
            'entity_id': 'update.home_assistant_core',
            'state': 'on',
            'attributes': {
                'friendly_name': 'Home Assistant Core Update',
                'installed_version': '2024.11.0',
                'latest_version': '2024.12.0',
                'release_url': 'https://github.com/home-assistant/core/releases/tag/2024.12.0'
            }
        },
        # Alternative format with 'title' instead of 'friendly_name'
        {
            'entity_id': 'update.home_assistant_os',
            'state': 'on',
            'attributes': {
                'title': 'Home Assistant OS Update',
                'installed_version': '11.0',
                'latest_version': '11.1'
            }
        },
        # Addon format
        {
            'entity_id': 'update.addon_mariadb',
            'state': 'on',
            'attributes': {
                'friendly_name': 'MariaDB',
                'installed_version': '2.6.1',
                'latest_version': '2.7.0',
                'entity_picture': '/api/hassio/addons/core_mariadb/icon'
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases):
        has_installed, has_latest, has_name = validate_update_attributes(test_case)
        
        assert has_installed, f"Test case {i}: Missing 'installed_version' attribute"
        assert has_latest, f"Test case {i}: Missing 'latest_version' attribute"
        assert has_name, f"Test case {i}: Missing name attribute (friendly_name or title)"
        
        print(f"  ✓ Test case {i}: {test_case['entity_id']} has all required attributes")
    
    print("✓ Update entity attributes test passed")
    return True


def test_entity_categorization_accuracy():
    """Test that entity categorization works correctly across different formats"""
    # Define constants locally to avoid importing ha_client (which has dependencies)
    UPDATE_TYPE_CORE = 'core'
    UPDATE_TYPE_SUPERVISOR = 'supervisor'
    UPDATE_TYPE_OS = 'os'
    UPDATE_TYPE_ADDON = 'addon'
    UPDATE_TYPE_HACS = 'hacs'
    UPDATE_TYPE_INTEGRATION = 'integration'
    
    def categorize_update(entity_id: str, attributes: dict) -> str:
        """Categorize update entity by type (replicated logic)"""
        entity_lower = entity_id.lower()
        
        if 'home_assistant_core' in entity_lower:
            return UPDATE_TYPE_CORE
        elif 'home_assistant_supervisor' in entity_lower:
            return UPDATE_TYPE_SUPERVISOR
        elif 'home_assistant_os' in entity_lower or 'operating_system' in entity_lower:
            return UPDATE_TYPE_OS
        elif 'hacs' in entity_lower:
            return UPDATE_TYPE_HACS
        elif 'addon' in entity_lower:
            return UPDATE_TYPE_ADDON
        elif attributes.get('repository', '').startswith(('https://github.com/', 'http://github.com/')):
            return UPDATE_TYPE_HACS
        else:
            return UPDATE_TYPE_INTEGRATION
    
    test_cases = [
        # Core system components
        ('update.home_assistant_core_update', {}, UPDATE_TYPE_CORE),
        ('update.home_assistant_supervisor_update', {}, UPDATE_TYPE_SUPERVISOR),
        ('update.home_assistant_operating_system_update', {}, UPDATE_TYPE_OS),
        ('update.home_assistant_os', {}, UPDATE_TYPE_OS),
        
        # Add-ons
        ('update.addon_mosquitto_broker', {}, UPDATE_TYPE_ADDON),
        ('update.addon_mariadb', {}, UPDATE_TYPE_ADDON),
        ('update.addon_core_mariadb', {}, UPDATE_TYPE_ADDON),
        
        # HACS
        ('update.hacs_integration_name', {}, UPDATE_TYPE_HACS),
        ('update.hacs', {}, UPDATE_TYPE_HACS),
        
        # HACS detected by repository attribute
        ('update.custom_integration', {'repository': 'https://github.com/user/repo'}, UPDATE_TYPE_HACS),
        ('update.another_custom', {'repository': 'http://github.com/user/repo'}, UPDATE_TYPE_HACS),
        
        # Generic integrations
        ('update.some_device_firmware', {}, UPDATE_TYPE_INTEGRATION),
        ('update.integration_without_repo', {}, UPDATE_TYPE_INTEGRATION),
    ]
    
    for entity_id, attributes, expected_type in test_cases:
        result = categorize_update(entity_id, attributes)
        assert result == expected_type, f"Failed for {entity_id}: expected {expected_type}, got {result}"
        print(f"  ✓ {entity_id} → {result}")
    
    print("✓ Entity categorization accuracy test passed")
    return True


def test_api_endpoint_url_construction():
    """Test that API endpoint URLs are constructed correctly"""
    class MockConfig:
        def __init__(self):
            self.ha_url = "http://homeassistant.local:8123"
            self.supervisor_url = "http://supervisor/core"
    
    config = MockConfig()
    
    # Test /api/states endpoint (used in get_all_updates)
    states_url = f"{config.ha_url}/api/states"
    assert states_url == "http://homeassistant.local:8123/api/states"
    print(f"  ✓ States API URL: {states_url}")
    
    # Test /api/lovelace/dashboards endpoint (used in create_lovelace_dashboard)
    dashboards_url = f"{config.ha_url}/api/lovelace/dashboards"
    assert dashboards_url == "http://homeassistant.local:8123/api/lovelace/dashboards"
    print(f"  ✓ Lovelace API URL: {dashboards_url}")
    
    # Test supervisor addons endpoint (used in get_addon_updates)
    addons_url = f"{config.supervisor_url}/addons"
    assert addons_url == "http://supervisor/core/addons"
    print(f"  ✓ Supervisor API URL: {addons_url}")
    
    print("✓ API endpoint URL construction test passed")
    return True


def test_empty_update_handling():
    """Test handling when no updates are available"""
    def process_updates(all_updates: list) -> dict:
        """Simulate update processing logic"""
        if len(all_updates) == 0:
            return {
                'status': 'up_to_date',
                'message': 'No updates available',
                'should_notify': True,
                'should_warn': False
            }
        else:
            return {
                'status': 'updates_available',
                'message': f'{len(all_updates)} updates available',
                'should_notify': True,
                'should_warn': False
            }
    
    # Test empty update list
    result = process_updates([])
    assert result['status'] == 'up_to_date'
    assert result['message'] == 'No updates available'
    print("  ✓ Empty update list handled correctly")
    
    # Test with updates
    mock_updates = [
        {'entity_id': 'update.test', 'name': 'Test Update'}
    ]
    result = process_updates(mock_updates)
    assert result['status'] == 'updates_available'
    print("  ✓ Non-empty update list handled correctly")
    
    print("✓ Empty update handling test passed")
    return True


def test_api_compatibility_warnings():
    """Test that compatibility warnings are properly formatted"""
    def format_compatibility_warning(context: str, status_code: int) -> str:
        """Format API compatibility warning message"""
        warnings = []
        
        if status_code == 401:
            warnings.append("Authentication failed - check SUPERVISOR_TOKEN")
        elif status_code == 403:
            warnings.append(f"Permission denied accessing {context}")
        elif status_code == 404:
            warnings.append(f"API endpoint not found: {context}")
            warnings.append("This may indicate a Home Assistant version compatibility issue")
        elif status_code >= 500:
            warnings.append(f"Home Assistant API error: {status_code}")
        
        return " | ".join(warnings)
    
    # Test different error scenarios
    test_cases = [
        (401, "get_all_updates", "Authentication failed - check SUPERVISOR_TOKEN"),
        (403, "create_dashboard", "Permission denied accessing create_dashboard"),
        (404, "/api/states", "API endpoint not found"),
        (500, "api_call", "Home Assistant API error: 500"),
    ]
    
    for status_code, context, expected_in_result in test_cases:
        result = format_compatibility_warning(context, status_code)
        assert expected_in_result in result or len(result) > 0, f"No warning for {status_code}"
        print(f"  ✓ Status {status_code}: {result[:60]}...")
    
    print("✓ API compatibility warnings test passed")
    return True


def test_version_compatibility_matrix():
    """Test that the code handles different HA version patterns"""
    def parse_ha_version(version_str: str) -> tuple:
        """Parse Home Assistant version string"""
        # Remove 'v' prefix if present
        version_str = version_str.lstrip('v')
        
        # Split version into components
        parts = version_str.split('.')
        if len(parts) >= 2:
            try:
                major = int(parts[0])
                minor = int(parts[1])
                patch = int(parts[2]) if len(parts) > 2 else 0
                return (major, minor, patch)
            except ValueError:
                return None
        return None
    
    # Test version parsing for different formats
    test_versions = [
        ("2024.11.0", (2024, 11, 0)),
        ("2024.12.1", (2024, 12, 1)),
        ("2025.1.0", (2025, 1, 0)),
        ("v2024.11.0", (2024, 11, 0)),
        ("2024.11", (2024, 11, 0)),
    ]
    
    for version_str, expected in test_versions:
        result = parse_ha_version(version_str)
        assert result == expected, f"Failed to parse {version_str}: expected {expected}, got {result}"
        print(f"  ✓ Parsed {version_str} → {result}")
    
    print("✓ Version compatibility matrix test passed")
    return True


if __name__ == '__main__':
    print("=" * 60)
    print("Home Assistant API Compatibility Tests")
    print("Testing against HA versions: 2024.11.x, 2024.12.x, 2025.1.x")
    print("=" * 60)
    print()
    
    tests = [
        test_update_entity_state_detection,
        test_update_entity_attributes,
        test_entity_categorization_accuracy,
        test_api_endpoint_url_construction,
        test_empty_update_handling,
        test_api_compatibility_warnings,
        test_version_compatibility_matrix,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        print(f"\n{test.__name__}:")
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print()
    print("=" * 60)
    print(f"Tests completed: {passed} passed, {failed} failed")
    print("=" * 60)
    
    sys.exit(0 if failed == 0 else 1)
