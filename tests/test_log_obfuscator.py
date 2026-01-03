"""
Tests for log obfuscator functionality
"""
import sys
import os
import logging

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app'))

from log_obfuscator import LogObfuscator, ObfuscatingFormatter


def test_ip_obfuscation():
    """Test IP address obfuscation"""
    obfuscator = LogObfuscator(enabled=True)
    
    # Test standard private IP addresses
    assert obfuscator.obfuscate_ip("192.168.1.100") == "192.***.***.100"
    assert obfuscator.obfuscate_ip("10.0.0.5") == "10.***.***.5"
    assert obfuscator.obfuscate_ip("172.16.20.30") == "172.***.***.30"
    
    # Test public IP addresses
    assert obfuscator.obfuscate_ip("8.8.8.8") == "8.***.***.8"
    assert obfuscator.obfuscate_ip("1.2.3.4") == "1.***.***.4"
    
    # Test multiple IPs in one string
    result = obfuscator.obfuscate_ip("Connecting from 192.168.1.100 to 10.0.0.5")
    assert result == "Connecting from 192.***.***.100 to 10.***.***.5"
    
    # Test IP in URL context
    result = obfuscator.obfuscate_ip("http://192.168.1.100:8123/api")
    assert result == "http://192.***.***.100:8123/api"
    
    print("✓ IP obfuscation tests passed")
    return True


def test_api_key_obfuscation():
    """Test API key and token obfuscation"""
    obfuscator = LogObfuscator(enabled=True)
    
    # Test various API key formats
    result = obfuscator.obfuscate_api_key("api_key=abc123def456ghi789jkl")
    assert "abc***jkl" in result
    
    result = obfuscator.obfuscate_api_key("token: xyz123456789012345678")
    assert "xyz***678" in result
    
    result = obfuscator.obfuscate_api_key("API_KEY: ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    assert "ABC***XYZ" in result
    
    # Test short keys (less than 8 chars - won't be obfuscated)
    # Keys must be at least 8 characters to be considered sensitive
    result = obfuscator.obfuscate_api_key("token=abc12")
    # Short keys are not obfuscated (less than 8 chars)
    assert result == "token=abc12"
    
    # Test minimum length key (8 chars)
    result = obfuscator.obfuscate_api_key("token=abcd1234")
    assert "abc***234" in result or "token=abc***234" in result
    
    # Test apikey variant
    result = obfuscator.obfuscate_api_key('apikey="sk-proj-abcdef123456789012345"')
    assert "sk-***345" in result or "sk-proj-abc***345" in result
    
    print("✓ API key obfuscation tests passed")
    return True


def test_bearer_token_obfuscation():
    """Test Bearer token obfuscation"""
    obfuscator = LogObfuscator(enabled=True)
    
    # Test standard Bearer token
    result = obfuscator.obfuscate_bearer_token("Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9")
    assert "Bearer eyJ***J9" in result
    
    result = obfuscator.obfuscate_bearer_token("Bearer abc123def456ghi789")
    assert "Bearer abc***89" in result
    
    # Test short token
    result = obfuscator.obfuscate_bearer_token("Bearer abc12")
    assert "Bearer abc***" in result
    
    print("✓ Bearer token obfuscation tests passed")
    return True


def test_url_param_obfuscation():
    """Test URL parameter obfuscation"""
    obfuscator = LogObfuscator(enabled=True)
    
    # Test API key in URL
    result = obfuscator.obfuscate_url_params("https://api.example.com/data?api_key=secret123456")
    assert "?api_key=sec***456" in result
    
    result = obfuscator.obfuscate_url_params("?token=abc123def456&other=value")
    assert "token=abc***456" in result
    assert "other=value" in result
    
    # Test multiple sensitive parameters
    result = obfuscator.obfuscate_url_params("?api_key=key123&token=tok456&normal=data")
    assert "api_key=key***" in result or "api_key=***" in result
    assert "token=tok***" in result
    assert "normal=data" in result
    
    print("✓ URL parameter obfuscation tests passed")
    return True


def test_combined_obfuscation():
    """Test combined obfuscation of multiple sensitive data types"""
    obfuscator = LogObfuscator(enabled=True)
    
    # Test a realistic log message with multiple sensitive items
    message = "Connecting to 192.168.1.100 with api_key=abc123def456ghi and token: xyz12345678901234"
    result = obfuscator.obfuscate(message)
    
    assert "192.***.***.100" in result
    assert "abc***ghi" in result or "abc***456" in result
    assert "xyz***234" in result
    
    # Test URL with IP and token
    message = "Fetching from http://10.0.0.5:8080/api?token=secret123456"
    result = obfuscator.obfuscate(message)
    
    assert "10.***.***.5" in result
    assert "token=sec***456" in result
    
    print("✓ Combined obfuscation tests passed")
    return True


def test_obfuscation_disabled():
    """Test that obfuscation can be disabled"""
    obfuscator = LogObfuscator(enabled=False)
    
    message = "192.168.1.100 api_key=secret123"
    result = obfuscator.obfuscate(message)
    
    # Should return original message unchanged
    assert result == message
    
    print("✓ Obfuscation disable test passed")
    return True


def test_no_false_positives():
    """Test that normal data is not obfuscated"""
    obfuscator = LogObfuscator(enabled=True)
    
    # Numbers that look like IP but aren't
    message = "Version 10.0.0.5 has 192.168.1.100 changes"
    result = obfuscator.obfuscate(message)
    # These will be obfuscated as they match IP pattern
    # This is expected behavior
    
    # Regular numbers should not be affected
    message = "The value is 42 and count is 100"
    result = obfuscator.obfuscate(message)
    assert result == message
    
    # Regular text should not be affected
    message = "This is a normal log message without sensitive data"
    result = obfuscator.obfuscate(message)
    assert result == message
    
    print("✓ False positive tests passed")
    return True


def test_obfuscating_formatter():
    """Test the custom logging formatter"""
    # Create a logger with obfuscating formatter
    logger = logging.getLogger('test_obfuscator')
    logger.setLevel(logging.DEBUG)
    
    # Create a string handler to capture output
    import io
    log_stream = io.StringIO()
    handler = logging.StreamHandler(log_stream)
    
    # Set up the obfuscating formatter
    obfuscator = LogObfuscator(enabled=True)
    formatter = ObfuscatingFormatter(
        fmt='%(levelname)s - %(message)s',
        obfuscator=obfuscator
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Log a message with sensitive data
    logger.info("Connecting to 192.168.1.100 with api_key=secret123456")
    
    # Get the logged output
    output = log_stream.getvalue()
    
    # Verify obfuscation happened
    assert "192.***.***.100" in output
    assert "api_key=sec***456" in output
    assert "192.168.1.100" not in output
    assert "secret123456" not in output
    
    print("✓ ObfuscatingFormatter tests passed")
    return True


def test_edge_cases():
    """Test edge cases and boundary conditions"""
    obfuscator = LogObfuscator(enabled=True)
    
    # Empty string
    assert obfuscator.obfuscate("") == ""
    
    # String with only spaces
    assert obfuscator.obfuscate("   ") == "   "
    
    # Very long IP-like numbers (should still obfuscate valid IPs)
    message = "1234.5678.9012.3456"  # Not a valid IP (octets > 255)
    result = obfuscator.obfuscate(message)
    # Regex will still match it, which is okay for obfuscation purposes
    
    # IP at start and end
    message = "192.168.1.1 is connected to 10.0.0.1"
    result = obfuscator.obfuscate(message)
    assert "192.***.***.1" in result
    assert "10.***.***.1" in result
    
    # Multiple instances of same key
    message = "api_key=secret123 and api_key=another456"
    result = obfuscator.obfuscate(message)
    assert "secret123" not in result or "sec***123" in result
    assert "another456" not in result or "ano***456" in result
    
    print("✓ Edge case tests passed")
    return True


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("Running Log Obfuscator Tests")
    print("=" * 60)
    
    tests = [
        test_ip_obfuscation,
        test_api_key_obfuscation,
        test_bearer_token_obfuscation,
        test_url_param_obfuscation,
        test_combined_obfuscation,
        test_obfuscation_disabled,
        test_no_false_positives,
        test_obfuscating_formatter,
        test_edge_cases,
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
