"""Tests for the /api/orphaned-entities and /api/broken-entities endpoints."""
import sys
import os
import asyncio
from typing import Dict, List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app'))

from web_server import DependencyTreeWebServer
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer


class MockConfigManager:
    enable_web_ui = True
    enable_dependency_graph = True


class MockDependencyGraphBuilder:
    def __init__(self):
        self.integrations = {}
        self.addons = {}
        self.dependency_map = {}
        self.HIGH_RISK_LIBRARIES = []


class MockSentryService:
    """Mock service exposing the orphan report attributes."""
    def __init__(self, report: Dict = None, status: str = 'completed'):
        self.orphaned_entity_report = report
        self._orphaned_check_status = status


SAMPLE_REPORT = {
    'summary': {
        'orphaned_entities': 2,
        'ghost_entities': 1,
        'broken_config_entries': 1,
        'orphaned_devices': 0,
        'stale_entities': 3,
    },
    'orphaned_entities': [
        {'entity_id': 'light.orphan1', 'suggestion': 'remove'},
        {'entity_id': 'light.orphan2', 'suggestion': 'remove'},
    ],
    'ghost_entities': [{'entity_id': 'switch.never_on'}],
    'broken_config_entries': [{'entry_id': 'abc', 'domain': 'mqtt', 'state': 'setup_error'}],
    'orphaned_devices': [],
    'stale_entities': [
        {'entity_id': f'sensor.stale{i}'} for i in range(3)
    ],
}


async def create_test_app(service):
    config = MockConfigManager()
    graph_builder = MockDependencyGraphBuilder()
    server = DependencyTreeWebServer(graph_builder, config, sentry_service=service, port=8099)
    server.app = web.Application(middlewares=[server.error_middleware])
    server._setup_routes()
    return server.app


async def test_orphan_endpoint_with_report():
    service = MockSentryService(report=SAMPLE_REPORT, status='completed')
    app = await create_test_app(service)
    async with TestClient(TestServer(app)) as client:
        resp = await client.get('/api/orphaned-entities')
        assert resp.status == 200
        data = await resp.json()
        assert data['summary']['orphaned_entities'] == 2
        assert data['summary']['ghost_entities'] == 1
        assert data['summary']['broken_config_entries'] == 1
        assert data['summary']['stale_entities'] == 3
        assert len(data['orphaned_entities']) == 2
        assert data['meta']['status'] == 'completed'


async def test_orphan_endpoint_no_report_yet():
    service = MockSentryService(report=None, status='not_started')
    app = await create_test_app(service)
    async with TestClient(TestServer(app)) as client:
        resp = await client.get('/api/orphaned-entities')
        assert resp.status == 200
        data = await resp.json()
        # Empty but well-formed
        assert data['summary']['orphaned_entities'] == 0
        assert data['orphaned_entities'] == []
        assert data['meta']['status'] == 'not_started'


async def test_orphan_endpoint_no_service():
    config = MockConfigManager()
    graph_builder = MockDependencyGraphBuilder()
    server = DependencyTreeWebServer(graph_builder, config, sentry_service=None, port=8099)
    server.app = web.Application(middlewares=[server.error_middleware])
    server._setup_routes()
    async with TestClient(TestServer(server.app)) as client:
        resp = await client.get('/api/orphaned-entities')
        assert resp.status == 200
        data = await resp.json()
        assert data['summary']['orphaned_entities'] == 0
        assert data['meta']['status'] == 'not_started'


async def test_broken_endpoint_with_report():
    service = MockSentryService(report=SAMPLE_REPORT, status='completed')
    app = await create_test_app(service)
    async with TestClient(TestServer(app)) as client:
        resp = await client.get('/api/broken-entities')
        assert resp.status == 200
        data = await resp.json()
        assert data['summary']['broken_config_entries'] == 1
        assert len(data['broken_config_entries']) == 1
        assert data['broken_config_entries'][0]['domain'] == 'mqtt'


async def test_broken_endpoint_no_report():
    service = MockSentryService(report=None, status='not_started')
    app = await create_test_app(service)
    async with TestClient(TestServer(app)) as client:
        resp = await client.get('/api/broken-entities')
        assert resp.status == 200
        data = await resp.json()
        assert data['summary']['broken_config_entries'] == 0
        assert data['broken_config_entries'] == []


if __name__ == '__main__':
    asyncio.run(test_orphan_endpoint_with_report())
    asyncio.run(test_orphan_endpoint_no_report_yet())
    asyncio.run(test_orphan_endpoint_no_service())
    asyncio.run(test_broken_endpoint_with_report())
    asyncio.run(test_broken_endpoint_no_report())
    print("All tests passed")
