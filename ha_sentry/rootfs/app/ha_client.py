"""
Home Assistant API Client
"""
import aiohttp
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Update type constants
UPDATE_TYPE_CORE = 'core'
UPDATE_TYPE_SUPERVISOR = 'supervisor'
UPDATE_TYPE_OS = 'os'
UPDATE_TYPE_ADDON = 'addon'
UPDATE_TYPE_HACS = 'hacs'
UPDATE_TYPE_INTEGRATION = 'integration'


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
        """Get all available updates from update entities (Core, Supervisor, OS, Add-ons, Integrations)"""
        try:
            url = f"{self.config.ha_url}/api/states"
            logger.debug(f"Fetching all update entities from: {url}")
            async with self.session.get(url) as response:
                if response.status == 200:
                    states = await response.json()
                    logger.debug(f"Retrieved {len(states)} total states")
                    
                    # Look for all update.* entities with state 'on' (update available)
                    all_updates = []
                    for state in states:
                        entity_id = state.get('entity_id', '')
                        # Filter for update domain entities
                        if entity_id.startswith('update.'):
                            # Check if update is available
                            entity_state = state.get('state', '')
                            if entity_state == 'on':
                                attributes = state.get('attributes', {})
                                
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
                    
                    logger.info(f"Found {len(all_updates)} total updates")
                    return all_updates
                else:
                    logger.error(f"Failed to get states: {response.status}")
                    if response.status == 401:
                        self._log_auth_error("Unable to fetch update entities from Home Assistant API")
                    return []
        except Exception as e:
            logger.error(f"Error getting all updates: {e}", exc_info=True)
            return []
    
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
        
        Note: This feature has limited support. Home Assistant add-ons may not have 
        sufficient permissions to create Lovelace dashboards via the API.
        Consider disabling auto_create_dashboard and manually creating dashboards instead.
        """
        try:
            url = f"{self.config.ha_url}/api/lovelace/dashboards"
            logger.info("Attempting to create Sentry dashboard in Lovelace")
            logger.debug(f"Dashboard creation URL: {url}")
            logger.debug(f"Dashboard config: {dashboard_config.get('url_path')}, title: {dashboard_config.get('title')}")
            
            # First, test if the endpoint exists by attempting a GET request
            logger.debug("Testing Lovelace dashboards endpoint accessibility...")
            try:
                async with self.session.get(url) as test_response:
                    logger.debug(f"GET endpoint test status: {test_response.status}")
                    if test_response.status == 404:
                        self._log_dashboard_endpoint_not_found()
                        return False
            except Exception as e:
                logger.debug(f"Endpoint test failed: {e}")
            
            # Attempt to create the dashboard
            async with self.session.post(url, json=dashboard_config) as response:
                if response.status in (200, 201):
                    logger.info("Successfully created Sentry dashboard")
                    return True
                elif response.status == 409:
                    logger.info("Dashboard already exists, skipping creation")
                    return True
                elif response.status == 404:
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
