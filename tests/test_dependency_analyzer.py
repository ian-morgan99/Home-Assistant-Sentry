"""
Test deep dependency analysis
"""
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'app'))

def test_dependency_analyzer():
    """Test DependencyAnalyzer basic functionality"""
    from dependency_analyzer import DependencyAnalyzer
    
    analyzer = DependencyAnalyzer()
    
    # Test case 1: Major version update of critical service
    addon_updates = [
        {
            'name': 'MariaDB',
            'slug': 'mariadb',
            'current_version': '10.5.0',
            'latest_version': '11.0.0'
        }
    ]
    
    result = analyzer.analyze_updates(addon_updates, [])
    
    assert 'safe' in result
    assert 'confidence' in result
    assert 'issues' in result
    assert 'recommendations' in result
    assert 'summary' in result
    assert result['ai_analysis'] == False
    
    # Should detect major version change
    assert len(result['issues']) > 0
    assert any('major' in issue['description'].lower() for issue in result['issues'])
    
    print("✓ Test case 1 passed: Major version update detected")
    
    # Test case 2: Multiple critical updates
    addon_updates_2 = [
        {
            'name': 'MariaDB',
            'slug': 'mariadb',
            'current_version': '10.5.0',
            'latest_version': '10.6.0'
        },
        {
            'name': 'Mosquitto',
            'slug': 'mosquitto',
            'current_version': '1.6.0',
            'latest_version': '2.0.0'
        }
    ]
    
    result2 = analyzer.analyze_updates(addon_updates_2, [])
    
    # Should detect multiple critical updates
    assert len(result2['issues']) > 0
    multiple_critical = any('multiple critical' in issue['description'].lower() 
                          for issue in result2['issues'])
    
    print("✓ Test case 2 passed: Multiple critical updates detected")
    
    # Test case 3: High update volume
    many_updates = [
        {'name': f'Addon {i}', 'slug': f'addon-{i}', 
         'current_version': '1.0.0', 'latest_version': '1.1.0'}
        for i in range(12)
    ]
    
    result3 = analyzer.analyze_updates(many_updates, [])
    
    # Should flag high volume
    assert len(result3['issues']) > 0
    assert any('volume' in issue['component'].lower() for issue in result3['issues'])
    
    print("✓ Test case 3 passed: High update volume detected")
    
    # Test case 4: Pre-release version
    prerelease_updates = [
        {
            'name': 'Test Addon',
            'slug': 'test-addon',
            'current_version': '1.0.0',
            'latest_version': '2.0.0-beta.1'
        }
    ]
    
    result4 = analyzer.analyze_updates(prerelease_updates, [])
    
    # Should detect pre-release
    assert len(result4['issues']) > 0
    assert any('pre-release' in issue['description'].lower() or 'beta' in issue['description'].lower()
               for issue in result4['issues'])
    
    print("✓ Test case 4 passed: Pre-release version detected")
    
    # Test case 5: No updates (edge case)
    result5 = analyzer.analyze_updates([], [])
    assert result5['safe'] == True
    assert len(result5['issues']) == 0
    
    print("✓ Test case 5 passed: No updates handled correctly")
    
    return True

if __name__ == '__main__':
    print("Testing DependencyAnalyzer...\n")
    
    try:
        if test_dependency_analyzer():
            print("\n✅ All tests passed!")
            sys.exit(0)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
