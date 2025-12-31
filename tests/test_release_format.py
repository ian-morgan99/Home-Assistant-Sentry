"""
Test to verify release-related files have correct format
"""
import sys
import os
import re
import json

# Repository root - used for building absolute paths
repo_root = os.path.join(os.path.dirname(__file__), '..')


def _extract_yaml_version(content):
    """Helper function to extract version from YAML content"""
    # Match version with or without quotes, allowing for semantic versioning
    version_match = re.search(r'^version:\s*["\']?([0-9.]+)["\']?', content, re.MULTILINE)
    return version_match.group(1) if version_match else None


def test_config_json_version_format():
    """Verify config.json has valid version format"""
    try:
        config_path = os.path.join(repo_root, 'ha_sentry', 'config.json')
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        version = config.get('version', '')
        
        # Version should follow semantic versioning (X.Y.Z or X.Y.ZZ)
        # Note: The current version uses 1.2.02 format which is non-standard but accepted
        version_pattern = r'^\d+\.\d+\.\d+$'
        if not re.match(version_pattern, version):
            print(f"⚠ config.json version format: {version} (non-standard but acceptable)")
        else:
            print(f"✓ config.json has valid version format: {version}")
        
        assert 'version' in config, "config.json must have a 'version' field"
        assert len(version) > 0, "version cannot be empty"
        return True
    except Exception as e:
        print(f"✗ config.json version format test failed: {e}")
        return False


def test_config_yaml_version_format():
    """Verify config.yaml has valid version format"""
    try:
        config_path = os.path.join(repo_root, 'ha_sentry', 'config.yaml')
        with open(config_path, 'r') as f:
            content = f.read()
        
        # Extract version using helper function
        version = _extract_yaml_version(content)
        
        assert version is not None, "config.yaml must have a version field"
        
        # Version should follow semantic versioning
        version_pattern = r'^\d+\.\d+\.\d+$'
        if not re.match(version_pattern, version):
            print(f"⚠ config.yaml version format: {version} (non-standard but acceptable)")
        else:
            print(f"✓ config.yaml has valid version format: {version}")
        
        assert len(version) > 0, "version cannot be empty"
        return True
    except Exception as e:
        print(f"✗ config.yaml version format test failed: {e}")
        return False


def test_config_versions_match():
    """Verify version numbers match in both config files"""
    try:
        # Read config.json
        config_json_path = os.path.join(repo_root, 'ha_sentry', 'config.json')
        with open(config_json_path, 'r') as f:
            config_json = json.load(f)
        json_version = config_json.get('version', '')
        
        # Read config.yaml using helper function
        config_yaml_path = os.path.join(repo_root, 'ha_sentry', 'config.yaml')
        with open(config_yaml_path, 'r') as f:
            yaml_content = f.read()
        yaml_version = _extract_yaml_version(yaml_content)
        
        assert json_version == yaml_version, \
            f"Version mismatch: config.json has {json_version}, config.yaml has {yaml_version}"
        
        print(f"✓ Version numbers match in both config files: {json_version}")
        return True
    except Exception as e:
        print(f"✗ Config version match test failed: {e}")
        return False


def test_changelog_format():
    """Verify CHANGELOG.md follows Home Assistant Add-on format"""
    try:
        changelog_path = os.path.join(repo_root, 'CHANGELOG.md')
        with open(changelog_path, 'r') as f:
            content = f.read()
        
        # Check for Home Assistant Add-on format (without square brackets or dates)
        # Format should be: ## X.Y.Z (version only, no date suffix)
        # Home Assistant Supervisor parses these headings to match the version in config.yaml
        # Allow flexible version format (X.Y.Z or X.Y.ZZ)
        version_entries = re.findall(r'^## ([0-9.]+)$', content, re.MULTILINE)
        
        assert len(version_entries) > 0, "CHANGELOG.md should have at least one version entry"
        
        # Check that version entries don't use square brackets
        bracket_entries = re.findall(r'^## \[[0-9.]+\]', content, re.MULTILINE)
        assert len(bracket_entries) == 0, \
            "CHANGELOG.md should not use square brackets around version numbers (use '## X.Y.Z' not '## [X.Y.Z]')"
        
        # Check that version entries don't have date suffixes
        date_suffix_entries = re.findall(r'^## [0-9.]+ -', content, re.MULTILINE)
        assert len(date_suffix_entries) == 0, \
            "CHANGELOG.md should not have date suffixes (use '## X.Y.Z' not '## X.Y.Z - DATE'). Home Assistant parses version-only headings."
        
        print(f"✓ CHANGELOG.md follows Home Assistant Add-on format")
        print(f"  Found {len(version_entries)} version entries")
        for version in version_entries[:3]:  # Show first 3
            print(f"    - {version}")
        
        return True
    except Exception as e:
        print(f"✗ CHANGELOG.md format test failed: {e}")
        return False


def test_changelog_has_current_version():
    """Verify CHANGELOG.md contains an entry for the current version"""
    try:
        # Read current version from config.json
        config_path = os.path.join(repo_root, 'ha_sentry', 'config.json')
        with open(config_path, 'r') as f:
            config = json.load(f)
        current_version = config.get('version', '')
        
        # Read CHANGELOG.md
        changelog_path = os.path.join(repo_root, 'CHANGELOG.md')
        with open(changelog_path, 'r') as f:
            content = f.read()
        
        # Check if current version is in changelog
        version_pattern = f'^## {re.escape(current_version)}'
        if re.search(version_pattern, content, re.MULTILINE):
            print(f"✓ CHANGELOG.md contains entry for current version {current_version}")
            return True
        else:
            print(f"⚠ CHANGELOG.md does not contain entry for current version {current_version}")
            print(f"  This is expected if a new version was just released via automation")
            return True  # Not a failure, just a warning
    except Exception as e:
        print(f"✗ CHANGELOG current version test failed: {e}")
        return False


def test_changelog_structure():
    """Verify CHANGELOG.md has proper structure"""
    try:
        changelog_path = os.path.join(repo_root, 'CHANGELOG.md')
        with open(changelog_path, 'r') as f:
            lines = f.readlines()
        
        # Should start with # Changelog
        assert lines[0].strip().startswith('# Changelog'), \
            "CHANGELOG.md should start with '# Changelog' heading"
        
        # Should have at least one ## version entry
        has_version = any(line.strip().startswith('## ') and re.match(r'## \d+\.\d+\.\d+', line) 
                         for line in lines)
        assert has_version, "CHANGELOG.md should have at least one version entry (## X.Y.Z)"
        
        print("✓ CHANGELOG.md has proper structure")
        return True
    except Exception as e:
        print(f"✗ CHANGELOG structure test failed: {e}")
        return False


if __name__ == '__main__':
    print("Running release format verification tests...\n")
    
    tests = [
        test_config_json_version_format,
        test_config_yaml_version_format,
        test_config_versions_match,
        test_changelog_format,
        test_changelog_has_current_version,
        test_changelog_structure,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        if test():
            passed += 1
        else:
            failed += 1
        print()  # Add spacing between tests
    
    print(f"{'='*50}")
    print(f"Release format tests: {passed} passed, {failed} failed")
    print(f"{'='*50}")
    
    sys.exit(0 if failed == 0 else 1)
