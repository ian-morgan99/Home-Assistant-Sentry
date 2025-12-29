"""
Test Merge Conflict Regression
Tests coordinated behavior between fallback logic, diagnostics, and dependency graph features
Addresses issues identified in PR #34, #35, and #36
"""
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app'))

# Import the modules we need to test
from ha_client import HomeAssistantClient
from dependency_graph_builder import DependencyGraphBuilder


def test_fallback_categorization_consistency():
    """
    Test that fallback logic correctly categorizes updates into addon_updates and hacs_updates
    Regression test for sentry_service.py lines 227-237
    """
    # Simulate the categorization logic from sentry_service.py
    UPDATE_TYPE_CORE = 'core'
    UPDATE_TYPE_SUPERVISOR = 'supervisor'
    UPDATE_TYPE_OS = 'os'
    UPDATE_TYPE_ADDON = 'addon'
    UPDATE_TYPE_HACS = 'hacs'
    UPDATE_TYPE_INTEGRATION = 'integration'
    
    ADDON_ANALYSIS_TYPES = [UPDATE_TYPE_CORE, UPDATE_TYPE_SUPERVISOR, UPDATE_TYPE_OS, UPDATE_TYPE_ADDON]
    INTEGRATION_ANALYSIS_TYPES = [UPDATE_TYPE_HACS, UPDATE_TYPE_INTEGRATION]
    
    # Test case 1: Mixed updates from unified API
    all_updates = [
        {'name': 'Core', 'type': UPDATE_TYPE_CORE},
        {'name': 'Supervisor', 'type': UPDATE_TYPE_SUPERVISOR},
        {'name': 'Addon1', 'type': UPDATE_TYPE_ADDON},
        {'name': 'HACS1', 'type': UPDATE_TYPE_HACS},
        {'name': 'Integration1', 'type': UPDATE_TYPE_INTEGRATION},
    ]
    
    addon_updates = []
    hacs_updates = []
    
    # Apply the fixed categorization logic
    if len(all_updates) > 0:
        if len(addon_updates) == 0:
            addon_updates = [u for u in all_updates if u.get('type') in ADDON_ANALYSIS_TYPES]
        if len(hacs_updates) == 0:
            hacs_updates = [u for u in all_updates if u.get('type') in INTEGRATION_ANALYSIS_TYPES]
    
    assert len(addon_updates) == 3, f"Expected 3 addon updates, got {len(addon_updates)}"
    assert len(hacs_updates) == 2, f"Expected 2 hacs updates, got {len(hacs_updates)}"
    print("✓ Test case 1: Mixed updates categorized correctly")
    
    # Test case 2: Fallback scenario - addon_updates already populated
    all_updates = [
        {'name': 'Core', 'type': UPDATE_TYPE_CORE},
        {'name': 'HACS1', 'type': UPDATE_TYPE_HACS},
    ]
    addon_updates = [{'name': 'Fallback Addon', 'type': UPDATE_TYPE_ADDON}]  # Pre-populated from fallback
    hacs_updates = []
    
    # Apply the fixed categorization logic
    if len(all_updates) > 0:
        if len(addon_updates) == 0:
            addon_updates = [u for u in all_updates if u.get('type') in ADDON_ANALYSIS_TYPES]
        if len(hacs_updates) == 0:
            hacs_updates = [u for u in all_updates if u.get('type') in INTEGRATION_ANALYSIS_TYPES]
    
    # addon_updates should NOT be overwritten, but hacs_updates should be populated
    assert len(addon_updates) == 1, f"Expected 1 addon update (from fallback), got {len(addon_updates)}"
    assert addon_updates[0]['name'] == 'Fallback Addon', "Fallback addon should be preserved"
    assert len(hacs_updates) == 1, f"Expected 1 hacs update, got {len(hacs_updates)}"
    print("✓ Test case 2: Fallback addon preserved, hacs categorized correctly")
    
    # Test case 3: All updates from fallback
    all_updates = [
        {'name': 'Fallback Addon', 'type': UPDATE_TYPE_ADDON}
    ]
    addon_updates = [{'name': 'Fallback Addon', 'type': UPDATE_TYPE_ADDON}]
    hacs_updates = []
    
    # Apply the fixed categorization logic
    if len(all_updates) > 0:
        if len(addon_updates) == 0:
            addon_updates = [u for u in all_updates if u.get('type') in ADDON_ANALYSIS_TYPES]
        if len(hacs_updates) == 0:
            hacs_updates = [u for u in all_updates if u.get('type') in INTEGRATION_ANALYSIS_TYPES]
    
    assert len(addon_updates) == 1, "Fallback addon should be preserved"
    assert len(hacs_updates) == 0, "No hacs updates should be found"
    print("✓ Test case 3: All fallback scenario handled correctly")


def test_update_entity_validation_consistency():
    """
    Test that update entity validation is consistent
    Regression test for ha_client.py _validate_update_entity method
    """
    from ha_client import HomeAssistantClient
    
    # Create a mock config
    class MockConfig:
        def __init__(self):
            self.ha_url = "http://localhost:8123"
            self.supervisor_url = "http://supervisor"
            self.headers = {"Authorization": "Bearer test_token"}
    
    config = MockConfig()
    client = HomeAssistantClient(config)
    
    # Test case 1: Valid update entity
    valid_entity = 'update.home_assistant_core'
    valid_attributes = {
        'installed_version': '2024.11.0',
        'latest_version': '2024.12.0',
        'friendly_name': 'Home Assistant Core'
    }
    assert client._validate_update_entity(valid_entity, valid_attributes) is True
    print("✓ Valid update entity validated correctly")
    
    # Test case 2: Missing installed_version
    invalid_entity_1 = 'update.broken_addon'
    invalid_attributes_1 = {
        'latest_version': '1.0.0'
    }
    assert client._validate_update_entity(invalid_entity_1, invalid_attributes_1) is False
    print("✓ Entity missing installed_version rejected correctly")
    
    # Test case 3: Missing latest_version
    invalid_entity_2 = 'update.broken_addon'
    invalid_attributes_2 = {
        'installed_version': '1.0.0'
    }
    assert client._validate_update_entity(invalid_entity_2, invalid_attributes_2) is False
    print("✓ Entity missing latest_version rejected correctly")
    
    # Test case 4: Empty attributes
    invalid_entity_3 = 'update.broken_addon'
    invalid_attributes_3 = {}
    assert client._validate_update_entity(invalid_entity_3, invalid_attributes_3) is False
    print("✓ Entity with empty attributes rejected correctly")


def test_update_categorization_consistency():
    """
    Test that update categorization is consistent across different entity types
    Regression test for ha_client.py _categorize_update method
    """
    from ha_client import HomeAssistantClient
    from ha_client import (
        UPDATE_TYPE_CORE, UPDATE_TYPE_SUPERVISOR, UPDATE_TYPE_OS,
        UPDATE_TYPE_ADDON, UPDATE_TYPE_HACS, UPDATE_TYPE_INTEGRATION
    )
    
    class MockConfig:
        def __init__(self):
            self.ha_url = "http://localhost:8123"
            self.supervisor_url = "http://supervisor"
            self.headers = {"Authorization": "Bearer test_token"}
    
    config = MockConfig()
    client = HomeAssistantClient(config)
    
    # Test core components
    assert client._categorize_update('update.home_assistant_core', {}) == UPDATE_TYPE_CORE
    assert client._categorize_update('update.home_assistant_supervisor', {}) == UPDATE_TYPE_SUPERVISOR
    assert client._categorize_update('update.home_assistant_os', {}) == UPDATE_TYPE_OS
    assert client._categorize_update('update.home_assistant_operating_system', {}) == UPDATE_TYPE_OS
    print("✓ Core system components categorized correctly")
    
    # Test add-ons
    assert client._categorize_update('update.addon_mosquitto', {}) == UPDATE_TYPE_ADDON
    assert client._categorize_update('update.addon_vscode', {}) == UPDATE_TYPE_ADDON
    print("✓ Add-ons categorized correctly")
    
    # Test HACS integrations
    assert client._categorize_update('update.hacs_someintegration', {}) == UPDATE_TYPE_HACS
    assert client._categorize_update('update.custom_hacs_component', {}) == UPDATE_TYPE_HACS
    print("✓ HACS integrations categorized correctly")
    
    # Test GitHub repository attribute (indicates HACS)
    assert client._categorize_update('update.custom_integration', 
                                     {'repository': 'https://github.com/user/repo'}) == UPDATE_TYPE_HACS
    print("✓ GitHub repository attribute indicates HACS correctly")
    
    # Test default to integration
    assert client._categorize_update('update.some_integration', {}) == UPDATE_TYPE_INTEGRATION
    print("✓ Default integration categorization works")


def test_dependency_graph_path_logging_no_duplicates():
    """
    Test that dependency graph builder doesn't produce duplicate path logging
    Regression test for dependency_graph_builder.py lines 59-76
    """
    import logging
    from io import StringIO
    
    # Set up logging capture
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(levelname)s: %(message)s')
    handler.setFormatter(formatter)
    
    # Get the logger and add our handler
    logger = logging.getLogger('dependency_graph_builder')
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    
    # Create builder and try to build from non-existent paths
    builder = DependencyGraphBuilder()
    graph_data = builder.build_graph_from_paths(['/nonexistent/path1', '/nonexistent/path2'])
    
    # Get the log output
    log_output = log_capture.getvalue()
    
    # Check that we don't have duplicate "Path does not exist" messages at the same level
    lines = log_output.split('\n')
    debug_path_messages = [l for l in lines if 'DEBUG: Path does not exist: /nonexistent/path' in l]
    warning_path_messages = [l for l in lines if 'WARNING: Path does not exist: /nonexistent/path' in l]
    
    # We should have debug messages (one per path) but NO individual warning messages
    # (only the summary warning about missing paths)
    assert len(debug_path_messages) == 2, f"Expected 2 debug messages for missing paths, got {len(debug_path_messages)}"
    assert len(warning_path_messages) == 0, f"Expected 0 individual warning messages for missing paths, got {len(warning_path_messages)}"
    
    # Verify summary warning exists
    summary_warnings = [l for l in lines if 'WARNING: Missing' in l and 'path(s):' in l]
    assert len(summary_warnings) == 1, "Expected 1 summary warning message"
    
    print("✓ No duplicate path logging detected")
    
    # Clean up
    logger.removeHandler(handler)


def test_custom_paths_integration_with_fallback():
    """
    Test that custom integration paths work correctly with fallback mechanisms
    Regression test for interaction between PRs #34 and #36
    """
    # Create builder
    builder = DependencyGraphBuilder()
    
    # Test with default paths (some may not exist)
    default_graph = builder.build_graph_from_paths()
    assert 'machine_readable' in default_graph
    assert 'dependency_map' in default_graph
    print("✓ Default paths handled gracefully")
    
    # Test with custom non-existent paths
    custom_paths = ['/custom/path1', '/custom/path2']
    custom_graph = builder.build_graph_from_paths(custom_paths)
    assert 'machine_readable' in custom_graph
    assert custom_graph['machine_readable']['statistics']['total_integrations'] == 0
    print("✓ Custom non-existent paths handled gracefully")
    
    # Test with None (should use defaults)
    none_graph = builder.build_graph_from_paths(None)
    assert 'machine_readable' in none_graph
    print("✓ None paths default to standard paths")


if __name__ == '__main__':
    print("=" * 60)
    print("Merge Conflict Regression Tests")
    print("=" * 60)
    print()
    
    print("Test 1: Fallback categorization consistency")
    test_fallback_categorization_consistency()
    print()
    
    print("Test 2: Update entity validation consistency")
    test_update_entity_validation_consistency()
    print()
    
    print("Test 3: Update categorization consistency")
    test_update_categorization_consistency()
    print()
    
    print("Test 4: Dependency graph path logging (no duplicates)")
    test_dependency_graph_path_logging_no_duplicates()
    print()
    
    print("Test 5: Custom paths integration with fallback")
    test_custom_paths_integration_with_fallback()
    print()
    
    print("=" * 60)
    print("✅ ALL REGRESSION TESTS PASSED")
    print("=" * 60)
