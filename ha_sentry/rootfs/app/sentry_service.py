"""
Main Sentry Service - Coordinates update checking and analysis
"""
import asyncio
import logging
from datetime import datetime, time, timedelta
from typing import Dict, List

from ha_client import HomeAssistantClient
from ai_client import AIClient
from dashboard_manager import DashboardManager
from dependency_graph_builder import DependencyGraphBuilder

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
    
    def __init__(self, config):
        """Initialize the sentry service"""
        self.config = config
        self.running = False
        self.dependency_graph = None
        
        # Build dependency graph on initialization if enabled
        if config.enable_dependency_graph:
            logger.info("Building dependency graph from installed integrations...")
            try:
                graph_builder = DependencyGraphBuilder()
                graph_data = graph_builder.build_graph_from_paths()
                self.dependency_graph = graph_data
                
                stats = graph_data.get('machine_readable', {}).get('statistics', {})
                logger.info(f"Dependency graph built: {stats.get('total_integrations', 0)} integrations, "
                           f"{stats.get('total_dependencies', 0)} dependencies")
                if stats.get('high_risk_dependencies', 0) > 0:
                    logger.info(f"Found {stats.get('high_risk_dependencies', 0)} high-risk dependencies")
            except Exception as e:
                logger.warning(f"Failed to build dependency graph: {e}")
                logger.info("Continuing without dependency graph analysis")
        else:
            logger.info("Dependency graph building is disabled in configuration")
        
        # Initialize AI client with dependency graph
        self.ai_client = AIClient(config, dependency_graph=self.dependency_graph)
        
        logger.info("Sentry Service initialized")
    
    async def start(self):
        """Start the service"""
        self.running = True
        logger.info(f"Starting service with schedule: {self.config.check_schedule}")
        
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
                    
                    # For backward compatibility with analysis, categorize updates
                    # The AI analyzer expects two categories: addon_updates (system) and hacs_updates (integrations)
                    addon_updates = [u for u in all_updates if u.get('type') in ADDON_ANALYSIS_TYPES]
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
                    'safe_to_update': True
                }
            )
        else:
            logger.debug("Dashboard entities disabled, skipping sensor update")
    
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
            # Add issues
            for issue in analysis.get('issues', [])[:5]:  # Limit to 5
                severity_emoji = {
                    'critical': '🔴',
                    'high': '🟠',
                    'medium': '🟡',
                    'low': '🟢'
                }.get(issue.get('severity', 'medium'), '🔵')
                
                notification_message += f"\n{severity_emoji} **{issue.get('component', 'Unknown')}**\n"
                notification_message += f"{issue.get('description', 'No description')}\n"
                logger.debug(f"  Issue: {issue.get('component')} - {issue.get('severity')}")
            
            notification_message += f"\n**Summary:**\n{analysis['summary']}\n"
            
            if analysis.get('recommendations'):
                notification_message += "\n**Recommendations:**\n"
                for rec in analysis['recommendations'][:5]:
                    notification_message += f"- {rec}\n"
        
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
