#!/usr/bin/env python3
"""
Verification Script for Directory Access
This script can be run inside the add-on container to verify that
directory mappings are working correctly.
"""
import os
import sys
import json
from pathlib import Path


def check_directory_access():
    """Check if required directories are accessible"""
    results = {
        'timestamp': None,
        'checks': [],
        'summary': {
            'total': 0,
            'accessible': 0,
            'not_accessible': 0,
            'custom_components_found': False,
            'integration_count': 0
        }
    }
    
    # Directories to check
    directories_to_check = [
        {
            'path': '/config',
            'description': 'Home Assistant config directory (mapped via config:ro)',
            'critical': True
        },
        {
            'path': '/config/custom_components',
            'description': 'HACS/Custom integrations directory',
            'critical': True
        },
        {
            'path': '/share',
            'description': 'Shared storage directory (mapped via share:ro)',
            'critical': False
        },
        {
            'path': '/homeassistant_config',
            'description': 'Alternative HA config path (mapped via homeassistant_config:ro)',
            'critical': False
        },
        {
            'path': '/usr/src/homeassistant/homeassistant/components',
            'description': 'Core integrations (NOT accessible - in HA container)',
            'critical': False,
            'expected_accessible': False
        }
    ]
    
    print("=" * 70)
    print("DIRECTORY ACCESS VERIFICATION")
    print("=" * 70)
    print()
    
    for dir_info in directories_to_check:
        path = dir_info['path']
        description = dir_info['description']
        critical = dir_info.get('critical', False)
        expected_accessible = dir_info.get('expected_accessible', True)
        
        results['summary']['total'] += 1
        check_result = {
            'path': path,
            'description': description,
            'critical': critical,
            'expected_accessible': expected_accessible,
            'exists': False,
            'readable': False,
            'writable': False,
            'contents_sample': []
        }
        
        # Check if path exists
        if os.path.exists(path):
            check_result['exists'] = True
            
            # Check if readable
            try:
                os.listdir(path) if os.path.isdir(path) else open(path, 'r').close()
                check_result['readable'] = True
                results['summary']['accessible'] += 1
                
                # List contents if it's a directory
                if os.path.isdir(path):
                    try:
                        contents = os.listdir(path)
                        check_result['contents_sample'] = contents[:5]  # First 5 items
                        check_result['total_items'] = len(contents)
                        
                        # Special check for custom_components
                        if path == '/config/custom_components':
                            results['summary']['custom_components_found'] = True
                            results['summary']['integration_count'] = len([
                                item for item in contents 
                                if os.path.isdir(os.path.join(path, item)) and 
                                   os.path.exists(os.path.join(path, item, 'manifest.json'))
                            ])
                    except Exception as e:
                        check_result['list_error'] = str(e)
                
            except Exception as e:
                check_result['read_error'] = str(e)
                results['summary']['not_accessible'] += 1
            
            # Check if writable (expect False for :ro mappings)
            try:
                test_file = os.path.join(path, '.write_test') if os.path.isdir(path) else path + '.test'
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                check_result['writable'] = True
            except:
                check_result['writable'] = False
        else:
            results['summary']['not_accessible'] += 1
        
        results['checks'].append(check_result)
        
        # Print status
        status_icon = "✅" if check_result['exists'] and check_result['readable'] else "❌"
        if not expected_accessible:
            status_icon = "⚠️" if not check_result['exists'] else "❌"
        
        print(f"{status_icon} {path}")
        print(f"   {description}")
        print(f"   Exists: {check_result['exists']}, Readable: {check_result['readable']}, Writable: {check_result['writable']}")
        
        if check_result.get('total_items'):
            print(f"   Contents: {check_result['total_items']} items")
            if check_result['contents_sample']:
                print(f"   Sample: {', '.join(check_result['contents_sample'][:3])}")
        
        if critical and not (check_result['exists'] and check_result['readable']):
            print(f"   ⚠️  CRITICAL PATH NOT ACCESSIBLE!")
        
        print()
    
    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total paths checked: {results['summary']['total']}")
    print(f"Accessible: {results['summary']['accessible']}")
    print(f"Not accessible: {results['summary']['not_accessible']}")
    print()
    print(f"Custom components directory found: {results['summary']['custom_components_found']}")
    if results['summary']['custom_components_found']:
        print(f"Integration count: {results['summary']['integration_count']}")
    print()
    
    # Verdict
    print("=" * 70)
    print("VERDICT")
    print("=" * 70)
    
    if results['summary']['custom_components_found'] and results['summary']['integration_count'] > 0:
        print("✅ SUCCESS: Dependency graph WILL be able to scan integrations")
        print(f"   Found {results['summary']['integration_count']} custom integrations in /config/custom_components")
        return_code = 0
    elif results['summary']['custom_components_found'] and results['summary']['integration_count'] == 0:
        print("⚠️  WARNING: /config/custom_components accessible but empty")
        print("   No custom integrations found (this may be expected if none are installed)")
        return_code = 0
    else:
        print("❌ FAILURE: /config/custom_components NOT accessible")
        print("   Directory mappings may not be configured correctly")
        print("   Add-on needs to be restarted after configuration changes")
        return_code = 1
    
    print("=" * 70)
    
    return return_code


if __name__ == '__main__':
    sys.exit(check_directory_access())
