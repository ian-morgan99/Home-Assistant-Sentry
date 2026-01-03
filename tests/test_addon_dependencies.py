"""
Test addon dependency tracking functionality
"""
import sys
import os
# Note: sys.path.insert used for test file portability
# In production, the app modules are in /app/ directory in the addon container
# For testing outside the container, we need to add the path explicitly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app'))

from dependency_graph_builder import DependencyGraphBuilder


def test_addon_tracking_structure():
    """Test that DependencyGraphBuilder has addon tracking structure"""
    builder = DependencyGraphBuilder()
    
    # Check that addons dict exists
    assert hasattr(builder, 'addons'), "Builder should have 'addons' attribute"
    assert isinstance(builder.addons, dict), "addons should be a dict"
    
    # Check that ha_client can be set
    assert hasattr(builder, 'ha_client'), "Builder should have 'ha_client' attribute"
    
    print("✓ Addon tracking structure test passed")


def test_addon_metadata_parsing():
    """Test addon metadata parsing"""
    builder = DependencyGraphBuilder()
    
    # Mock addon details
    addon_details = {
        'name': 'Test Addon',
        'version': '1.0.0',
        'repository': 'core',
        'homeassistant': '2024.11.0',
        'description': 'Test addon',
        'installed': True,
        'state': 'started'
    }
    
    # Parse the addon
    builder._parse_addon_metadata('test_addon', addon_details)
    
    # Check that addon was added
    assert 'test_addon' in builder.addons, "Addon should be added to builder"
    assert builder.addons['test_addon']['name'] == 'Test Addon'
    assert builder.addons['test_addon']['type'] == 'core_addon'
    assert builder.addons['test_addon']['homeassistant'] == '2024.11.0'
    
    print("✓ Addon metadata parsing test passed")


def test_dependency_map_with_addons():
    """Test that dependency map includes addon HA version requirements"""
    builder = DependencyGraphBuilder()
    
    # Add a mock addon
    builder.addons['test_addon'] = {
        'name': 'Test Addon',
        'slug': 'test_addon',
        'version': '1.0.0',
        'type': 'core_addon',
        'homeassistant': '2024.11.0',
        'repository': 'core',
        'description': 'Test',
        'installed': True,
        'state': 'started'
    }
    
    # Build dependency map
    builder._build_dependency_map()
    
    # Check that homeassistant_version is in dependency map
    assert 'homeassistant_version' in builder.dependency_map, "HA version should be in dependency map"
    
    # Check that the addon is listed as a user of HA version
    ha_users = builder.dependency_map['homeassistant_version']
    assert len(ha_users) == 1, "Should have 1 HA version user"
    assert ha_users[0]['integration'] == 'Test Addon'
    assert ha_users[0]['type'] == 'addon'
    assert ha_users[0]['specifier'] == '2024.11.0'
    
    print("✓ Dependency map with addons test passed")


def test_graph_structure_includes_addons():
    """Test that generated graph structure includes addon data"""
    builder = DependencyGraphBuilder()
    
    # Add a mock addon
    builder.addons['test_addon'] = {
        'name': 'Test Addon',
        'slug': 'test_addon',
        'version': '1.0.0',
        'type': 'core_addon',
        'homeassistant': '2024.11.0',
        'repository': 'core',
        'description': 'Test',
        'installed': True,
        'state': 'started'
    }
    
    # Build dependency map
    builder._build_dependency_map()
    
    # Generate graph structure
    graph = builder._generate_graph_structure()
    
    # Check that graph includes addon data
    assert 'addons' in graph, "Graph should include 'addons' key"
    assert 'test_addon' in graph['addons'], "Graph should include test addon"
    
    # Check statistics
    stats = graph.get('machine_readable', {}).get('statistics', {})
    assert 'total_addons' in stats, "Statistics should include total_addons"
    assert stats['total_addons'] == 1, "Should have 1 addon"
    
    print("✓ Graph structure includes addons test passed")


def main():
    """Run all addon dependency tests"""
    print("=" * 60)
    print("Running Addon Dependency Tracking Tests")
    print("=" * 60)
    print()
    
    tests = [
        test_addon_tracking_structure,
        test_addon_metadata_parsing,
        test_dependency_map_with_addons,
        test_graph_structure_includes_addons
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
    
    print()
    print("=" * 60)
    print(f"Tests completed: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
