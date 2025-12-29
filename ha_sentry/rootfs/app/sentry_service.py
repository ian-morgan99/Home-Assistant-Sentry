"""
Main Sentry Service - Coordinates update checking and analysis
"""
import asyncio
import logging
from datetime import datetime, time, timedelta
from typing import Dict, List

from ha_client import HomeAssistantClient, HA_COMPATIBILITY_VERSIONS
from ai_client import AIClient
from dashboard_manager import DashboardManager
from dependency_graph_builder import DependencyGraphBuilder
from web_server import DependencyTreeWebServer

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
        
        # Build dependency graph on initialization if enabled
        if config.enable_dependency_graph:
            logger.info("=" * 60)
            logger.info("DEPENDENCY GRAPH INITIALIZATION")
            logger.info("=" * 60)
            logger.info("Building dependency graph from installed integrations...")
            try:
                graph_builder = DependencyGraphBuilder()
                
                # Use custom paths if provided, otherwise use defaults
                integration_paths = None
                if hasattr(config, 'custom_integration_paths') and config.custom_integration_paths:
                    logger.info(f"Using custom integration paths: {config.custom_integration_paths}")
                    integration_paths = config.custom_integration_paths
                else:
                    logger.info("Using default integration paths")
                
                graph_data = graph_builder.build_graph_from_paths(integration_paths)
                self.dependency_graph = graph_data
                self.dependency_graph_builder = graph_builder
                
                stats = graph_data.get('machine_readable', {}).get('statistics', {})
                logger.info(f"✅ Dependency graph built successfully")
                logger.info(f"   Total integrations: {stats.get('total_integrations', 0)}")
                logger.info(f"   Total dependencies: {stats.get('total_dependencies', 0)}")
                if stats.get('high_risk_dependencies', 0) > 0:
                    logger.info(f"   High-risk dependencies: {stats.get('high_risk_dependencies', 0)}")
                logger.info("=" * 60)
            except Exception as e:
                logger.error("=" * 60)
                logger.error("DEPENDENCY GRAPH BUILD FAILED")
                logger.error("=" * 60)
                logger.error(f"Failed to build dependency graph: {e}", exc_info=True)
                logger.error("")
                logger.error("This means:")
                logger.error("  - The web UI will not be available (503 errors)")
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
        else:
            logger.info("Dependency graph building is disabled in configuration")
            logger.info("  enable_dependency_graph: false")
            logger.info("  Note: Web UI will not be available without dependency graph")
        
        # Initialize AI client with dependency graph
        self.ai_client = AIClient(config, dependency_graph=self.dependency_graph)
        
        logger.info("Sentry Service initialized")
    
    async def start(self):
        """Start the service"""
        self.running = True
        logger.info(f"Starting service with schedule: {self.config.check_schedule}")
        
        # Start web server for dependency visualization if enabled
        if self.config.enable_web_ui and self.dependency_graph_builder:
            try:
                logger.info("Starting web server for dependency visualization...")
                logger.info(f"  Web UI port: {self.WEB_UI_PORT}")
                logger.info(f"  Dependency graph available: Yes")
                logger.info(f"  Total integrations loaded: {len(self.dependency_graph_builder.integrations)}")
                self.web_server = DependencyTreeWebServer(
                    self.dependency_graph_builder,
                    self.config,
                    port=self.WEB_UI_PORT
                )
                await self.web_server.start()
            except Exception as e:
                logger.error(f"Failed to start web server: {e}", exc_info=True)
                logger.error("Web UI will not be available")
                logger.info("To troubleshoot:")
                logger.info(f"  1. Check if port {self.WEB_UI_PORT} is already in use")
                logger.info("  2. Verify 'enable_dependency_graph' is true in configuration")
                logger.info("  3. Check add-on logs for dependency graph building errors")
                logger.info("Continuing without web UI")
        elif self.config.enable_web_ui and not self.dependency_graph_builder:
            logger.error("Web UI is enabled but dependency graph is not available")
            logger.error("Web UI requires the dependency graph to function")
            logger.error("Configuration mismatch detected:")
            logger.error(f"  enable_web_ui: {self.config.enable_web_ui}")
            logger.error(f"  enable_dependency_graph: {self.config.enable_dependency_graph}")
            logger.error(f"  dependency_graph_builder: {self.dependency_graph_builder is not None}")
            logger.error("")
            logger.error("To fix this issue:")
            logger.error("  1. Go to Settings → Add-ons → Home Assistant Sentry → Configuration")
            logger.error("  2. Enable 'enable_dependency_graph: true'")
            logger.error("  3. Restart the add-on")
            logger.error("")
            logger.error("If you don't need the web UI, you can disable it:")
            logger.error("  Set 'enable_web_ui: false' in configuration")
        elif not self.config.enable_web_ui:
            logger.info("Web UI disabled in configuration (enable_web_ui: false)")
        
        # Send startup notification to help users find sensors
        await self._send_startup_notification()
        
        # Create dashboard if auto_create_dashboard is enabled
        if self.config.auto_create_dashboard:
            logger.info("Auto-create dashboard is enabled, creating Sentry dashboard")
            try:
                async with HomeAssistantClient(self.config) as ha_client:
                    dashboard_mgr = DashboardManager(ha_client)
                    await dashboard_mgr.create_sentry_dashboard()
            except Exception as e:
                logger.error(f"Error creating dashboard: {e}", exc_info=True)
        
        # Run initial check
        await self.run_update_check()
        
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
**📊 Dependency Tree Visualization:**

View dependency trees and impact analysis via the Sentry panel in your sidebar, or visit:
- Settings → Add-ons → Home Assistant Sentry → Open Web UI

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
    
    def _get_ingress_url(self, path: str = "") -> str:
        """
        Generate a URL for the web UI accessible via Home Assistant ingress
        
        Args:
            path: Optional path to append to the base URL (e.g., "?mode=whereused")
        
        Returns:
            str: The full ingress URL
        """
        base_url = f"/api/hassio_ingress/{self.ADDON_SLUG}"
        if path:
            return f"{base_url}/{path}"
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
                notification_message += f"\n{severity_emoji} **{component_name}**\n"
                notification_message += f"{issue.get('description', 'No description')}\n"
                
                # Add "Where Used" link if web UI is enabled and we have a valid component
                if self.config.enable_web_ui and component_name != 'Unknown':
                    component_domain = self._extract_component_domain(component_name)
                    where_used_url = self._get_ingress_url() + f"#whereused:{component_domain}"
                    notification_message += f"  [🔍 View Impact]({where_used_url})\n"
                    changed_components.append(component_domain)
                
                logger.debug(f"  Issue: {issue.get('component')} - {issue.get('severity')}")
            
            notification_message += f"\n**Summary:**\n{analysis['summary']}\n"
            
            if analysis.get('recommendations'):
                notification_message += "\n**Recommendations:**\n"
                for rec in analysis['recommendations'][:5]:
                    notification_message += f"- {rec}\n"
        
        # Add web UI links section if enabled
        if self.config.enable_web_ui:
            notification_message += "\n---\n**📊 Detailed Analysis:**\n"
            
            # For review required case with changed components, add impact report link
            if not safe and 'changed_components' in locals() and changed_components:
                components_param = ','.join(changed_components[:10])  # Limit to avoid URL length issues
                impact_url = self._get_ingress_url() + f"#impact:{components_param}"
                affected_count = len(analysis.get('issues', []))
                notification_message += f"- [⚡ Change Impact Report]({impact_url}) - View {len(changed_components)} changed components and their affected dependencies\n"
            
            # Always add link to main dashboard
            dashboard_url = self._get_ingress_url()
            notification_message += f"- [🛡️ Dependency Dashboard]({dashboard_url}) - Explore all component dependencies\n"
        
        notification_message += f"\n*Analysis powered by: {'AI' if analysis.get('ai_analysis') else 'Heuristics'}*"
        notification_message += f"\n*Last check: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
        
        logger.debug("Creating persistent notification in Home Assistant")
        await ha_client.create_persistent_notification(
            notification_title,
            notification_message,
            'ha_sentry_report'
        )
        
        logger.info("Results reported to Home Assistant")
    
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
