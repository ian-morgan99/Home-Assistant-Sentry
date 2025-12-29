"""
Tests for custom integration path configuration
"""
import sys
import os
import json
import tempfile
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app'))


def test_custom_paths_configuration():
    """Test that custom paths can be configured and used"""
    try:
        from dependency_graph_builder import DependencyGraphBuilder
        
        builder = DependencyGraphBuilder()
        
        # Create temporary test structure
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create custom integration path
            custom_path = Path(tmpdir) / 'my_custom_integrations'
            custom_path.mkdir()
            
            # Create a test integration
            integration_dir = custom_path / 'test_custom_integration'
            integration_dir.mkdir()
            
            manifest = {
                'domain': 'test_custom_integration',
                'name': 'Test Custom Integration',
                'version': '1.0.0',
                'requirements': ['requests>=2.28.0']
            }
            
            with open(integration_dir / 'manifest.json', 'w') as f:
                json.dump(manifest, f)
            
            # Build graph with custom path
            graph_data = builder.build_graph_from_paths([str(custom_path)])
            
            # Verify integration was found
            assert 'test_custom_integration' in builder.integrations
            assert builder.integrations['test_custom_integration']['name'] == 'Test Custom Integration'
            
            # Verify statistics
            stats = graph_data['machine_readable']['statistics']
            assert stats['total_integrations'] == 1
            
        print("✓ Custom paths configuration test passed")
        return True
    except Exception as e:
        print(f"✗ Custom paths configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_missing_paths_handling():
    """Test that missing paths are handled gracefully"""
    try:
        from dependency_graph_builder import DependencyGraphBuilder
        
        builder = DependencyGraphBuilder()
        
        # Use non-existent paths
        non_existent_paths = [
            '/nonexistent/path1',
            '/nonexistent/path2'
        ]
        
        # Should not raise an exception
        graph_data = builder.build_graph_from_paths(non_existent_paths)
        
        # Graph should be empty but valid
        assert isinstance(graph_data, dict)
        assert 'machine_readable' in graph_data
        assert 'integrations' in graph_data
        
        # No integrations should be found
        stats = graph_data['machine_readable']['statistics']
        assert stats['total_integrations'] == 0
        
        print("✓ Missing paths handling test passed")
        return True
    except Exception as e:
        print(f"✗ Missing paths handling test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_mixed_valid_and_invalid_paths():
    """Test handling of both valid and invalid paths together"""
    try:
        from dependency_graph_builder import DependencyGraphBuilder
        
        builder = DependencyGraphBuilder()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a valid path with an integration
            valid_path = Path(tmpdir) / 'valid_integrations'
            valid_path.mkdir()
            
            integration_dir = valid_path / 'test_integration'
            integration_dir.mkdir()
            
            manifest = {
                'domain': 'test_integration',
                'name': 'Test Integration',
                'version': '1.0.0',
                'requirements': ['aiohttp>=3.9.0']
            }
            
            with open(integration_dir / 'manifest.json', 'w') as f:
                json.dump(manifest, f)
            
            # Mix valid and invalid paths
            mixed_paths = [
                '/nonexistent/path1',
                str(valid_path),
                '/nonexistent/path2'
            ]
            
            # Should process the valid path without failing
            graph_data = builder.build_graph_from_paths(mixed_paths)
            
            # Should find the one integration
            assert 'test_integration' in builder.integrations
            stats = graph_data['machine_readable']['statistics']
            assert stats['total_integrations'] == 1
            
        print("✓ Mixed valid and invalid paths test passed")
        return True
    except Exception as e:
        print(f"✗ Mixed valid and invalid paths test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_manager_custom_paths():
    """Test that ConfigManager can parse custom integration paths"""
    try:
        from config_manager import ConfigManager
        
        # Test with valid JSON array
        os.environ['CUSTOM_INTEGRATION_PATHS'] = json.dumps(['/path1', '/path2'])
        config = ConfigManager()
        
        assert hasattr(config, 'custom_integration_paths')
        assert isinstance(config.custom_integration_paths, list)
        assert '/path1' in config.custom_integration_paths
        assert '/path2' in config.custom_integration_paths
        
        # Test with empty array
        os.environ['CUSTOM_INTEGRATION_PATHS'] = '[]'
        config2 = ConfigManager()
        assert config2.custom_integration_paths == []
        
        # Test with invalid JSON (should not crash)
        os.environ['CUSTOM_INTEGRATION_PATHS'] = 'invalid json'
        config3 = ConfigManager()
        assert config3.custom_integration_paths == []
        
        # Clean up
        if 'CUSTOM_INTEGRATION_PATHS' in os.environ:
            del os.environ['CUSTOM_INTEGRATION_PATHS']
        
        print("✓ ConfigManager custom paths test passed")
        return True
    except Exception as e:
        print(f"✗ ConfigManager custom paths test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_suggest_alternative_paths():
    """Test the alternative path suggestion functionality"""
    try:
        from dependency_graph_builder import DependencyGraphBuilder
        
        builder = DependencyGraphBuilder()
        
        # This test just ensures the method doesn't crash
        # In a real scenario, it would check actual filesystem locations
        builder._suggest_alternative_paths(['/nonexistent/path'])
        
        print("✓ Suggest alternative paths test passed")
        return True
    except Exception as e:
        print(f"✗ Suggest alternative paths test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_count_manifests():
    """Test the manifest counting helper method"""
    try:
        from dependency_graph_builder import DependencyGraphBuilder
        
        builder = DependencyGraphBuilder()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a structure with multiple integrations
            test_path = Path(tmpdir) / 'integrations'
            test_path.mkdir()
            
            # Create 3 integrations
            for i in range(3):
                int_dir = test_path / f'integration_{i}'
                int_dir.mkdir()
                
                manifest = {
                    'domain': f'integration_{i}',
                    'name': f'Integration {i}'
                }
                
                with open(int_dir / 'manifest.json', 'w') as f:
                    json.dump(manifest, f)
            
            # Count manifests
            count = builder._count_manifests(str(test_path))
            assert count == 3
            
            # Test with non-existent path
            count_empty = builder._count_manifests('/nonexistent/path')
            assert count_empty == 0
            
        print("✓ Count manifests test passed")
        return True
    except Exception as e:
        print(f"✗ Count manifests test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("Running custom integration paths tests...\n")
    
    tests = [
        test_custom_paths_configuration,
        test_missing_paths_handling,
        test_mixed_valid_and_invalid_paths,
        test_config_manager_custom_paths,
        test_suggest_alternative_paths,
        test_count_manifests
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
