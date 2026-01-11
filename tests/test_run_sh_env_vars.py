"""Test that run.sh exports all required environment variables"""
import subprocess
import os
import re


def test_run_sh_has_all_required_exports():
    """Verify run.sh exports all config options as environment variables"""
    
    # Read config.yaml to extract all option keys
    config_yaml_path = os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'config.yaml')
    with open(config_yaml_path, 'r') as f:
        config_content = f.read()
    
    # Extract option keys from config.yaml (between "options:" and "schema:")
    options_match = re.search(r'options:\s*\n(.*?)\nschema:', config_content, re.DOTALL)
    if not options_match:
        raise ValueError("Could not find options section in config.yaml")
    
    options_section = options_match.group(1)
    option_keys = []
    for line in options_section.split('\n'):
        line = line.strip()
        if line and not line.startswith('#') and ':' in line:
            key = line.split(':')[0].strip()
            option_keys.append(key)
    
    # Read run.sh to extract exported variables
    run_sh_path = os.path.join(os.path.dirname(__file__), '..', 'ha_sentry', 'rootfs', 'usr', 'bin', 'run.sh')
    with open(run_sh_path, 'r') as f:
        run_sh_content = f.read()
    
    # Extract export statements
    export_vars = []
    for line in run_sh_content.split('\n'):
        if line.strip().startswith('export ') and '=' in line:
            var_name = line.split('export ')[1].split('=')[0].strip()
            export_vars.append(var_name)
    
    # Convert option keys to expected env var names (lowercase to UPPERCASE)
    expected_env_vars = [key.upper() for key in option_keys]
    
    # Check for missing exports
    missing_exports = []
    for expected_var in expected_env_vars:
        if expected_var not in export_vars:
            missing_exports.append(expected_var)
    
    # Check for unexpected exports
    unexpected_exports = []
    for export_var in export_vars:
        # Skip SUPERVISOR_TOKEN and CUSTOM_INTEGRATION_PATHS (special handling)
        if export_var in ['SUPERVISOR_TOKEN', 'CUSTOM_INTEGRATION_PATHS']:
            continue
        if export_var not in expected_env_vars:
            unexpected_exports.append(export_var)
    
    # Report findings
    print(f"\nConfig options: {len(option_keys)}")
    print(f"Expected env vars: {expected_env_vars}")
    print(f"\nExported vars: {len([v for v in export_vars if v not in ['SUPERVISOR_TOKEN', 'CUSTOM_INTEGRATION_PATHS']])}")
    print(f"Actual exports: {[v for v in export_vars if v not in ['SUPERVISOR_TOKEN', 'CUSTOM_INTEGRATION_PATHS']]}")
    
    if missing_exports:
        print(f"\n❌ MISSING EXPORTS: {missing_exports}")
    if unexpected_exports:
        print(f"\n❌ UNEXPECTED EXPORTS (deprecated): {unexpected_exports}")
    
    # Assert that all required exports exist
    assert len(missing_exports) == 0, f"Missing environment variable exports in run.sh: {missing_exports}"
    assert len(unexpected_exports) == 0, f"Deprecated environment variable exports in run.sh: {unexpected_exports}"
    
    print("\n✅ All config options are properly exported as environment variables")


if __name__ == "__main__":
    test_run_sh_has_all_required_exports()
