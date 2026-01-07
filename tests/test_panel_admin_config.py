"""
Test panel_admin configuration for ingress support
"""
import sys
import os
import json
import yaml

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app'))


def test_panel_admin_in_config_json():
    """Test that panel_admin is set to true in config.json"""
    try:
        config_path = os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'config.json')
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Check that panel_admin field exists
        assert 'panel_admin' in config, "panel_admin field missing from config.json"
        
        # Check that panel_admin is true (this is an admin tool)
        assert config['panel_admin'] is True, f"panel_admin should be true, got {config['panel_admin']}"
        
        # Verify ingress is enabled
        assert config.get('ingress') is True, "ingress must be enabled when using panel_admin"
        
        # Verify ingress_port is set
        assert 'ingress_port' in config, "ingress_port must be set when using ingress"
        assert config['ingress_port'] == 8099, f"ingress_port should be 8099, got {config['ingress_port']}"
        
        # Verify panel settings
        assert 'panel_icon' in config, "panel_icon should be set for sidebar display"
        assert 'panel_title' in config, "panel_title should be set for sidebar display"
        
        print("✓ panel_admin configuration test passed for config.json")
        print(f"  panel_admin: {config['panel_admin']}")
        print(f"  panel_title: {config['panel_title']}")
        print(f"  panel_icon: {config['panel_icon']}")
        print(f"  ingress: {config['ingress']}")
        print(f"  ingress_port: {config['ingress_port']}")
        return True
    except Exception as e:
        print(f"✗ panel_admin configuration test failed for config.json: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_panel_admin_in_config_yaml():
    """Test that panel_admin is set to true in config.yaml"""
    try:
        config_path = os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'config.yaml')
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Check that panel_admin field exists
        assert 'panel_admin' in config, "panel_admin field missing from config.yaml"
        
        # Check that panel_admin is true (this is an admin tool)
        assert config['panel_admin'] is True, f"panel_admin should be true, got {config['panel_admin']}"
        
        # Verify ingress is enabled
        assert config.get('ingress') is True, "ingress must be enabled when using panel_admin"
        
        # Verify ingress_port is set
        assert 'ingress_port' in config, "ingress_port must be set when using ingress"
        assert config['ingress_port'] == 8099, f"ingress_port should be 8099, got {config['ingress_port']}"
        
        # Verify panel settings
        assert 'panel_icon' in config, "panel_icon should be set for sidebar display"
        assert 'panel_title' in config, "panel_title should be set for sidebar display"
        
        print("✓ panel_admin configuration test passed for config.yaml")
        print(f"  panel_admin: {config['panel_admin']}")
        print(f"  panel_title: {config['panel_title']}")
        print(f"  panel_icon: {config['panel_icon']}")
        print(f"  ingress: {config['ingress']}")
        print(f"  ingress_port: {config['ingress_port']}")
        return True
    except Exception as e:
        print(f"✗ panel_admin configuration test failed for config.yaml: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_json_yaml_consistency():
    """Test that panel_admin is consistent between config.json and config.yaml"""
    try:
        json_path = os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'config.json')
        yaml_path = os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'config.yaml')
        
        with open(json_path, 'r') as f:
            json_config = json.load(f)
        
        with open(yaml_path, 'r') as f:
            yaml_config = yaml.safe_load(f)
        
        # Check consistency of panel_admin
        assert json_config.get('panel_admin') == yaml_config.get('panel_admin'), \
            f"panel_admin mismatch: JSON={json_config.get('panel_admin')}, YAML={yaml_config.get('panel_admin')}"
        
        # Check consistency of other ingress-related fields
        assert json_config.get('ingress') == yaml_config.get('ingress'), \
            f"ingress mismatch: JSON={json_config.get('ingress')}, YAML={yaml_config.get('ingress')}"
        
        assert json_config.get('ingress_port') == yaml_config.get('ingress_port'), \
            f"ingress_port mismatch: JSON={json_config.get('ingress_port')}, YAML={yaml_config.get('ingress_port')}"
        
        assert json_config.get('panel_icon') == yaml_config.get('panel_icon'), \
            f"panel_icon mismatch: JSON={json_config.get('panel_icon')}, YAML={yaml_config.get('panel_icon')}"
        
        assert json_config.get('panel_title') == yaml_config.get('panel_title'), \
            f"panel_title mismatch: JSON={json_config.get('panel_title')}, YAML={yaml_config.get('panel_title')}"
        
        print("✓ Configuration consistency test passed")
        print("  Both config.json and config.yaml have matching panel and ingress settings")
        return True
    except Exception as e:
        print(f"✗ Configuration consistency test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("Running panel_admin configuration tests...\n")
    
    tests = [
        test_panel_admin_in_config_json,
        test_panel_admin_in_config_yaml,
        test_config_json_yaml_consistency
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        print()
        if test():
            passed += 1
        else:
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"Tests completed: {passed} passed, {failed} failed")
    print(f"{'='*50}")
    
    sys.exit(0 if failed == 0 else 1)
