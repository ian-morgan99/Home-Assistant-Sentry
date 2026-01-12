"""
Test for installation review timeout and logging improvements

This test verifies:
1. The timeout is set to 300 seconds (5 minutes) for installation reviews
2. Progress logging is present and clear
3. Parsing logs provide detailed feedback
"""
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app'))

import re


def test_timeout_value_is_300_seconds():
    """Verify that the timeout for installation reviews is set to 300 seconds"""
    
    print("Testing installation review timeout value...")
    
    # Read the installation_reviewer.py file
    reviewer_path = os.path.join(
        os.path.dirname(__file__), 
        '..', 
        'ha_sentry', 
        'rootfs', 
        'app', 
        'installation_reviewer.py'
    )
    
    with open(reviewer_path, 'r') as f:
        content = f.read()
    
    # Check that timeout_seconds = 300.0 is set
    assert 'timeout_seconds = 300.0' in content, \
        "Installation review timeout should be set to 300.0 seconds"
    
    print("✓ Timeout correctly set to 300 seconds (5 minutes)")
    
    # Verify the timeout is used in asyncio.wait_for (on separate line due to formatting)
    assert 'timeout=timeout_seconds' in content, \
        "Timeout should be passed to asyncio.wait_for"
    
    print("✓ Timeout correctly used in asyncio.wait_for call")
    
    return True


def test_progress_logging_exists():
    """Verify that progress logging indicators are present"""
    
    print("Testing for progress logging indicators...")
    
    reviewer_path = os.path.join(
        os.path.dirname(__file__), 
        '..', 
        'ha_sentry', 
        'rootfs', 
        'app', 
        'installation_reviewer.py'
    )
    
    with open(reviewer_path, 'r') as f:
        content = f.read()
    
    # Check for hourglass emoji indicating waiting
    assert '⏳ Waiting for AI to analyze installation' in content, \
        "Should have waiting indicator log message"
    
    print("✓ Found waiting indicator (⏳)")
    
    # Check for checkmark emoji indicating success
    assert '✅ AI call completed successfully' in content, \
        "Should have success indicator log message"
    
    print("✓ Found success indicator (✅)")
    
    # Check for X mark emoji indicating failure
    assert '❌ AI installation review timed out' in content, \
        "Should have timeout indicator log message"
    
    print("✓ Found timeout indicator (❌)")
    
    # Check for detailed timeout info logging
    assert 'Waiting for AI response (timeout:' in content, \
        "Should log timeout value before waiting"
    
    print("✓ Found detailed timeout info logging")
    
    return True


def test_parsing_logs_exist():
    """Verify that detailed parsing logs are present"""
    
    print("Testing for detailed parsing logs...")
    
    reviewer_path = os.path.join(
        os.path.dirname(__file__), 
        '..', 
        'ha_sentry', 
        'rootfs', 
        'app', 
        'installation_reviewer.py'
    )
    
    with open(reviewer_path, 'r') as f:
        content = f.read()
    
    # Check for JSON extraction logging
    assert 'Found JSON start at position' in content, \
        "Should log JSON start position"
    
    print("✓ Found JSON start position logging")
    
    # Check for JSON end position logging
    assert 'Found JSON end at position' in content, \
        "Should log JSON end position"
    
    print("✓ Found JSON end position logging")
    
    # Check for parsing success summary
    assert 'Successfully parsed AI review:' in content, \
        "Should log parsing success summary"
    
    print("✓ Found parsing success summary")
    
    # Check for recommendation/insight/warning counts in success log
    assert 'recommendations' in content and 'insights' in content and 'warnings' in content, \
        "Should log counts of recommendations, insights, and warnings"
    
    print("✓ Found detailed success metrics logging")
    
    return True


def test_sentry_service_logging_improvements():
    """Verify that sentry_service.py has improved logging for installation reviews"""
    
    print("Testing sentry_service.py logging improvements...")
    
    service_path = os.path.join(
        os.path.dirname(__file__), 
        '..', 
        'ha_sentry', 
        'rootfs', 
        'app', 
        'sentry_service.py'
    )
    
    with open(service_path, 'r') as f:
        content = f.read()
    
    # Check for completion banner
    assert 'INSTALLATION REVIEW COMPLETED SUCCESSFULLY' in content, \
        "Should have success banner"
    
    print("✓ Found completion success banner")
    
    # Check for failure banner
    assert 'INSTALLATION REVIEW FAILED' in content, \
        "Should have failure banner"
    
    print("✓ Found failure banner")
    
    # Check for detailed success metrics
    assert 'Recommendations:' in content and 'AI-powered:' in content, \
        "Should log detailed completion metrics"
    
    print("✓ Found detailed completion metrics")
    
    return True


if __name__ == '__main__':
    print("Running Installation Review Timeout and Logging Tests...\n")
    
    tests = [
        test_timeout_value_is_300_seconds,
        test_progress_logging_exists,
        test_parsing_logs_exist,
        test_sentry_service_logging_improvements,
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
