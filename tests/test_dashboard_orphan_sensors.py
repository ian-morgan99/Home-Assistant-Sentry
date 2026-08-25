"""Tests for DashboardManager.update_orphan_sensors advisory method."""
import sys
import os
import asyncio
from typing import Dict, List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app'))

from dashboard_manager import DashboardManager


class MockHAClient:
    """Captures every set_sensor_state call."""
    def __init__(self):
        self.calls: List[Dict] = []

    async def set_sensor_state(self, entity_id, state, attributes):
        self.calls.append({
            'entity_id': entity_id,
            'state': state,
            'attributes': dict(attributes),
        })


SAMPLE_REPORT = {
    'summary': {
        'orphaned_entities': 4,
        'ghost_entities': 2,
        'broken_config_entries': 1,
        'orphaned_devices': 0,
        'stale_entities': 5,
    },
    'orphaned_entities': [],
    'ghost_entities': [],
    'broken_config_entries': [],
    'orphaned_devices': [],
    'stale_entities': [],
}


async def test_update_orphan_sensors_sets_all_four():
    client = MockHAClient()
    mgr = DashboardManager(client)
    await mgr.update_orphan_sensors(SAMPLE_REPORT)
    entity_ids = [c['entity_id'] for c in client.calls]
    assert 'sensor.ha_sentry_orphaned_entities_count' in entity_ids
    assert 'sensor.ha_sentry_ghost_entities_count' in entity_ids
    assert 'sensor.ha_sentry_broken_config_entries_count' in entity_ids
    assert 'sensor.ha_sentry_stale_entities_count' in entity_ids
    # State values are the counts as strings
    by_id = {c['entity_id']: c for c in client.calls}
    assert by_id['sensor.ha_sentry_orphaned_entities_count']['state'] == '4'
    assert by_id['sensor.ha_sentry_ghost_entities_count']['state'] == '2'
    assert by_id['sensor.ha_sentry_broken_config_entries_count']['state'] == '1'
    assert by_id['sensor.ha_sentry_stale_entities_count']['state'] == '5'
    # Attributes include last_check
    for call in client.calls:
        assert 'last_check' in call['attributes']
        assert 'friendly_name' in call['attributes']


async def test_update_orphan_sensors_empty_report():
    client = MockHAClient()
    mgr = DashboardManager(client)
    await mgr.update_orphan_sensors({'summary': {}})
    for call in client.calls:
        assert call['state'] == '0'


async def test_update_orphan_sensors_none_report():
    """None report should not raise; should still emit 0-valued sensors."""
    client = MockHAClient()
    mgr = DashboardManager(client)
    await mgr.update_orphan_sensors(None)
    assert len(client.calls) == 4
    for call in client.calls:
        assert call['state'] == '0'


if __name__ == '__main__':
    asyncio.run(test_update_orphan_sensors_sets_all_four())
    asyncio.run(test_update_orphan_sensors_empty_report())
    asyncio.run(test_update_orphan_sensors_none_report())
    print("All tests passed")
