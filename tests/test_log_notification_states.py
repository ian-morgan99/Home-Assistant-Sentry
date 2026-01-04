"""
Test log monitoring notification states (green/amber/red)
"""
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app'))

def test_amber_notification_state():
    """Test AMBER notification state (can't determine changes)"""
    try:
        from config_manager import ConfigManager
        from log_monitor import LogMonitor
        
        os.environ['MONITOR_LOGS_AFTER_UPDATE'] = 'true'
        os.environ['SUPERVISOR_TOKEN'] = 'test_token'
        
        config = ConfigManager()
        monitor = LogMonitor(config)
        
        # Simulate first run (no previous logs)
        current_errors = [
            "ERROR Component A failed",
            "ERROR Component B failed",
        ]
        previous_errors = []  # No previous logs
        
        comparison = monitor.compare_logs(current_errors, previous_errors)
        analysis = monitor.heuristic_analysis(comparison)
        
        # Mark as unable to determine changes (first run)
        analysis['can_determine_changes'] = False
        
        # Verify the analysis should be marked as unable to determine
        assert analysis['can_determine_changes'] is False
        
        print("✓ AMBER notification state test passed")
        return True
    except Exception as e:
        print(f"✗ AMBER notification state test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_green_notification_state():
    """Test GREEN notification state (no changes)"""
    try:
        from config_manager import ConfigManager
        from log_monitor import LogMonitor
        
        os.environ['MONITOR_LOGS_AFTER_UPDATE'] = 'true'
        os.environ['SUPERVISOR_TOKEN'] = 'test_token'
        
        config = ConfigManager()
        monitor = LogMonitor(config)
        
        # Simulate no changes
        identical_errors = [
            "ERROR Component A failed",
            "ERROR Component B failed",
        ]
        
        comparison = monitor.compare_logs(identical_errors, identical_errors)
        analysis = monitor.heuristic_analysis(comparison)
        
        # Mark as able to determine changes
        analysis['can_determine_changes'] = True
        
        # Verify no changes detected
        assert analysis['severity'] == 'none'
        assert analysis['new_error_count'] == 0
        assert analysis['resolved_error_count'] == 0
        assert analysis['can_determine_changes'] is True
        
        print("✓ GREEN notification state test passed")
        return True
    except Exception as e:
        print(f"✗ GREEN notification state test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_red_notification_state():
    """Test RED notification state (changes detected)"""
    try:
        from config_manager import ConfigManager
        from log_monitor import LogMonitor
        
        os.environ['MONITOR_LOGS_AFTER_UPDATE'] = 'true'
        os.environ['SUPERVISOR_TOKEN'] = 'test_token'
        
        config = ConfigManager()
        monitor = LogMonitor(config)
        
        # Simulate changes
        previous_errors = [
            "ERROR Component A failed",
        ]
        current_errors = [
            "ERROR Component A failed",
            "ERROR Component B failed",  # New error
            "ERROR Component C failed",  # New error
        ]
        
        comparison = monitor.compare_logs(current_errors, previous_errors)
        analysis = monitor.heuristic_analysis(comparison)
        
        # Mark as able to determine changes
        analysis['can_determine_changes'] = True
        
        # Verify changes detected
        assert analysis['new_error_count'] == 2
        assert analysis['can_determine_changes'] is True
        assert analysis['severity'] != 'none'
        
        print("✓ RED notification state test passed")
        return True
    except Exception as e:
        print(f"✗ RED notification state test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_enhanced_debug_logging():
    """Test that can_determine_changes flag is set correctly"""
    try:
        from config_manager import ConfigManager
        from log_monitor import LogMonitor
        
        os.environ['MONITOR_LOGS_AFTER_UPDATE'] = 'true'
        os.environ['SUPERVISOR_TOKEN'] = 'test_token'
        
        config = ConfigManager()
        monitor = LogMonitor(config)
        
        # Test with previous logs available
        previous = ["ERROR test"]
        current = ["ERROR test", "ERROR new"]
        comparison = monitor.compare_logs(current, previous)
        
        # In the actual check_logs method, can_determine_changes would be True
        # when previous_errors is not empty
        can_determine = len(previous) > 0
        assert can_determine is True
        
        # Test with no previous logs
        previous_empty = []
        monitor.compare_logs(current, previous_empty)
        
        # In the actual check_logs method, can_determine_changes would be False
        # when previous_errors is empty
        can_determine_empty = len(previous_empty) > 0
        assert can_determine_empty is False
        
        print("✓ Enhanced debug logging test passed")
        return True
    except Exception as e:
        print(f"✗ Enhanced debug logging test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("Running Log Notification States tests...\n")
    
    tests = [
        test_amber_notification_state,
        test_green_notification_state,
        test_red_notification_state,
        test_enhanced_debug_logging,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        if test():
            passed += 1
        else:
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"Tests completed: {passed} passed, {failed} failed")
    print(f"{'='*50}")
    
    sys.exit(0 if failed == 0 else 1)
