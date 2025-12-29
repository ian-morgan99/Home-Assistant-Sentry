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

# Configure logging
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
        logger.info(f"Configuration loaded: AI Enabled={config.ai_enabled}, Provider={config.ai_provider}")
        
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
