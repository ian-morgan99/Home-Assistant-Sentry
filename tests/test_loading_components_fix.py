"""
Test for the loading components fix
Validates that status tracking and error handling work correctly
"""
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app'))


def test_status_tracking():
    """Test that status tracking fields exist and are properly initialized"""
    from sentry_service import SentryService
    
    # Create a minimal config
    class MockConfig:
        enable_dependency_graph = True
        enable_web_ui = True
        create_dashboard_entities = False
        auto_create_dashboard = False
        check_schedule = "02:00"
        ai_enabled = False
        save_reports = False
        
    config = MockConfig()
    service = SentryService(config)
    
    # Check that status tracking fields exist
    assert hasattr(service, '_graph_build_status'), "Missing _graph_build_status field"
    assert hasattr(service, '_graph_build_error'), "Missing _graph_build_error field"
    
    # Check initial status
    assert service._graph_build_status == 'not_started', f"Expected 'not_started', got '{service._graph_build_status}'"
    assert service._graph_build_error is None, "Error should be None initially"
    
    print("✓ Status tracking fields exist and are properly initialized")
    return True


def test_status_tracking_disabled():
    """Test status when dependency graph is disabled"""
    from sentry_service import SentryService
    
    class MockConfig:
        enable_dependency_graph = False
        enable_web_ui = False
        create_dashboard_entities = False
        auto_create_dashboard = False
        check_schedule = "02:00"
        ai_enabled = False
        save_reports = False
    
    config = MockConfig()
    service = SentryService(config)
    
    # Check that status is set to disabled
    assert service._graph_build_status == 'disabled', f"Expected 'disabled', got '{service._graph_build_status}'"
    
    print("✓ Status correctly set to 'disabled' when dependency graph is disabled")
    return True


def test_ingress_url_format():
    """Test that ingress URLs are generated correctly"""
    from sentry_service import SentryService
    
    class MockConfig:
        enable_dependency_graph = True
        enable_web_ui = True
        create_dashboard_entities = False
        auto_create_dashboard = False
        check_schedule = "02:00"
        ai_enabled = False
        save_reports = False
    
    config = MockConfig()
    service = SentryService(config)
    
    # Test base URL
    base_url = service._get_ingress_url()
    assert base_url == "/api/hassio_ingress/ha_sentry", f"Expected '/api/hassio_ingress/ha_sentry', got '{base_url}'"
    print(f"✓ Base ingress URL correct: {base_url}")
    
    # Test URL with fragment
    url_with_fragment = service._get_ingress_url() + "#whereused:component"
    assert "#whereused:component" in url_with_fragment, "Fragment not included"
    assert url_with_fragment.startswith("/api/hassio_ingress/ha_sentry"), "Base URL incorrect"
    print(f"✓ URL with fragment correct: {url_with_fragment}")
    
    # Test URL with path
    url_with_path = service._get_ingress_url("some/path")
    assert url_with_path == "/api/hassio_ingress/ha_sentry/some/path", f"Expected '/api/hassio_ingress/ha_sentry/some/path', got '{url_with_path}'"
    print(f"✓ URL with path correct: {url_with_path}")
    
    return True


def test_web_server_sentry_service_reference():
    """Test that web server can receive sentry service reference"""
    from web_server import DependencyTreeWebServer
    from dependency_graph_builder import DependencyGraphBuilder
    
    class MockConfig:
        enable_web_ui = True
        enable_dependency_graph = True
    
    class MockSentryService:
        _graph_build_status = 'building'
        _graph_build_error = None
    
    builder = DependencyGraphBuilder()
    config = MockConfig()
    sentry = MockSentryService()
    
    # Create web server with sentry service reference
    server = DependencyTreeWebServer(builder, config, port=8099, sentry_service=sentry)
    
    # Check that reference is stored
    assert server.sentry_service == sentry, "Sentry service reference not stored"
    assert hasattr(server.sentry_service, '_graph_build_status'), "Sentry service missing status field"
    
    print("✓ Web server correctly stores sentry service reference")
    return True


if __name__ == '__main__':
    print("\n" + "="*60)
    print("Testing Loading Components Fix")
    print("="*60 + "\n")
    
    tests = [
        ("Status Tracking Initialization", test_status_tracking),
        ("Status Tracking When Disabled", test_status_tracking_disabled),
        ("Ingress URL Format", test_ingress_url_format),
        ("Web Server Sentry Service Reference", test_web_server_sentry_service_reference),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\nRunning: {test_name}")
        print("-" * 60)
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
    
    print("="*60)
    print(f"Tests completed: {passed} passed, {failed} failed")
    print("="*60)
    
    sys.exit(0 if failed == 0 else 1)
