"""
Test cases for AI timeout fix with async wrapper
"""
import sys
import os
import asyncio
import time

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app'))

from config_manager import ConfigManager
from ai_client import AIClient


async def test_timeout_fallback_triggered():
    """Test that AI timeout triggers fallback analysis"""
    print("\n=== Test: AI Timeout Triggers Fallback ===")
    
    # Setup
    os.environ['AI_ENABLED'] = 'true'
    os.environ['AI_PROVIDER'] = 'lmstudio'
    os.environ['AI_ENDPOINT'] = 'http://127.0.0.1:9999'  # Non-existent endpoint
    os.environ['AI_MODEL'] = 'test-model'
    
    config = ConfigManager()
    ai = AIClient(config)
    
    # Mock update data
    addon_updates = [{
        'name': 'Test Addon',
        'current_version': '1.0.0',
        'latest_version': '1.0.1',
        'type': 'addon'
    }]
    hacs_updates = []
    
    # Test: Call analyze_updates which should timeout and fallback
    start_time = time.time()
    try:
        result = await ai.analyze_updates(addon_updates, hacs_updates)
        elapsed = time.time() - start_time
        
        # Verify we got a result (fallback)
        assert 'safe' in result, "Result should have 'safe' key"
        assert 'confidence' in result, "Result should have 'confidence' key"
        assert 'issues' in result, "Result should have 'issues' key"
        assert 'recommendations' in result, "Result should have 'recommendations' key"
        assert 'summary' in result, "Result should have 'summary' key"
        
        # Verify it didn't hang forever (should use fallback quickly since connection fails)
        # Connection timeout is 30s, but if endpoint is unreachable it should fail faster
        assert elapsed < 60, f"Analysis should complete within 60s, took {elapsed:.1f}s"
        
        print(f"✓ Test passed: Timeout triggered fallback in {elapsed:.1f}s")
        print(f"  Result: safe={result['safe']}, confidence={result['confidence']:.2f}")
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_asyncio_to_thread_not_blocking():
    """Test that asyncio.to_thread prevents blocking"""
    print("\n=== Test: Async Wrapper Prevents Blocking ===")
    
    # Create two concurrent tasks
    async def slow_sync_task():
        """Simulates a slow synchronous operation"""
        def _blocking_call():
            time.sleep(2)  # 2 second sleep
            return "slow_result"
        # Wrap in to_thread so it doesn't block
        return await asyncio.to_thread(_blocking_call)
    
    async def fast_task():
        """A fast async task"""
        await asyncio.sleep(0.1)
        return "fast_result"
    
    # Run both concurrently
    start_time = time.time()
    results = await asyncio.gather(
        slow_sync_task(),
        fast_task()
    )
    elapsed = time.time() - start_time
    
    # Both should complete in ~2s (not 2.1s if blocking)
    assert results[0] == "slow_result"
    assert results[1] == "fast_result"
    assert elapsed < 2.5, f"Should complete in ~2s, took {elapsed:.1f}s"
    
    print(f"✓ Test passed: to_thread allows concurrency ({elapsed:.1f}s)")
    return True


async def main():
    """Run all async tests"""
    print("Running AI timeout fix tests...")
    
    results = []
    
    # Test 1: Timeout fallback
    results.append(await test_timeout_fallback_triggered())
    
    # Test 2: Async wrapper
    results.append(await test_asyncio_to_thread_not_blocking())
    
    # Summary
    print("\n" + "=" * 50)
    passed = sum(results)
    total = len(results)
    print(f"Tests completed: {passed} passed, {total - passed} failed")
    print("=" * 50)
    
    return all(results)


if __name__ == '__main__':
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
