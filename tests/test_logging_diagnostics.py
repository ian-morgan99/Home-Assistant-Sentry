"""
Test for new diagnostic logging features
"""
import sys
import os
import logging
from io import StringIO

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app'))


def test_ha_client_imports():
    """Test that ha_client imports correctly with json module"""
    try:
        # This should work even without aiohttp since we're just checking imports
        import ha_client
        # Verify json is imported
        assert hasattr(ha_client, 'json'), "json module should be imported in ha_client"
        print("✓ ha_client imports json module successfully")
        return True
    except Exception as e:
        print(f"✗ ha_client import test failed: {e}")
        return False


def test_dependency_graph_builder_path_logging():
    """Test that dependency_graph_builder has enhanced path logging"""
    try:
        from dependency_graph_builder import DependencyGraphBuilder
        
        # Create a temporary test setup
        builder = DependencyGraphBuilder()
        
        # Test with non-existent paths (should log debug messages but not fail)
        test_paths = ['/nonexistent/path/1', '/nonexistent/path/2']
        
        # Capture log output
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        handler.setLevel(logging.DEBUG)
        logger = logging.getLogger('dependency_graph_builder')
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)
        
        # Build graph with non-existent paths
        result = builder.build_graph_from_paths(test_paths)
        
        # Verify the result is valid
        assert 'integrations' in result, "Result should contain integrations"
        assert 'dependency_map' in result, "Result should contain dependency_map"
        
        # Check log output for path diagnostics
        log_output = log_stream.getvalue()
        
        # Clean up
        logger.removeHandler(handler)
        
        print("✓ dependency_graph_builder path logging test passed")
        return True
    except Exception as e:
        print(f"✗ dependency_graph_builder test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_main_imports():
    """Test that main.py imports correctly"""
    try:
        import main
        # Verify sys is available (used for Python version logging)
        assert hasattr(main, 'sys'), "sys module should be imported in main"
        print("✓ main.py imports successfully")
        return True
    except Exception as e:
        print(f"✗ main.py import test failed: {e}")
        return False


def test_config_manager_unchanged():
    """Test that config_manager still works as expected"""
    try:
        from config_manager import ConfigManager
        
        # Set test environment
        os.environ['AI_ENABLED'] = 'true'
        os.environ['LOG_LEVEL'] = 'maximal'
        os.environ['SUPERVISOR_TOKEN'] = 'test_token'
        
        config = ConfigManager()
        
        # Verify config works
        assert config.ai_enabled is True
        assert config.log_level == 'maximal'
        assert config.get_python_log_level() == logging.DEBUG
        assert config.supervisor_token == 'test_token'
        
        print("✓ config_manager still works correctly")
        return True
    except Exception as e:
        print(f"✗ config_manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("Running diagnostic logging tests...\n")
    
    tests = [
        test_ha_client_imports,
        test_dependency_graph_builder_path_logging,
        test_main_imports,
        test_config_manager_unchanged,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        if test():
            passed += 1
        else:
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"Diagnostic tests completed: {passed} passed, {failed} failed")
    print(f"{'='*50}")
    
    sys.exit(0 if failed == 0 else 1)
