"""
Test to verify the diagnostic logging code changes compile and have correct structure
"""
import sys
import os
import ast

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app'))


def test_ha_client_has_json_import():
    """Verify ha_client.py imports json module"""
    try:
        with open('../ha_sentry/rootfs/app/ha_client.py', 'r') as f:
            content = f.read()
        
        # Parse the AST
        tree = ast.parse(content)
        
        # Check for json import
        has_json_import = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == 'json':
                        has_json_import = True
        
        assert has_json_import, "json module should be imported"
        print("✓ ha_client.py imports json module")
        return True
    except Exception as e:
        print(f"✗ ha_client json import test failed: {e}")
        return False


def test_ha_client_has_entity_domain_logging():
    """Verify ha_client.py has entity domain logging code"""
    try:
        with open('../ha_sentry/rootfs/app/ha_client.py', 'r') as f:
            content = f.read()
        
        # Check for key logging statements
        assert "Entity domains:" in content, "Should have entity domain logging"
        assert "entities with 'update.' domain" in content, "Should log update entity count"
        assert "Sample:" in content, "Should have sample entity logging"
        assert "POST {url}" in content, "Should log POST URL"
        assert "json.dumps(dashboard_config" in content, "Should log dashboard payload"
        
        print("✓ ha_client.py has all required diagnostic logging")
        return True
    except Exception as e:
        print(f"✗ ha_client diagnostic logging test failed: {e}")
        return False


def test_dependency_graph_builder_has_path_diagnostics():
    """Verify dependency_graph_builder.py has path diagnostic logging"""
    try:
        with open('../ha_sentry/rootfs/app/dependency_graph_builder.py', 'r') as f:
            content = f.read()
        
        # Check for path diagnostic code
        assert "Parent directory exists:" in content, "Should check parent directory"
        assert "Parent contains:" in content, "Should list parent contents"
        assert "Cannot list parent:" in content, "Should handle exceptions"
        
        print("✓ dependency_graph_builder.py has path diagnostics")
        return True
    except Exception as e:
        print(f"✗ dependency_graph_builder path diagnostics test failed: {e}")
        return False


def test_main_has_system_banner():
    """Verify main.py has system information banner"""
    try:
        with open('../ha_sentry/rootfs/app/main.py', 'r') as f:
            content = f.read()
        
        # Check for system banner
        assert "SYSTEM INFORMATION" in content, "Should have system information banner"
        assert "Python:" in content, "Should log Python version"
        assert "Home Assistant URL:" in content, "Should log HA URL"
        assert "Has Supervisor Token:" in content, "Should log supervisor token presence"
        
        print("✓ main.py has system information banner")
        return True
    except Exception as e:
        print(f"✗ main.py system banner test failed: {e}")
        return False


def test_all_files_compile():
    """Test that all modified files compile successfully"""
    try:
        import py_compile
        
        files = [
            '../ha_sentry/rootfs/app/ha_client.py',
            '../ha_sentry/rootfs/app/dependency_graph_builder.py',
            '../ha_sentry/rootfs/app/main.py',
        ]
        
        for filepath in files:
            py_compile.compile(filepath, doraise=True)
        
        print("✓ All modified files compile successfully")
        return True
    except Exception as e:
        print(f"✗ File compilation test failed: {e}")
        return False


if __name__ == '__main__':
    print("Running code structure verification tests...\n")
    
    # Change to tests directory so relative paths work
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    tests = [
        test_ha_client_has_json_import,
        test_ha_client_has_entity_domain_logging,
        test_dependency_graph_builder_has_path_diagnostics,
        test_main_has_system_banner,
        test_all_files_compile,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        if test():
            passed += 1
        else:
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"Code verification tests: {passed} passed, {failed} failed")
    print(f"{'='*50}")
    
    sys.exit(0 if failed == 0 else 1)
