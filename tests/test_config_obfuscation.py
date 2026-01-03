"""
Test configuration integration with log obfuscation
"""
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app'))


def test_config_obfuscate_logs():
    """Test that obfuscate_logs configuration is read correctly"""
    from config_manager import ConfigManager
    
    # Test with obfuscation enabled
    os.environ['OBFUSCATE_LOGS'] = 'true'
    config = ConfigManager()
    assert config.obfuscate_logs is True
    print("✓ obfuscate_logs=true works")
    
    # Test with obfuscation disabled
    os.environ['OBFUSCATE_LOGS'] = 'false'
    config = ConfigManager()
    assert config.obfuscate_logs is False
    print("✓ obfuscate_logs=false works")
    
    # Test default value (should be True)
    if 'OBFUSCATE_LOGS' in os.environ:
        del os.environ['OBFUSCATE_LOGS']
    config = ConfigManager()
    assert config.obfuscate_logs is True
    print("✓ obfuscate_logs default is True")
    
    return True


def test_obfuscation_integration():
    """Test that obfuscation integrates with configuration"""
    from config_manager import ConfigManager
    from log_obfuscator import LogObfuscator
    
    # Set up test environment
    os.environ['OBFUSCATE_LOGS'] = 'true'
    os.environ['SUPERVISOR_TOKEN'] = 'test_token_abc123def456'
    
    config = ConfigManager()
    obfuscator = LogObfuscator(enabled=config.obfuscate_logs)
    
    # Test IP obfuscation
    test_message = "Connecting to 192.168.1.100"
    result = obfuscator.obfuscate(test_message)
    assert "192.***.***.100" in result
    assert "192.168.1.100" not in result
    print("✓ IP obfuscation working with config")
    
    # Test token obfuscation
    test_message = f"Token: {config.supervisor_token}"
    result = obfuscator.obfuscate(test_message)
    assert config.supervisor_token not in result
    assert "tes***456" in result or "test_token_abc***456" in result
    print("✓ Token obfuscation working with config")
    
    # Test with obfuscation disabled
    obfuscator = LogObfuscator(enabled=False)
    test_message = "Connecting to 192.168.1.100 with token abc123def456"
    result = obfuscator.obfuscate(test_message)
    assert result == test_message
    print("✓ Obfuscation can be disabled")
    
    return True


def test_logging_formatter_integration():
    """Test that logging formatter works with configuration"""
    import logging
    import io
    from config_manager import ConfigManager
    from log_obfuscator import LogObfuscator, ObfuscatingFormatter
    
    os.environ['OBFUSCATE_LOGS'] = 'true'
    config = ConfigManager()
    
    # Create a test logger
    test_logger = logging.getLogger('test_integration')
    test_logger.setLevel(logging.INFO)
    test_logger.handlers.clear()
    
    # Add handler with obfuscating formatter
    log_stream = io.StringIO()
    handler = logging.StreamHandler(log_stream)
    
    obfuscator = LogObfuscator(enabled=config.obfuscate_logs)
    formatter = ObfuscatingFormatter(
        fmt='%(message)s',
        obfuscator=obfuscator
    )
    handler.setFormatter(formatter)
    test_logger.addHandler(handler)
    
    # Log a message with sensitive data
    test_logger.info("Connecting to 192.168.1.100 with api_key=secret123456789")
    
    # Check the output
    output = log_stream.getvalue()
    assert "192.***.***.100" in output
    assert "192.168.1.100" not in output
    assert "api_key=sec***789" in output
    assert "secret123456789" not in output
    
    print("✓ Logging formatter integration working")
    return True


def run_all_tests():
    """Run all integration tests"""
    print("=" * 60)
    print("Running Configuration Integration Tests")
    print("=" * 60)
    
    tests = [
        test_config_obfuscate_logs,
        test_obfuscation_integration,
        test_logging_formatter_integration,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except AssertionError as e:
            failed += 1
            print(f"✗ {test.__name__} failed: {e}")
        except Exception as e:
            failed += 1
            print(f"✗ {test.__name__} error: {e}")
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
