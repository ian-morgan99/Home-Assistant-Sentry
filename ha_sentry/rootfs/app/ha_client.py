"""
Home Assistant API Client
"""
import aiohttp
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Update type constants
UPDATE_TYPE_CORE = 'core'
UPDATE_TYPE_SUPERVISOR = 'supervisor'
UPDATE_TYPE_OS = 'os'
UPDATE_TYPE_ADDON = 'addon'
UPDATE_TYPE_HACS = 'hacs'
UPDATE_TYPE_INTEGRATION = 'integration'

# Home Assistant version compatibility
HA_COMPATIBILITY_VERSIONS = '2024.11.x - 2025.1.x'


class HomeAssistantClient:
    """Client for interacting with Home Assistant APIs"""
    
    def __init__(self, config):
        """Initialize the HA client"""
        self.config = config
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        logger.debug("Initializing Home Assistant client session")
        self.session = aiohttp.ClientSession(headers=self.config.headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            logger.debug("Closing Home Assistant client session")
            await self.session.close()
    
    def _log_auth_error(self, context: str = ""):
        """Log authentication error with helpful information"""
        logger.error("=" * 60)
        logger.error("AUTHENTICATION FAILED (401 Unauthorized)")
        logger.error("=" * 60)
        logger.error("The SUPERVISOR_TOKEN is missing or invalid.")
        logger.error("")
        logger.error("This add-on requires the SUPERVISOR_TOKEN to communicate with Home Assistant.")
        logger.error("This token should be automatically provided by the Home Assistant Supervisor.")
        logger.error("")
        logger.error("TROUBLESHOOTING STEPS:")
        logger.error("1. Verify 'homeassistant_api: true' is set in config.json (should be by default)")
        logger.error("2. Restart the add-on")
        logger.error("3. If the issue persists, restart Home Assistant")
        logger.error("4. Check if other add-ons can access Home Assistant API")
        logger.error("")
        if context:
            logger.error(f"Context: {context}")
        logger.error("=" * 60)
    
    def _log_dashboard_permission_error(self):
        """Log dashboard creation permission error with helpful information"""
        logger.warning("Dashboard creation failed due to insufficient permissions.")
        logger.warning("This is a known limitation - Home Assistant add-ons cannot create Lovelace dashboards via the API.")
        logger.info("SOLUTION: Disable 'auto_create_dashboard' in the add-on configuration and manually create your dashboard.")
        logger.info("See the documentation for example dashboard configurations: https://github.com/ian-morgan99/Home-Assistant-Sentry/blob/main/DOCS.md#dashboard-integration")
        logger.info("The add-on will continue to work normally and update sensor entities.")
    
    def _log_dashboard_endpoint_not_found(self):
        """Log dashboard endpoint not found error with helpful information"""
        logger.error("=" * 60)
        logger.error("DASHBOARD ENDPOINT NOT FOUND (404)")
        logger.error("=" * 60)
        logger.error("The Lovelace dashboard API endpoint does not exist or is not accessible.")
        logger.error("")
        logger.error("POSSIBLE CAUSES:")
        logger.error("1. Home Assistant version does not support the dashboard API endpoint")
        logger.error("2. The API endpoint path has changed in your Home Assistant version")
        logger.error("3. Add-on lacks necessary permissions to access the endpoint")
        logger.error("4. Running in a restricted environment (e.g., Container vs. Supervisor)")
        logger.error("")
        logger.error("SOLUTION:")
        logger.error("Set 'auto_create_dashboard: false' in the add-on configuration")
        logger.error("and manually create your dashboard using the sensor entities.")
        logger.error("")
        logger.error("See documentation: https://github.com/ian-morgan99/Home-Assistant-Sentry/blob/main/DOCS.md#dashboard-integration")
        logger.error("The add-on will continue to work normally and update sensor entities.")
        logger.error("=" * 60)
    
    async def get_addon_updates(self) -> List[Dict]:
        """Get available add-on updates from Supervisor API"""
        try:
            url = f"{self.config.supervisor_url}/addons"
            logger.debug(f"Fetching add-ons from: {url}")
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    addons = data.get('data', {}).get('addons', [])
                    logger.debug(f"Retrieved {len(addons)} total add-ons")
                    
                    updates = []
                    for addon in addons:
                        if addon.get('update_available', False):
                            update_info = {
                                'name': addon.get('name'),
                                'slug': addon.get('slug'),
                                'current_version': addon.get('version'),
                                'latest_version': addon.get('version_latest'),
                                'repository': addon.get('repository'),
                                'description': addon.get('description', '')
                            }
                            updates.append(update_info)
                            logger.debug(f"  Update available: {update_info['name']} ({update_info['current_version']} → {update_info['latest_version']})")
                    
                    logger.info(f"Found {len(updates)} add-on updates")
                    return updates
                else:
                    logger.error(f"Failed to get add-ons: {response.status}")
                    if response.status == 401:
                        self._log_auth_error("Unable to fetch add-ons from Supervisor API")
                    return []
        except Exception as e:
            logger.error(f"Error getting add-on updates: {e}", exc_info=True)
            return []
    
    async def get_addon_details(self, addon_slug: str) -> Optional[Dict]:
        """Get detailed information about an add-on"""
        try:
            url = f"{self.config.supervisor_url}/addons/{addon_slug}/info"
            logger.debug(f"Fetching add-on details for: {addon_slug}")
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('data', {})
                else:
                    logger.warning(f"Failed to get details for {addon_slug}: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error getting add-on details: {e}", exc_info=True)
            return None
    
    async def get_all_updates(self) -> List[Dict]:
        """Get all available updates from update entities (Core, Supervisor, OS, Add-ons, Integrations)
        
        Compatible with Home Assistant versions: {HA_COMPATIBILITY_VERSIONS}
        """
        try:
            url = f"{self.config.ha_url}/api/states"
            logger.debug(f"Fetching all update entities from: {url}")
            async with self.session.get(url) as response:
                if response.status == 200:
                    states = await response.json()
                    logger.debug(f"Retrieved {len(states)} total states")
                    
                    # Log entity domain breakdown
                    if logger.isEnabledFor(logging.DEBUG):
                        domains = {}
                        for state in states:
                            domain = state.get('entity_id', '').split('.')[0]
                            domains[domain] = domains.get(domain, 0) + 1
                        logger.debug(f"Entity domains: {dict(sorted(domains.items(), key=lambda x: -x[1])[:10])}")
                    
                    # Log sample update entities
                    update_entities = [s for s in states if s.get('entity_id', '').startswith('update.')]
                    logger.debug(f"Found {len(update_entities)} entities with 'update.' domain")
                    
                    if update_entities and logger.isEnabledFor(logging.DEBUG):
                        sample_entities = update_entities[:5]
                        for entity in sample_entities:
                            logger.debug(f"  Sample: {entity.get('entity_id')} | state={entity.get('state')}")
                    
                    # Look for all update.* entities with state 'on' (update available)
                    all_updates = []
                    update_entities_found = 0
                    
                    for state in states:
                        entity_id = state.get('entity_id', '')
                        # Filter for update domain entities
                        if entity_id.startswith('update.'):
                            update_entities_found += 1
                            # Check if update is available
                            entity_state = state.get('state', '')
                            if entity_state == 'on':
                                attributes = state.get('attributes', {})
                                
                                # Validate that required attributes are present
                                if not self._validate_update_entity(entity_id, attributes):
                                    logger.warning(f"Update entity {entity_id} missing required attributes, skipping")
                                    continue
                                
                                # Determine update type based on entity_id
                                update_type = self._categorize_update(entity_id, attributes)
                                
                                update_info = {
                                    'entity_id': entity_id,
                                    'name': attributes.get('friendly_name', attributes.get('title', entity_id)),
                                    'type': update_type,
                                    'current_version': attributes.get('installed_version', 'unknown'),
                                    'latest_version': attributes.get('latest_version', 'unknown'),
                                    'release_summary': attributes.get('release_summary', ''),
                                    'release_url': attributes.get('release_url', ''),
                                    'entity_picture': attributes.get('entity_picture', ''),
                                }
                                all_updates.append(update_info)
                                logger.debug(f"  Update: {update_info['name']} ({update_info['type']}) {update_info['current_version']} → {update_info['latest_version']}")
                    
                    logger.info(f"Found {len(all_updates)} total updates from {update_entities_found} update entities")
                    
                    # Log a compatibility hint if no update entities were found at all
                    if update_entities_found == 0:
                        logger.warning("No update.* entities found in Home Assistant")
                        logger.warning("This may indicate:")
                        logger.warning("  - Updates are not yet available")
                        logger.warning("  - Update entities are not enabled in your HA configuration")
                        logger.warning("  - Compatibility issue with HA version (expected 2024.11+)")
                    
                    return all_updates
                elif response.status == 404:
                    logger.error(f"API endpoint not found: {url}")
                    logger.error("This is unexpected - the /api/states endpoint should exist in all HA installations")
                    logger.error("Please verify:")
                    logger.error("  - Home Assistant is running and accessible")
                    logger.error("  - The HA URL is correct in add-on configuration")
                    logger.error("  - Your HA version (this add-on is tested with 2024.11+)")
                    return []
                else:
                    logger.error(f"Failed to get states: {response.status}")
                    if response.status == 401:
                        self._log_auth_error("Unable to fetch update entities from Home Assistant API")
                    elif response.status == 403:
                        logger.error("Permission denied accessing Home Assistant API")
                        logger.error("Ensure 'homeassistant_api: true' is set in the add-on configuration")
                    return []
        except Exception as e:
            logger.error(f"Error getting all updates: {e}", exc_info=True)
            return []
    
    def _validate_update_entity(self, entity_id: str, attributes: Dict) -> bool:
        """Validate that update entity has required attributes for compatibility"""
        # At minimum, we expect version information
        has_installed = 'installed_version' in attributes
        has_latest = 'latest_version' in attributes
        
        if not (has_installed and has_latest):
            logger.debug(f"Entity {entity_id} missing version attributes: "
                        f"installed_version={has_installed}, latest_version={has_latest}")
            return False
        
        return True
    
    def _categorize_update(self, entity_id: str, attributes: Dict) -> str:
        """Categorize update entity by type"""
        entity_lower = entity_id.lower()
        
        # Check for specific system components first (most specific)
        if 'home_assistant_core' in entity_lower:
            return UPDATE_TYPE_CORE
        elif 'home_assistant_supervisor' in entity_lower:
            return UPDATE_TYPE_SUPERVISOR
        elif 'home_assistant_os' in entity_lower or 'operating_system' in entity_lower:
            return UPDATE_TYPE_OS
        # Check if it's a HACS integration
        # HACS entities typically have 'hacs' in the entity_id or specific attributes
        elif 'hacs' in entity_lower:
            return UPDATE_TYPE_HACS
        # Check for add-on specific patterns
        elif 'addon' in entity_lower:
            return UPDATE_TYPE_ADDON
        # Check if it has a repository URL (likely a custom integration, treat as HACS)
        elif attributes.get('repository', '').startswith(('https://github.com/', 'http://github.com/')):
            return UPDATE_TYPE_HACS
        # Default to integration for other update entities
        else:
            return UPDATE_TYPE_INTEGRATION
    
    async def get_hacs_updates(self) -> List[Dict]:
        """Get available HACS integration updates (legacy method, prefer get_all_updates)"""
        try:
            # Check if HACS is installed by looking for HACS entities
            url = f"{self.config.ha_url}/api/states"
            logger.debug(f"Fetching states from: {url}")
            async with self.session.get(url) as response:
                if response.status == 200:
                    states = await response.json()
                    logger.debug(f"Retrieved {len(states)} total states")
                    
                    # Look for HACS update sensors
                    hacs_updates = []
                    for state in states:
                        entity_id = state.get('entity_id', '')
                        if 'hacs' in entity_id.lower() and 'update' in entity_id.lower():
                            if state.get('state') == 'on' or state.get('state', '').isdigit():
                                attributes = state.get('attributes', {})
                                update_info = {
                                    'entity_id': entity_id,
                                    'name': attributes.get('friendly_name', entity_id),
                                    'current_version': attributes.get('current_version', 'unknown'),
                                    'latest_version': attributes.get('latest_version', 'unknown'),
                                    'repository': attributes.get('repository', ''),
                                }
                                hacs_updates.append(update_info)
                                logger.debug(f"  HACS update: {update_info['name']} ({update_info['current_version']} → {update_info['latest_version']})")
                    
                    logger.info(f"Found {len(hacs_updates)} HACS updates")
                    return hacs_updates
                else:
                    logger.error(f"Failed to get states: {response.status}")
                    if response.status == 401:
                        self._log_auth_error("Unable to fetch HACS updates from Home Assistant API")
                    return []
        except Exception as e:
            logger.error(f"Error getting HACS updates: {e}", exc_info=True)
            return []
    
    async def create_persistent_notification(self, title: str, message: str, notification_id: str):
        """Create a persistent notification in Home Assistant"""
        try:
            url = f"{self.config.ha_url}/api/services/persistent_notification/create"
            logger.debug(f"Creating persistent notification: {notification_id}")
            payload = {
                'title': title,
                'message': message,
                'notification_id': notification_id
            }
            async with self.session.post(url, json=payload) as response:
                if response.status in (200, 201):
                    logger.info(f"Created notification: {notification_id}")
                    return True
                else:
                    logger.error(f"Failed to create notification: {response.status}")
                    if response.status == 401:
                        self._log_auth_error("Unable to create notification")
                    return False
        except Exception as e:
            logger.error(f"Error creating notification: {e}", exc_info=True)
            return False
    
    async def set_sensor_state(self, entity_id: str, state: str, attributes: Dict):
        """Set state for a custom sensor entity"""
        try:
            url = f"{self.config.ha_url}/api/states/{entity_id}"
            logger.debug(f"Updating sensor: {entity_id} = {state}")
            payload = {
                'state': state,
                'attributes': attributes
            }
            async with self.session.post(url, json=payload) as response:
                if response.status in (200, 201):
                    logger.debug(f"Updated sensor {entity_id}")
                    return True
                else:
                    logger.error(f"Failed to update sensor: {response.status}")
                    if response.status == 401:
                        self._log_auth_error("Unable to update sensor state")
                    return False
        except Exception as e:
            logger.error(f"Error updating sensor: {e}", exc_info=True)
            return False
    
    async def create_lovelace_dashboard(self, dashboard_config: Dict) -> bool:
        """Create a Lovelace dashboard in Home Assistant
        
        DEPRECATED: This feature is deprecated and does not work for Home Assistant add-ons.
        The Lovelace dashboard API endpoint is not accessible to add-ons due to permission
        restrictions. Users should use the built-in WebUI for visualization instead.
        
        This method is kept for backward compatibility but will always fail.
        
        Compatible with Home Assistant versions: {HA_COMPATIBILITY_VERSIONS}
        """
        logger.warning("=" * 60)
        logger.warning("ATTEMPTING DEPRECATED DASHBOARD CREATION")
        logger.warning("=" * 60)
        logger.warning("This will fail due to Home Assistant API restrictions.")
        logger.warning("Please use the WebUI instead (accessible via Sentry sidebar panel).")
        logger.warning("=" * 60)
        
        try:
            url = f"{self.config.ha_url}/api/lovelace/dashboards"
            logger.info("Attempting to create Sentry dashboard in Lovelace")
            logger.debug(f"Dashboard API URL: {url}")
            logger.debug(f"POST {url}")
            logger.debug(f"Payload: {json.dumps(dashboard_config, indent=2)[:500]}")
            logger.debug(f"Dashboard creation URL: {url}")
            logger.debug(f"Dashboard config: {dashboard_config.get('url_path')}, title: {dashboard_config.get('title')}")
            
            # First, test if the endpoint exists by attempting a GET request
            # Note: Some endpoints may only accept POST and return 405 for GET,
            # in which case we proceed with the POST attempt anyway.
            logger.debug("Testing Lovelace dashboards endpoint accessibility...")
            try:
                async with self.session.get(url) as test_response:
                    logger.debug(f"GET endpoint test status: {test_response.status}")
                    if test_response.status == 404:
                        self._log_dashboard_endpoint_not_found()
                        return False
                    elif test_response.status == 401:
                        self._log_dashboard_permission_error()
                        return False
                    # Note: 405 Method Not Allowed is acceptable here - endpoint exists but doesn't accept GET
            except Exception as e:
                logger.debug(f"Endpoint test failed: {e}")
                # Continue to POST attempt even if GET test fails due to network issues
            
            # Attempt to create the dashboard
            async with self.session.post(url, json=dashboard_config) as response:
                if response.status in (200, 201):
                    logger.info("Successfully created Sentry dashboard")
                    return True
                elif response.status == 409:
                    logger.info("Dashboard already exists, skipping creation")
                    return True
                elif response.status == 404:
                    logger.error(f"Lovelace dashboard API endpoint not found: {url}")
                    logger.error("This may indicate a Home Assistant version compatibility issue")
                    logger.error("The /api/lovelace/dashboards endpoint should be available in HA 2024.11+")
                    logger.info("WORKAROUND: Disable 'auto_create_dashboard' and manually create your dashboard")
                    logger.info("See documentation: https://github.com/ian-morgan99/Home-Assistant-Sentry/blob/main/DOCS.md#dashboard-integration")
                    return False
                elif response.status == 403:
                    logger.error("Permission denied creating Lovelace dashboard")
                    response_text = await response.text()
                    logger.error(f"Failed to create dashboard: {response.status} - {response_text}")
                    self._log_dashboard_endpoint_not_found()
                    return False
                elif response.status == 401:
                    response_text = await response.text()
                    logger.error(f"Failed to create dashboard: {response.status} - {response_text}")
                    self._log_dashboard_permission_error()
                    return False
                else:
                    response_text = await response.text()
                    logger.error(f"Failed to create dashboard: {response.status} - {response_text}")
                    return False
        except Exception as e:
            logger.error(f"Error creating dashboard: {e}", exc_info=True)
            return False
    
    async def get_installation_summary(self, scope: str = 'full') -> Dict:
        """
        Get a privacy-preserving summary of the Home Assistant installation
        for AI review and recommendations.
        
        This method collects metadata about the installation WITHOUT collecting
        sensitive data like:
        - Entity state values
        - Personal information
        - Location data
        - API keys or tokens
        - Device identifiers
        
        Args:
            scope: What to collect - 'full', 'integrations', or 'automations'
        
        Returns:
            Dict with installation summary including:
            - integration_count: Number of active integrations
            - device_count: Number of devices
            - entity_counts: Count by domain (sensor, switch, light, etc.)
            - automation_count: Number of automations
            - helper_count: Number of input helpers
            - dashboard_count: Number of dashboards
            - integration_list: List of integration domains (no config data)
            - device_types: Counts by device type/manufacturer
            - entity_domains: Breakdown of entities by domain
        """
        try:
            logger.info(f"Collecting installation summary (scope: {scope})")
            summary = {
                'scope': scope,
                'timestamp': datetime.now().isoformat()
            }
            
            # Always collect basic integration info (core to all scopes)
            if scope in ['full', 'integrations']:
                # Get all entity states to derive integration info
                url = f"{self.config.ha_url}/api/states"
                logger.debug(f"Fetching entity states for integration analysis: {url}")
                async with self.session.get(url) as response:
                    if response.status == 200:
                        states = await response.json()
                        
                        # Count entities by domain (sensor, light, switch, etc.)
                        entity_domains = {}
                        integration_domains = set()
                        
                        for state in states:
                            entity_id = state.get('entity_id', '')
                            domain = entity_id.split('.')[0] if '.' in entity_id else 'unknown'
                            entity_domains[domain] = entity_domains.get(domain, 0) + 1
                            
                            # Track unique integrations via entity attributes
                            # Check multiple possible attributes: integration, attribution, etc.
                            attributes = state.get('attributes', {})
                            
                            # Try 'integration' first (most common)
                            if 'integration' in attributes:
                                integration_domains.add(attributes['integration'])
                            # Try 'attribution' (used by many integrations)
                            elif 'attribution' in attributes:
                                attribution = attributes['attribution']
                                # Extract integration name from attribution string
                                # Common formats: "Data provided by X", "Powered by X", etc.
                                # Also look for integration domain in attribution
                                if isinstance(attribution, str):
                                    # If attribution contains a recognizable domain, use it
                                    parts = attribution.lower().split()
                                    for part in parts:
                                        if part in ['hacs', 'mqtt', 'esphome', 'zwave', 'zigbee']:
                                            integration_domains.add(part)
                                            break
                            # Try to infer from entity_id domain for core integrations
                            elif domain in ['sensor', 'binary_sensor', 'light', 'switch', 
                                          'climate', 'cover', 'fan', 'lock', 'media_player']:
                                # For common domains, check device_class or other hints
                                # Don't add the domain itself as integration unless it's clear
                                pass
                        
                        summary['entity_domains'] = entity_domains
                        summary['entity_count'] = len(states)
                        summary['unique_domains'] = len(entity_domains)
                        summary['integrations'] = sorted(list(integration_domains))
                        summary['integration_count'] = len(integration_domains)
                        
                        logger.debug(f"Collected entity domain statistics: {len(entity_domains)} unique domains")
                    else:
                        logger.warning(f"Failed to fetch states: {response.status}")
                        summary['entity_domains'] = {}
                        summary['entity_count'] = 0
                
                # Get device registry info (without sensitive device data)
                try:
                    url = f"{self.config.ha_url}/api/config/device_registry/list"
                    logger.debug(f"Fetching device registry: {url}")
                    async with self.session.get(url) as response:
                        if response.status == 200:
                            devices = await response.json()
                            
                            # Count devices by manufacturer (anonymized)
                            manufacturers = {}
                            device_types = {}
                            
                            for device in devices:
                                # Get manufacturer without exposing specific device IDs
                                manufacturer = device.get('manufacturer', 'Unknown')
                                manufacturers[manufacturer] = manufacturers.get(manufacturer, 0) + 1
                                
                                # Get model type for categorization
                                model = device.get('model', 'Unknown')
                                device_types[model] = device_types.get(model, 0) + 1
                            
                            summary['device_count'] = len(devices)
                            summary['manufacturers'] = manufacturers
                            summary['device_types'] = device_types
                            
                            logger.debug(f"Collected device statistics: {len(devices)} devices from {len(manufacturers)} manufacturers")
                        else:
                            logger.warning(f"Failed to fetch device registry: {response.status}")
                            summary['device_count'] = 0
                except Exception as e:
                    logger.warning(f"Error fetching device registry: {e}")
                    summary['device_count'] = 0
            
            # Collect automation and script info
            if scope in ['full', 'automations']:
                try:
                    # Get automation count and basic metadata (no automation logic)
                    url = f"{self.config.ha_url}/api/states"
                    async with self.session.get(url) as response:
                        if response.status == 200:
                            states = await response.json()
                            
                            # Count automations and scripts
                            automation_count = sum(1 for s in states if s.get('entity_id', '').startswith('automation.'))
                            script_count = sum(1 for s in states if s.get('entity_id', '').startswith('script.'))
                            
                            # Count input helpers (input_boolean, input_number, etc.)
                            helper_count = sum(1 for s in states if s.get('entity_id', '').startswith('input_'))
                            
                            summary['automation_count'] = automation_count
                            summary['script_count'] = script_count
                            summary['helper_count'] = helper_count
                            
                            logger.debug(f"Collected automation statistics: {automation_count} automations, {script_count} scripts, {helper_count} helpers")
                except Exception as e:
                    logger.warning(f"Error collecting automation statistics: {e}")
                    summary['automation_count'] = 0
                    summary['script_count'] = 0
                    summary['helper_count'] = 0
            
            # Collect dashboard info (count only, no content)
            if scope == 'full':
                try:
                    # Get dashboard count
                    url = f"{self.config.ha_url}/api/lovelace/dashboards"
                    async with self.session.get(url) as response:
                        if response.status == 200:
                            dashboards = await response.json()
                            summary['dashboard_count'] = len(dashboards) if isinstance(dashboards, list) else 0
                            logger.debug(f"Collected dashboard count: {summary['dashboard_count']}")
                        else:
                            # Dashboard API may not be accessible
                            summary['dashboard_count'] = 0
                except Exception as e:
                    logger.debug(f"Dashboard count not available: {e}")
                    summary['dashboard_count'] = 0
            
            logger.info(f"Installation summary collected: {summary.get('entity_count', 0)} entities, "
                       f"{summary.get('device_count', 0)} devices, "
                       f"{summary.get('integration_count', 0)} integrations")
            
            return summary
            
        except Exception as e:
            logger.error(f"Error collecting installation summary: {e}", exc_info=True)
            return {'error': str(e), 'scope': scope}
