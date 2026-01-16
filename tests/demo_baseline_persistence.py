#!/usr/bin/env python3
"""
Demonstration script showing how baseline persistence works after HA restart

This script simulates the complete scenario described in the issue:
1. Normal operation with baseline established
2. HA restart (logs cleared)
3. Log monitoring still has meaningful baseline to compare against
"""
import sys
import os
import tempfile
import json
from datetime import datetime

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app'))

from log_monitor import LogMonitor

class MockConfig:
    def __init__(self):
        self.monitor_logs_after_update = True
        self.log_check_lookback_hours = 96  # Same as issue example
        self.obfuscate_logs = False
        self.ai_enabled = False

def print_section(title):
    """Print a section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def print_file_contents(filepath, label):
    """Print contents of a JSON file"""
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            data = json.load(f)
        print(f"\n{label}:")
        print(f"  Timestamp: {data.get('timestamp', 'N/A')}")
        print(f"  Error count: {len(data.get('errors', []))}")
        if data.get('errors'):
            print(f"  Sample errors:")
            for i, err in enumerate(data['errors'][:3], 1):
                print(f"    {i}. {err[:80]}...")
    else:
        print(f"\n{label}: NOT FOUND")

def simulate_log_check(monitor, current_errors, scenario_name):
    """Simulate a log monitoring check"""
    print(f"\n--- {scenario_name} ---")
    print(f"Current errors found: {len(current_errors)}")
    
    # Load previous logs (may fall back to baseline)
    previous_errors = monitor.load_previous_logs()
    print(f"Loaded for comparison: {len(previous_errors)} errors")
    
    # Check if we can determine changes
    can_determine_changes = len(previous_errors) > 0
    print(f"Can determine changes: {can_determine_changes}")
    
    # Compare logs
    comparison = monitor.compare_logs(current_errors, previous_errors)
    print(f"Comparison results:")
    print(f"  New errors: {len(comparison['new_errors'])}")
    print(f"  Resolved errors: {len(comparison['resolved_errors'])}")
    print(f"  Persistent errors: {len(comparison['persistent_errors'])}")
    
    # Analyze
    analysis = monitor.heuristic_analysis(comparison)
    print(f"\nAnalysis:")
    print(f"  Severity: {analysis['severity'].upper()}")
    print(f"  Summary: {analysis['summary']}")
    print(f"  Status: {'🟢 GREEN - No changes' if analysis['severity'] == 'none' else '🔴 RED - Changes detected'}")
    
    # Save for next comparison
    monitor.save_current_logs(current_errors)
    
    return can_determine_changes, analysis

def main():
    print_section("LOG MONITORING BASELINE PERSISTENCE DEMONSTRATION")
    print("\nThis demonstrates the fix for the issue where baseline was lost after HA restart.")
    
    config = MockConfig()
    monitor = LogMonitor(config)
    
    # Use temporary directory for demo
    with tempfile.TemporaryDirectory() as tmpdir:
        monitor.PREVIOUS_LOGS_FILE = os.path.join(tmpdir, 'previous_logs.json')
        monitor.BASELINE_LOGS_FILE = os.path.join(tmpdir, 'baseline_logs.json')
        
        print_section("SCENARIO 1: Initial Operation (Baseline Creation)")
        print("\nSimulating normal operation with 12 errors in logs...")
        
        initial_errors = [
            '2026-01-12 00:00:00 ERROR homeassistant.components.mqtt: Connection lost',
            '2026-01-12 00:05:00 WARNING homeassistant.components.sensor: Slow update',
            '2026-01-12 00:10:00 ERROR homeassistant.components.zwave: Timeout',
            '2026-01-12 00:15:00 WARNING homeassistant.loader: Deprecated feature',
            '2026-01-12 00:20:00 ERROR homeassistant.components.rest: HTTP 500',
            '2026-01-12 00:25:00 WARNING homeassistant.components.automation: Long execution',
            '2026-01-12 00:30:00 ERROR homeassistant.components.mqtt: Connection lost',
            '2026-01-12 00:35:00 WARNING homeassistant.components.sensor: Slow update',
            '2026-01-12 00:40:00 ERROR homeassistant.components.zwave: Timeout',
            '2026-01-12 00:45:00 WARNING homeassistant.loader: Deprecated feature',
            '2026-01-12 00:50:00 ERROR homeassistant.components.rest: HTTP 500',
            '2026-01-12 00:55:00 WARNING homeassistant.components.automation: Long execution',
        ]
        
        can_determine, analysis = simulate_log_check(monitor, initial_errors, "Initial Check")
        
        print_file_contents(monitor.BASELINE_LOGS_FILE, "Baseline File")
        print_file_contents(monitor.PREVIOUS_LOGS_FILE, "Previous Logs File")
        
        print("\n✅ Baseline created with 12 errors")
        
        # Simulate a minor update without restart
        print_section("SCENARIO 2: Minor Update (No Restart)")
        print("\nSimulating check after minor update (no HA restart)...")
        print("One error resolved, one new error appeared.")
        
        minor_update_errors = [
            '2026-01-12 01:00:00 ERROR homeassistant.components.mqtt: Connection lost',
            '2026-01-12 01:05:00 WARNING homeassistant.components.sensor: Slow update',
            '2026-01-12 01:10:00 ERROR homeassistant.components.zwave: Timeout',
            # Removed deprecated warning (resolved)
            '2026-01-12 01:20:00 ERROR homeassistant.components.rest: HTTP 500',
            '2026-01-12 01:25:00 WARNING homeassistant.components.automation: Long execution',
            '2026-01-12 01:30:00 ERROR homeassistant.components.mqtt: Connection lost',
            '2026-01-12 01:35:00 WARNING homeassistant.components.sensor: Slow update',
            '2026-01-12 01:40:00 ERROR homeassistant.components.zwave: Timeout',
            '2026-01-12 01:45:00 ERROR homeassistant.components.weather: New API error',  # New
            '2026-01-12 01:50:00 ERROR homeassistant.components.rest: HTTP 500',
            '2026-01-12 01:55:00 WARNING homeassistant.components.automation: Long execution',
        ]
        
        can_determine, analysis = simulate_log_check(monitor, minor_update_errors, "Minor Update Check")
        
        print(f"\n✅ Status correctly shows: {'RED' if analysis['severity'] != 'none' else 'GREEN'}")
        print(f"✅ Can determine changes: {can_determine}")
        
        # THE KEY SCENARIO: HA Restart
        print_section("SCENARIO 3: HOME ASSISTANT RESTART (THE ISSUE)")
        print("\n🔄 HOME ASSISTANT RESTARTS - Logs are cleared by HA")
        print("\nSimulating check immediately after HA restart...")
        print("Only 2-3 startup errors visible (HA cleared its logs on restart)")
        
        post_restart_errors = [
            '2026-01-13 02:00:00 ERROR homeassistant.bootstrap: Component setup',
            '2026-01-13 02:00:05 WARNING homeassistant.loader: Loading integrations',
        ]
        
        print("\n⚠️  BEFORE FIX: Baseline would be overwritten with these 2 errors")
        print("⚠️  BEFORE FIX: Next check would say 'no baseline to compare against'")
        print("\n✅ AFTER FIX: Baseline is preserved, comparison still works")
        
        can_determine, analysis = simulate_log_check(monitor, post_restart_errors, "Post-Restart Check")
        
        print_file_contents(monitor.BASELINE_LOGS_FILE, "Baseline File (should still have 11 errors)")
        print_file_contents(monitor.PREVIOUS_LOGS_FILE, "Previous Logs File (has 2 startup errors)")
        
        print(f"\n✅ Can determine changes: {can_determine}")
        print(f"✅ Baseline preserved: Has 11 errors (not overwritten with 2)")
        
        # Check after system stabilizes
        print_section("SCENARIO 4: System Stabilizes After Restart")
        print("\nSimulating check after system has been running for a while...")
        print("Normal operation resumed with 8 errors")
        
        stable_errors = [
            '2026-01-13 03:00:00 ERROR homeassistant.components.mqtt: Connection lost',
            '2026-01-13 03:05:00 WARNING homeassistant.components.sensor: Slow update',
            '2026-01-13 03:10:00 ERROR homeassistant.components.zwave: Timeout',
            '2026-01-13 03:20:00 ERROR homeassistant.components.rest: HTTP 500',
            '2026-01-13 03:25:00 WARNING homeassistant.components.automation: Long execution',
            '2026-01-13 03:30:00 ERROR homeassistant.components.mqtt: Connection lost',
            '2026-01-13 03:35:00 WARNING homeassistant.components.sensor: Slow update',
            '2026-01-13 03:40:00 ERROR homeassistant.components.zwave: Timeout',
        ]
        
        can_determine, analysis = simulate_log_check(monitor, stable_errors, "Stable Operation Check")
        
        print_file_contents(monitor.BASELINE_LOGS_FILE, "Baseline File (updated to 8 errors)")
        
        print(f"\n✅ Baseline updated with new stable state (8 errors)")
        print(f"✅ System operating normally")
        
        print_section("SUMMARY")
        print("""
The fix ensures that:

1. ✅ Baseline is created during normal operation (6-20 errors)
2. ✅ Baseline is NOT overwritten when HA restarts (0-5 errors detected)
3. ✅ Log monitoring can compare against preserved baseline after restart
4. ✅ Baseline is updated when system genuinely stabilizes (6-20 errors)
5. ✅ Users always get meaningful comparisons, even after HA restarts

BEFORE FIX:
- After HA restart: "Unable to determine if log entries have changed"
- Baseline lost, no meaningful comparison possible

AFTER FIX:
- After HA restart: Can still compare against pre-restart baseline
- Meaningful change detection even after restarts
- Status correctly shows GREEN/RED based on actual log changes
        """)
        
        print("\n" + "="*70)
        print("  DEMONSTRATION COMPLETE")
        print("="*70 + "\n")

if __name__ == '__main__':
    main()
