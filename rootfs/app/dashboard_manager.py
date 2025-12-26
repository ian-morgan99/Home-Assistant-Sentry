"""
Dashboard Manager - Creates and updates Home Assistant entities
"""
import logging
from datetime import datetime
from typing import Dict, List

logger = logging.getLogger(__name__)


class DashboardManager:
    """Manages Home Assistant dashboard entities for Sentry"""
    
    def __init__(self, ha_client):
        """Initialize dashboard manager"""
        self.ha_client = ha_client
    
    async def update_sensors(self, addon_updates: List[Dict], 
                            hacs_updates: List[Dict], 
                            analysis: Dict):
        """Update all sensor entities with current status"""
        total_updates = len(addon_updates) + len(hacs_updates)
        safe = analysis['safe']
        confidence = analysis['confidence']
        
        # Main status sensor
        await self.ha_client.set_sensor_state(
            'sensor.ha_sentry_update_status',
            'safe' if safe else 'review_required',
            {
                'friendly_name': 'HA Sentry Update Status',
                'icon': 'mdi:shield-check' if safe else 'mdi:shield-alert',
                'last_check': datetime.now().isoformat(),
                'updates_available': total_updates,
                'safe_to_update': safe,
                'confidence': confidence,
                'ai_enabled': analysis.get('ai_analysis', False)
            }
        )
        
        # Update count sensor
        await self.ha_client.set_sensor_state(
            'sensor.ha_sentry_updates_available',
            str(total_updates),
            {
                'friendly_name': 'Updates Available',
                'icon': 'mdi:package-up',
                'unit_of_measurement': 'updates',
                'addon_updates': len(addon_updates),
                'hacs_updates': len(hacs_updates),
                'last_check': datetime.now().isoformat()
            }
        )
        
        # Add-on updates sensor
        await self.ha_client.set_sensor_state(
            'sensor.ha_sentry_addon_updates',
            str(len(addon_updates)),
            {
                'friendly_name': 'Add-on Updates',
                'icon': 'mdi:puzzle',
                'unit_of_measurement': 'updates',
                'addons': [
                    {
                        'name': a['name'],
                        'current': a['current_version'],
                        'latest': a['latest_version']
                    } for a in addon_updates
                ],
                'last_check': datetime.now().isoformat()
            }
        )
        
        # HACS updates sensor
        await self.ha_client.set_sensor_state(
            'sensor.ha_sentry_hacs_updates',
            str(len(hacs_updates)),
            {
                'friendly_name': 'HACS Updates',
                'icon': 'mdi:home-assistant',
                'unit_of_measurement': 'updates',
                'integrations': [
                    {
                        'name': h['name'],
                        'current': h['current_version'],
                        'latest': h['latest_version']
                    } for h in hacs_updates
                ],
                'last_check': datetime.now().isoformat()
            }
        )
        
        # Issues sensor
        issues = analysis.get('issues', [])
        await self.ha_client.set_sensor_state(
            'sensor.ha_sentry_issues',
            str(len(issues)),
            {
                'friendly_name': 'Sentry Issues Detected',
                'icon': 'mdi:alert-circle',
                'unit_of_measurement': 'issues',
                'critical': len([i for i in issues if i.get('severity') == 'critical']),
                'high': len([i for i in issues if i.get('severity') == 'high']),
                'medium': len([i for i in issues if i.get('severity') == 'medium']),
                'low': len([i for i in issues if i.get('severity') == 'low']),
                'issues_list': issues,
                'last_check': datetime.now().isoformat()
            }
        )
        
        # Confidence sensor
        await self.ha_client.set_sensor_state(
            'sensor.ha_sentry_confidence',
            f"{confidence:.2f}",
            {
                'friendly_name': 'Analysis Confidence',
                'icon': 'mdi:gauge',
                'unit_of_measurement': '%',
                'confidence_percent': f"{confidence * 100:.0f}",
                'last_check': datetime.now().isoformat()
            }
        )
        
        logger.info("Dashboard sensors updated")
