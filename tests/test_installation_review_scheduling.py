"""
Test for installation review scheduling bug fix

This test verifies that the installation review check runs independently
of whether updates are available, fixing the bug where the early return
when no updates were found prevented installation review from running.
"""
import sys
import os
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta
import asyncio

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app'))

from config_manager import ConfigManager
from sentry_service import SentryService


def test_installation_review_runs_when_no_updates():
    """Test that installation review check executes even when no updates are available"""
    
    print("Testing installation review scheduling with no updates available...")
    
    # Set up test environment
    os.environ['AI_ENABLED'] = 'false'
    os.environ['SUPERVISOR_TOKEN'] = 'test_token'
    os.environ['ENABLE_INSTALLATION_REVIEW'] = 'true'
    os.environ['INSTALLATION_REVIEW_SCHEDULE'] = 'weekly'
    
    config = ConfigManager()
    service = SentryService(config)
    
    # Set last review to 8 days ago (should trigger review for weekly schedule)
    service._last_installation_review = datetime.now() - timedelta(days=8)
    
    # Track if _should_run_installation_review was called
    review_check_called = []
    original_should_run = service._should_run_installation_review
    
    def mock_should_run():
        result = original_should_run()
        review_check_called.append(result)
        return result
    
    service._should_run_installation_review = mock_should_run
    
    # Mock the run_installation_review method to avoid actual execution
    service.run_installation_review = AsyncMock()
    
    # Mock HomeAssistantClient to return no updates
    async def run_test():
        with patch('sentry_service.HomeAssistantClient') as mock_ha_client_class:
            mock_ha_client = AsyncMock()
            mock_ha_client.__aenter__ = AsyncMock(return_value=mock_ha_client)
            mock_ha_client.__aexit__ = AsyncMock()
            
            # Return empty list for all update checks
            mock_ha_client.get_all_updates = AsyncMock(return_value=[])
            mock_ha_client.get_addon_updates = AsyncMock(return_value=[])
            mock_ha_client.get_hacs_updates = AsyncMock(return_value=[])
            
            mock_ha_client_class.return_value = mock_ha_client
            
            # Mock other dependencies
            service.log_monitor.check_logs = AsyncMock(return_value=None)
            
            # Mock _report_no_updates to avoid errors
            service._report_no_updates = AsyncMock()
            
            # Run the update check
            await service.run_update_check()
            
            # Give async task time to be created (but not necessarily complete)
            await asyncio.sleep(0.1)
    
    # Run the async test
    asyncio.run(run_test())
    
    # Verify that _should_run_installation_review was called
    assert len(review_check_called) > 0, "Installation review check was not called"
    assert review_check_called[0] is True, "Installation review should have been scheduled to run"
    
    # Verify that run_installation_review was actually invoked
    service.run_installation_review.assert_called_once()
    
    print("✓ Installation review check was called when no updates were available")
    print(f"  _should_run_installation_review returned: {review_check_called[0]}")
    print("✓ run_installation_review was invoked")
    
    return True


def test_installation_review_not_run_when_manual():
    """Test that installation review respects 'manual' schedule setting"""
    
    print("Testing installation review with 'manual' schedule...")
    
    # Set up test environment
    os.environ['AI_ENABLED'] = 'false'
    os.environ['SUPERVISOR_TOKEN'] = 'test_token'
    os.environ['ENABLE_INSTALLATION_REVIEW'] = 'true'
    os.environ['INSTALLATION_REVIEW_SCHEDULE'] = 'manual'
    
    config = ConfigManager()
    service = SentryService(config)
    
    # Set last review to 8 days ago
    service._last_installation_review = datetime.now() - timedelta(days=8)
    
    # Verify that _should_run_installation_review returns False for manual
    result = service._should_run_installation_review()
    assert result is False, "Installation review should not run automatically when schedule is 'manual'"
    
    print("✓ Installation review correctly respects 'manual' schedule")
    print(f"  _should_run_installation_review returned: {result}")
    
    return True


def test_installation_review_scheduling_logic():
    """Test the scheduling logic for weekly and monthly schedules"""
    
    print("Testing installation review scheduling logic...")
    
    # Set up test environment
    os.environ['AI_ENABLED'] = 'false'
    os.environ['SUPERVISOR_TOKEN'] = 'test_token'
    os.environ['ENABLE_INSTALLATION_REVIEW'] = 'true'
    
    # Test weekly schedule
    os.environ['INSTALLATION_REVIEW_SCHEDULE'] = 'weekly'
    config = ConfigManager()
    service = SentryService(config)
    
    # First run - should trigger
    service._last_installation_review = None
    assert service._should_run_installation_review() is True, "First run should trigger review"
    print("✓ First run triggers review")
    
    # Recent review - should not trigger
    service._last_installation_review = datetime.now() - timedelta(days=3)
    assert service._should_run_installation_review() is False, "Recent review should not trigger (weekly, 3 days ago)"
    print("✓ Recent review (3 days) does not trigger for weekly schedule")
    
    # Old review - should trigger
    service._last_installation_review = datetime.now() - timedelta(days=8)
    assert service._should_run_installation_review() is True, "Old review should trigger (weekly, 8 days ago)"
    print("✓ Old review (8 days) triggers for weekly schedule")
    
    # Test monthly schedule
    os.environ['INSTALLATION_REVIEW_SCHEDULE'] = 'monthly'
    config = ConfigManager()
    service = SentryService(config)
    
    # Recent review (20 days) - should not trigger for monthly
    service._last_installation_review = datetime.now() - timedelta(days=20)
    assert service._should_run_installation_review() is False, "Recent review should not trigger (monthly, 20 days ago)"
    print("✓ Recent review (20 days) does not trigger for monthly schedule")
    
    # Old review (31 days) - should trigger for monthly
    service._last_installation_review = datetime.now() - timedelta(days=31)
    assert service._should_run_installation_review() is True, "Old review should trigger (monthly, 31 days ago)"
    print("✓ Old review (31 days) triggers for monthly schedule")
    
    return True


if __name__ == '__main__':
    print("Running Installation Review Scheduling Tests...\n")
    
    tests = [
        test_installation_review_runs_when_no_updates,
        test_installation_review_not_run_when_manual,
        test_installation_review_scheduling_logic
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
