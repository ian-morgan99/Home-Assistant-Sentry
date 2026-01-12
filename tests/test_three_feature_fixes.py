"""
Test for three feature fixes:
1. WebUI notification links
2. Installation review configuration
3. Log comparison across HA restarts
"""
import sys
import os
import json
import tempfile

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app'))

def test_installation_review_env_vars():
    """Test that installation review environment variables are set in run.sh"""
    run_sh_path = os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'usr', 'bin', 'run.sh')
    
    with open(run_sh_path, 'r') as f:
        run_sh_content = f.read()
    
    # Check that all installation review environment variables are exported
    required_exports = [
        'ENABLE_INSTALLATION_REVIEW',
        'INSTALLATION_REVIEW_SCHEDULE',
        'INSTALLATION_REVIEW_SCOPE'
    ]
    
    for export_var in required_exports:
        assert f'export {export_var}=' in run_sh_content, f"Missing export for {export_var} in run.sh"
        print(f"✓ Found export for {export_var}")
    
    # Verify the config.yaml has the options
    config_yaml_path = os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'config.yaml')
    with open(config_yaml_path, 'r') as f:
        config_content = f.read()
    
    assert 'enable_installation_review:' in config_content, "Missing enable_installation_review in config.yaml"
    assert 'installation_review_schedule:' in config_content, "Missing installation_review_schedule in config.yaml"
    assert 'installation_review_scope:' in config_content, "Missing installation_review_scope in config.yaml"
    print("✓ All installation review options present in config.yaml")
    
    return True

def test_webui_notification_links():
    """Test that WebUI notification messages provide clear instructions"""
    # Read sentry_service.py
    sentry_service_path = os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app', 'sentry_service.py')
    
    with open(sentry_service_path, 'r') as f:
        sentry_content = f.read()
    
    # Check that notification includes clear access instructions
    assert 'How to Access WebUI' in sentry_content or 'Via Sidebar Panel' in sentry_content, \
        "Missing clear WebUI access instructions in notifications"
    print("✓ Notification includes WebUI access instructions")
    
    # Check that we're not relying solely on markdown links
    assert 'Look for' in sentry_content and 'Sentry' in sentry_content and 'sidebar' in sentry_content, \
        "Missing sidebar panel instructions"
    print("✓ Notification directs users to sidebar panel")
    
    # Check that fallback method is mentioned
    assert 'Settings' in sentry_content and 'Add-ons' in sentry_content, \
        "Missing fallback access method via Settings"
    print("✓ Notification includes fallback access method")
    
    return True

def test_log_monitoring_baseline():
    """Test that log monitoring maintains baseline across restarts"""
    from log_monitor import LogMonitor
    
    # Create mock config
    class MockConfig:
        def __init__(self):
            self.monitor_logs_after_update = True
            self.log_check_lookback_hours = 24
            self.obfuscate_logs = False
    
    config = MockConfig()
    monitor = LogMonitor(config)
    
    # Check that baseline file path is defined
    assert hasattr(monitor, 'BASELINE_LOGS_FILE'), "Missing BASELINE_LOGS_FILE attribute"
    assert monitor.BASELINE_LOGS_FILE == '/data/baseline_logs.json', \
        f"Expected '/data/baseline_logs.json', got '{monitor.BASELINE_LOGS_FILE}'"
    print("✓ Baseline log file path defined correctly")
    
    # Test save_current_logs creates baseline
    with tempfile.TemporaryDirectory() as tmpdir:
        # Override file paths for testing
        monitor.PREVIOUS_LOGS_FILE = os.path.join(tmpdir, 'previous_logs.json')
        monitor.BASELINE_LOGS_FILE = os.path.join(tmpdir, 'baseline_logs.json')
        
        # Save logs (should create both files on first run)
        test_errors = [
            '2025-01-12 00:00:00 ERROR test error 1',
            '2025-01-12 00:00:01 WARNING test warning 1'
        ]
        monitor.save_current_logs(test_errors)
        
        # Check that both files were created
        assert os.path.exists(monitor.PREVIOUS_LOGS_FILE), "Previous logs file not created"
        assert os.path.exists(monitor.BASELINE_LOGS_FILE), "Baseline logs file not created"
        print("✓ Both previous and baseline log files created")
        
        # Load baseline and verify
        with open(monitor.BASELINE_LOGS_FILE, 'r') as f:
            baseline_data = json.load(f)
        
        assert len(baseline_data['errors']) == 2, "Baseline should have 2 errors"
        assert 'timestamp' in baseline_data, "Baseline missing timestamp"
        print("✓ Baseline log snapshot saved correctly")
        
        # Test load_previous_logs falls back to baseline when previous is empty
        monitor.PREVIOUS_LOGS_FILE = os.path.join(tmpdir, 'previous_logs_empty.json')
        # Create empty previous logs (simulating post-restart)
        with open(monitor.PREVIOUS_LOGS_FILE, 'w') as f:
            json.dump({'timestamp': '2025-01-12T00:00:00', 'errors': [], 'lookback_hours': 24}, f)
        
        loaded_logs = monitor.load_previous_logs()
        assert len(loaded_logs) == 2, f"Should load 2 errors from baseline, got {len(loaded_logs)}"
        print("✓ Fallback to baseline when previous logs are empty")
    
    return True

def test_log_monitoring_enhanced_logging():
    """Test that log monitoring has enhanced logging for baseline creation"""
    log_monitor_path = os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app', 'log_monitor.py')
    
    with open(log_monitor_path, 'r') as f:
        log_monitor_content = f.read()
    
    # Check for enhanced logging messages
    assert 'ESTABLISHING BASELINE' in log_monitor_content, "Missing 'ESTABLISHING BASELINE' log message"
    assert 'Creating baseline snapshot' in log_monitor_content, "Missing baseline creation message"
    assert 'persists across HA restarts' in log_monitor_content, "Missing explanation about persistence"
    print("✓ Enhanced logging messages for baseline creation present")
    
    # Check that baseline is mentioned in docstrings
    assert 'baseline' in log_monitor_content.lower(), "No mention of baseline in log_monitor.py"
    print("✓ Baseline concept documented in code")
    
    return True

def test_installation_review_enhanced_logging():
    """Test that installation review has enhanced logging"""
    sentry_service_path = os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app', 'sentry_service.py')
    
    with open(sentry_service_path, 'r') as f:
        sentry_content = f.read()
    
    # Check for enhanced installation review logging
    assert 'INSTALLATION REVIEW FEATURE ENABLED' in sentry_content, \
        "Missing clear 'INSTALLATION REVIEW FEATURE ENABLED' message"
    print("✓ Installation review feature has clear enabled message")
    
    # Check that schedule and scope are logged
    assert 'Schedule:' in sentry_content and 'Scope:' in sentry_content, \
        "Missing schedule and scope logging"
    print("✓ Installation review logs schedule and scope")
    
    # Check that disabled state is also logged clearly
    assert 'Installation review feature is disabled' in sentry_content, \
        "Missing clear disabled message"
    print("✓ Installation review has clear disabled message")
    
    return True

if __name__ == '__main__':
    print("\n" + "="*60)
    print("Testing Three Feature Fixes")
    print("="*60 + "\n")
    
    tests = [
        ("Installation Review Environment Variables", test_installation_review_env_vars),
        ("WebUI Notification Links", test_webui_notification_links),
        ("Log Monitoring Baseline", test_log_monitoring_baseline),
        ("Log Monitoring Enhanced Logging", test_log_monitoring_enhanced_logging),
        ("Installation Review Enhanced Logging", test_installation_review_enhanced_logging),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\nRunning: {test_name}")
        print("-" * 60)
        try:
            if test_func():
                passed += 1
                print(f"✓ {test_name} PASSED\n")
            else:
                failed += 1
                print(f"✗ {test_name} FAILED\n")
        except Exception as e:
            failed += 1
            print(f"✗ {test_name} FAILED with error: {e}\n")
            import traceback
            traceback.print_exc()
    
    print("="*60)
    print(f"Tests completed: {passed} passed, {failed} failed")
    print("="*60)
    
    sys.exit(0 if failed == 0 else 1)
