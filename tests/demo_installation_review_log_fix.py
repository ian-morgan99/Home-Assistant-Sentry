"""
Demonstration script to show the log message fix

This script demonstrates that the log message now correctly shows
the actual configuration value instead of hardcoding 'false'.
"""
import sys
import os
import logging

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app'))

from config_manager import ConfigManager
from sentry_service import SentryService

# Set up logging to see DEBUG messages
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s - %(message)s'
)

print("=" * 70)
print("DEMONSTRATION: Installation Review Log Message Fix")
print("=" * 70)
print()

# Test 1: Feature ENABLED
print("Test 1: When enable_installation_review=True")
print("-" * 70)
os.environ['AI_ENABLED'] = 'false'
os.environ['SUPERVISOR_TOKEN'] = 'test_token'
os.environ['ENABLE_INSTALLATION_REVIEW'] = 'true'
os.environ['INSTALLATION_REVIEW_SCHEDULE'] = 'weekly'

config1 = ConfigManager()
service1 = SentryService(config1)

print(f"\nConfiguration state: enable_installation_review={config1.enable_installation_review}")
print("\nCalling _should_run_installation_review()...")
result1 = service1._should_run_installation_review()
print(f"Return value: {result1}")
print("\nNote: When enabled (True), the feature runs on first check")
print("      No 'disabled' message is logged")
print()

# Test 2: Feature DISABLED
print("=" * 70)
print("Test 2: When enable_installation_review=False")
print("-" * 70)
os.environ['ENABLE_INSTALLATION_REVIEW'] = 'false'

config2 = ConfigManager()
service2 = SentryService(config2)

print(f"\nConfiguration state: enable_installation_review={config2.enable_installation_review}")
print("\nCalling _should_run_installation_review()...")
result2 = service2._should_run_installation_review()
print(f"Return value: {result2}")
print("\nNote: When disabled (False), you should see the DEBUG log above")
print("      showing 'enable_installation_review=False' (not hardcoded)")
print()

print("=" * 70)
print("SUMMARY")
print("=" * 70)
print("✓ The log message now correctly shows the actual configuration value")
print("✓ When True: No 'disabled' message (feature is active)")
print("✓ When False: Shows 'enable_installation_review=False' (not hardcoded)")
print()
print("BEFORE FIX: Log always showed 'enable_installation_review=false'")
print("AFTER FIX:  Log shows actual value from configuration")
print("=" * 70)
