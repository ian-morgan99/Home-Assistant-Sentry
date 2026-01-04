"""
Manual demonstration of log notification states

This script demonstrates the three notification states:
- GREEN: No changes in log entries
- AMBER: Can't determine changes (first run)
- RED: Changes detected in log entries

Run this to see how the notification logic works.
"""
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app'))

def simulate_notification_logic(analysis):
    """Simulate the notification logic from _report_log_analysis"""
    severity = analysis.get('severity', 'none')
    new_count = analysis.get('new_error_count', 0)
    resolved_count = analysis.get('resolved_error_count', 0)
    can_determine_changes = analysis.get('can_determine_changes', True)
    
    print("\n" + "=" * 60)
    print("NOTIFICATION SIMULATION")
    print("=" * 60)
    
    # Determine notification status
    if not can_determine_changes:
        # AMBER
        status = "AMBER"
        emoji = "⚠️"
        title = f"{emoji} Home Assistant Log Monitor - Unable to Compare"
        print(f"Status: {status}")
        print(f"Title: {title}")
        print(f"Reason: First run or no previous baseline available")
        print(f"New errors found: {new_count}")
    elif severity == 'none' and new_count == 0 and resolved_count == 0:
        # GREEN
        status = "GREEN"
        emoji = "✅"
        title = f"{emoji} Home Assistant Log Monitor - All Clear"
        print(f"Status: {status}")
        print(f"Title: {title}")
        print(f"Reason: No changes detected in logs")
    else:
        # RED
        status = "RED"
        emoji = "🔴"
        title = f"{emoji} Home Assistant Log Monitor - Changes Detected"
        print(f"Status: {status}")
        print(f"Title: {title}")
        print(f"Severity: {severity.upper()}")
        print(f"New errors: {new_count}")
        print(f"Resolved errors: {resolved_count}")
    
    print("=" * 60)
    return status

def main():
    print("\n" + "=" * 60)
    print("LOG NOTIFICATION STATES DEMONSTRATION")
    print("=" * 60)
    
    # Scenario 1: AMBER (First run)
    print("\n### SCENARIO 1: First Run (AMBER) ###")
    analysis_amber = {
        'severity': 'none',
        'new_error_count': 3,
        'resolved_error_count': 0,
        'can_determine_changes': False,
        'summary': 'Establishing baseline for future comparisons'
    }
    simulate_notification_logic(analysis_amber)
    
    # Scenario 2: GREEN (No changes)
    print("\n### SCENARIO 2: No Changes (GREEN) ###")
    analysis_green = {
        'severity': 'none',
        'new_error_count': 0,
        'resolved_error_count': 0,
        'can_determine_changes': True,
        'summary': 'No changes in error logs since last check.'
    }
    simulate_notification_logic(analysis_green)
    
    # Scenario 3: RED with low severity
    print("\n### SCENARIO 3: Minor Changes (RED - Low) ###")
    analysis_red_low = {
        'severity': 'low',
        'new_error_count': 1,
        'resolved_error_count': 0,
        'can_determine_changes': True,
        'summary': '1 new error detected'
    }
    simulate_notification_logic(analysis_red_low)
    
    # Scenario 4: RED with critical severity
    print("\n### SCENARIO 4: Critical Changes (RED - Critical) ###")
    analysis_red_critical = {
        'severity': 'critical',
        'new_error_count': 8,
        'resolved_error_count': 2,
        'can_determine_changes': True,
        'summary': '8 new errors detected, including 5 significant integration failures',
        'significant_errors': [
            'ERROR homeassistant.components.mqtt: Setup failed',
            'ERROR homeassistant.components.zwave: Integration could not be set up',
            'ERROR homeassistant.loader: Cannot import component',
        ]
    }
    simulate_notification_logic(analysis_red_critical)
    
    print("\n" + "=" * 60)
    print("DEMONSTRATION COMPLETE")
    print("=" * 60)
    print("\nKey Points:")
    print("- AMBER (⚠️): Shown on first run or when previous logs unavailable")
    print("- GREEN (✅): Shown when no log changes detected")
    print("- RED (🔴): Shown when changes detected, severity varies")
    print("\nAll three states will now create notifications in Home Assistant!")

if __name__ == '__main__':
    main()
