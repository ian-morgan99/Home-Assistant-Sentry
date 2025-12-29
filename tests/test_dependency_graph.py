"""
Tests for Dependency Graph Builder and Shared Dependency Detection
"""
import sys
import os
import json
import tempfile
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app'))


def test_dependency_graph_builder_init():
    """Test DependencyGraphBuilder initialization"""
    try:
        from dependency_graph_builder import DependencyGraphBuilder
        
        builder = DependencyGraphBuilder()
        assert builder.integrations == {}
        assert builder.dependency_map == {}
        assert builder.graph == {}
        
        print("✓ DependencyGraphBuilder initialization test passed")
        return True
    except Exception as e:
        print(f"✗ DependencyGraphBuilder initialization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_manifest_parsing():
    """Test manifest.json parsing with various formats"""
    try:
        from dependency_graph_builder import DependencyGraphBuilder
        
        builder = DependencyGraphBuilder()
        
        # Create temporary test manifests
        with tempfile.TemporaryDirectory() as tmpdir:
            # Test 1: Valid manifest with requirements
            integration1_dir = Path(tmpdir) / 'test_integration_1'
            integration1_dir.mkdir()
            
            manifest1 = {
                'domain': 'test_integration_1',
                'name': 'Test Integration 1',
                'version': '1.0.0',
                'homeassistant': '2024.1.0',
                'requirements': ['aiohttp>=3.9.0', 'requests>=2.28.0']
            }
            
            with open(integration1_dir / 'manifest.json', 'w') as f:
                json.dump(manifest1, f)
            
            # Test 2: Valid manifest without requirements
            integration2_dir = Path(tmpdir) / 'test_integration_2'
            integration2_dir.mkdir()
            
            manifest2 = {
                'domain': 'test_integration_2',
                'name': 'Test Integration 2',
                'version': '2.0.0',
                'requirements': []
            }
            
            with open(integration2_dir / 'manifest.json', 'w') as f:
                json.dump(manifest2, f)
            
            # Test 3: Malformed JSON
            integration3_dir = Path(tmpdir) / 'test_integration_3'
            integration3_dir.mkdir()
            
            with open(integration3_dir / 'manifest.json', 'w') as f:
                f.write('{invalid json}')
            
            # Scan the test directory
            builder._scan_integration_path(tmpdir)
            
            # Verify parsing
            assert 'test_integration_1' in builder.integrations
            assert 'test_integration_2' in builder.integrations
            assert 'test_integration_3' in builder.integrations
            
            # Check integration 1
            int1 = builder.integrations['test_integration_1']
            assert int1['name'] == 'Test Integration 1'
            assert len(int1['requirements']) == 2
            assert int1['requirements'][0]['package'] == 'aiohttp'
            assert int1['requirements'][0]['high_risk'] is True  # aiohttp is high-risk
            
            # Check integration 2
            int2 = builder.integrations['test_integration_2']
            assert len(int2['requirements']) == 0
            
            # Check integration 3 (malformed)
            int3 = builder.integrations['test_integration_3']
            assert 'error' in int3
            
        print("✓ Manifest parsing test passed")
        return True
    except Exception as e:
        print(f"✗ Manifest parsing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_shared_dependency_detection():
    """Test detection of shared dependencies"""
    try:
        from dependency_graph_builder import DependencyGraphBuilder
        
        builder = DependencyGraphBuilder()
        
        # Create test data directly
        builder.integrations = {
            'integration_a': {
                'name': 'Integration A',
                'domain': 'integration_a',
                'requirements': [
                    {'package': 'aiohttp', 'specifier': '>=3.9', 'high_risk': True},
                    {'package': 'numpy', 'specifier': '>=1.23', 'high_risk': True}
                ]
            },
            'integration_b': {
                'name': 'Integration B',
                'domain': 'integration_b',
                'requirements': [
                    {'package': 'aiohttp', 'specifier': '<3.9', 'high_risk': True},
                    {'package': 'requests', 'specifier': '>=2.28', 'high_risk': False}
                ]
            },
            'integration_c': {
                'name': 'Integration C',
                'domain': 'integration_c',
                'requirements': [
                    {'package': 'aiohttp', 'specifier': '>=3.8', 'high_risk': True}
                ]
            }
        }
        
        # Build dependency map
        builder._build_dependency_map()
        
        # Check shared dependencies
        shared = builder.get_shared_dependencies()
        
        assert len(shared) > 0
        
        # aiohttp should be shared by 3 integrations
        aiohttp_shared = [s for s in shared if s['package'] == 'aiohttp'][0]
        assert aiohttp_shared['user_count'] == 3
        assert aiohttp_shared['high_risk'] is True
        assert aiohttp_shared['has_version_conflict'] is True
        
        print("✓ Shared dependency detection test passed")
        return True
    except Exception as e:
        print(f"✗ Shared dependency detection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_version_conflict_detection():
    """Test detection of version conflicts"""
    try:
        from dependency_graph_builder import DependencyGraphBuilder
        
        builder = DependencyGraphBuilder()
        
        # Create test data with version conflicts
        builder.integrations = {
            'integration_a': {
                'name': 'Integration A',
                'domain': 'integration_a',
                'requirements': [
                    {'package': 'cryptography', 'specifier': '>=40.0', 'high_risk': True}
                ]
            },
            'integration_b': {
                'name': 'Integration B',
                'domain': 'integration_b',
                'requirements': [
                    {'package': 'cryptography', 'specifier': '<40.0', 'high_risk': True}
                ]
            }
        }
        
        # Build dependency map
        builder._build_dependency_map()
        
        # Detect conflicts
        conflicts = builder.detect_version_conflicts()
        
        assert len(conflicts) > 0
        
        # Check cryptography conflict
        crypto_conflict = [c for c in conflicts if c['package'] == 'cryptography'][0]
        assert crypto_conflict['high_risk'] is True
        assert crypto_conflict['conflict_type'] == 'version_constraint_mismatch'
        assert len(crypto_conflict['affected_integrations']) == 2
        
        print("✓ Version conflict detection test passed")
        return True
    except Exception as e:
        print(f"✗ Version conflict detection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_dependency_analyzer_with_graph():
    """Test DependencyAnalyzer with dependency graph"""
    try:
        from dependency_analyzer import DependencyAnalyzer
        
        # Create a mock dependency graph
        dependency_graph = {
            'dependency_map': {
                'aiohttp': [
                    {'integration': 'Integration A', 'specifier': '>=3.9', 'high_risk': True},
                    {'integration': 'Integration B', 'specifier': '>=3.9', 'high_risk': True},
                    {'integration': 'Integration C', 'specifier': '>=3.9', 'high_risk': True},
                    {'integration': 'Integration D', 'specifier': '>=3.9', 'high_risk': True},
                    {'integration': 'Integration E', 'specifier': '>=3.9', 'high_risk': True},
                ],
                'requests': [
                    {'integration': 'Integration A', 'specifier': '>=2.28', 'high_risk': False},
                    {'integration': 'Integration B', 'specifier': '<2.28', 'high_risk': False},
                ]
            }
        }
        
        analyzer = DependencyAnalyzer(dependency_graph=dependency_graph)
        
        # Run analysis
        result = analyzer.analyze_updates([], [])
        
        assert 'safe' in result
        assert 'confidence' in result
        assert 'issues' in result
        assert 'recommendations' in result
        
        # Check for shared dependency issues
        shared_issues = [i for i in result['issues'] if 'shared_dependency' in i['component']]
        assert len(shared_issues) > 0
        
        # Should detect aiohttp as high-risk with 5 users
        aiohttp_issue = [i for i in shared_issues if 'aiohttp' in i['component']]
        assert len(aiohttp_issue) > 0
        assert aiohttp_issue[0]['severity'] in ['high', 'medium']
        
        print("✓ DependencyAnalyzer with graph test passed")
        return True
    except Exception as e:
        print(f"✗ DependencyAnalyzer with graph test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_graph_output_formats():
    """Test that graph generates both machine and human-readable output"""
    try:
        from dependency_graph_builder import DependencyGraphBuilder
        
        builder = DependencyGraphBuilder()
        
        # Create minimal test data
        builder.integrations = {
            'test_int': {
                'name': 'Test Integration',
                'domain': 'test_int',
                'requirements': [
                    {'package': 'aiohttp', 'specifier': '>=3.9', 'high_risk': True}
                ]
            }
        }
        
        builder._build_dependency_map()
        graph_data = builder._generate_graph_structure()
        
        # Check structure
        assert 'machine_readable' in graph_data
        assert 'human_readable' in graph_data
        assert 'integrations' in graph_data
        assert 'dependency_map' in graph_data
        
        # Check machine-readable format
        mr = graph_data['machine_readable']
        assert 'integrations' in mr
        assert 'dependency_map' in mr
        assert 'statistics' in mr
        
        # Check human-readable format
        hr = graph_data['human_readable']
        assert isinstance(hr, str)
        assert 'DEPENDENCY GRAPH SUMMARY' in hr
        assert 'Total Integrations' in hr
        
        print("✓ Graph output formats test passed")
        return True
    except Exception as e:
        print(f"✗ Graph output formats test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("Running Dependency Graph and Shared Dependency Detection tests...\n")
    
    tests = [
        test_dependency_graph_builder_init,
        test_manifest_parsing,
        test_shared_dependency_detection,
        test_version_conflict_detection,
        test_dependency_analyzer_with_graph,
        test_graph_output_formats
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
