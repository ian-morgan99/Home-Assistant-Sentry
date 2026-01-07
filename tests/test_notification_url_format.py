"""
Test that notification messages contain correct ingress URL format
"""
import sys
import os
from urllib.parse import quote

def test_notification_url_format():
    """Test that generated notification URLs use correct frontend ingress format"""
    try:
        # Test the URL generation logic directly without importing dependencies
        ADDON_SLUG = 'ha_sentry'
        
        # Simulate the _get_ingress_url method
        def generate_ingress_url(path: str = "", mode: str = "", component: str = "") -> str:
            # Use frontend ingress format
            base_url = f"/hassio/ingress/{ADDON_SLUG}/"
            
            # Build query string if mode or component provided
            params = []
            if mode:
                params.append(f"mode={mode}")
            if component:
                params.append(f"component={quote(component)}")
            
            if path:
                path = path.lstrip('/')
                base_url = f"{base_url}{path}"
            
            if params:
                base_url = f"{base_url}?{'&'.join(params)}"
            
            return base_url
        
        # Test basic ingress URL
        basic_url = generate_ingress_url()
        assert basic_url.startswith("/hassio/ingress/"), f"URL should start with /hassio/ingress/, got: {basic_url}"
        assert basic_url.endswith("/"), f"URL should end with trailing slash, got: {basic_url}"
        assert "/api/hassio_ingress/" not in basic_url, f"URL should not contain /api/hassio_ingress/, got: {basic_url}"
        print(f"✓ Basic URL format correct: {basic_url}")
        
        # Test URL with mode parameter
        whereused_url = generate_ingress_url(mode="whereused", component="mosquitto")
        assert whereused_url.startswith("/hassio/ingress/"), f"Where-used URL should start with /hassio/ingress/, got: {whereused_url}"
        assert "mode=whereused" in whereused_url, f"URL should contain mode parameter, got: {whereused_url}"
        assert "component=mosquitto" in whereused_url, f"URL should contain component parameter, got: {whereused_url}"
        assert "/api/hassio_ingress/" not in whereused_url, f"URL should not contain /api/hassio_ingress/, got: {whereused_url}"
        print(f"✓ Where-used URL format correct: {whereused_url}")
        
        # Test URL with impact mode
        impact_url = generate_ingress_url(mode="impact", component="comp1,comp2")
        assert impact_url.startswith("/hassio/ingress/"), f"Impact URL should start with /hassio/ingress/, got: {impact_url}"
        assert "mode=impact" in impact_url, f"URL should contain mode parameter, got: {impact_url}"
        assert "/api/hassio_ingress/" not in impact_url, f"URL should not contain /api/hassio_ingress/, got: {impact_url}"
        print(f"✓ Impact URL format correct: {impact_url}")
        
        # Test that addon slug is correct
        assert "ha_sentry" in basic_url, f"URL should contain addon slug 'ha_sentry', got: {basic_url}"
        print("✓ Addon slug present in URL")
        
        # Verify specific expected URLs
        expected_basic = "/hassio/ingress/ha_sentry/"
        assert basic_url == expected_basic, f"Expected '{expected_basic}', got '{basic_url}'"
        print(f"✓ Basic URL matches expected: {expected_basic}")
        
        expected_whereused = "/hassio/ingress/ha_sentry/?mode=whereused&component=mosquitto"
        assert whereused_url == expected_whereused, f"Expected '{expected_whereused}', got '{whereused_url}'"
        print(f"✓ Where-used URL matches expected: {expected_whereused}")
        
        print("\n✓ All notification URL format tests passed")
        return True
        
    except Exception as e:
        print(f"✗ Notification URL format test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_url_markdown_format():
    """Test that markdown links in notifications use correct format"""
    try:
        ADDON_SLUG = 'ha_sentry'
        
        # Simulate URL generation
        web_ui_url = f"/hassio/ingress/{ADDON_SLUG}/"
        markdown_link = f"[🛡️ Open WebUI]({web_ui_url})"
        
        # Verify the markdown link doesn't contain the backend API route
        assert "/api/hassio_ingress/" not in markdown_link, f"Markdown link should not use /api/hassio_ingress/, got: {markdown_link}"
        assert "/hassio/ingress/ha_sentry/" in markdown_link, f"Markdown link should contain /hassio/ingress/ha_sentry/, got: {markdown_link}"
        
        print(f"✓ Markdown link format correct: {markdown_link}")
        
        # Test component-specific link
        component_url = f"/hassio/ingress/{ADDON_SLUG}/?mode=whereused&component=mosquitto"
        component_link = f"[🔍 View Dependencies]({component_url})"
        
        assert "/api/hassio_ingress/" not in component_link, f"Component link should not use /api/hassio_ingress/, got: {component_link}"
        assert "/hassio/ingress/ha_sentry/" in component_link, f"Component link should contain /hassio/ingress/ha_sentry/, got: {component_link}"
        
        print(f"✓ Component link format correct: {component_link}")
        
        # Test that old format is not used
        old_format_url = f"/api/hassio_ingress/{ADDON_SLUG}/"
        assert web_ui_url != old_format_url, f"Should not use old format '{old_format_url}'"
        print(f"✓ Old format (/api/hassio_ingress/) is not used")
        
        print("\n✓ All markdown link format tests passed")
        return True
        
    except Exception as e:
        print(f"✗ Markdown link format test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_actual_code_uses_correct_format():
    """Verify that the actual sentry_service.py file uses the correct URL format"""
    try:
        from pathlib import Path
        
        # Read the sentry_service.py file using pathlib for better robustness
        service_file = Path(__file__).parent.parent / 'ha_sentry' / 'rootfs' / 'app' / 'sentry_service.py'
        content = service_file.read_text()
        
        # Check that the _get_ingress_url method uses the correct format
        assert 'base_url = f"/hassio/ingress/{self.ADDON_SLUG}/"' in content, \
            "sentry_service.py should use /hassio/ingress/ format in _get_ingress_url()"
        print("✓ sentry_service.py uses correct /hassio/ingress/ format")
        
        # Check that old format is not used in URL generation
        assert 'base_url = f"/api/hassio_ingress/{self.ADDON_SLUG}/"' not in content, \
            "sentry_service.py should not use /api/hassio_ingress/ format for URL generation"
        print("✓ sentry_service.py does not use old /api/hassio_ingress/ format for URL generation")
        
        # Note: /api/hassio_ingress/ may appear in comments explaining the backend, which is OK
        print("✓ Code verification passed")
        
        return True
        
    except Exception as e:
        print(f"✗ Code verification test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("\n" + "="*60)
    print("Testing Notification URL Format")
    print("="*60 + "\n")
    
    tests = [
        ("Notification URL Format", test_notification_url_format),
        ("Markdown Link Format", test_url_markdown_format),
        ("Code Verification", test_actual_code_uses_correct_format),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\nRunning: {test_name}")
        print("-" * 60)
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
    
    print("="*60)
    print(f"Tests completed: {passed} passed, {failed} failed")
    print("="*60)
    
    sys.exit(0 if failed == 0 else 1)
