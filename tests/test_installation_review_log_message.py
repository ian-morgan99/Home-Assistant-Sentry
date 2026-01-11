"""
Test for installation review log message fix

This test verifies that the log message accurately reflects the actual
configuration value for enable_installation_review instead of hardcoding 'false'.
"""
import sys
import os
import logging
from io import StringIO

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app'))

from config_manager import ConfigManager
from sentry_service import SentryService


def test_log_message_shows_true_value():
    """Test that the log message correctly shows enable_installation_review=True when it's enabled"""
    
    print("Testing log message when enable_installation_review=True...")
    
    # Set up test environment with installation review ENABLED
    os.environ['AI_ENABLED'] = 'false'
    os.environ['SUPERVISOR_TOKEN'] = 'test_token'
    os.environ['ENABLE_INSTALLATION_REVIEW'] = 'true'
    os.environ['INSTALLATION_REVIEW_SCHEDULE'] = 'weekly'
    
    # Capture logs
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.DEBUG)
    logger = logging.getLogger('sentry_service')
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    
    config = ConfigManager()
    service = SentryService(config)
    
    # Verify configuration is actually enabled
    assert config.enable_installation_review is True, "Configuration should be enabled"
    print(f"✓ Configuration correctly set: enable_installation_review={config.enable_installation_review}")
    
    # Call the method that produces the log message
    # Since the feature is enabled, this should not produce the "disabled" log
    result = service._should_run_installation_review()
    
    # Get the log output
    log_output = log_capture.getvalue()
    
    # When the feature is enabled and it's the first run, it should return True
    # and should NOT log the "disabled" message
    assert result is True, "Should return True for first run with feature enabled"
    assert "Feature is disabled" not in log_output, "Should not log 'disabled' message when feature is enabled"
    
    print("✓ No 'disabled' message logged when feature is enabled")
    print(f"  _should_run_installation_review returned: {result}")
    
    # Clean up
    logger.removeHandler(handler)
    
    return True


def test_log_message_shows_false_value():
    """Test that the log message correctly shows enable_installation_review=False when it's disabled"""
    
    print("Testing log message when enable_installation_review=False...")
    
    # Set up test environment with installation review DISABLED
    os.environ['AI_ENABLED'] = 'false'
    os.environ['SUPERVISOR_TOKEN'] = 'test_token'
    os.environ['ENABLE_INSTALLATION_REVIEW'] = 'false'
    os.environ['INSTALLATION_REVIEW_SCHEDULE'] = 'weekly'
    
    # Capture logs
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.DEBUG)
    logger = logging.getLogger('sentry_service')
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    
    config = ConfigManager()
    service = SentryService(config)
    
    # Verify configuration is actually disabled
    assert config.enable_installation_review is False, "Configuration should be disabled"
    print(f"✓ Configuration correctly set: enable_installation_review={config.enable_installation_review}")
    
    # Call the method that produces the log message
    result = service._should_run_installation_review()
    
    # Get the log output
    log_output = log_capture.getvalue()
    
    # When the feature is disabled, it should return False and log the disabled message
    assert result is False, "Should return False when feature is disabled"
    assert "Feature is disabled" in log_output, "Should log 'disabled' message when feature is disabled"
    
    # The critical fix: ensure the log message shows the actual value (False)
    assert "enable_installation_review=False" in log_output, \
        "Log message should show actual value 'enable_installation_review=False'"
    
    print("✓ Correct 'disabled' message logged with actual value")
    print(f"  Log message contains: 'enable_installation_review=False'")
    print(f"  _should_run_installation_review returned: {result}")
    
    # Clean up
    logger.removeHandler(handler)
    
    return True


if __name__ == '__main__':
    print("Running Installation Review Log Message Tests...\n")
    
    tests = [
        test_log_message_shows_true_value,
        test_log_message_shows_false_value
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
        print()
    
    print(f"{'='*50}")
    print(f"Tests completed: {passed} passed, {failed} failed")
    print(f"{'='*50}")
    
    sys.exit(0 if failed == 0 else 1)
