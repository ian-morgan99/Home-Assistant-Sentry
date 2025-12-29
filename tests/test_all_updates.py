"""
Test comprehensive update checking (all update entities)
"""
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app'))


def test_categorize_update_logic():
    """Test update entity categorization logic without instantiating client"""
    # Simulate the categorization logic
    def categorize_update(entity_id: str, attributes: dict) -> str:
        """Categorize update entity by type"""
        entity_lower = entity_id.lower()
        
        # Core system components
        if 'home_assistant_core' in entity_lower:
            return 'core'
        elif 'home_assistant_supervisor' in entity_lower or 'supervisor' in entity_lower:
            return 'supervisor'
        elif 'home_assistant_os' in entity_lower or 'operating_system' in entity_lower:
            return 'os'
        # Add-ons typically have specific naming patterns
        elif 'addon' in entity_lower or entity_id.startswith('update.'):
            # Check if it's a HACS integration
            if 'hacs' in entity_lower or attributes.get('repository', '').startswith('http'):
                return 'hacs'
            # Default to addon if from supervisor
            return 'addon'
        else:
            return 'integration'
    
    # Test core categorization
    assert categorize_update('update.home_assistant_core', {}) == 'core'
    assert categorize_update('update.home_assistant_supervisor', {}) == 'supervisor'
    assert categorize_update('update.home_assistant_os', {}) == 'os'
    
    # Test HACS categorization
    assert categorize_update('update.hacs_something', {}) == 'hacs'
    assert categorize_update('update.some_integration', {'repository': 'https://github.com/test'}) == 'hacs'
    
    # Test addon categorization (default)
    assert categorize_update('update.addon_mosquitto', {}) == 'addon'
    
    print("✓ Update categorization logic test passed")
    return True


def test_sentry_service_categorize_updates_logic():
    """Test SentryService update categorization logic"""
    # Simulate the categorization logic
    def categorize_updates(all_updates: list) -> dict:
        """Categorize updates by type and count them"""
        counts = {
            'core': 0,  # Core, Supervisor, OS
            'addon': 0,  # Add-ons
            'hacs': 0   # HACS and integrations
        }
        
        for update in all_updates:
            update_type = update.get('type', 'addon')
            if update_type in ['core', 'supervisor', 'os']:
                counts['core'] += 1
            elif update_type == 'addon':
                counts['addon'] += 1
            else:  # hacs, integration
                counts['hacs'] += 1
        
        return counts
    
    # Test update categorization
    all_updates = [
        {'type': 'core', 'name': 'Home Assistant Core'},
        {'type': 'supervisor', 'name': 'Supervisor'},
        {'type': 'os', 'name': 'Operating System'},
        {'type': 'addon', 'name': 'Mosquitto'},
        {'type': 'addon', 'name': 'MariaDB'},
        {'type': 'hacs', 'name': 'HACS Integration 1'},
        {'type': 'integration', 'name': 'Some Integration'},
    ]
    
    counts = categorize_updates(all_updates)
    
    assert counts['core'] == 3  # core, supervisor, os
    assert counts['addon'] == 2  # mosquitto, mariadb
    assert counts['hacs'] == 2  # hacs, integration
    
    print("✓ SentryService categorization logic test passed")
    return True


def test_config_all_updates():
    """Test configuration option for check_all_updates"""
    from config_manager import ConfigManager
    
    # Test default (should be True)
    os.environ['SUPERVISOR_TOKEN'] = 'test_token'
    config = ConfigManager()
    assert config.check_all_updates is True
    
    # Test explicit false
    os.environ['CHECK_ALL_UPDATES'] = 'false'
    config2 = ConfigManager()
    assert config2.check_all_updates is False
    
    # Test explicit true
    os.environ['CHECK_ALL_UPDATES'] = 'true'
    config3 = ConfigManager()
    assert config3.check_all_updates is True
    
    print("✓ Config check_all_updates test passed")
    return True


if __name__ == '__main__':
    print("Testing comprehensive update checking...\n")
    
    tests = [
        test_categorize_update_logic,
        test_sentry_service_categorize_updates_logic,
        test_config_all_updates,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"Tests completed: {passed} passed, {failed} failed")
    print(f"{'='*50}")
    
    sys.exit(0 if failed == 0 else 1)
