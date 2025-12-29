"""
Tests for Dependency Tree Web Server
"""
import sys
import os
import asyncio
from unittest.mock import Mock

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app'))


def test_web_server_init():
    """Test DependencyTreeWebServer initialization"""
    try:
        from web_server import DependencyTreeWebServer
        from dependency_graph_builder import DependencyGraphBuilder
        
        # Create a mock config
        config = Mock()
        config.enable_web_ui = True
        
        # Create graph builder
        builder = DependencyGraphBuilder()
        
        # Initialize web server
        server = DependencyTreeWebServer(builder, config, port=8099)
        
        assert server.dependency_graph_builder == builder
        assert server.config == config
        assert server.port == 8099
        assert server.app is None  # Not started yet
        
        print("✓ Web server initialization test passed")
        return True
    except Exception as e:
        print(f"✗ Web server initialization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_web_server_routes():
    """Test that web server sets up routes correctly"""
    try:
        from web_server import DependencyTreeWebServer
        from dependency_graph_builder import DependencyGraphBuilder
        
        config = Mock()
        config.enable_web_ui = True
        
        builder = DependencyGraphBuilder()
        server = DependencyTreeWebServer(builder, config)
        
        # Create app without starting server
        from aiohttp import web
        server.app = web.Application()
        server._setup_routes()
        
        # Check that routes are configured
        route_paths = [route.resource.canonical for route in server.app.router.routes()]
        
        assert '/' in route_paths
        assert any('/api/components' in path for path in route_paths)
        assert any('/api/dependency-tree' in path for path in route_paths)
        assert any('/api/where-used' in path for path in route_paths)
        assert any('/api/change-impact' in path for path in route_paths)
        assert any('/api/graph-data' in path for path in route_paths)
        
        print("✓ Web server routes test passed")
        return True
    except Exception as e:
        print(f"✗ Web server routes test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_html_generation():
    """Test that HTML interface is generated correctly"""
    try:
        from web_server import DependencyTreeWebServer
        from dependency_graph_builder import DependencyGraphBuilder
        
        config = Mock()
        config.enable_web_ui = True
        
        builder = DependencyGraphBuilder()
        server = DependencyTreeWebServer(builder, config)
        
        html = server._generate_html()
        
        # Check for key elements
        assert '<!DOCTYPE html>' in html
        assert 'Home Assistant Sentry' in html
        assert 'Dependency Tree Visualization' in html
        assert 'api/components' in html
        assert 'api/dependency-tree' in html
        assert 'api/where-used' in html
        assert 'api/change-impact' in html
        
        print("✓ HTML generation test passed")
        return True
    except Exception as e:
        print(f"✗ HTML generation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_api_get_components():
    """Test the get components API endpoint"""
    try:
        from web_server import DependencyTreeWebServer
        from dependency_graph_builder import DependencyGraphBuilder
        from aiohttp import web
        from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
        
        config = Mock()
        config.enable_web_ui = True
        
        # Create test data
        builder = DependencyGraphBuilder()
        builder.integrations = {
            'test_integration_1': {
                'name': 'Test Integration 1',
                'domain': 'test_integration_1',
                'version': '1.0.0',
                'requirements': [
                    {'package': 'aiohttp', 'specifier': '>=3.9', 'high_risk': True}
                ]
            },
            'test_integration_2': {
                'name': 'Test Integration 2',
                'domain': 'test_integration_2',
                'version': '2.0.0',
                'requirements': []
            }
        }
        
        server = DependencyTreeWebServer(builder, config)
        
        # Create mock request
        request = Mock()
        
        # Call handler
        response = await server._handle_get_components(request)
        
        # Check response
        assert response.status == 200
        import json
        data = json.loads(response.text)
        assert 'components' in data
        assert len(data['components']) == 2
        assert data['total'] == 2
        
        print("✓ API get components test passed")
        return True
    except Exception as e:
        print(f"✗ API get components test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_api_dependency_tree():
    """Test the dependency tree API endpoint"""
    try:
        from web_server import DependencyTreeWebServer
        from dependency_graph_builder import DependencyGraphBuilder
        from aiohttp import web
        
        config = Mock()
        config.enable_web_ui = True
        
        # Create test data
        builder = DependencyGraphBuilder()
        builder.integrations = {
            'test_integration': {
                'name': 'Test Integration',
                'domain': 'test_integration',
                'version': '1.0.0',
                'requirements': [
                    {'package': 'aiohttp', 'specifier': '>=3.9', 'high_risk': True},
                    {'package': 'requests', 'specifier': '>=2.28', 'high_risk': False}
                ]
            }
        }
        builder.dependency_map = {
            'aiohttp': [
                {'integration': 'Test Integration', 'domain': 'test_integration', 'specifier': '>=3.9', 'high_risk': True}
            ],
            'requests': [
                {'integration': 'Test Integration', 'domain': 'test_integration', 'specifier': '>=2.28', 'high_risk': False}
            ]
        }
        
        server = DependencyTreeWebServer(builder, config)
        
        # Create mock request
        request = Mock()
        request.match_info = {'component': 'test_integration'}
        
        # Call handler
        response = await server._handle_dependency_tree(request)
        
        # Check response
        assert response.status == 200
        import json
        data = json.loads(response.text)
        assert data['component'] == 'test_integration'
        assert data['name'] == 'Test Integration'
        assert len(data['dependencies']) == 2
        
        print("✓ API dependency tree test passed")
        return True
    except Exception as e:
        print(f"✗ API dependency tree test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_api_where_used():
    """Test the where used API endpoint"""
    try:
        from web_server import DependencyTreeWebServer
        from dependency_graph_builder import DependencyGraphBuilder
        
        config = Mock()
        config.enable_web_ui = True
        
        # Create test data
        builder = DependencyGraphBuilder()
        builder.integrations = {}
        builder.dependency_map = {
            'aiohttp': [
                {'integration': 'Integration A', 'domain': 'integration_a', 'specifier': '>=3.9', 'high_risk': True},
                {'integration': 'Integration B', 'domain': 'integration_b', 'specifier': '>=3.9', 'high_risk': True}
            ]
        }
        builder.HIGH_RISK_LIBRARIES = {'aiohttp', 'cryptography'}
        
        server = DependencyTreeWebServer(builder, config)
        
        # Create mock request
        request = Mock()
        request.match_info = {'component': 'aiohttp'}
        
        # Call handler
        response = await server._handle_where_used(request)
        
        # Check response
        assert response.status == 200
        import json
        data = json.loads(response.text)
        assert data['type'] == 'package'
        assert data['package'] == 'aiohttp'
        assert len(data['used_by']) == 2
        assert data['high_risk'] is True
        
        print("✓ API where used test passed")
        return True
    except Exception as e:
        print(f"✗ API where used test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_api_change_impact():
    """Test the change impact API endpoint"""
    try:
        from web_server import DependencyTreeWebServer
        from dependency_graph_builder import DependencyGraphBuilder
        from unittest.mock import MagicMock
        
        config = Mock()
        config.enable_web_ui = True
        
        # Create test data
        builder = DependencyGraphBuilder()
        builder.integrations = {
            'component_a': {
                'name': 'Component A',
                'domain': 'component_a',
                'requirements': [
                    {'package': 'aiohttp', 'specifier': '>=3.9', 'high_risk': True}
                ]
            }
        }
        builder.dependency_map = {
            'aiohttp': [
                {'integration': 'Component A', 'domain': 'component_a', 'specifier': '>=3.9', 'high_risk': True},
                {'integration': 'Component B', 'domain': 'component_b', 'specifier': '>=3.9', 'high_risk': True}
            ]
        }
        
        server = DependencyTreeWebServer(builder, config)
        
        # Create mock request
        request = Mock()
        request.query = {'components': 'component_a'}
        
        # Call handler
        response = await server._handle_change_impact(request)
        
        # Check response
        assert response.status == 200
        import json
        data = json.loads(response.text)
        assert 'component_a' in data['changed_components']
        assert len(data['affected_packages']) > 0
        assert len(data['high_risk_changes']) > 0
        
        print("✓ API change impact test passed")
        return True
    except Exception as e:
        print(f"✗ API change impact test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_async_test(test_func):
    """Helper to run async tests"""
    return asyncio.run(test_func())


if __name__ == '__main__':
    print("Running Dependency Tree Web Server tests...\n")
    
    tests = [
        ('sync', test_web_server_init),
        ('sync', test_web_server_routes),
        ('sync', test_html_generation),
        ('async', test_api_get_components),
        ('async', test_api_dependency_tree),
        ('async', test_api_where_used),
        ('async', test_api_change_impact),
    ]
    
    passed = 0
    failed = 0
    
    for test_type, test in tests:
        try:
            if test_type == 'sync':
                if test():
                    passed += 1
                else:
                    failed += 1
            else:
                if run_async_test(test):
                    passed += 1
                else:
                    failed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} raised exception: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"Tests completed: {passed} passed, {failed} failed")
    print(f"{'='*50}")
    
    sys.exit(0 if failed == 0 else 1)
