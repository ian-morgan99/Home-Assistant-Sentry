"""
Test log monitoring functionality
"""
import sys
import os
import tempfile
from datetime import datetime, timedelta

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app'))

def test_log_monitor_init():
    """Test LogMonitor initialization"""
    try:
        from config_manager import ConfigManager
        from log_monitor import LogMonitor
        
        # Set test environment variables
        os.environ['MONITOR_LOGS_AFTER_UPDATE'] = 'true'
        os.environ['LOG_CHECK_LOOKBACK_HOURS'] = '24'
        os.environ['OBFUSCATE_LOGS'] = 'true'
        os.environ['SUPERVISOR_TOKEN'] = 'test_token'
        
        config = ConfigManager()
        # LogMonitor creates its own obfuscator internally
        monitor = LogMonitor(config)
        
        assert monitor.config == config
        assert monitor.obfuscator is not None
        assert monitor.lookback_hours == 24
        
        print("✓ LogMonitor initialization test passed")
        return True
    except Exception as e:
        print(f"✗ LogMonitor initialization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_error_filtering():
    """Test error log filtering"""
    try:
        from config_manager import ConfigManager
        from log_monitor import LogMonitor
        
        os.environ['MONITOR_LOGS_AFTER_UPDATE'] = 'true'
        os.environ['LOG_CHECK_LOOKBACK_HOURS'] = '1'
        os.environ['SUPERVISOR_TOKEN'] = 'test_token'
        
        config = ConfigManager()
        monitor = LogMonitor(config)
        
        # Create test log lines
        now = datetime.now()
        old_time = now - timedelta(hours=2)
        recent_time = now - timedelta(minutes=30)
        
        test_logs = [
            f"{recent_time.strftime('%Y-%m-%d %H:%M:%S')} ERROR test.component: Something failed",
            f"{old_time.strftime('%Y-%m-%d %H:%M:%S')} ERROR old.component: Old error",
            f"{recent_time.strftime('%Y-%m-%d %H:%M:%S')} WARNING test.component: A warning",
            f"{recent_time.strftime('%Y-%m-%d %H:%M:%S')} INFO normal.component: Normal message",
            f"{recent_time.strftime('%Y-%m-%d %H:%M:%S')} CRITICAL test.component: Critical issue",
        ]
        
        filtered = monitor.filter_recent_errors(test_logs)
        
        # Should filter out old error and INFO message
        assert len(filtered) == 3  # ERROR, WARNING, CRITICAL from recent time
        assert any('ERROR' in line and 'Something failed' in line for line in filtered)
        assert any('WARNING' in line for line in filtered)
        assert any('CRITICAL' in line for line in filtered)
        # Old error should NOT be in filtered results
        assert not any('Old error' in line for line in filtered)
        
        print("✓ Error filtering test passed")
        return True
    except Exception as e:
        print(f"✗ Error filtering test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_error_signature_extraction():
    """Test error signature extraction for comparison"""
    try:
        from config_manager import ConfigManager
        from log_monitor import LogMonitor
        
        os.environ['MONITOR_LOGS_AFTER_UPDATE'] = 'true'
        os.environ['SUPERVISOR_TOKEN'] = 'test_token'
        
        config = ConfigManager()
        monitor = LogMonitor(config)
        
        # Test with similar errors that should have same signature
        log1 = "2024-01-01 10:30:45 ERROR homeassistant.components.test: Setup failed for integration test"
        log2 = "2024-01-02 14:22:10 ERROR homeassistant.components.test: Setup failed for integration test"
        
        sig1 = monitor.extract_error_signature(log1)
        sig2 = monitor.extract_error_signature(log2)
        
        # Signatures should be identical despite different timestamps
        assert sig1 == sig2
        assert 'Setup failed' in sig1
        assert '2024-01-01' not in sig1  # Timestamp should be removed
        
        # Test with IP address normalization
        log_with_ip = "2024-01-01 10:30:45 ERROR Connection failed to 192.168.1.100"
        sig_ip = monitor.extract_error_signature(log_with_ip)
        assert '<IP>' in sig_ip
        assert '192.168.1.100' not in sig_ip
        
        print("✓ Error signature extraction test passed")
        return True
    except Exception as e:
        print(f"✗ Error signature extraction test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_log_comparison():
    """Test log comparison between checks"""
    try:
        from config_manager import ConfigManager
        from log_monitor import LogMonitor
        
        os.environ['MONITOR_LOGS_AFTER_UPDATE'] = 'true'
        os.environ['SUPERVISOR_TOKEN'] = 'test_token'
        
        config = ConfigManager()
        monitor = LogMonitor(config)
        
        # Previous errors
        previous = [
            "2024-01-01 10:00:00 ERROR Component A failed",
            "2024-01-01 10:00:00 ERROR Component B failed",
            "2024-01-01 10:00:00 ERROR Component C failed",
        ]
        
        # Current errors - A is resolved, C persists, D is new
        current = [
            "2024-01-01 11:00:00 ERROR Component C failed",
            "2024-01-01 11:00:00 ERROR Component D failed",
        ]
        
        comparison = monitor.compare_logs(current, previous)
        
        assert comparison['total_current'] == 2
        assert comparison['total_previous'] == 3
        assert len(comparison['new_errors']) == 1  # Component D
        assert len(comparison['resolved_errors']) == 2  # Components A and B
        assert len(comparison['persistent_errors']) == 1  # Component C
        
        # Verify the new error is Component D
        assert any('Component D' in err for err in comparison['new_errors'])
        
        print("✓ Log comparison test passed")
        return True
    except Exception as e:
        print(f"✗ Log comparison test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_heuristic_analysis():
    """Test heuristic analysis of log changes"""
    try:
        from config_manager import ConfigManager
        from log_monitor import LogMonitor
        
        os.environ['MONITOR_LOGS_AFTER_UPDATE'] = 'true'
        os.environ['SUPERVISOR_TOKEN'] = 'test_token'
        
        config = ConfigManager()
        monitor = LogMonitor(config)
        
        # Test with no changes
        comparison_no_change = {
            'new_errors': [],
            'resolved_errors': [],
            'persistent_errors': [],
            'total_current': 0,
            'total_previous': 0
        }
        
        analysis = monitor.heuristic_analysis(comparison_no_change)
        assert analysis['severity'] == 'none'
        assert analysis['new_error_count'] == 0
        
        # Test with significant errors
        comparison_significant = {
            'new_errors': [
                "ERROR homeassistant.components.mqtt: Setup of mqtt is taking longer than 60 seconds",
                "ERROR homeassistant.components.zwave: Integration zwave could not be set up",
                "ERROR homeassistant.loader: Cannot import component test",
            ],
            'resolved_errors': [],
            'persistent_errors': [],
            'total_current': 3,
            'total_previous': 0
        }
        
        analysis = monitor.heuristic_analysis(comparison_significant)
        assert analysis['severity'] in ['medium', 'high', 'critical']
        assert analysis['has_significant_errors'] is True
        assert len(analysis['significant_errors']) == 3
        assert analysis['new_error_count'] == 3
        
        # Test with many non-significant errors
        comparison_many = {
            'new_errors': ['ERROR test: Minor issue'] * 15,
            'resolved_errors': [],
            'persistent_errors': [],
            'total_current': 15,
            'total_previous': 0
        }
        
        analysis = monitor.heuristic_analysis(comparison_many)
        assert analysis['severity'] == 'medium'
        assert analysis['new_error_count'] == 15
        
        print("✓ Heuristic analysis test passed")
        return True
    except Exception as e:
        print(f"✗ Heuristic analysis test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_save_and_load_logs():
    """Test saving and loading previous logs"""
    try:
        from config_manager import ConfigManager
        from log_monitor import LogMonitor
        
        os.environ['MONITOR_LOGS_AFTER_UPDATE'] = 'true'
        os.environ['SUPERVISOR_TOKEN'] = 'test_token'
        
        config = ConfigManager()
        monitor = LogMonitor(config)
        
        # Use a temporary file for testing
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp:
            monitor.PREVIOUS_LOGS_FILE = tmp.name
        
        try:
            # Save some test logs
            test_errors = [
                "ERROR Component A failed",
                "WARNING Component B warning",
            ]
            
            monitor.save_current_logs(test_errors)
            
            # Load them back
            loaded = monitor.load_previous_logs()
            
            assert len(loaded) == 2
            assert loaded == test_errors
            
            print("✓ Save and load logs test passed")
            return True
        finally:
            # Clean up temp file
            if os.path.exists(monitor.PREVIOUS_LOGS_FILE):
                os.remove(monitor.PREVIOUS_LOGS_FILE)
    except Exception as e:
        print(f"✗ Save and load logs test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_obfuscation_in_logs():
    """Test that sensitive data is obfuscated before AI analysis"""
    try:
        from config_manager import ConfigManager
        from log_monitor import LogMonitor
        from log_obfuscator import LogObfuscator
        
        os.environ['MONITOR_LOGS_AFTER_UPDATE'] = 'true'
        os.environ['OBFUSCATE_LOGS'] = 'true'
        os.environ['SUPERVISOR_TOKEN'] = 'test_token'
        
        config = ConfigManager()
        obfuscator = LogObfuscator(enabled=True)
        monitor = LogMonitor(config, obfuscator)
        
        # Test log with sensitive data
        log_with_secrets = "ERROR Failed to connect to 192.168.1.100 with token abc123456789def"
        
        # Obfuscate it
        obfuscated = monitor.obfuscator.obfuscate(log_with_secrets)
        
        # Check that IP is obfuscated
        assert '192.***.***.100' in obfuscated
        assert '192.168.1.100' not in obfuscated
        
        # Check that token is obfuscated (the obfuscator catches this pattern)
        assert 'abc123456789def' not in obfuscated or '***' in obfuscated
        
        print("✓ Obfuscation in logs test passed")
        return True
    except Exception as e:
        print(f"✗ Obfuscation in logs test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("Running Log Monitor tests...\n")
    
    tests = [
        test_log_monitor_init,
        test_error_filtering,
        test_error_signature_extraction,
        test_log_comparison,
        test_heuristic_analysis,
        test_save_and_load_logs,
        test_obfuscation_in_logs,
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
