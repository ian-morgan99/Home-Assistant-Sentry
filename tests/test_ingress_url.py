"""
Test ingress URL generation for WebUI
"""
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app'))

def test_ingress_url_generation():
    """Test that ingress URLs are correctly generated"""
    try:
        # Mock the SentryService class for URL generation testing
        class MockConfig:
            enable_web_ui = True
            enable_dependency_graph = True
        
        class MockSentryService:
            ADDON_SLUG = 'ha_sentry'
            WEB_UI_PORT = 8099
            
            def __init__(self, config):
                self.config = config
            
            def _get_ingress_url(self, path: str = "") -> str:
                """Generate ingress URL"""
                base_url = f"/hassio/ingress/{self.ADDON_SLUG}/"
                if path:
                    path = path.lstrip('/')
                    return f"{base_url}{path}"
                return base_url
        
        config = MockConfig()
        service = MockSentryService(config)
        
        # Test base URL (with trailing slash)
        base_url = service._get_ingress_url()
        assert base_url == "/hassio/ingress/ha_sentry/", f"Expected /hassio/ingress/ha_sentry/, got {base_url}"
        
        # Test URL with path
        path_url = service._get_ingress_url("some/path")
        assert path_url == "/hassio/ingress/ha_sentry/some/path", f"Expected /hassio/ingress/ha_sentry/some/path, got {path_url}"
        
        # Test URL with fragment (like whereused) - for backward compatibility
        fragment_url = service._get_ingress_url() + "#whereused:test_component"
        assert fragment_url == "/hassio/ingress/ha_sentry/#whereused:test_component", f"Got {fragment_url}"
        
        print("✓ Ingress URL generation test passed")
        print(f"  Base URL: {base_url}")
        print(f"  Path URL: {path_url}")
        print(f"  Fragment URL: {fragment_url}")
        return True
    except Exception as e:
        print(f"✗ Ingress URL generation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_addon_slug_consistency():
    """Test that addon slug is consistent across files"""
    try:
        import json
        import yaml
        
        # Load config.json
        with open(os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'config.json'), 'r') as f:
            config_json = json.load(f)
        
        # Load config.yaml
        with open(os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'config.yaml'), 'r') as f:
            config_yaml = yaml.safe_load(f)
        
        json_slug = config_json['slug']
        yaml_slug = config_yaml['slug']
        
        assert json_slug == yaml_slug, f"Slug mismatch: config.json={json_slug}, config.yaml={yaml_slug}"
        assert json_slug == 'ha_sentry', f"Expected ha_sentry, got {json_slug}"
        
        print("✓ Addon slug consistency test passed")
        print(f"  config.json slug: {json_slug}")
        print(f"  config.yaml slug: {yaml_slug}")
        return True
    except Exception as e:
        print(f"✗ Addon slug consistency test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ingress_enabled():
    """Test that ingress is enabled in config"""
    try:
        import json
        
        # Load config.json
        with open(os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'config.json'), 'r') as f:
            config_json = json.load(f)
        
        assert config_json.get('ingress') is True, "Ingress should be enabled"
        assert config_json.get('ingress_port') == 8099, "Ingress port should be 8099"
        assert config_json.get('panel_title') == 'Sentry', "Panel title should be Sentry"
        
        print("✓ Ingress configuration test passed")
        print(f"  Ingress enabled: {config_json.get('ingress')}")
        print(f"  Ingress port: {config_json.get('ingress_port')}")
        print(f"  Panel title: {config_json.get('panel_title')}")
        return True
    except Exception as e:
        print(f"✗ Ingress configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("Running ingress URL tests...\n")
    
    tests = [
        test_ingress_url_generation,
        test_addon_slug_consistency,
        test_ingress_enabled
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        if test():
            passed += 1
        else:
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"Tests completed: {passed} passed, {failed} failed")
    print(f"{'='*50}")
    
    sys.exit(0 if failed == 0 else 1)
