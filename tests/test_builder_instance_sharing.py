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
            ('if not self.dependency_graph_builder:\n                self.dependency_graph_builder = DependencyGraphBuilder()', 
             'Builder created before async task'),
            ('graph_builder = self.dependency_graph_builder', 
             'Reuses existing builder instance in async method'),
            ('# No need to reassign self.dependency_graph_builder', 
             'Comment confirming no reassignment needed'),
        ]
        
        passed = 0
        failed = 0
        
        for check_str, description in checks:
            # Normalize whitespace for comparison
            normalized_check = ' '.join(check_str.split())
            normalized_source = ' '.join(source.split())
            
            if normalized_check in normalized_source:
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
            source = f.read()
        
        # Extract the _build_dependency_graph_async method
        start_marker = 'async def _build_dependency_graph_async(self):'
        end_marker = 'async def rebuild_dependency_graph(self):'
        
        start_idx = source.find(start_marker)
        end_idx = source.find(end_marker, start_idx)
        
        if start_idx == -1 or end_idx == -1:
            print("✗ Could not find method boundaries")
            return 0, 1
        
        method_source = source[start_idx:end_idx]
        
        # Check that the method does NOT create a new builder
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
        
        # In the start() method, we should:
        # 1. Create builder first
        # 2. Pass it to async task (implicitly via self.dependency_graph_builder)
        # 3. Pass it to web server
        
        checks = [
            ('self.web_server = DependencyTreeWebServer(\n                    self.dependency_graph_builder,', 
             'Web server receives builder instance'),
        ]
        
        passed = 0
        failed = 0
        
        for check_str, description in checks:
            # Normalize whitespace for comparison
            normalized_check = ' '.join(check_str.split())
            normalized_source = ' '.join(source.split())
            
            if normalized_check in normalized_source:
                print(f"✓ {description}")
                passed += 1
            else:
                print(f"✗ {description} - NOT FOUND")
                failed += 1
        
        return passed, failed
        
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
