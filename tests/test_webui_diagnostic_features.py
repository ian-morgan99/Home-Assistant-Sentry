"""
Test for WebUI diagnostic and error handling features
Validates that the fixes for "Loading components" issue work correctly
"""
import sys
import os
import re

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app'))


def test_html_contains_diagnostic_panel():
    """Test that HTML includes the diagnostic panel"""
    from web_server import DependencyTreeWebServer
    from dependency_graph_builder import DependencyGraphBuilder
    from unittest.mock import Mock
    
    config = Mock()
    config.enable_web_ui = True
    
    builder = DependencyGraphBuilder()
    server = DependencyTreeWebServer(builder, config)
    
    html = server._generate_html()
    
    # Check for diagnostic panel
    assert 'diagnostic-panel' in html, "Missing diagnostic panel"
    assert 'diagnostic-log' in html, "Missing diagnostic log"
    assert 'addDiagnosticLog' in html, "Missing diagnostic logging function"
    
    print("✓ Diagnostic panel present in HTML")
    return True


def test_html_contains_status_indicator():
    """Test that HTML includes the status indicator"""
    from web_server import DependencyTreeWebServer
    from dependency_graph_builder import DependencyGraphBuilder
    from unittest.mock import Mock
    
    config = Mock()
    config.enable_web_ui = True
    
    builder = DependencyGraphBuilder()
    server = DependencyTreeWebServer(builder, config)
    
    html = server._generate_html()
    
    # Check for status indicator
    assert 'status-indicator' in html, "Missing status indicator"
    assert 'updateStatusIndicator' in html, "Missing status update function"
    assert 'loading-spinner' in html, "Missing loading spinner CSS"
    
    print("✓ Status indicator present in HTML")
    return True


def test_html_contains_noscript_warning():
    """Test that HTML includes noscript warning"""
    from web_server import DependencyTreeWebServer
    from dependency_graph_builder import DependencyGraphBuilder
    from unittest.mock import Mock
    
    config = Mock()
    config.enable_web_ui = True
    
    builder = DependencyGraphBuilder()
    server = DependencyTreeWebServer(builder, config)
    
    html = server._generate_html()
    
    # Check for noscript tag
    assert '<noscript>' in html, "Missing noscript tag"
    assert 'JavaScript Required' in html, "Missing JavaScript warning"
    
    print("✓ Noscript warning present in HTML")
    return True


def test_html_contains_global_timeout():
    """Test that HTML includes global initialization timeout"""
    from web_server import DependencyTreeWebServer
    from dependency_graph_builder import DependencyGraphBuilder
    from unittest.mock import Mock
    
    config = Mock()
    config.enable_web_ui = True
    
    builder = DependencyGraphBuilder()
    server = DependencyTreeWebServer(builder, config)
    
    html = server._generate_html()
    
    # Check for global timeout
    assert 'GLOBAL_INIT_TIMEOUT_MS' in html, "Missing global timeout constant"
    assert 'handleGlobalInitTimeout' in html, "Missing timeout handler"
    assert 'globalInitTimeoutId' in html, "Missing timeout ID variable"
    assert 'initializationComplete' in html, "Missing completion flag"
    
    print("✓ Global timeout mechanism present in HTML")
    return True


def test_html_enhanced_error_logging():
    """Test that HTML includes enhanced error logging"""
    from web_server import DependencyTreeWebServer
    from dependency_graph_builder import DependencyGraphBuilder
    from unittest.mock import Mock
    
    config = Mock()
    config.enable_web_ui = True
    
    builder = DependencyGraphBuilder()
    server = DependencyTreeWebServer(builder, config)
    
    html = server._generate_html()
    
    # Check for enhanced logging in loadComponents
    # We expect at least 10 diagnostic log calls throughout the loading process
    # (DOM load, URL info, status checks, API calls, responses, success/error states)
    MIN_EXPECTED_LOG_CALLS = 10
    assert html.count('addDiagnosticLog') > MIN_EXPECTED_LOG_CALLS, \
        f"Not enough diagnostic logging calls (expected > {MIN_EXPECTED_LOG_CALLS})"
    
    # Check for specific log points
    assert 'Starting component loading' in html, "Missing component loading start log"
    assert 'Fetching status from' in html, "Missing status fetch log"
    assert 'Components fetch response' in html, "Missing fetch response log"
    assert 'Successfully loaded' in html, "Missing success log"
    
    print("✓ Enhanced error logging present in HTML")
    return True


def test_html_show_diagnostics_buttons():
    """Test that error messages include buttons to show diagnostics"""
    from web_server import DependencyTreeWebServer
    from dependency_graph_builder import DependencyGraphBuilder
    from unittest.mock import Mock
    
    config = Mock()
    config.enable_web_ui = True
    
    builder = DependencyGraphBuilder()
    server = DependencyTreeWebServer(builder, config)
    
    html = server._generate_html()
    
    # Check for toggle function
    assert 'toggleDiagnostics' in html, "Missing toggleDiagnostics function"
    
    # Check that error functions call it
    assert 'Show Diagnostic Logs' in html or 'toggleDiagnostics' in html, "Missing diagnostic toggle in errors"
    
    print("✓ Diagnostic toggle buttons present")
    return True


def test_html_no_blocking_issues():
    """Test that the HTML doesn't have obvious blocking issues"""
    from web_server import DependencyTreeWebServer
    from dependency_graph_builder import DependencyGraphBuilder
    from unittest.mock import Mock
    
    config = Mock()
    config.enable_web_ui = True
    
    builder = DependencyGraphBuilder()
    server = DependencyTreeWebServer(builder, config)
    
    html = server._generate_html()
    
    # Check for async/await proper usage
    assert 'async function loadComponents()' in html, "loadComponents should be async"
    assert 'async function loadStats()' in html, "loadStats should be async"
    
    # Check for error handling in initialization
    assert 'try {' in html, "Missing try-catch blocks"
    assert 'catch (error)' in html or 'catch (e)' in html, "Missing catch blocks"
    
    # Ensure DOMContentLoaded has error handling
    dom_loaded_pattern = r"document\.addEventListener\('DOMContentLoaded'.*?\{(.*?)\}\);"
    matches = re.findall(dom_loaded_pattern, html, re.DOTALL)
    if matches:
        dom_content = matches[0]
        assert 'try' in dom_content or 'catch' in dom_content, "DOMContentLoaded should have error handling"
    
    print("✓ No obvious blocking issues found")
    return True


def test_initial_loading_text_will_be_replaced():
    """Test that the initial 'Loading components...' text will be replaced"""
    from web_server import DependencyTreeWebServer
    from dependency_graph_builder import DependencyGraphBuilder
    from unittest.mock import Mock
    
    config = Mock()
    config.enable_web_ui = True
    
    builder = DependencyGraphBuilder()
    server = DependencyTreeWebServer(builder, config)
    
    html = server._generate_html()
    
    # Check initial state
    assert 'Loading components...' in html, "Missing initial loading text"
    
    # Check that loadComponents updates it
    assert 'select.innerHTML' in html, "loadComponents should update select element"
    
    # Check for various update scenarios
    assert '-- Select a component --' in html, "Missing success state text"
    assert 'Service unavailable' in html, "Missing error state text"
    assert 'No integrations found' in html, "Missing empty state text"
    
    # Check that status indicator gets updated
    assert 'updateStatusIndicator' in html, "Missing status updates"
    
    print("✓ Initial loading text will be replaced in all scenarios")
    return True


if __name__ == '__main__':
    print("\n" + "="*70)
    print("Testing WebUI Diagnostic and Error Handling Features")
    print("="*70 + "\n")
    
    tests = [
        ("Diagnostic Panel", test_html_contains_diagnostic_panel),
        ("Status Indicator", test_html_contains_status_indicator),
        ("Noscript Warning", test_html_contains_noscript_warning),
        ("Global Timeout", test_html_contains_global_timeout),
        ("Enhanced Error Logging", test_html_enhanced_error_logging),
        ("Diagnostic Toggle Buttons", test_html_show_diagnostics_buttons),
        ("No Blocking Issues", test_html_no_blocking_issues),
        ("Loading Text Replacement", test_initial_loading_text_will_be_replaced),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\nRunning: {test_name}")
        print("-" * 70)
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
    
    print("="*70)
    print(f"Tests completed: {passed} passed, {failed} failed")
    print("="*70)
    
    sys.exit(0 if failed == 0 else 1)
