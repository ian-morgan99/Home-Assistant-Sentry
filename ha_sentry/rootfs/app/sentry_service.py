"""
Main Sentry Service - Coordinates update checking and analysis
"""
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List
from urllib.parse import quote

from ha_client import HomeAssistantClient, HA_COMPATIBILITY_VERSIONS
from ai_client import AIClient
from dashboard_manager import DashboardManager
from dependency_graph_builder import DependencyGraphBuilder
from web_server import DependencyTreeWebServer
from log_monitor import LogMonitor
from log_obfuscator import LogObfuscator

logger = logging.getLogger(__name__)

# Update type categorization constants
UPDATE_TYPE_CORE = 'core'
UPDATE_TYPE_SUPERVISOR = 'supervisor'
UPDATE_TYPE_OS = 'os'
UPDATE_TYPE_ADDON = 'addon'
UPDATE_TYPE_HACS = 'hacs'
UPDATE_TYPE_INTEGRATION = 'integration'

# Grouping for analysis (for backward compatibility with existing AI analysis)
# These map to the two categories the AI analyzer expects: addon_updates and hacs_updates
ADDON_ANALYSIS_TYPES = [UPDATE_TYPE_CORE, UPDATE_TYPE_SUPERVISOR, UPDATE_TYPE_OS, UPDATE_TYPE_ADDON]
INTEGRATION_ANALYSIS_TYPES = [UPDATE_TYPE_HACS, UPDATE_TYPE_INTEGRATION]


class SentryService:
    """Main service for monitoring and analyzing Home Assistant updates"""
    
    # Constants
    WEB_UI_PORT = 8099  # Port for dependency visualization web interface
    ADDON_SLUG = 'ha_sentry'  # Addon slug for ingress URLs
    
    def __init__(self, config):
        """Initialize the sentry service"""
        self.config = config
        self.running = False
        self.dependency_graph = None
        self.dependency_graph_builder = None
        self.web_server = None
        self._graph_build_task = None
        self._graph_build_status = 'not_started'  # Track graph build status: not_started, building, completed, failed
        self._graph_build_error = None  # Store error message if build fails
        
        # Note: Dependency graph will be built asynchronously after service starts
        # This ensures the web server starts quickly without blocking
        if not config.enable_dependency_graph:
            logger.info("Dependency graph building is disabled in configuration")
            logger.info("  enable_dependency_graph: false")
            logger.info("  Note: Web UI will not be available without dependency graph")
            self._graph_build_status = 'disabled'
        
        # Initialize AI client with dependency graph (will be None initially)
        self.ai_client = AIClient(config, dependency_graph=self.dependency_graph)
        
        # Initialize log monitor
        obfuscator = LogObfuscator(enabled=config.obfuscate_logs)
        self.log_monitor = LogMonitor(config, obfuscator=obfuscator)
        
        logger.info("Sentry Service initialized")
    
    async def _build_dependency_graph_async(self):
        """Build dependency graph asynchronously in background"""
        try:
            self._graph_build_status = 'building'
            logger.info("=" * 60)
            logger.info("DEPENDENCY GRAPH INITIALIZATION (Background)")
            logger.info("=" * 60)
            logger.info("Building dependency graph from installed integrations and addons...")
            
            # Reuse the existing builder instance that was passed to the web server
            # This ensures the web server sees the populated data when building completes
            graph_builder = self.dependency_graph_builder
            
            # Create HA client for addon metadata fetching
            async with HomeAssistantClient(self.config) as ha_client:
                # Set the client on the builder for addon fetching
                graph_builder.ha_client = ha_client
                
                # Use custom paths if provided, otherwise use defaults
                integration_paths = None
                if hasattr(self.config, 'custom_integration_paths') and self.config.custom_integration_paths:
                    logger.info(f"Using custom integration paths: {self.config.custom_integration_paths}")
                    integration_paths = self.config.custom_integration_paths
                else:
                    logger.info("Using default integration paths")
                
                # Build the graph (runs in executor to avoid blocking)
                graph_data = await asyncio.get_event_loop().run_in_executor(
                    None, graph_builder.build_graph_from_paths, integration_paths
                )
                
                # Fetch addon dependencies
                logger.info("Fetching addon dependencies from Supervisor API...")
                try:
                    await graph_builder.fetch_addon_dependencies()
                    # Rebuild dependency map to include addon data
                    await asyncio.get_event_loop().run_in_executor(
                        None, graph_builder._build_dependency_map
                    )
                    # Regenerate graph structure with addon data
                    graph_data = await asyncio.get_event_loop().run_in_executor(
                        None, graph_builder._generate_graph_structure
                    )
                except Exception as e:
                    logger.warning(f"Failed to fetch addon dependencies: {e}")
                    logger.info("Continuing with integration dependencies only")
            
            self.dependency_graph = graph_data
            # No need to reassign self.dependency_graph_builder - we're using the same instance
            
            # Update AI client with new graph
            self.ai_client.dependency_graph = graph_data
            
            stats = graph_data.get('machine_readable', {}).get('statistics', {})
            
            # Check if we actually found any integrations
            if stats.get('total_integrations', 0) == 0:
                self._graph_build_status = 'failed'
                self._graph_build_error = 'No integrations found - check add-on logs for path scanning details'
                logger.warning("=" * 60)
                logger.warning("DEPENDENCY GRAPH BUILD COMPLETED BUT EMPTY")
                logger.warning("=" * 60)
                logger.warning("The dependency graph was built successfully, but no integrations were found.")
                logger.warning("")
                logger.warning("This means:")
                logger.warning("  - The web UI will show 'No integrations found'")
                logger.warning("  - Dependency analysis features will be limited")
                logger.warning("")
                logger.warning("Common causes:")
                logger.warning("  1. Integration paths are incorrect or not accessible")
                logger.warning("  2. Home Assistant is installed in a non-standard location")
                logger.warning("  3. File system permissions prevent reading integration directories")
                logger.warning("")
                logger.warning("The add-on will continue to run with limited functionality.")
                logger.warning("Check the logs above for path scanning details and suggestions.")
                logger.warning("=" * 60)
            else:
                self._graph_build_status = 'completed'
                logger.info(f"✅ Dependency graph built successfully")
                logger.info(f"   Total integrations: {stats.get('total_integrations', 0)}")
                logger.info(f"   Total dependencies: {stats.get('total_dependencies', 0)}")
                if stats.get('high_risk_dependencies', 0) > 0:
                    logger.info(f"   High-risk dependencies: {stats.get('high_risk_dependencies', 0)}")
                logger.info("=" * 60)
            
        except Exception as e:
            self._graph_build_status = 'failed'
            self._graph_build_error = str(e)
            logger.error("=" * 60)
            logger.error("DEPENDENCY GRAPH BUILD FAILED")
            logger.error("=" * 60)
            logger.error(f"Failed to build dependency graph: {e}", exc_info=True)
            logger.error("")
            logger.error("This means:")
            logger.error("  - The web UI will show an error message indicating the dependency graph is unavailable")
            logger.error("  - Dependency analysis features will be limited")
            logger.error("")
            logger.error("Common causes:")
            logger.error("  1. Integration manifest files are corrupted or missing")
            logger.error("  2. File system permissions issues")
            logger.error("  3. Invalid custom integration paths in configuration")
            logger.error("")
            logger.error("To resolve:")
            logger.error("  1. Check add-on logs for detailed error information")
            logger.error("  2. Verify Home Assistant integrations are properly installed")
            logger.error("  3. Try disabling custom_integration_paths if configured")
            logger.error("  4. If issue persists, disable dependency graph:")
            logger.error("     Set 'enable_dependency_graph: false' in configuration")
            logger.error("=" * 60)
            logger.info("Continuing without dependency graph analysis")
    
    async def rebuild_dependency_graph(self):
        """Rebuild the dependency graph (e.g., after new component installation)"""
        logger.info("Rebuilding dependency graph...")
        await self._build_dependency_graph_async()
    
    async def stop(self):
        """Stop the service and cleanup background tasks"""
        logger.info("Stopping Sentry service...")
        self.running = False
        
        # Cancel the graph build task if still running
        if self._graph_build_task and not self._graph_build_task.done():
            logger.info("Cancelling dependency graph build task...")
            self._graph_build_task.cancel()
            try:
                await self._graph_build_task
            except asyncio.CancelledError:
                logger.debug("Dependency graph build task cancelled")
        
        # Stop web server
        if self.web_server:
            await self.web_server.stop()
        
        logger.info("Sentry service stopped")
    
    async def start(self):
        """Start the service"""
        self.running = True
        logger.info(f"Starting service with schedule: {self.config.check_schedule}")
        
        # Create the dependency graph builder instance first
        # This single instance will be shared by both the async builder and web server
        # ensuring they reference the same data structure
        if self.config.enable_dependency_graph:
            if not self.dependency_graph_builder:
                self.dependency_graph_builder = DependencyGraphBuilder()
            logger.info("Starting dependency graph build in background...")
            self._graph_build_task = asyncio.create_task(self._build_dependency_graph_async())
        else:
            self._graph_build_status = 'disabled'
        
        # Start web server for dependency visualization if enabled
        # Note: Web server will start immediately, even before graph is built
        # The /api/components endpoint will return empty list until graph is ready
        if self.config.enable_web_ui:
            try:
                logger.info("Starting web server for dependency visualization...")
                logger.info(f"  Web UI port: {self.config.port}")
                logger.info(f"  Dependency graph: Building in background...")
                # Ensure builder exists (in case dependency_graph is disabled)
                # The web server needs a builder reference to function
                if not self.dependency_graph_builder:
                    self.dependency_graph_builder = DependencyGraphBuilder()
                self.web_server = DependencyTreeWebServer(
                    self.dependency_graph_builder,
                    self.config,
                    port=self.config.port,
                    sentry_service=self  # Pass self for status checking
                )
                await self.web_server.start()
            except Exception as e:
                logger.error(f"Failed to start web server: {e}", exc_info=True)
                logger.error("Web UI will not be available")
                logger.info("To troubleshoot:")
                logger.info(f"  1. Check if port {self.config.port} is already in use")
                logger.info("  2. Verify 'enable_dependency_graph' is true in configuration")
                logger.info("  3. Check add-on logs for dependency graph building errors")
                logger.info("Continuing without web UI")
        elif not self.config.enable_web_ui:
            logger.info("Web UI disabled in configuration (enable_web_ui: false)")
        
        # Send startup notification to help users find sensors
        await self._send_startup_notification()
        
        # Delay initial check to allow web UI to become fully responsive first
        # This ensures users can access the WebUI even if AI provider is slow/unresponsive
        # The 5-second delay gives the web server time to handle initial page loads
        logger.info("Scheduling initial update check as background task (delayed 5 seconds)...")
        asyncio.create_task(self._run_initial_check_delayed())
        
        # Start scheduled checks
        await self._schedule_checks()
    
    async def _send_startup_notification(self):
        """Send a startup notification to guide users on accessing sensors"""
        try:
            async with HomeAssistantClient(self.config) as ha_client:
                notification_title = "🚀 Home Assistant Sentry Started"
                
                # Check if web UI is available
                web_ui_info = ""
                if self.config.enable_web_ui and self.web_server:
                    web_ui_info = """
**📊 WebUI - Dependency Tree Visualization:**

Access the interactive WebUI for dependency analysis and impact visualization:
1. **Via Sidebar Panel**: Look for the 'Sentry' panel in your Home Assistant sidebar (preferred method)
2. **Via Add-on Settings**: Settings → Add-ons → Home Assistant Sentry → Open Web UI
3. **Direct Ingress URL**: `/hassio/ingress/ha_sentry`

The WebUI provides:
- Interactive dependency graphs
- "Where Used" analysis for any integration
- Change impact reports
- Full system dependency visualization

"""
                
                if self.config.create_dashboard_entities:
                    notification_message = f"""✅ **Home Assistant Sentry is now running!**

**How to View Your Sensors:**

After the first check completes, you should see 6 sensor entities:

1. Go to **Developer Tools** → **States**
2. Search for `sensor.ha_sentry` to see all Sentry sensors:
   - `sensor.ha_sentry_update_status` - Overall status
   - `sensor.ha_sentry_updates_available` - Update count
   - `sensor.ha_sentry_addon_updates` - Add-on updates
   - `sensor.ha_sentry_hacs_updates` - HACS updates
   - `sensor.ha_sentry_issues` - Issues detected
   - `sensor.ha_sentry_confidence` - Analysis confidence

**Create Your Dashboard:**

Add these sensors to a dashboard card. See the [Documentation](https://github.com/ian-morgan99/Home-Assistant-Sentry/blob/main/DOCS.md#dashboard-integration) for examples.

{web_ui_info}**What Happens Next:**

- First update check is running now
- You'll receive a notification with analysis results
- Daily checks run at {self.config.check_schedule}

**Troubleshooting:**

If sensors don't appear, check the add-on logs for authentication errors. The add-on requires proper Home Assistant API permissions to create sensors.

*This notification will not be shown again.*
"""
                else:
                    notification_message = f"""✅ **Home Assistant Sentry is now running!**

**What Happens Next:**

- First update check is running now
- You'll receive a notification with analysis results
- Daily checks run at {self.config.check_schedule}

**Note:** Dashboard entities are currently disabled in your configuration. Enable `create_dashboard_entities: true` to see sensor entities.

*This notification will not be shown again.*
"""
                
                await ha_client.create_persistent_notification(
                    notification_title,
                    notification_message,
                    'ha_sentry_startup'
                )
                logger.info("Sent startup notification to guide users")
        except Exception as e:
            logger.error(f"Error sending startup notification: {e}", exc_info=True)
    
    async def _run_initial_check_delayed(self):
        """Run the initial update check as a background task with delay
        
        Delays the initial update check by 5 seconds to ensure the WebUI becomes
        responsive before potentially slow AI analysis starts. This prevents users
        from experiencing blocked or slow WebUI during the critical startup window.
        """
        try:
            # Wait 5 seconds to allow web UI to become responsive first
            # This prevents slow/unresponsive AI providers from affecting WebUI load
            logger.debug("Waiting 5 seconds before initial update check...")
            await asyncio.sleep(5)
            logger.info("Running initial update check...")
            await self.run_update_check()
            logger.info("Initial update check completed")
        except Exception as e:
            logger.error(f"Error in initial update check: {e}", exc_info=True)
            logger.info("Initial check failed, but service will continue with scheduled checks")
    
    async def _run_initial_check(self):
        """Run the initial update check as a background task (no delay)
        
        This method is kept for potential future use (e.g., manual triggers, tests)
        but is not currently called during normal startup. Use _run_initial_check_delayed
        for startup to ensure WebUI responsiveness.
        """
        try:
            logger.info("Running initial update check...")
            await self.run_update_check()
            logger.info("Initial update check completed")
        except Exception as e:
            logger.error(f"Error in initial update check: {e}", exc_info=True)
            logger.info("Initial check failed, but service will continue with scheduled checks")
    
    async def _schedule_checks(self):
        """Schedule periodic update checks"""
        while self.running:
            try:
                # Parse schedule time (HH:MM format)
                schedule_hour, schedule_minute = map(int, self.config.check_schedule.split(':'))
                
                # Calculate time until next check
                now = datetime.now()
                target_time = now.replace(hour=schedule_hour, minute=schedule_minute, second=0, microsecond=0)
                
                # If target time has passed today, schedule for tomorrow
                if target_time <= now:
                    target_time += timedelta(days=1)
                
                wait_seconds = (target_time - now).total_seconds()
                logger.info(f"Next check scheduled in {wait_seconds/3600:.2f} hours at {target_time}")
                logger.debug(f"Waiting {wait_seconds} seconds until next scheduled check")
                
                # Wait until scheduled time
                await asyncio.sleep(wait_seconds)
                
                # Run the check
                logger.debug("Scheduled time reached, starting update check")
                await self.run_update_check()
                
            except Exception as e:
                logger.error(f"Error in scheduler: {e}", exc_info=True)
                # Wait 1 hour before retrying on error
                logger.info("Retrying in 1 hour due to scheduler error")
                await asyncio.sleep(3600)
    
    async def run_update_check(self):
        """Run a complete update check and analysis"""
        logger.info("=" * 60)
        logger.info("Starting update check cycle")
        logger.info("=" * 60)
        
        try:
            async with HomeAssistantClient(self.config) as ha_client:
                # Gather updates - use comprehensive update checking by default
                all_updates = []
                addon_updates = []
                hacs_updates = []
                
                if self.config.check_all_updates:
                    # New comprehensive method: get all update entities
                    logger.info("Checking for all available updates (Core, Supervisor, OS, Add-ons, Integrations)...")
                    logger.debug("Querying Home Assistant API for all update.* entities")
                    all_updates = await ha_client.get_all_updates()
                    logger.info(f"Found {len(all_updates)} total updates")
                    
                    # If get_all_updates returns empty, try fallback to legacy methods
                    if len(all_updates) == 0:
                        logger.warning("No updates found via unified API - attempting legacy fallback methods")
                        logger.info("This may indicate:")
                        logger.info("  - No updates are currently available (normal)")
                        logger.info("  - Update entities are not configured in Home Assistant")
                        logger.info("  - Possible API compatibility issue with HA version")
                        
                        # Try fallback: check supervisor API directly for add-ons
                        logger.debug("Fallback: Checking Supervisor API for add-on updates")
                        addon_updates_fallback = await ha_client.get_addon_updates()
                        if len(addon_updates_fallback) > 0:
                            logger.info(f"Fallback successful: Found {len(addon_updates_fallback)} add-on updates via Supervisor API")
                            addon_updates = addon_updates_fallback
                            all_updates.extend(addon_updates_fallback)
                        else:
                            logger.debug("No add-on updates found via Supervisor API fallback")
                    
                    # For backward compatibility with analysis, categorize updates
                    # The AI analyzer expects two categories: addon_updates (system) and hacs_updates (integrations)
                    # Only categorize if we haven't already populated each category from fallback
                    if len(all_updates) > 0:
                        if len(addon_updates) == 0:
                            addon_updates = [u for u in all_updates if u.get('type') in ADDON_ANALYSIS_TYPES]
                        if len(hacs_updates) == 0:
                            hacs_updates = [u for u in all_updates if u.get('type') in INTEGRATION_ANALYSIS_TYPES]
                        
                        logger.debug(f"  System/Add-on updates: {len(addon_updates)}")
                        logger.debug(f"  Integration/HACS updates: {len(hacs_updates)}")
                else:
                    # Legacy method: check individually based on flags
                    if self.config.check_addons:
                        logger.info("Checking for add-on updates...")
                        logger.debug("Querying Supervisor API for add-on information")
                        addon_updates = await ha_client.get_addon_updates()
                        logger.info(f"Found {len(addon_updates)} add-on updates")
                    else:
                        logger.debug("Add-on checking is disabled in configuration")
                    
                    if self.config.check_hacs:
                        logger.info("Checking for HACS updates...")
                        logger.debug("Querying Home Assistant API for HACS update entities")
                        hacs_updates = await ha_client.get_hacs_updates()
                        logger.info(f"Found {len(hacs_updates)} HACS updates")
                    else:
                        logger.debug("HACS checking is disabled in configuration")
                    
                    all_updates = addon_updates + hacs_updates
                
                total_updates = len(all_updates)
                
                if total_updates == 0:
                    logger.info("No updates available")
                    logger.debug("Reporting up-to-date status to Home Assistant")
                    await self._report_no_updates(ha_client)
                    return
                
                # Analyze updates with AI
                logger.info(f"Analyzing {total_updates} updates...")
                logger.debug(f"AI enabled: {self.config.ai_enabled}, Provider: {self.config.ai_provider}")
                analysis = await self.ai_client.analyze_updates(addon_updates, hacs_updates)
                
                logger.info(f"Analysis complete: Safe={analysis['safe']}, Confidence={analysis['confidence']:.2f}")
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"Analysis details: {analysis}")
                
                # Report results
                logger.debug("Reporting analysis results to Home Assistant")
                await self._report_results(ha_client, addon_updates, hacs_updates, analysis, all_updates)
                
                # Check logs for errors after updates (if enabled)
                log_analysis = await self.log_monitor.check_logs(ha_client, self.ai_client)
                if log_analysis:
                    await self._report_log_analysis(ha_client, log_analysis)
                
                # Save machine-readable report (Feature 4) if enabled
                if self.config.save_reports:
                    self._save_machine_readable_report(all_updates, analysis)
                
        except Exception as e:
            logger.error(f"Error during update check: {e}", exc_info=True)
    
    async def _report_no_updates(self, ha_client: HomeAssistantClient):
        """Report when no updates are available"""
        logger.info("All systems up to date - no updates available")
        logger.debug("Creating up-to-date status sensor")
        
        if self.config.create_dashboard_entities:
            await ha_client.set_sensor_state(
                'sensor.ha_sentry_update_status',
                'up_to_date',
                {
                    'friendly_name': 'HA Sentry Update Status',
                    'icon': 'mdi:check-circle',
                    'last_check': datetime.now().isoformat(),
                    'updates_available': 0,
                    'safe_to_update': True,
                    'ha_compatibility': HA_COMPATIBILITY_VERSIONS
                }
            )
            
            # Also update the updates_available sensor
            await ha_client.set_sensor_state(
                'sensor.ha_sentry_updates_available',
                '0',
                {
                    'friendly_name': 'HA Sentry Updates Available',
                    'icon': 'mdi:update',
                    'last_check': datetime.now().isoformat()
                }
            )
        else:
            logger.debug("Dashboard entities disabled, skipping sensor update")
        
        # Send a notification about the up-to-date status
        await ha_client.create_persistent_notification(
            "✅ Home Assistant Up to Date",
            f"""Your Home Assistant installation is up to date!

**Last Check:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

No updates are currently available for:
- Home Assistant Core
- Supervisor
- Operating System
- Add-ons
- Integrations (HACS)

*Next check scheduled: {self.config.check_schedule}*
""",
            'ha_sentry_no_updates'
        )
    
    def _categorize_updates(self, all_updates: List[Dict]) -> Dict[str, int]:
        """Categorize updates by type and count them"""
        counts = {
            'core': 0,  # Core, Supervisor, OS
            'addon': 0,  # Add-ons
            'hacs': 0   # HACS and integrations
        }
        
        for update in all_updates:
            update_type = update.get('type', UPDATE_TYPE_ADDON)
            if update_type in [UPDATE_TYPE_CORE, UPDATE_TYPE_SUPERVISOR, UPDATE_TYPE_OS]:
                counts['core'] += 1
            elif update_type == UPDATE_TYPE_ADDON:
                counts['addon'] += 1
            else:  # hacs, integration
                counts['hacs'] += 1
        
        return counts
    
    def _get_ingress_url(self, path: str = "", mode: str = "", component: str = "") -> str:
        """
        Generate a URL for the web UI accessible via Home Assistant ingress
        
        Args:
            path: Optional path to append to the base URL
            mode: Optional mode parameter (whereused, impact, dependency)
            component: Optional component parameter
        
        Returns:
            str: The full ingress URL
            
        Note:
            This uses the Home Assistant frontend ingress URL format: /hassio/ingress/<slug>
            
            The /hassio/ingress/ format is used for notification links and frontend navigation,
            as it keeps users within the Home Assistant interface. The /api/hassio_ingress/
            format is the backend proxy endpoint used by the frontend internally.
            
            Query parameters are used instead of URL fragments because Home Assistant's
            persistent notification system may not preserve fragments in markdown links.
            
            If the links in notifications don't work:
            1. Check your Home Assistant version (ingress format changed in HA 2021.x+)
            2. Try accessing the Web UI via: Settings → Add-ons → Home Assistant Sentry → Open Web UI
            3. Look for the "Sentry" panel in your Home Assistant sidebar
            4. Check the add-on logs for the actual ingress URL being used
            
            The ingress URL format may vary based on:
            - Home Assistant version
            - How the add-on was installed (built-in vs. custom repository)
            - Reverse proxy configuration
        """
        # Always include trailing slash for proper ingress routing
        # Home Assistant's ingress system expects URLs in the format:
        # /hassio/ingress/<slug>/ (with trailing slash) for frontend navigation
        base_url = f"/hassio/ingress/{self.ADDON_SLUG}/"
        
        # Build query string if mode or component provided
        params = []
        if mode:
            params.append(f"mode={mode}")
        if component:
            # URL encode the component name
            params.append(f"component={quote(component)}")
        
        if path:
            # Remove leading slash from path to avoid double slashes
            path = path.lstrip('/')
            base_url = f"{base_url}{path}"
        
        if params:
            base_url = f"{base_url}?{'&'.join(params)}"
        
        return base_url
    
    def _extract_component_domain(self, component_name: str) -> str:
        """
        Extract the domain/slug from a component name for use in URLs
        
        Args:
            component_name: The component name from the issue (e.g., "Home Assistant Core", "mosquitto")
        
        Returns:
            str: A sanitized component domain/slug
        """
        # Convert to lowercase and replace spaces with underscores
        domain = component_name.lower().replace(' ', '_').replace('-', '_')
        # Remove special characters
        domain = ''.join(c for c in domain if c.isalnum() or c == '_')
        return domain
    
    def _get_component_type_label(self, component_type: str) -> str:
        """
        Get a user-friendly label for component type
        
        Args:
            component_type: The component type (e.g., 'addon', 'hacs', 'core', 'integration')
        
        Returns:
            str: A formatted label for display
        """
        type_labels = {
            'core': 'Core',
            'supervisor': 'Supervisor',
            'os': 'OS',
            'addon': 'Add-on',
            'hacs': 'HACS Integration',
            'integration': 'Integration'
        }
        return type_labels.get(component_type, component_type.capitalize())
    
    def _format_updates_with_links(self, all_updates: List[Dict], max_items: int = 10) -> tuple:
        """
        Format a list of updates with links to the WebUI dependency diagram
        
        Args:
            all_updates: List of update dictionaries
            max_items: Maximum number of items to include in the list
        
        Returns:
            tuple: (formatted_message, list_of_component_domains)
        """
        if not all_updates or not self.config.enable_web_ui:
            return ("", [])
        
        message = "\n**📦 Available Updates:**\n\n"
        component_domains = []
        
        for update in all_updates[:max_items]:
            # Determine component type and name
            component_type = update.get('type', update.get('update_type', 'unknown'))
            component_name = update.get('name', 'Unknown')
            
            # Format version info
            current_version = update.get('current_version', update.get('installed_version', '?'))
            latest_version = update.get('latest_version', update.get('version', '?'))
            
            # Format type label
            type_label = self._get_component_type_label(component_type)
            
            # Generate link only for integrations and HACS (only these are in dependency graph)
            component_domain = self._extract_component_domain(component_name)
            
            # Format the update line
            message += f"• **{component_name}** ({type_label}): {current_version} → {latest_version}"
            
            if component_type in ['integration', 'hacs']:
                where_used_url = self._get_ingress_url(mode="whereused", component=component_domain)
                message += f" [🔍 View Dependencies]({where_used_url})"
                component_domains.append(component_domain)
            
            message += "\n"
        
        if len(all_updates) > max_items:
            message += f"\n_...and {len(all_updates) - max_items} more updates_\n"
        
        return (message, component_domains)
    
    async def _report_results(self, ha_client: HomeAssistantClient, 
                            addon_updates: List[Dict], 
                            hacs_updates: List[Dict], 
                            analysis: Dict,
                            all_updates: List[Dict] = None):
        """Report analysis results to Home Assistant"""
        # Use all_updates if provided, otherwise combine addon and hacs
        if all_updates is None:
            all_updates = addon_updates + hacs_updates
        
        total_updates = len(all_updates)
        safe = analysis['safe']
        
        logger.debug(f"Preparing to report results: {total_updates} updates, safe={safe}")
        
        # Create dashboard entities if enabled
        if self.config.create_dashboard_entities:
            logger.debug("Updating dashboard sensors")
            dashboard_mgr = DashboardManager(ha_client)
            await dashboard_mgr.update_sensors(addon_updates, hacs_updates, analysis)
        else:
            logger.debug("Dashboard entities disabled, skipping sensor updates")
        
        # Categorize updates by type for better reporting
        update_counts = self._categorize_updates(all_updates)
        
        # Create notification with results
        notification_title = "🔔 Home Assistant Sentry Update Report"
        
        if safe:
            logger.debug("Generating SAFE update notification")
            notification_message = f"""✅ **Updates are SAFE to install**

**Confidence:** {analysis['confidence']:.0%}

**Updates Available:** {total_updates}
"""
            # Add breakdown by type
            if update_counts['core'] > 0:
                notification_message += f"- Core/System: {update_counts['core']}\n"
            if update_counts['addon'] > 0:
                notification_message += f"- Add-ons: {update_counts['addon']}\n"
            if update_counts['hacs'] > 0:
                notification_message += f"- HACS/Integrations: {update_counts['hacs']}\n"
            
            notification_message += f"""
**Summary:**
{analysis['summary']}

"""
            if analysis.get('recommendations'):
                notification_message += "**Recommendations:**\n"
                for rec in analysis['recommendations'][:5]:  # Limit to 5
                    notification_message += f"- {rec}\n"
            
            # Initialize changed_components list for safe case
            changed_components = []
            
            # Add list of all updates with links (for safe case)
            if total_updates > 0:
                updates_message, update_domains = self._format_updates_with_links(all_updates, max_items=10)
                notification_message += updates_message
                # Use set for efficient deduplication
                changed_components = list(set(update_domains))
        else:
            logger.debug("Generating REVIEW REQUIRED notification")
            notification_message = f"""⚠️ **REVIEW REQUIRED before updating**

**Confidence:** {analysis['confidence']:.0%}

**Updates Available:** {total_updates}
"""
            # Add breakdown by type
            if update_counts['core'] > 0:
                notification_message += f"- Core/System: {update_counts['core']}\n"
            if update_counts['addon'] > 0:
                notification_message += f"- Add-ons: {update_counts['addon']}\n"
            if update_counts['hacs'] > 0:
                notification_message += f"- HACS/Integrations: {update_counts['hacs']}\n"
            
            notification_message += f"""
**Issues Found:** {len(analysis.get('issues', []))}

"""
            # Add issues with links to web UI
            changed_components = []  # Track components for impact report link
            for issue in analysis.get('issues', [])[:5]:  # Limit to 5
                severity_emoji = {
                    'critical': '🔴',
                    'high': '🟠',
                    'medium': '🟡',
                    'low': '🟢'
                }.get(issue.get('severity', 'medium'), '🔵')
                
                component_name = issue.get('component', 'Unknown')
                component_type = issue.get('component_type', '')
                
                # Format the component display with type label
                if component_type:
                    type_label = self._get_component_type_label(component_type)
                    component_display = f"{component_name} ({type_label})"
                else:
                    component_display = component_name
                
                notification_message += f"\n{severity_emoji} **{component_display}**\n"
                notification_message += f"{issue.get('description', 'No description')}\n"
                
                # Add "Where Used" link if web UI is enabled and component is an integration/HACS
                # Only integrations and HACS components are in the dependency graph
                # Addons, Core, Supervisor, and OS updates are NOT in the dependency graph
                if (self.config.enable_web_ui and 
                    component_name != 'Unknown' and 
                    component_type in ['integration', 'hacs']):
                    # Extract domain for URL - for integrations, use the component name as-is
                    # since it should already be a domain-like identifier
                    component_domain = self._extract_component_domain(component_name)
                    where_used_url = self._get_ingress_url(mode="whereused", component=component_domain)
                    notification_message += f"  [🔍 View Impact]({where_used_url})\n"
                    changed_components.append(component_domain)
                
                logger.debug(f"  Issue: {issue.get('component')} ({component_type}) - {issue.get('severity')}")
            
            notification_message += f"\n**Summary:**\n{analysis['summary']}\n"
            
            if analysis.get('recommendations'):
                notification_message += "\n**Recommendations:**\n"
                for rec in analysis['recommendations'][:5]:
                    notification_message += f"- {rec}\n"
            
            # Add list of all updates with links (for review required case)
            if total_updates > 0:
                updates_message, update_domains = self._format_updates_with_links(all_updates, max_items=10)
                notification_message += updates_message
                # Merge with changed_components from issues using set for efficient deduplication
                changed_components = list(set(changed_components + update_domains))
        
        # Add web UI links section if enabled
        if self.config.enable_web_ui:
            notification_message += "\n---\n**📊 Interactive WebUI - Detailed Analysis:**\n"
            
            # Add impact report link if we have changed components (both safe and review required)
            if changed_components:
                components_param = ','.join(changed_components[:10])  # Limit to avoid URL length issues
                impact_url = self._get_ingress_url(mode="impact", component=components_param)
                notification_message += f"- [⚡ Change Impact Report]({impact_url}) - View {len(changed_components)} changed components and their affected dependencies\n"
                logger.debug(f"Generated impact report URL: {impact_url}")
            
            # Always add link to main web UI (ingress panel)
            web_ui_url = self._get_ingress_url()
            notification_message += f"- [🛡️ Open WebUI]({web_ui_url}) - Full dependency visualization and analysis\n"
            logger.debug(f"Generated web UI URL: {web_ui_url}")
            notification_message += "\n**Alternative Access Methods:**\n"
            notification_message += "- Look for the '**Sentry**' panel in your Home Assistant sidebar (easiest)\n"
            notification_message += "- Or: Settings → Add-ons → Home Assistant Sentry → Open Web UI\n"
        
        notification_message += f"\n*Analysis powered by: {'AI' if analysis.get('ai_analysis') else 'Heuristics'}*"
        notification_message += f"\n*Last check: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
        
        logger.debug("Creating persistent notification in Home Assistant")
        await ha_client.create_persistent_notification(
            notification_title,
            notification_message,
            'ha_sentry_report'
        )
        
        logger.info("Results reported to Home Assistant")
    
    async def _report_log_analysis(self, ha_client: HomeAssistantClient, log_analysis: Dict):
        """Report log analysis results to Home Assistant
        
        Always creates a notification with one of three states:
        - GREEN (✅): No changes in log entries
        - AMBER (⚠️): Can't determine changes (first run or missing previous logs)
        - RED (🔴): Changes detected in log entries
        """
        severity = log_analysis.get('severity', 'none')
        new_count = log_analysis.get('new_error_count', 0)
        resolved_count = log_analysis.get('resolved_error_count', 0)
        can_determine_changes = log_analysis.get('can_determine_changes', True)
        
        # Determine notification status and color
        if not can_determine_changes:
            # AMBER: Can't determine changes
            status_emoji = '⚠️'
            status_color = 'AMBER'
            notification_title = f"{status_emoji} Home Assistant Log Monitor - Unable to Compare"
            
            logger.debug("Creating AMBER notification - cannot determine log changes")
            notification_message = f"""**Log Monitoring Status: {status_color}**

⚠️ **Unable to determine if log entries have changed.**

This is the first log check, or previous log data is unavailable. Starting fresh baseline.

**Current Status:**
- Errors/warnings found: {new_count}
- Previous baseline: None available

**What This Means:**
This is expected on first run or after clearing log history. Future checks should be able to compare against this baseline.

"""
        elif severity == 'none' and new_count == 0 and resolved_count == 0:
            # GREEN: No changes, no errors
            status_emoji = '✅'
            status_color = 'GREEN'
            notification_title = f"{status_emoji} Home Assistant Log Monitor - All Clear"
            
            logger.debug("Creating GREEN notification - no log changes")
            notification_message = f"""**Log Monitoring Status: {status_color}**

✅ **No changes in log entries since last check.**

Your Home Assistant system logs are stable with no new errors or warnings.

**Summary:**
{log_analysis['summary']}

"""
        else:
            # RED: Changes detected
            status_emoji = '🔴'
            status_color = 'RED'
            
            # Use severity-specific emoji for title
            severity_emoji = {
                'critical': '🔴',
                'high': '🟠',
                'medium': '🟡',
                'low': '🟢'
            }
            emoji = severity_emoji.get(severity, status_emoji)
            notification_title = f"{emoji} Home Assistant Log Monitor - Changes Detected"
            
            logger.debug(f"Creating RED notification - log changes detected (severity: {severity})")
            notification_message = f"""**Log Monitoring Status: {status_color}**

🔴 **Changes detected in log entries since last check.**

**Severity:** {severity.upper()}

**Summary:**
{log_analysis['summary']}

"""
            
            # Add statistics
            if new_count > 0 or resolved_count > 0:
                notification_message += f"""**Changes:**
- New errors/warnings: {new_count}
- Resolved errors: {resolved_count}

"""
            
            # Add significant errors if any
            significant_errors = log_analysis.get('significant_errors', [])
            if significant_errors:
                notification_message += "**Significant Errors Detected:**\n"
                for i, error in enumerate(significant_errors[:5], 1):  # Limit to 5
                    # Truncate long error lines
                    error_preview = error[:150] + "..." if len(error) > 150 else error
                    notification_message += f"{i}. `{error_preview}`\n"
                
                if len(significant_errors) > 5:
                    notification_message += f"\n... and {len(significant_errors) - 5} more errors\n"
                
                notification_message += "\n"
            
            # Add recommendations
            recommendations = log_analysis.get('recommendations', [])
            if recommendations:
                notification_message += "**Recommendations:**\n"
                for rec in recommendations:
                    notification_message += f"- {rec}\n"
                notification_message += "\n"
        
        # Add footer (common for all statuses)
        check_time = log_analysis.get('check_time', datetime.now(tz=timezone.utc))
        notification_message += f"""---
*Analysis powered by: {'AI' if log_analysis.get('ai_powered') else 'Heuristics'}*
*Check time: {check_time.strftime('%Y-%m-%d %H:%M:%S UTC')}*
*Log lookback period: {self.config.log_check_lookback_hours} hours*
"""
        
        # Add next steps for RED status only
        if status_color == 'RED':
            notification_message += f"""
**Next Steps:**
1. Review the error messages in your Home Assistant logs
2. Check if any integrations or add-ons are failing to load
3. Consider rolling back recent updates if errors are critical
"""
        
        logger.debug(f"Creating log analysis notification in Home Assistant (Status: {status_color})")
        await ha_client.create_persistent_notification(
            notification_title,
            notification_message,
            'ha_sentry_log_report'
        )
        
        logger.info(f"Log analysis reported: {status_color} status, severity={severity}, new={new_count}, resolved={resolved_count}")
    
    def _save_machine_readable_report(self, updates: List[Dict], analysis: Dict):
        """
        Save machine-readable report to JSON file (Feature 4)
        Includes dependency graph and analysis results
        """
        try:
            import json
            import os
            
            # Create reports directory if it doesn't exist
            reports_dir = '/data/reports'
            os.makedirs(reports_dir, exist_ok=True)
            
            # Build comprehensive report
            report = {
                'timestamp': datetime.now().isoformat(),
                'updates': {
                    'total': len(updates),
                    'by_type': self._categorize_updates(updates),
                    'details': updates
                },
                'analysis': {
                    'safe': analysis.get('safe'),
                    'confidence': analysis.get('confidence'),
                    'summary': analysis.get('summary'),
                    'ai_powered': analysis.get('ai_analysis', False),
                    'issues': analysis.get('issues', []),
                    'recommendations': analysis.get('recommendations', [])
                },
                'dependency_graph': None
            }
            
            # Include dependency graph if available
            if self.dependency_graph:
                report['dependency_graph'] = {
                    'statistics': self.dependency_graph.get('machine_readable', {}).get('statistics', {}),
                    'high_risk_dependencies': [
                        {
                            'package': pkg,
                            'users': len(users)
                        }
                        for pkg, users in self.dependency_graph.get('dependency_map', {}).items()
                        if pkg in {'aiohttp', 'cryptography', 'numpy', 'pyjwt', 'sqlalchemy', 'protobuf', 'requests', 'urllib3'}
                    ]
                }
            
            # Save to file
            report_file = os.path.join(reports_dir, 'latest_report.json')
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Machine-readable report saved to {report_file}")
            
            # Also save timestamped version
            timestamp_file = os.path.join(reports_dir, f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            with open(timestamp_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.debug(f"Timestamped report saved to {timestamp_file}")
            
        except Exception as e:
            logger.warning(f"Failed to save machine-readable report: {e}")
            # Don't fail the entire check just because we couldn't save the report
