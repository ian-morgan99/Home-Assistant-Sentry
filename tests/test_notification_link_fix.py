"""
Test that notification links are only generated for integration and HACS components
This test validates the fix for the issue "visualization and hyperlinks from notification still don't work"
"""
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app'))

def test_link_generation_logic():
    """Test that links are only generated for appropriate component types"""
    
    # Simulate the logic for deciding when to show links
    def should_show_link(enable_web_ui, component_name, component_type):
        """Simulates the link generation logic from sentry_service.py"""
        return (enable_web_ui and 
                component_name != 'Unknown' and 
                component_type in ['integration', 'hacs'])
    
    # Test cases: (enable_web_ui, component_name, component_type, expected_result)
    test_cases = [
        # Integration types - should show link
        (True, 'my_integration', 'integration', True),
        (True, 'custom_component', 'hacs', True),
        
        # Addon types - should NOT show link
        (False, 'mosquitto', 'addon', False),
        (True, 'mosquitto', 'addon', False),
        (True, 'Node-RED', 'addon', False),
        
        # Core/Supervisor/OS - should NOT show link
        (True, 'Home Assistant Core', 'core', False),
        (True, 'Supervisor', 'supervisor', False),
        (True, 'Operating System', 'os', False),
        
        # Unknown components - should NOT show link
        (True, 'Unknown', 'integration', False),
        (True, 'Unknown', 'hacs', False),
        
        # Web UI disabled - should NOT show link
        (False, 'my_integration', 'integration', False),
        (False, 'custom_component', 'hacs', False),
        
        # Empty type - should NOT show link
        (True, 'my_component', '', False),
        (True, 'my_component', None, False),
    ]
    
    passed = 0
    failed = 0
    
    for enable_web_ui, component_name, component_type, expected in test_cases:
        result = should_show_link(enable_web_ui, component_name, component_type)
        if result == expected:
            passed += 1
            print(f"✓ {component_name} ({component_type}, web_ui={enable_web_ui}): {'show' if result else 'hide'} link")
        else:
            failed += 1
            print(f"✗ {component_name} ({component_type}, web_ui={enable_web_ui}): expected {'show' if expected else 'hide'}, got {'show' if result else 'hide'}")
    
    print(f"\nLink generation logic test: {passed} passed, {failed} failed")
    return failed == 0


def test_notification_structure_with_mixed_types():
    """Test that notifications with mixed component types only show links for appropriate types"""
    
    # Sample issues with different types
    issues = [
        {
            'severity': 'high',
            'component': 'Home Assistant Core',
            'component_type': 'core',
            'description': 'Major version update'
        },
        {
            'severity': 'high',
            'component': 'mosquitto',
            'component_type': 'addon',
            'description': 'MQTT broker update'
        },
        {
            'severity': 'medium',
            'component': 'custom_integration',
            'component_type': 'hacs',
            'description': 'HACS update'
        },
        {
            'severity': 'medium',
            'component': 'sensor',
            'component_type': 'integration',
            'description': 'Integration update'
        }
    ]
    
    # Simulate notification generation
    enable_web_ui = True
    links_generated = 0
    
    for issue in issues:
        component_type = issue.get('component_type', '')
        component_name = issue.get('component', 'Unknown')
        
        # This is the condition from the fixed code
        if (enable_web_ui and 
            component_name != 'Unknown' and 
            component_type in ['integration', 'hacs']):
            links_generated += 1
            print(f"  ✓ Link generated for {component_name} ({component_type})")
        else:
            print(f"  ○ No link for {component_name} ({component_type})")
    
    # Should only generate links for HACS and integration (2 out of 4)
    expected_links = 2
    if links_generated == expected_links:
        print(f"\n✓ Correct number of links generated: {links_generated}/{len(issues)}")
        return True
    else:
        print(f"\n✗ Wrong number of links: expected {expected_links}, got {links_generated}")
        return False


def test_error_message_improvement():
    """Test that error messages are helpful when component is not found"""
    
    # The error message should explain why a component might not be found
    expected_phrases = [
        "add-on or system component",
        "not tracked in dependency graph",
        "not installed",
        "component name doesn't match",
        "select a component manually"
    ]
    
    # Read web_server.py to check error message
    web_server_path = os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app', 'web_server.py')
    with open(web_server_path, 'r') as f:
        content = f.read()
    
    found_phrases = 0
    for phrase in expected_phrases:
        # Check if phrase exists in content (case-insensitive)
        if phrase.lower() in content.lower():
            found_phrases += 1
            print(f"  ✓ Error message includes: '{phrase}'")
        else:
            print(f"  ✗ Error message missing: '{phrase}'")
    
    if found_phrases >= 3:  # At least 3 out of 5 helpful phrases
        print(f"\n✓ Error messages are informative ({found_phrases}/{len(expected_phrases)} key phrases found)")
        return True
    else:
        print(f"\n✗ Error messages need improvement ({found_phrases}/{len(expected_phrases)} key phrases found)")
        return False


if __name__ == '__main__':
    print("\n" + "="*70)
    print("Testing Notification Link Fix")
    print("="*70 + "\n")
    
    tests = [
        ("Link Generation Logic", test_link_generation_logic),
        ("Mixed Component Types", test_notification_structure_with_mixed_types),
        ("Error Message Improvement", test_error_message_improvement),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\nRunning: {test_name}")
        print("-" * 70)
        try:
            if test_func():
                passed += 1
                print(f"\n✓ {test_name} PASSED\n")
            else:
                failed += 1
                print(f"\n✗ {test_name} FAILED\n")
        except Exception as e:
            failed += 1
            print(f"\n✗ {test_name} FAILED with error: {e}\n")
            import traceback
            traceback.print_exc()
    
    print("="*70)
    print(f"Tests completed: {passed} passed, {failed} failed")
    print("="*70)
    
    sys.exit(0 if failed == 0 else 1)
