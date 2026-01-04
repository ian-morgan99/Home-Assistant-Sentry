"""
Test 404 handling for API and HTML routes
"""
import sys
import os
import asyncio

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app'))

from web_server import DependencyTreeWebServer
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer


class MockConfigManager:
    """Mock configuration manager"""
    enable_web_ui = True
    enable_dependency_graph = True


class MockDependencyGraphBuilder:
    """Mock dependency graph builder"""
    def __init__(self):
        self.integrations = {
            'test_integration': {
                'name': 'Test Integration',
                'version': '1.0.0',
                'requirements': []
            }
        }
        self.addons = {}
        self.dependency_map = {}
        self.HIGH_RISK_LIBRARIES = []


async def create_test_app():
    """Create the test application"""
    config = MockConfigManager()
    graph_builder = MockDependencyGraphBuilder()
    server = DependencyTreeWebServer(graph_builder, config, port=8099)
    # Setup routes without starting the server
    server.app = web.Application(middlewares=[server.error_middleware])
    server._setup_routes()
    return server.app


async def test_api_404_returns_json():
    """Test that API paths return JSON 404 responses"""
    app = await create_test_app()
    async with TestClient(TestServer(app)) as client:
        resp = await client.get("/api/nonexistent")
        assert resp.status == 404
        assert resp.content_type == 'application/json'
        
        data = await resp.json()
        assert 'error' in data
        assert data['error'] == 'Not Found'
        assert 'path' in data
        assert data['path'] == '/api/nonexistent'
        print("✓ API 404 returns JSON response")


async def test_ingress_404_returns_json():
    """Test that /ingress/ paths return JSON 404 responses"""
    app = await create_test_app()
    async with TestClient(TestServer(app)) as client:
        resp = await client.get("/ingress/validate_session")
        assert resp.status == 404
        assert resp.content_type == 'application/json'
        
        data = await resp.json()
        assert 'error' in data
        assert data['error'] == 'Not Found'
        print("✓ /ingress/ path returns JSON 404 response")


async def test_html_404_with_json_accept():
    """Test that requests with JSON Accept header get JSON 404"""
    app = await create_test_app()
    async with TestClient(TestServer(app)) as client:
        resp = await client.get(
            "/some/random/path",
            headers={'Accept': 'application/json'}
        )
        assert resp.status == 404
        assert resp.content_type == 'application/json'
        
        data = await resp.json()
        assert 'error' in data
        print("✓ Request with JSON Accept header returns JSON 404")


async def test_browser_404_returns_html():
    """Test that browser requests return HTML 404 responses"""
    app = await create_test_app()
    async with TestClient(TestServer(app)) as client:
        resp = await client.get(
            "/nonexistent.html",
            headers={'Accept': 'text/html'}
        )
        assert resp.status == 404
        assert resp.content_type == 'text/html'
        
        text = await resp.text()
        assert 'Page Not Found' in text or 'Not Found' in text
        print("✓ Browser request returns HTML 404 response")


async def test_valid_route_still_works():
    """Test that valid routes still work after adding 404 handler"""
    app = await create_test_app()
    async with TestClient(TestServer(app)) as client:
        resp = await client.get("/api/status")
        # Should get 200 or 503 (if graph not available), not 404
        assert resp.status in [200, 503]
        assert resp.content_type == 'application/json'
        print("✓ Valid routes still work correctly")


async def run_tests():
    """Run all tests"""
    tests = [
        ("API 404 returns JSON", test_api_404_returns_json),
        ("Ingress 404 returns JSON", test_ingress_404_returns_json),
        ("JSON Accept header gets JSON 404", test_html_404_with_json_accept),
        ("Browser request returns HTML 404", test_browser_404_returns_html),
        ("Valid routes still work", test_valid_route_still_works),
    ]
    
    passed = 0
    failed = 0
    
    print("\nRunning 404 handling tests...\n")
    
    for test_name, test_func in tests:
        try:
            await test_func()
            passed += 1
        except Exception as e:
            print(f"✗ {test_name} failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"Tests completed: {passed} passed, {failed} failed")
    print(f"{'='*50}")
    
    return failed == 0


if __name__ == '__main__':
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)

