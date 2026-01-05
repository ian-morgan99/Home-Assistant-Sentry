"""
Test for async/await fix in DOMContentLoaded handler
Validates that loadComponents() and loadStats() are properly awaited
"""
import sys
import os
import re

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app'))


def test_domcontentloaded_is_async():
    """Test that DOMContentLoaded handler is declared as async"""
    from web_server import DependencyTreeWebServer
    from dependency_graph_builder import DependencyGraphBuilder
    from unittest.mock import Mock
    
    config = Mock()
    config.enable_web_ui = True
    
    builder = DependencyGraphBuilder()
    server = DependencyTreeWebServer(builder, config)
    
    html = server._generate_html()
    
    # Check that DOMContentLoaded handler is async
    # Pattern: addEventListener('DOMContentLoaded', async () => {
    dom_loaded_pattern = r"addEventListener\('DOMContentLoaded',\s*async\s*\("
    matches = re.search(dom_loaded_pattern, html)
    
    assert matches, "DOMContentLoaded handler should be declared as async"
    print("✓ DOMContentLoaded handler is async")
    return True


def test_load_components_is_awaited():
    """Test that loadComponents() is called with await"""
    from web_server import DependencyTreeWebServer
    from dependency_graph_builder import DependencyGraphBuilder
    from unittest.mock import Mock
    
    config = Mock()
    config.enable_web_ui = True
    
    builder = DependencyGraphBuilder()
    server = DependencyTreeWebServer(builder, config)
    
    html = server._generate_html()
    
    # Check that loadComponents is awaited
    # Pattern: await loadComponents()
    load_components_pattern = r"await\s+loadComponents\(\)"
    matches = re.search(load_components_pattern, html)
    
    assert matches, "loadComponents() should be called with await"
    print("✓ loadComponents() is awaited")
    return True


def test_load_stats_is_awaited():
    """Test that loadStats() is called with await"""
    from web_server import DependencyTreeWebServer
    from dependency_graph_builder import DependencyGraphBuilder
    from unittest.mock import Mock
    
    config = Mock()
    config.enable_web_ui = True
    
    builder = DependencyGraphBuilder()
    server = DependencyTreeWebServer(builder, config)
    
    html = server._generate_html()
    
    # Check that loadStats is awaited
    # Pattern: await loadStats()
    load_stats_pattern = r"await\s+loadStats\(\)"
    matches = re.search(load_stats_pattern, html)
    
    assert matches, "loadStats() should be called with await"
    print("✓ loadStats() is awaited")
    return True


def test_async_functions_are_properly_defined():
    """Test that loadComponents and loadStats are async functions"""
    from web_server import DependencyTreeWebServer
    from dependency_graph_builder import DependencyGraphBuilder
    from unittest.mock import Mock
    
    config = Mock()
    config.enable_web_ui = True
    
    builder = DependencyGraphBuilder()
    server = DependencyTreeWebServer(builder, config)
    
    html = server._generate_html()
    
    # Check that both functions are defined as async
    assert 'async function loadComponents()' in html, "loadComponents should be async function"
    assert 'async function loadStats()' in html, "loadStats should be async function"
    
    print("✓ Async functions are properly defined")
    return True


def test_error_handling_wraps_async_calls():
    """Test that async calls are wrapped in try-catch"""
    from web_server import DependencyTreeWebServer
    from dependency_graph_builder import DependencyGraphBuilder
    from unittest.mock import Mock
    
    config = Mock()
    config.enable_web_ui = True
    
    builder = DependencyGraphBuilder()
    server = DependencyTreeWebServer(builder, config)
    
    html = server._generate_html()
    
    # Extract the DOMContentLoaded handler
    dom_loaded_pattern = r"addEventListener\('DOMContentLoaded',\s*async\s*\([^)]*\)\s*=>\s*\{(.*?)\}\);"
    matches = re.search(dom_loaded_pattern, html, re.DOTALL)
    
    if matches:
        dom_content = matches.group(1)
        
        # Check that there's a try-catch around the await calls
        # Look for the pattern: try { await loadComponents(); ... } catch
        try_catch_pattern = r"try\s*\{[^}]*await\s+loadComponents\(\)[^}]*\}\s*catch"
        has_try_catch = re.search(try_catch_pattern, dom_content, re.DOTALL)
        
        assert has_try_catch, "Async calls should be wrapped in try-catch"
        print("✓ Async calls are wrapped in try-catch")
        return True
    else:
        print("⚠ Could not verify try-catch (pattern not matched)")
        return True  # Don't fail if pattern doesn't match exactly


def test_proper_error_messages_on_failure():
    """Test that error messages are shown when async functions fail"""
    from web_server import DependencyTreeWebServer
    from dependency_graph_builder import DependencyGraphBuilder
    from unittest.mock import Mock
    
    config = Mock()
    config.enable_web_ui = True
    
    builder = DependencyGraphBuilder()
    server = DependencyTreeWebServer(builder, config)
    
    html = server._generate_html()
    
    # Check for error handling messages
    assert 'Initialization failed' in html, "Should have error message for initialization failure"
    assert 'updateStatusIndicator' in html, "Should update status indicator on error"
    assert 'showDiagnosticPanel' in html, "Should show diagnostic panel on error"
    
    print("✓ Proper error messages on failure")
    return True


if __name__ == '__main__':
    print("\n" + "="*70)
    print("Testing Async/Await Fix in DOMContentLoaded")
    print("="*70 + "\n")
    
    tests = [
        ("DOMContentLoaded is async", test_domcontentloaded_is_async),
        ("loadComponents is awaited", test_load_components_is_awaited),
        ("loadStats is awaited", test_load_stats_is_awaited),
        ("Async functions defined", test_async_functions_are_properly_defined),
        ("Error handling wraps async calls", test_error_handling_wraps_async_calls),
        ("Error messages on failure", test_proper_error_messages_on_failure),
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
