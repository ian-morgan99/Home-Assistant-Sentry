#!/usr/bin/env python3
"""
Demonstration of new diagnostic logging features
This script shows how the new logging works without requiring a full HA instance
"""
import sys
import os
import logging
from io import StringIO

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app'))

# Configure logging to capture output
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def demo_dependency_graph_path_logging():
    """Demonstrate path discovery diagnostics"""
    print("\n" + "=" * 70)
    print("DEMO: Path Discovery Diagnostics (dependency_graph_builder.py)")
    print("=" * 70)
    
    from dependency_graph_builder import DependencyGraphBuilder
    
    # Test with mix of real and non-existent paths
    test_paths = [
        '/nonexistent/path/to/integrations',
        '/tmp',  # This exists
        '/home/runner/nonexistent',
    ]
    
    builder = DependencyGraphBuilder()
    print("\nBuilding dependency graph with test paths...")
    print(f"Test paths: {test_paths}\n")
    
    result = builder.build_graph_from_paths(test_paths)
    
    print(f"\nResult: Found {len(result['integrations'])} integrations")
    print("\nNote: When paths don't exist, the new logging will:")
    print("  1. Log that the path doesn't exist")
    print("  2. Check if parent directory exists")
    print("  3. List contents of parent directory (first 10 items)")


def demo_main_startup_banner():
    """Demonstrate startup banner"""
    print("\n" + "=" * 70)
    print("DEMO: Startup Banner (main.py)")
    print("=" * 70)
    
    from config_manager import ConfigManager
    
    # Set environment for DEBUG mode
    os.environ['LOG_LEVEL'] = 'maximal'
    os.environ['AI_ENABLED'] = 'true'
    os.environ['AI_PROVIDER'] = 'ollama'
    os.environ['SUPERVISOR_TOKEN'] = 'demo_token_12345'
    
    config = ConfigManager()
    log_level = config.get_python_log_level()
    
    print("\nWith DEBUG log level enabled, the startup will show:")
    print("\n" + "=" * 60)
    print("SYSTEM INFORMATION")
    print("=" * 60)
    print(f"  Python: {sys.version.split()[0]}")
    print(f"  Home Assistant URL: {config.ha_url}")
    print(f"  Has Supervisor Token: {bool(config.supervisor_token)}")
    print("=" * 60)
    print("Full configuration:")
    print(f"  AI Enabled: {config.ai_enabled}")
    print(f"  AI Provider: {config.ai_provider}")
    print(f"  Check Schedule: {config.check_schedule}")
    print(f"  Safety Threshold: {config.safety_threshold}")
    print("  ... (and more)")


def demo_entity_filtering_concept():
    """Demonstrate entity filtering logging concept"""
    print("\n" + "=" * 70)
    print("DEMO: Entity Filtering Diagnostics (ha_client.py)")
    print("=" * 70)
    
    # Simulate what the logging would show
    print("\nWhen fetching entities from Home Assistant, the new logging shows:")
    print("\nExample debug output:")
    print("-" * 70)
    print("Retrieved 247 total states")
    print("Entity domains: {'sensor': 89, 'switch': 34, 'light': 28, 'binary_sensor': 24, 'update': 15, ...}")
    print("Found 15 entities with 'update.' domain")
    print("  Sample: update.home_assistant_core_update | state=on")
    print("  Sample: update.home_assistant_supervisor_update | state=off")
    print("  Sample: update.home_assistant_operating_system_update | state=off")
    print("  Sample: update.hacs_update | state=on")
    print("  Sample: update.esphome_addon_update | state=on")
    print("-" * 70)
    
    print("\nThis helps troubleshoot:")
    print("  • What entities exist in your HA instance")
    print("  • How many update entities are available")
    print("  • Which updates are currently available (state=on)")


def demo_dashboard_api_logging():
    """Demonstrate dashboard API logging concept"""
    print("\n" + "=" * 70)
    print("DEMO: Dashboard API Diagnostics (ha_client.py)")
    print("=" * 70)
    
    print("\nWhen creating a dashboard, the new logging shows:")
    print("\nExample debug output:")
    print("-" * 70)
    print("Attempting to create Sentry dashboard in Lovelace")
    print("POST http://supervisor/core/api/lovelace/dashboards")
    print('Payload: {')
    print('  "url_path": "sentry",')
    print('  "title": "Sentry Updates",')
    print('  "icon": "mdi:security",')
    print('  "show_in_sidebar": true,')
    print('  "require_admin": false,')
    print('  "views": [')
    print('    {')
    print('      "title": "Updates Overview",')
    print('      ...')
    print('  ]')
    print('}')
    print("-" * 70)
    
    print("\nThis helps troubleshoot:")
    print("  • The exact API endpoint being used")
    print("  • The payload structure being sent")
    print("  • Dashboard creation issues")


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("HOME ASSISTANT SENTRY - DIAGNOSTIC LOGGING DEMONSTRATION")
    print("=" * 70)
    print("\nThis demonstrates the new diagnostic logging features added to the addon.")
    print("These improvements help troubleshoot entity filtering, API calls, and paths.")
    
    demo_main_startup_banner()
    demo_entity_filtering_concept()
    demo_dashboard_api_logging()
    demo_dependency_graph_path_logging()
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("\nThe diagnostic improvements add detailed logging for:")
    print("  ✓ Entity domain breakdown (what types of entities exist)")
    print("  ✓ Update entity filtering (which updates are found vs filtered)")
    print("  ✓ Dashboard API calls (exact endpoints and payloads)")
    print("  ✓ Path discovery (missing paths and alternatives)")
    print("  ✓ Startup banner (system information at DEBUG level)")
    print("\nAll new logging only appears at DEBUG level (LOG_LEVEL=maximal)")
    print("to avoid cluttering standard logs.")
    print("=" * 70 + "\n")
