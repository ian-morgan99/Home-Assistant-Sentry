"""
Test cases for AIClient, specifically for edge cases and new functionality
"""
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app'))

from config_manager import ConfigManager
from ai_client import AIClient


def test_prepare_analysis_context_without_slug():
    """Test that _prepare_analysis_context handles updates without 'slug' field"""
    # Setup
    os.environ['AI_ENABLED'] = 'false'
    config = ConfigManager()
    ai = AIClient(config)
    
    # Test case 1: Update with entity_id but no slug
    addon_updates = [
        {
            'name': 'Mosquitto Broker',
            'entity_id': 'update.mosquitto',
            'current_version': '6.4.0',
            'latest_version': '6.4.1',
            'type': 'addon'
        }
    ]
    
    try:
        context = ai._prepare_analysis_context(addon_updates, [])
        assert 'Mosquitto Broker' in context
        assert 'update.mosquitto' in context
        assert '6.4.0' in context
        assert '6.4.1' in context
        print("✓ Test passed: _prepare_analysis_context handles entity_id without slug")
        return True
    except KeyError as e:
        print(f"✗ Test failed: KeyError raised for {e}")
        return False
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_prepare_analysis_context_without_slug_or_entity_id():
    """Test that _prepare_analysis_context handles updates with neither slug nor entity_id"""
    # Setup
    os.environ['AI_ENABLED'] = 'false'
    config = ConfigManager()
    ai = AIClient(config)
    
    # Test case: Update with neither slug nor entity_id
    addon_updates = [
        {
            'name': 'Test Addon',
            'current_version': '1.0.0',
            'latest_version': '1.0.1',
            'type': 'addon'
        }
    ]
    
    try:
        context = ai._prepare_analysis_context(addon_updates, [])
        assert 'Test Addon' in context
        assert '1.0.0' in context
        assert '1.0.1' in context
        # Should not crash, and should not include empty parentheses
        assert '()' not in context
        print("✓ Test passed: _prepare_analysis_context handles updates without slug or entity_id")
        return True
    except KeyError as e:
        print(f"✗ Test failed: KeyError raised for {e}")
        return False
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_prepare_analysis_context_with_slug():
    """Test that _prepare_analysis_context still works with slug field"""
    # Setup
    os.environ['AI_ENABLED'] = 'false'
    config = ConfigManager()
    ai = AIClient(config)
    
    # Test case: Update with slug (traditional format)
    addon_updates = [
        {
            'name': 'Test Addon',
            'slug': 'test_addon',
            'current_version': '1.0.0',
            'latest_version': '1.0.1',
            'type': 'addon'
        }
    ]
    
    try:
        context = ai._prepare_analysis_context(addon_updates, [])
        assert 'Test Addon' in context
        assert 'test_addon' in context
        assert '1.0.0' in context
        assert '1.0.1' in context
        print("✓ Test passed: _prepare_analysis_context handles slug field correctly")
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_get_dependency_info_without_graph():
    """Test _get_dependency_info_for_update when dependency_graph is None"""
    # Setup
    os.environ['AI_ENABLED'] = 'false'
    config = ConfigManager()
    ai = AIClient(config, dependency_graph=None)
    
    # Test with any update
    update = {
        'name': 'Test Addon',
        'slug': 'test_addon',
        'type': 'addon'
    }
    
    try:
        result = ai._get_dependency_info_for_update(update)
        assert result == {}
        print("✓ Test passed: _get_dependency_info_for_update returns empty dict without graph")
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_get_dependency_info_system_update():
    """Test _get_dependency_info_for_update for system updates (core, supervisor, os)"""
    # Setup mock dependency graph
    mock_graph = {
        'integrations': {
            'integration1': {'name': 'Integration 1'},
            'integration2': {'name': 'Integration 2'},
            'integration3': {'name': 'Integration 3'}
        },
        'dependency_map': {
            'aiohttp': [
                {'integration': 'integration1'},
                {'integration': 'integration2'}
            ],
            'cryptography': [
                {'integration': 'integration1'},
                {'integration': 'integration2'},
                {'integration': 'integration3'}
            ],
            'requests': [
                {'integration': 'integration1'}
            ]
        }
    }
    
    os.environ['AI_ENABLED'] = 'false'
    config = ConfigManager()
    ai = AIClient(config, dependency_graph=mock_graph)
    
    # Test system update types
    for update_type in ['core', 'supervisor', 'os']:
        update = {
            'name': 'Home Assistant Core',
            'type': update_type,
            'current_version': '2024.12.0',
            'latest_version': '2024.12.1'
        }
        
        try:
            result = ai._get_dependency_info_for_update(update)
            
            assert result.get('type') == 'system'
            assert 'high_risk_dependencies' in result
            assert 'impact_radius' in result
            assert result['impact_radius'] == 3  # Number of integrations
            
            # Check high-risk dependencies
            high_risk_deps = result['high_risk_dependencies']
            assert len(high_risk_deps) > 0
            
            # Verify structure of high-risk dependencies
            for dep in high_risk_deps:
                assert 'package' in dep
                assert 'user_count' in dep
                assert 'high_risk' in dep
                assert dep['high_risk'] is True
                # All high-risk dependencies returned should be from HIGH_RISK_LIBRARIES
                # since that's the only source for system update high-risk deps
                assert dep['package'] in AIClient.HIGH_RISK_LIBRARIES
            
            print(f"✓ Test passed: _get_dependency_info_for_update handles {update_type} update correctly")
        except Exception as e:
            print(f"✗ Test failed for {update_type}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    return True


def test_get_dependency_info_integration_update():
    """Test _get_dependency_info_for_update for integration updates"""
    # Setup mock dependency graph
    mock_graph = {
        'integrations': {
            'mqtt': {
                'name': 'MQTT',
                'requirements': [
                    {'package': 'paho-mqtt', 'specifier': '>=1.5.0', 'high_risk': False},
                    {'package': 'aiohttp', 'specifier': '>=3.8.0', 'high_risk': True},
                    {'package': 'cryptography', 'specifier': '>=3.4.0', 'high_risk': True}
                ]
            },
            'integration2': {
                'name': 'Integration 2'
            }
        },
        'dependency_map': {
            'paho-mqtt': [
                {'integration': 'mqtt'}
            ],
            'aiohttp': [
                {'integration': 'mqtt'},
                {'integration': 'integration2'}
            ],
            'cryptography': [
                {'integration': 'mqtt'},
                {'integration': 'integration2'}
            ]
        }
    }
    
    os.environ['AI_ENABLED'] = 'false'
    config = ConfigManager()
    ai = AIClient(config, dependency_graph=mock_graph)
    
    # Test with matching slug
    update = {
        'name': 'MQTT Broker',
        'slug': 'mqtt',
        'type': 'addon'
    }
    
    try:
        result = ai._get_dependency_info_for_update(update)
        
        assert result.get('type') == 'integration'
        assert 'requirements' in result
        assert 'high_risk_count' in result
        assert 'shared_dependency_impact' in result
        
        # Should have found the requirements
        assert len(result['requirements']) > 0
        assert result['high_risk_count'] == 2  # aiohttp and cryptography
        
        # Shared dependency impact should be > 1 (includes itself and integration2)
        assert result['shared_dependency_impact'] >= 2
        
        print("✓ Test passed: _get_dependency_info_for_update handles integration update with matching slug")
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test with matching name
    update2 = {
        'name': 'MQTT',
        'type': 'addon'
    }
    
    try:
        result = ai._get_dependency_info_for_update(update2)
        
        assert result.get('type') == 'integration'
        assert len(result['requirements']) > 0
        
        print("✓ Test passed: _get_dependency_info_for_update handles integration update with matching name")
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def test_get_dependency_info_no_match():
    """Test _get_dependency_info_for_update when no integration matches"""
    # Setup mock dependency graph
    mock_graph = {
        'integrations': {
            'mqtt': {'name': 'MQTT'}
        },
        'dependency_map': {}
    }
    
    os.environ['AI_ENABLED'] = 'false'
    config = ConfigManager()
    ai = AIClient(config, dependency_graph=mock_graph)
    
    # Test with non-matching update
    update = {
        'name': 'Unknown Addon',
        'slug': 'unknown',
        'type': 'addon'
    }
    
    try:
        result = ai._get_dependency_info_for_update(update)
        assert result == {}
        print("✓ Test passed: _get_dependency_info_for_update returns empty dict for non-matching update")
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_matching_logic_no_false_positives():
    """Test that matching logic doesn't produce false positives"""
    # Setup mock dependency graph with 'test' domain
    mock_graph = {
        'integrations': {
            'test': {
                'name': 'Test Integration',
                'requirements': [
                    {'package': 'test-lib', 'specifier': '>=1.0.0', 'high_risk': False}
                ]
            }
        },
        'dependency_map': {
            'test-lib': [
                {'integration': 'test'}
            ]
        }
    }
    
    os.environ['AI_ENABLED'] = 'false'
    config = ConfigManager()
    ai = AIClient(config, dependency_graph=mock_graph)
    
    # Test case: update named "my_test_addon" should NOT match "test" domain
    # This is checking for the false positive mentioned in the review
    update = {
        'name': 'my_test_addon',
        'type': 'addon'
    }
    
    try:
        result = ai._get_dependency_info_for_update(update)
        # Since we now use exact matching, this should not match
        assert result == {} or result.get('type') != 'integration'
        print("✓ Test passed: Matching logic avoids false positives")
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_release_summary_truncation_with_ellipsis():
    """Test that release summaries are truncated with ellipsis when too long"""
    os.environ['AI_ENABLED'] = 'false'
    config = ConfigManager()
    ai = AIClient(config)
    
    # Create a long release summary
    long_summary = "A" * (AIClient.MAX_RELEASE_SUMMARY_LENGTH + 50)
    
    addon_updates = [
        {
            'name': 'Test Addon',
            'slug': 'test',
            'current_version': '1.0.0',
            'latest_version': '1.0.1',
            'type': 'addon',
            'release_summary': long_summary
        }
    ]
    
    try:
        context = ai._prepare_analysis_context(addon_updates, [])
        
        # Check that the summary is truncated
        assert long_summary not in context
        
        # Check that ellipsis is added
        assert '...' in context
        
        # The truncated version should be in the context
        expected_truncated = long_summary[:AIClient.MAX_RELEASE_SUMMARY_LENGTH] + "..."
        assert expected_truncated in context
        
        print("✓ Test passed: Release summary truncation includes ellipsis")
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_release_summary_no_truncation_when_short():
    """Test that short release summaries are not truncated"""
    os.environ['AI_ENABLED'] = 'false'
    config = ConfigManager()
    ai = AIClient(config)
    
    # Create a short release summary
    short_summary = "This is a short summary"
    
    addon_updates = [
        {
            'name': 'Test Addon',
            'slug': 'test',
            'current_version': '1.0.0',
            'latest_version': '1.0.1',
            'type': 'addon',
            'release_summary': short_summary
        }
    ]
    
    try:
        context = ai._prepare_analysis_context(addon_updates, [])
        
        # Short summary should be in context as-is
        assert short_summary in context
        
        # Should not have ellipsis after this specific summary
        # (checking the summary line specifically)
        summary_line = f"  - Summary: {short_summary}\n"
        assert summary_line in context
        
        print("✓ Test passed: Short release summary is not truncated")
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("Running AI Client edge case tests...\n")
    
    tests = [
        test_prepare_analysis_context_without_slug,
        test_prepare_analysis_context_without_slug_or_entity_id,
        test_prepare_analysis_context_with_slug,
        test_get_dependency_info_without_graph,
        test_get_dependency_info_system_update,
        test_get_dependency_info_integration_update,
        test_get_dependency_info_no_match,
        test_matching_logic_no_false_positives,
        test_release_summary_truncation_with_ellipsis,
        test_release_summary_no_truncation_when_short
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
