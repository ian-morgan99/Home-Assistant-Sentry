#!/usr/bin/env python3
"""
Test that web server shares the same DependencyGraphBuilder instance
This test verifies the fix for the "Loading Components" issue
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app'))

def test_builder_instance_reuse():
    """
    Test that sentry_service.py reuses the same builder instance
    instead of creating a new one
    """
    try:
        sentry_file = os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app', 'sentry_service.py')
        with open(sentry_file, 'r') as f:
            source = f.read()
        
        # Check that we create builder BEFORE starting async task
        checks = [
            ('self.dependency_graph_builder = DependencyGraphBuilder()', 
             'Builder created/initialized'),
            ('graph_builder = self.dependency_graph_builder', 
             'Reuses existing builder instance in async method'),
        ]
        
        passed = 0
        failed = 0
        
        for check_str, description in checks:
            if check_str in source:
                print(f"✓ {description}")
                passed += 1
            else:
                print(f"✗ {description} - NOT FOUND")
                print(f"  Looking for: {check_str[:100]}...")
                failed += 1
        
        return passed, failed
        
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 0, 1

def test_no_new_builder_in_async():
    """
    Test that _build_dependency_graph_async does NOT create a new builder
    """
    try:
        sentry_file = os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app', 'sentry_service.py')
        with open(sentry_file, 'r') as f:
            lines = f.readlines()
        
        # Find the _build_dependency_graph_async method
        in_method = False
        method_lines = []
        for i, line in enumerate(lines):
            if 'async def _build_dependency_graph_async(self):' in line:
                in_method = True
            elif in_method:
                # Stop when we hit the next method definition
                if line.strip().startswith('async def ') or line.strip().startswith('def '):
                    break
                method_lines.append(line)
        
        method_source = ''.join(method_lines)
        
        # Check that the method reuses existing builder
        # We should see: graph_builder = self.dependency_graph_builder
        # We should NOT see: graph_builder = DependencyGraphBuilder()
        
        has_reuse = 'graph_builder = self.dependency_graph_builder' in method_source
        has_new_creation = 'graph_builder = DependencyGraphBuilder()' in method_source
        
        if has_reuse and not has_new_creation:
            print("✓ Method reuses existing builder instance (does not create new)")
            return 1, 0
        elif has_new_creation:
            print("✗ Method creates NEW builder instance - this will break component loading!")
            print("  The web server will hold a reference to an empty builder")
            return 0, 1
        else:
            print("✗ Could not determine builder usage pattern")
            print(f"  has_reuse: {has_reuse}, has_new_creation: {has_new_creation}")
            return 0, 1
            
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 0, 1

def test_builder_shared_with_webserver():
    """
    Test that the same builder instance is passed to web server
    """
    try:
        sentry_file = os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app', 'sentry_service.py')
        with open(sentry_file, 'r') as f:
            source = f.read()
        
        # Web server should receive the builder instance
        check = 'DependencyTreeWebServer(\n                    self.dependency_graph_builder,'
        # Also check without strict formatting
        check_alt = 'DependencyTreeWebServer(self.dependency_graph_builder'
        
        if check in source or check_alt in source:
            print("✓ Web server receives builder instance")
            return 1, 0
        else:
            print("✗ Web server does not receive builder instance - NOT FOUND")
            return 0, 1
        
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        return 0, 1

if __name__ == "__main__":
    print("Testing DependencyGraphBuilder instance sharing fix...\n")
    print("This verifies the fix for 'Loading Components' issue")
    print("=" * 70)
    
    total_passed = 0
    total_failed = 0
    
    print("\nTest 1: Builder instance reuse pattern")
    print("-" * 70)
    passed, failed = test_builder_instance_reuse()
    total_passed += passed
    total_failed += failed
    
    print("\nTest 2: No new builder creation in async method")
    print("-" * 70)
    passed, failed = test_no_new_builder_in_async()
    total_passed += passed
    total_failed += failed
    
    print("\nTest 3: Builder shared with web server")
    print("-" * 70)
    passed, failed = test_builder_shared_with_webserver()
    total_passed += passed
    total_failed += failed
    
    print("\n" + "=" * 70)
    print(f"Tests completed: {total_passed} passed, {total_failed} failed")
    print("=" * 70)
    
    if total_failed == 0:
        print("\n✅ All tests passed! The fix should resolve the 'Loading Components' issue.")
        print("   The web server now references the same builder instance that gets populated.")
    else:
        print("\n❌ Some tests failed. The fix may not work correctly.")
    
    sys.exit(0 if total_failed == 0 else 1)
