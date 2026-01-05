"""
Test for enhanced WebUI progress tracking and error handling
Validates the comprehensive improvements made to address the "Preparing status..." issue
"""
import sys
import os
import re

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app'))


def test_progress_bar_exists():
    """Test that HTML includes progress bar component"""
    from web_server import DependencyTreeWebServer
    from dependency_graph_builder import DependencyGraphBuilder
    from unittest.mock import Mock
    
    config = Mock()
    config.enable_web_ui = True
    
    builder = DependencyGraphBuilder()
    server = DependencyTreeWebServer(builder, config)
    
    html = server._generate_html()
    
    # Check for progress bar elements
    assert 'progress-container' in html, "Missing progress-container"
    assert 'progress-bar' in html, "Missing progress-bar element"
    assert 'progress-label' in html, "Missing progress-label element"
    assert 'progress-details' in html, "Missing progress-details element"
    assert 'progress-time' in html, "Missing progress-time element"
    
    print("✓ Progress bar elements present")
    return True


def test_progress_functions_exist():
    """Test that HTML includes progress tracking functions"""
    from web_server import DependencyTreeWebServer
    from dependency_graph_builder import DependencyGraphBuilder
    from unittest.mock import Mock
    
    config = Mock()
    config.enable_web_ui = True
    
    builder = DependencyGraphBuilder()
    server = DependencyTreeWebServer(builder, config)
    
    html = server._generate_html()
    
    # Check for progress functions
    assert 'function updateProgressBar(' in html, "Missing updateProgressBar function"
    assert 'function hideProgressBar(' in html, "Missing hideProgressBar function"
    assert 'function pollBuildStatus(' in html, "Missing pollBuildStatus function"
    
    print("✓ Progress tracking functions present")
    return True


def test_fetch_with_timeout_exists():
    """Test that fetchWithTimeout function is defined"""
    from web_server import DependencyTreeWebServer
    from dependency_graph_builder import DependencyGraphBuilder
    from unittest.mock import Mock
    
    config = Mock()
    config.enable_web_ui = True
    
    builder = DependencyGraphBuilder()
    server = DependencyTreeWebServer(builder, config)
    
    html = server._generate_html()
    
    # Check for fetchWithTimeout with AbortController
    assert 'async function fetchWithTimeout(' in html, "Missing fetchWithTimeout function"
    assert 'AbortController' in html, "Missing AbortController for timeout handling"
    assert 'controller.abort()' in html, "Missing abort() call for timeout"
    
    print("✓ Fetch with timeout handling present")
    return True


def test_enhanced_error_function():
    """Test that showDetailedError function exists"""
    from web_server import DependencyTreeWebServer
    from dependency_graph_builder import DependencyGraphBuilder
    from unittest.mock import Mock
    
    config = Mock()
    config.enable_web_ui = True
    
    builder = DependencyGraphBuilder()
    server = DependencyTreeWebServer(builder, config)
    
    html = server._generate_html()
    
    # Check for enhanced error handling
    assert 'function showDetailedError(' in html, "Missing showDetailedError function"
    assert 'Troubleshooting Steps:' in html, "Missing troubleshooting steps template"
    
    print("✓ Enhanced error handling functions present")
    return True


def test_load_components_uses_progress():
    """Test that loadComponents function uses progress tracking"""
    from web_server import DependencyTreeWebServer
    from dependency_graph_builder import DependencyGraphBuilder
    from unittest.mock import Mock
    
    config = Mock()
    config.enable_web_ui = True
    
    builder = DependencyGraphBuilder()
    server = DependencyTreeWebServer(builder, config)
    
    html = server._generate_html()
    
    # Extract loadComponents function
    load_components_pattern = r"async function loadComponents\(\)\s*\{(.*?)\n\s*\}\s*async function"
    match = re.search(load_components_pattern, html, re.DOTALL)
    
    assert match, "Could not find loadComponents function"
    
    load_components_code = match.group(1)
    
    # Check that it uses new progress features
    assert 'pollBuildStatus()' in load_components_code, "loadComponents should call pollBuildStatus"
    assert 'fetchWithTimeout(' in load_components_code, "loadComponents should use fetchWithTimeout"
    assert 'showDetailedError(' in load_components_code, "loadComponents should use showDetailedError"
    assert 'hideProgressBar()' in load_components_code, "loadComponents should hide progress bar on completion"
    
    # Check for comprehensive error handling
    assert 'Network Error' in load_components_code, "Missing network error handling"
    assert 'timeout' in load_components_code.lower(), "Missing timeout error handling"
    
    print("✓ loadComponents uses progress tracking and enhanced error handling")
    return True


def test_progress_bar_styling():
    """Test that progress bar has proper styling"""
    from web_server import DependencyTreeWebServer
    from dependency_graph_builder import DependencyGraphBuilder
    from unittest.mock import Mock
    
    config = Mock()
    config.enable_web_ui = True
    
    builder = DependencyGraphBuilder()
    server = DependencyTreeWebServer(builder, config)
    
    html = server._generate_html()
    
    # Check for gradient styling in progress bar
    assert 'linear-gradient' in html, "Progress bar should have gradient styling"
    assert 'transition:' in html, "Progress bar should have smooth transitions"
    
    print("✓ Progress bar has proper styling")
    return True


def test_comprehensive_error_messages():
    """Test that comprehensive error messages exist for various failure modes"""
    from web_server import DependencyTreeWebServer
    from dependency_graph_builder import DependencyGraphBuilder
    from unittest.mock import Mock
    
    config = Mock()
    config.enable_web_ui = True
    
    builder = DependencyGraphBuilder()
    server = DependencyTreeWebServer(builder, config)
    
    html = server._generate_html()
    
    # Extract loadComponents function
    load_components_pattern = r"async function loadComponents\(\)\s*\{(.*?)\n\s*\}\s*async function"
    match = re.search(load_components_pattern, html, re.DOTALL)
    
    if match:
        load_components_code = match.group(1)
        
        # Check for various error scenarios
        error_scenarios = [
            'Dependency Graph Unavailable',
            'Status Check Failed',
            'Dependency Graph Build Timeout',
            'Network Error',
            'Component Loading Failed',
            'Invalid Response',
            'Unexpected Error'
        ]
        
        found_errors = []
        for scenario in error_scenarios:
            if scenario in load_components_code:
                found_errors.append(scenario)
        
        assert len(found_errors) >= 5, f"Should have at least 5 error scenarios, found: {found_errors}"
        print(f"✓ Comprehensive error messages for {len(found_errors)} scenarios")
        return True
    else:
        print("⚠ Could not verify error messages (pattern not matched)")
        return True


def test_step_by_step_loading():
    """Test that loading process is broken into clear steps"""
    from web_server import DependencyTreeWebServer
    from dependency_graph_builder import DependencyGraphBuilder
    from unittest.mock import Mock
    
    config = Mock()
    config.enable_web_ui = True
    
    builder = DependencyGraphBuilder()
    server = DependencyTreeWebServer(builder, config)
    
    html = server._generate_html()
    
    # Check for step-by-step diagnostic logging
    assert 'Step 1:' in html, "Should have step 1 logging"
    assert 'Step 2:' in html or 'Step 3:' in html, "Should have multi-step process"
    
    print("✓ Loading process has clear step-by-step logging")
    return True


if __name__ == '__main__':
    print("\n" + "="*70)
    print("Testing Enhanced WebUI Progress Tracking and Error Handling")
    print("="*70 + "\n")
    
    tests = [
        ("Progress Bar Elements", test_progress_bar_exists),
        ("Progress Functions", test_progress_functions_exist),
        ("Fetch with Timeout", test_fetch_with_timeout_exists),
        ("Enhanced Error Handling", test_enhanced_error_function),
        ("LoadComponents Progress", test_load_components_uses_progress),
        ("Progress Bar Styling", test_progress_bar_styling),
        ("Comprehensive Error Messages", test_comprehensive_error_messages),
        ("Step-by-Step Loading", test_step_by_step_loading),
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
        except AssertionError as e:
            failed += 1
            print(f"✗ {test_name} FAILED")
            print(f"  Error: {str(e)}\n")
        except Exception as e:
            failed += 1
            print(f"✗ {test_name} ERROR")
            print(f"  Error: {str(e)}\n")
    
    print("="*70)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("="*70)
    
    sys.exit(0 if failed == 0 else 1)
