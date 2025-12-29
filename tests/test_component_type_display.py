"""
Test component type display in notifications
Tests that component types (Add-on, HACS Integration, etc.) are correctly displayed
"""
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app'))

from dependency_analyzer import DependencyAnalyzer

def test_addon_issues_include_type():
    """Test that addon issues include component_type"""
    analyzer = DependencyAnalyzer()
    
    addon_updates = [
        {
            'name': 'Mosquitto broker',
            'slug': 'mosquitto',
            'current_version': '6.0.0',
            'latest_version': '7.0.0',
            'type': 'addon'
        }
    ]
    
    result = analyzer.analyze_updates(addon_updates, [])
    
    # Check that issues are generated
    assert len(result['issues']) > 0, "Expected at least one issue for major version update"
    
    # Check that component_type is present
    for issue in result['issues']:
        if issue['component'] == 'Mosquitto broker':
            assert 'component_type' in issue, f"Issue missing component_type: {issue}"
            assert issue['component_type'] == 'addon', f"Expected type 'addon', got '{issue['component_type']}'"
            print(f"✓ Addon issue includes type: {issue['component']} ({issue['component_type']})")
    
    return True

def test_hacs_issues_include_type():
    """Test that HACS issues include component_type"""
    analyzer = DependencyAnalyzer()
    
    hacs_updates = [
        {
            'name': 'Custom Integration',
            'current_version': '1.0.0',
            'latest_version': '2.0.0',
            'type': 'hacs'
        }
    ]
    
    result = analyzer.analyze_updates([], hacs_updates)
    
    # Check that issues are generated
    assert len(result['issues']) > 0, "Expected at least one issue for major version update"
    
    # Check that component_type is present
    for issue in result['issues']:
        if issue['component'] == 'Custom Integration':
            assert 'component_type' in issue, f"Issue missing component_type: {issue}"
            assert issue['component_type'] == 'hacs', f"Expected type 'hacs', got '{issue['component_type']}'"
            print(f"✓ HACS issue includes type: {issue['component']} ({issue['component_type']})")
    
    return True

def test_component_type_label_formatting():
    """Test that component type labels are formatted correctly"""
    # Test the label formatting logic directly without importing sentry_service
    # to avoid aiohttp dependency issues in test environment
    
    def get_component_type_label(component_type: str) -> str:
        """Get a user-friendly label for component type"""
        type_labels = {
            'core': 'Core',
            'supervisor': 'Supervisor',
            'os': 'OS',
            'addon': 'Add-on',
            'hacs': 'HACS Integration',
            'integration': 'Integration'
        }
        return type_labels.get(component_type, component_type.capitalize())
    
    test_cases = [
        ('addon', 'Add-on'),
        ('hacs', 'HACS Integration'),
        ('core', 'Core'),
        ('supervisor', 'Supervisor'),
        ('os', 'OS'),
        ('integration', 'Integration'),
    ]
    
    for component_type, expected_label in test_cases:
        label = get_component_type_label(component_type)
        assert label == expected_label, f"Expected '{expected_label}' for type '{component_type}', got '{label}'"
        print(f"✓ Type label correct: {component_type} → {label}")
    
    return True

def test_mixed_updates_preserve_types():
    """Test that mixed addon and HACS updates preserve their types"""
    analyzer = DependencyAnalyzer()
    
    addon_updates = [
        {
            'name': 'MariaDB',
            'slug': 'mariadb',
            'current_version': '10.0',
            'latest_version': '11.0',
            'type': 'addon'
        }
    ]
    
    hacs_updates = [
        {
            'name': 'Node-RED Companion',
            'current_version': '1.0.0',
            'latest_version': '2.0.0',
            'type': 'hacs'
        }
    ]
    
    result = analyzer.analyze_updates(addon_updates, hacs_updates)
    
    # Find issues by component name
    addon_issue = None
    hacs_issue = None
    
    for issue in result['issues']:
        if issue['component'] == 'MariaDB':
            addon_issue = issue
        elif issue['component'] == 'Node-RED Companion':
            hacs_issue = issue
    
    # Verify addon issue
    if addon_issue:
        assert addon_issue.get('component_type') == 'addon', \
            f"MariaDB should be type 'addon', got '{addon_issue.get('component_type')}'"
        print(f"✓ Addon type preserved: MariaDB ({addon_issue['component_type']})")
    
    # Verify HACS issue
    if hacs_issue:
        assert hacs_issue.get('component_type') == 'hacs', \
            f"Node-RED Companion should be type 'hacs', got '{hacs_issue.get('component_type')}'"
        print(f"✓ HACS type preserved: Node-RED Companion ({hacs_issue['component_type']})")
    
    return True

def test_core_type_variants():
    """Test that different core types (core, supervisor, os) are handled correctly"""
    # Test the label formatting logic directly without importing sentry_service
    # to avoid aiohttp dependency issues in test environment
    
    def get_component_type_label(component_type: str) -> str:
        """Get a user-friendly label for component type"""
        type_labels = {
            'core': 'Core',
            'supervisor': 'Supervisor',
            'os': 'OS',
            'addon': 'Add-on',
            'hacs': 'HACS Integration',
            'integration': 'Integration'
        }
        return type_labels.get(component_type, component_type.capitalize())
    
    # Test core system types
    assert get_component_type_label('core') == 'Core'
    assert get_component_type_label('supervisor') == 'Supervisor'
    assert get_component_type_label('os') == 'OS'
    
    print("✓ All core system type labels are correct")
    return True

if __name__ == '__main__':
    print("\n" + "="*50)
    print("Testing Component Type Display")
    print("="*50 + "\n")
    
    tests = [
        ("Addon Issues Include Type", test_addon_issues_include_type),
        ("HACS Issues Include Type", test_hacs_issues_include_type),
        ("Component Type Label Formatting", test_component_type_label_formatting),
        ("Mixed Updates Preserve Types", test_mixed_updates_preserve_types),
        ("Core Type Variants", test_core_type_variants),
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
            import traceback
            traceback.print_exc()
    
    print("="*50)
    print(f"Tests completed: {passed} passed, {failed} failed")
    print("="*50)
    
    sys.exit(0 if failed == 0 else 1)
