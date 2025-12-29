#!/usr/bin/env python3
"""
Home Assistant Sentry - Main application entry point
"""
import asyncio
import logging
import os
import sys
from datetime import datetime

from sentry_service import SentryService
from config_manager import ConfigManager

# Initial logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


async def main():
    """Main application entry point"""
    logger.info("Home Assistant Sentry starting...")
    
    try:
        # Load configuration
        config = ConfigManager()
        
        # Reconfigure logging based on user preference
        log_level = config.get_python_log_level()
        logging.getLogger().setLevel(log_level)
        
        # Log configuration details based on log level
        if log_level <= logging.INFO:
            logger.info(f"Configuration loaded: AI Enabled={config.ai_enabled}, Provider={config.ai_provider}")
            logger.info(f"Log Level set to: {config.log_level} (Python level: {logging.getLevelName(log_level)})")
        
        if log_level == logging.DEBUG:
            logger.debug("=" * 60)
            logger.debug("SYSTEM INFORMATION")
            logger.debug("=" * 60)
            logger.debug(f"  Python: {sys.version}")
            logger.debug(f"  Home Assistant URL: {config.ha_url}")
            logger.debug(f"  Has Supervisor Token: {bool(config.supervisor_token)}")
            logger.debug("=" * 60)
            logger.debug(f"Full configuration:")
            logger.debug(f"  AI Enabled: {config.ai_enabled}")
            logger.debug(f"  AI Provider: {config.ai_provider}")
            logger.debug(f"  AI Endpoint: {config.ai_endpoint}")
            logger.debug(f"  AI Model: {config.ai_model}")
            logger.debug(f"  Check Schedule: {config.check_schedule}")
            logger.debug(f"  Create Dashboard Entities: {config.create_dashboard_entities}")
            logger.debug(f"  Check Addons: {config.check_addons}")
            logger.debug(f"  Check HACS: {config.check_hacs}")
            logger.debug(f"  Safety Threshold: {config.safety_threshold}")
            logger.debug(f"  Home Assistant URL: {config.ha_url}")
            logger.debug(f"  Supervisor URL: {config.supervisor_url}")
        
        # Initialize the sentry service
        service = SentryService(config)
        
        # Start the service
        await service.start()
        
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
