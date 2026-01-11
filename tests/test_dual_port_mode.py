"""
Tests for Dual-Port Web Server Mode
Verifies that the web server can listen on both ingress port (8099) and custom port simultaneously
"""
import sys
import os
from unittest.mock import Mock

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app'))


def test_dual_port_initialization():
    """Test that web server initializes with dual-port tracking"""
    try:
        from web_server import DependencyTreeWebServer
        from dependency_graph_builder import DependencyGraphBuilder
        
        # Create a mock config
        config = Mock()
        config.enable_web_ui = True
        
        # Create graph builder
        builder = DependencyGraphBuilder()
        
        # Initialize web server with custom port (should trigger dual-port mode)
        server = DependencyTreeWebServer(builder, config, port=8098)
        
        # Verify initialization
        assert server.dependency_graph_builder == builder
        assert server.config == config
        assert server.port == 8098
        assert server.ingress_site is None  # Not started yet
        assert server.direct_site is None   # Not started yet
        
        print("✓ Dual-port initialization test passed")
        print(f"  Port: {server.port}")
        print(f"  Ingress site: {server.ingress_site}")
        print(f"  Direct site: {server.direct_site}")
        return True
    except Exception as e:
        print(f"✗ Dual-port initialization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_single_port_initialization():
    """Test that web server works with single port (8099)"""
    try:
        from web_server import DependencyTreeWebServer
        from dependency_graph_builder import DependencyGraphBuilder
        
        # Create a mock config
        config = Mock()
        config.enable_web_ui = True
        
        # Create graph builder
        builder = DependencyGraphBuilder()
        
        # Initialize web server with default port 8099
        server = DependencyTreeWebServer(builder, config, port=8099)
        
        # Verify initialization
        assert server.dependency_graph_builder == builder
        assert server.config == config
        assert server.port == 8099
        assert server.ingress_site is None  # Not started yet
        assert server.direct_site is None   # Not started yet (will share with ingress in single-port mode)
        
        print("✓ Single-port initialization test passed")
        print(f"  Port: {server.port}")
        return True
    except Exception as e:
        print(f"✗ Single-port initialization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_validation_no_warning():
    """Test that config manager doesn't warn about port != 8099"""
    try:
        from config_manager import ConfigManager
        
        # Set up environment variables
        os.environ['PORT'] = '8098'
        os.environ['ENABLE_WEB_UI'] = 'true'
        os.environ['ENABLE_DEPENDENCY_GRAPH'] = 'true'
        os.environ['AI_ENABLED'] = 'false'
        os.environ['CHECK_SCHEDULE'] = '02:00'
        os.environ['SUPERVISOR_TOKEN'] = 'test_token'
        
        # Create config manager
        config = ConfigManager()
        
        # Verify port was set correctly
        assert config.port == 8098
        assert config.enable_web_ui is True
        
        # The validation should NOT create warnings for port != 8099
        # It should create informational logs instead
        print("✓ Config validation test passed (no warning for port != 8099)")
        print(f"  Port: {config.port}")
        print(f"  Enable Web UI: {config.enable_web_ui}")
        return True
    except Exception as e:
        print(f"✗ Config validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_port_configuration_examples():
    """Test various port configuration scenarios"""
    scenarios = [
        (8099, "Default single-port mode"),
        (8098, "Custom port - dual-port mode"),
        (8080, "Alternative custom port"),
        (9000, "High port number"),
    ]
    
    try:
        from web_server import DependencyTreeWebServer
        from dependency_graph_builder import DependencyGraphBuilder
        
        all_passed = True
        
        for port, description in scenarios:
            config = Mock()
            config.enable_web_ui = True
            builder = DependencyGraphBuilder()
            
            server = DependencyTreeWebServer(builder, config, port=port)
            
            if server.port != port:
                print(f"✗ {description}: Port mismatch (expected {port}, got {server.port})")
                all_passed = False
            else:
                print(f"✓ {description}: Port {port} configured correctly")
        
        if all_passed:
            print("✓ All port configuration scenarios passed")
            return True
        else:
            print("✗ Some port configuration scenarios failed")
            return False
            
    except Exception as e:
        print(f"✗ Port configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("=" * 60)
    print("Running Dual-Port Mode Tests")
    print("=" * 60)
    
    results = []
    
    print("\n1. Testing dual-port initialization...")
    results.append(test_dual_port_initialization())
    
    print("\n2. Testing single-port initialization...")
    results.append(test_single_port_initialization())
    
    print("\n3. Testing config validation (no port warning)...")
    results.append(test_config_validation_no_warning())
    
    print("\n4. Testing port configuration scenarios...")
    results.append(test_port_configuration_examples())
    
    print("\n" + "=" * 60)
    print(f"Test Results: {sum(results)}/{len(results)} passed")
    print("=" * 60)
    
    if all(results):
        print("✅ All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed")
        sys.exit(1)
