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

logger = logging.getLogger(__name__)


class SentryService:
    """Main service for monitoring and analyzing Home Assistant updates"""
    
    def __init__(self, config):
        """Initialize the sentry service"""
        self.config = config
        self.ai_client = AIClient(config)
        self.running = False
        
        logger.info("Sentry Service initialized")
    
    async def start(self):
        """Start the service"""
        self.running = True
        logger.info(f"Starting service with schedule: {self.config.check_schedule}")
        
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
                # Gather updates
                addon_updates = []
                hacs_updates = []
                
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
                
                total_updates = len(addon_updates) + len(hacs_updates)
                
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
                await self._report_results(ha_client, addon_updates, hacs_updates, analysis)
                
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
    
    async def _report_results(self, ha_client: HomeAssistantClient, 
                            addon_updates: List[Dict], 
                            hacs_updates: List[Dict], 
                            analysis: Dict):
        """Report analysis results to Home Assistant"""
        total_updates = len(addon_updates) + len(hacs_updates)
        safe = analysis['safe']
        
        logger.debug(f"Preparing to report results: {total_updates} updates, safe={safe}")
        
        # Create dashboard entities if enabled
        if self.config.create_dashboard_entities:
            logger.debug("Updating dashboard sensors")
            dashboard_mgr = DashboardManager(ha_client)
            await dashboard_mgr.update_sensors(addon_updates, hacs_updates, analysis)
        else:
            logger.debug("Dashboard entities disabled, skipping sensor updates")
        
        # Create notification with results
        notification_title = "🔔 Home Assistant Sentry Update Report"
        
        if safe:
            logger.debug("Generating SAFE update notification")
            notification_message = f"""✅ **Updates are SAFE to install**

**Confidence:** {analysis['confidence']:.0%}

**Updates Available:** {total_updates}
- Add-ons: {len(addon_updates)}
- HACS Integrations: {len(hacs_updates)}

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
- Add-ons: {len(addon_updates)}
- HACS Integrations: {len(hacs_updates)}

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
