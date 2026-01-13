"""
Test baseline persistence across HA restarts

This test verifies that the log monitoring baseline is preserved when
Home Assistant restarts and clears its logs.
"""
import sys
import os
import tempfile
import json

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app'))

def test_baseline_not_overwritten_on_restart():
    """
    Test that baseline is NOT overwritten when HA restarts and logs are empty
    
    Scenario:
    1. Initial state: baseline with 10 errors exists
    2. HA restarts, logs are cleared
    3. Monitor finds 0-5 errors (HA just restarted)
    4. Baseline should NOT be overwritten
    5. Next check can still compare against pre-restart baseline
    """
    try:
        from config_manager import ConfigManager
        from log_monitor import LogMonitor
        
        # Set up test environment
        os.environ['MONITOR_LOGS_AFTER_UPDATE'] = 'true'
        os.environ['SUPERVISOR_TOKEN'] = 'test_token'
        
        class MockConfig:
            def __init__(self):
                self.monitor_logs_after_update = True
                self.log_check_lookback_hours = 24
                self.obfuscate_logs = False
        
        config = MockConfig()
        monitor = LogMonitor(config)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Override file paths for testing
            monitor.PREVIOUS_LOGS_FILE = os.path.join(tmpdir, 'previous_logs.json')
            monitor.BASELINE_LOGS_FILE = os.path.join(tmpdir, 'baseline_logs.json')
            
            # Step 1: Create initial baseline with 10 errors (normal operation)
            print("Step 1: Creating baseline with 10 errors (normal operation)")
            initial_errors = [f'2025-01-12 10:00:00 ERROR test error {i}' for i in range(10)]
            monitor.save_current_logs(initial_errors)
            
            # Verify baseline was created
            assert os.path.exists(monitor.BASELINE_LOGS_FILE), "Baseline should be created"
            with open(monitor.BASELINE_LOGS_FILE, 'r') as f:
                baseline_data = json.load(f)
            assert len(baseline_data['errors']) == 10, "Baseline should have 10 errors"
            print(f"✓ Baseline created with {len(baseline_data['errors'])} errors")
            
            # Step 2: Simulate HA restart - very few errors (0-5)
            print("\nStep 2: Simulating HA restart with 2 errors (logs cleared)")
            post_restart_errors = [
                '2025-01-12 11:00:00 ERROR startup error 1',
                '2025-01-12 11:00:01 WARNING startup warning 1'
            ]
            monitor.save_current_logs(post_restart_errors)
            
            # Step 3: Verify baseline was NOT overwritten (preserved from step 1)
            print("\nStep 3: Verifying baseline was preserved")
            with open(monitor.BASELINE_LOGS_FILE, 'r') as f:
                baseline_after_restart = json.load(f)
            
            assert len(baseline_after_restart['errors']) == 10, \
                f"Baseline should still have 10 errors (preserved), but has {len(baseline_after_restart['errors'])}"
            
            # Verify the baseline still contains the original errors, not the post-restart ones
            baseline_error_text = '\n'.join(baseline_after_restart['errors'])
            assert 'test error 0' in baseline_error_text, "Baseline should contain original errors"
            assert 'startup error' not in baseline_error_text, "Baseline should NOT contain post-restart errors"
            
            print(f"✓ Baseline preserved with {len(baseline_after_restart['errors'])} errors after restart")
            
            # Step 4: Verify previous_logs was updated (should have the 2 new errors)
            with open(monitor.PREVIOUS_LOGS_FILE, 'r') as f:
                previous_data = json.load(f)
            assert len(previous_data['errors']) == 2, "Previous logs should have 2 errors"
            print(f"✓ Previous logs updated with {len(previous_data['errors'])} errors")
            
            # Step 5: Test that baseline IS updated when we have 6-20 errors (genuinely stable)
            print("\nStep 4: Testing baseline update with 8 errors (genuinely stable)")
            stable_errors = [f'2025-01-12 12:00:00 ERROR stable error {i}' for i in range(8)]
            monitor.save_current_logs(stable_errors)
            
            with open(monitor.BASELINE_LOGS_FILE, 'r') as f:
                baseline_after_stable = json.load(f)
            
            assert len(baseline_after_stable['errors']) == 8, \
                f"Baseline should be updated to 8 errors, but has {len(baseline_after_stable['errors'])}"
            
            baseline_error_text = '\n'.join(baseline_after_stable['errors'])
            assert 'stable error' in baseline_error_text, "Baseline should contain stable errors"
            print(f"✓ Baseline updated with {len(baseline_after_stable['errors'])} errors (genuinely stable)")
            
        print("\n✓ Baseline persistence test passed")
        return True
        
    except Exception as e:
        print(f"\n✗ Baseline persistence test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_baseline_creation_on_first_run():
    """
    Test that baseline IS created on first run even with 0 errors
    """
    try:
        from log_monitor import LogMonitor
        
        os.environ['MONITOR_LOGS_AFTER_UPDATE'] = 'true'
        os.environ['SUPERVISOR_TOKEN'] = 'test_token'
        
        class MockConfig:
            def __init__(self):
                self.monitor_logs_after_update = True
                self.log_check_lookback_hours = 24
                self.obfuscate_logs = False
        
        config = MockConfig()
        monitor = LogMonitor(config)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            monitor.PREVIOUS_LOGS_FILE = os.path.join(tmpdir, 'previous_logs.json')
            monitor.BASELINE_LOGS_FILE = os.path.join(tmpdir, 'baseline_logs.json')
            
            # First run with 0 errors should still create baseline
            print("Testing first run with 0 errors")
            monitor.save_current_logs([])
            
            assert os.path.exists(monitor.BASELINE_LOGS_FILE), "Baseline should be created on first run"
            with open(monitor.BASELINE_LOGS_FILE, 'r') as f:
                baseline_data = json.load(f)
            assert len(baseline_data['errors']) == 0, "Baseline should have 0 errors"
            print("✓ Baseline created on first run even with 0 errors")
            
        return True
        
    except Exception as e:
        print(f"✗ First run test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_load_previous_logs_fallback():
    """
    Test that load_previous_logs correctly falls back to baseline when previous logs are empty
    """
    try:
        from log_monitor import LogMonitor
        
        os.environ['MONITOR_LOGS_AFTER_UPDATE'] = 'true'
        os.environ['SUPERVISOR_TOKEN'] = 'test_token'
        
        class MockConfig:
            def __init__(self):
                self.monitor_logs_after_update = True
                self.log_check_lookback_hours = 24
                self.obfuscate_logs = False
        
        config = MockConfig()
        monitor = LogMonitor(config)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            monitor.PREVIOUS_LOGS_FILE = os.path.join(tmpdir, 'previous_logs.json')
            monitor.BASELINE_LOGS_FILE = os.path.join(tmpdir, 'baseline_logs.json')
            
            # Create baseline with errors
            baseline_errors = [f'ERROR baseline {i}' for i in range(5)]
            baseline_data = {
                'timestamp': '2025-01-12T10:00:00',
                'errors': baseline_errors,
                'lookback_hours': 24
            }
            with open(monitor.BASELINE_LOGS_FILE, 'w') as f:
                json.dump(baseline_data, f)
            
            # Create previous logs with NO errors (simulating restart)
            previous_data = {
                'timestamp': '2025-01-12T11:00:00',
                'errors': [],
                'lookback_hours': 24
            }
            with open(monitor.PREVIOUS_LOGS_FILE, 'w') as f:
                json.dump(previous_data, f)
            
            # Load should fall back to baseline
            print("Testing fallback to baseline when previous logs are empty")
            loaded = monitor.load_previous_logs()
            
            assert len(loaded) == 5, f"Should load 5 errors from baseline, got {len(loaded)}"
            assert 'baseline' in loaded[0], "Should load baseline errors"
            print(f"✓ Correctly fell back to baseline with {len(loaded)} errors")
            
        return True
        
    except Exception as e:
        print(f"✗ Fallback test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("Testing baseline persistence across HA restarts\n")
    print("=" * 60)
    
    tests = [
        test_baseline_not_overwritten_on_restart,
        test_baseline_creation_on_first_run,
        test_load_previous_logs_fallback,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        print(f"\n{'='*60}")
        print(f"Running: {test.__name__}")
        print('='*60)
        if test():
            passed += 1
        else:
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"Tests completed: {passed} passed, {failed} failed")
    print(f"{'='*60}")
    
    sys.exit(0 if failed == 0 else 1)
