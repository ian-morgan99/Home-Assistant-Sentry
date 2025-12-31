#!/usr/bin/env python3
"""
Test async dependency graph building
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app'))

def test_sentry_service_has_async_methods():
    """Test that SentryService has async graph building methods"""
    try:
        # Read the source file
        sentry_file = os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app', 'sentry_service.py')
        with open(sentry_file, 'r') as f:
            source = f.read()
        
        # Check for async methods
        checks = [
            ('async def _build_dependency_graph_async', '_build_dependency_graph_async method exists'),
            ('async def rebuild_dependency_graph', 'rebuild_dependency_graph method exists'),
            ('async def stop', 'stop method exists for cleanup'),
            ('asyncio.create_task(self._build_dependency_graph_async())', 'Background task creation'),
            ('self._graph_build_task', 'Graph build task tracking'),
            ('self._graph_build_task.cancel()', 'Task cancellation in stop method'),
        ]
        
        passed = 0
        failed = 0
        
        for check_str, description in checks:
            if check_str in source:
                print(f"✓ {description}")
                passed += 1
            else:
                print(f"✗ {description} - NOT FOUND")
                failed += 1
        
        return passed, failed
        
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        return 0, 1

def test_web_server_has_retry_logic():
    """Test that web_server.py has component loading retry logic"""
    try:
        web_server_file = os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app', 'web_server.py')
        with open(web_server_file, 'r') as f:
            source = f.read()
        
        checks = [
            ('componentLoadAttempts', 'Component load attempts tracking'),
            ('MAX_COMPONENT_LOAD_RETRIES', 'Max retry limit constant'),
            ('setTimeout(loadComponents, 2000)', 'Retry with delay'),
            ('Loading components (building dependency graph)...', 'Loading message'),
        ]
        
        passed = 0
        failed = 0
        
        for check_str, description in checks:
            if check_str in source:
                print(f"✓ {description}")
                passed += 1
            else:
                print(f"✗ {description} - NOT FOUND")
                failed += 1
        
        return passed, failed
        
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        return 0, 1

def test_workflow_exists():
    """Test that sync-version-on-merge workflow exists"""
    try:
        workflow_file = os.path.join(os.path.dirname(__file__), '..', '.github', 'workflows', 'sync-version-on-merge.yml')
        
        if os.path.exists(workflow_file):
            with open(workflow_file, 'r') as f:
                content = f.read()
            
            checks = [
                ('on:', 'Has workflow trigger'),
                ('push:', 'Triggers on push'),
                ('branches:', 'Branch filter'),
                ('- main', 'Main branch trigger'),
                ('sync-version', 'Sync version job'),
            ]
            
            passed = 0
            failed = 0
            
            for check_str, description in checks:
                if check_str in content:
                    print(f"✓ {description}")
                    passed += 1
                else:
                    print(f"✗ {description} - NOT FOUND")
                    failed += 1
            
            return passed, failed
        else:
            print(f"✗ Workflow file not found: {workflow_file}")
            return 0, 1
            
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        return 0, 1

if __name__ == "__main__":
    print("Running async dependency graph building tests...\n")
    
    total_passed = 0
    total_failed = 0
    
    print("=" * 60)
    print("Test 1: SentryService async methods")
    print("=" * 60)
    passed, failed = test_sentry_service_has_async_methods()
    total_passed += passed
    total_failed += failed
    
    print("\n" + "=" * 60)
    print("Test 2: WebServer retry logic")
    print("=" * 60)
    passed, failed = test_web_server_has_retry_logic()
    total_passed += passed
    total_failed += failed
    
    print("\n" + "=" * 60)
    print("Test 3: Version sync workflow")
    print("=" * 60)
    passed, failed = test_workflow_exists()
    total_passed += passed
    total_failed += failed
    
    print("\n" + "=" * 60)
    print(f"Tests completed: {total_passed} passed, {total_failed} failed")
    print("=" * 60)
    
    sys.exit(0 if total_failed == 0 else 1)
