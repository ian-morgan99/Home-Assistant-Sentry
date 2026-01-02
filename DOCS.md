# Home Assistant Sentry - Documentation

> **Important**: This is a Home Assistant **add-on**, not a HACS integration. It must be installed through the Supervisor Add-on Store, not through HACS.

> **✅ Compatibility**: Tested and verified with Home Assistant versions **2024.11.x**, **2024.12.x**, and **2025.1.x**

## Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Configuration Guide](#configuration-guide)
4. [WebUI Access](#webui-access)
5. [AI Provider Setup](#ai-provider-setup)
6. [Dashboard Integration](#dashboard-integration)
7. [Understanding the Analysis](#understanding-the-analysis)
8. [Troubleshooting](#troubleshooting)
9. [Advanced Usage](#advanced-usage)

## Introduction

Home Assistant Sentry is an add-on that helps you safely manage updates to your Home Assistant installation. It automatically checks for updates to add-ons and HACS integrations, analyzes them for potential conflicts, and provides recommendations on whether it's safe to proceed with updates.

## Installation

### Prerequisites

- Home Assistant OS or Supervised installation
- Home Assistant Core **2024.11 or later** (tested with 2024.11.x, 2024.12.x, and 2025.1.x)
- (Optional) HACS installed for integration update monitoring
- (Optional) AI service for enhanced analysis (Ollama, LMStudio, OpenWebUI, or OpenAI)

### Steps

1. **Add the Repository**
   - Navigate to Supervisor → Add-on Store
   - Click the menu (⋮) in the top right
   - Select "Repositories"
   - Add: `https://github.com/ian-morgan99/Home-Assistant-Sentry`

2. **Install the Add-on**
   - Find "Home Assistant Sentry" in the add-on store
   - Click on it and press "Install"
   - Wait for the installation to complete

3. **Configure the Add-on**
   - Go to the Configuration tab
   - Set your preferences (see Configuration Guide)
   - Save the configuration

4. **Start the Add-on**
   - Go to the Info tab
   - Click "Start"
   - Enable "Start on boot" if desired
   - Check the logs to ensure it's running correctly

5. **Access the Web UI (Optional)**
   - After the add-on starts, a "Sentry" panel will appear in your Home Assistant sidebar
   - Click on "Sentry" in the sidebar to access the dependency visualization web interface
   - The web UI allows you to:
     - Explore component dependencies
     - View "where used" analysis for any component
     - Analyze the impact of multiple component changes
   - The web UI is accessible via the ingress URL: `/api/hassio_ingress/ha_sentry`
   - Note: It may take up to 60 seconds for the dependency graph to build on first load

## Configuration Guide

### Basic Setup (No AI)

For a setup without AI, using deep dependency analysis:

```yaml
ai_enabled: false
check_schedule: "02:00"
create_dashboard_entities: true
check_addons: true
check_hacs: true
```

This will use advanced heuristic analysis that examines:
- Major version changes and breaking updates
- Pre-release versions (alpha, beta, RC)
- Known critical service conflicts
- Update volume and simultaneous critical updates
- Version jump patterns that may skip migration steps

The analysis is more sophisticated than basic pattern matching, providing detailed issue detection and recommendations without requiring AI.

### AI-Enabled Setup

For enhanced analysis with AI:

```yaml
ai_enabled: true
ai_provider: "ollama"
ai_endpoint: "http://homeassistant.local:11434"
ai_model: "llama2"
check_schedule: "02:00"
create_dashboard_entities: true
check_addons: true
check_hacs: true
safety_threshold: 0.7
```

### Configuration Parameters

#### Core Settings

- **check_schedule**: Time of day to run the check (HH:MM format, 24-hour)
  - Example: `"02:00"` for 2 AM, `"14:30"` for 2:30 PM
  - The add-on will run daily at this time

- **check_addons**: Enable/disable add-on update checking
  - Set to `false` if you only want to check HACS integrations

- **check_hacs**: Enable/disable HACS integration checking
  - Set to `false` if you don't use HACS or only want add-on checks

- **create_dashboard_entities**: Create sensor entities
  - Set to `true` to enable dashboard integration
  - Set to `false` if you only want notifications

#### AI Settings

- **ai_enabled**: Enable AI-powered analysis
  - `true`: Use AI for detailed analysis
  - `false`: Use heuristic analysis only

- **ai_provider**: Choose your AI provider
  - `"ollama"`: Local Ollama instance
  - `"lmstudio"`: Local LMStudio instance
  - `"openwebui"`: OpenWebUI instance
  - `"openai"`: OpenAI cloud service

- **ai_endpoint**: URL of your AI service
  - Ollama default: `"http://localhost:11434"`
  - LMStudio default: `"http://localhost:1234"`
  - OpenAI: `"https://api.openai.com/v1"`

- **ai_model**: Model to use for analysis
  - Ollama: `"llama2"`, `"mistral"`, `"codellama"`
  - LMStudio: Whatever model you have loaded
  - OpenAI: `"gpt-3.5-turbo"`, `"gpt-4"`

- **api_key**: API key for authentication
  - Required for OpenAI
  - Not required for Ollama or LMStudio
  - May be required for OpenWebUI depending on setup

- **safety_threshold**: Confidence threshold (0.0 to 1.0)
  - Higher values = more conservative
  - Recommended: `0.7` for balanced approach

#### Advanced Settings

- **enable_dependency_graph**: Enable dependency graph analysis
  - `true`: Build dependency graph from installed integrations (default)
  - `false`: Disable dependency graph analysis
  - The dependency graph helps identify shared dependencies and potential conflicts

- **save_reports**: Save machine-readable reports to disk
  - `true`: Save JSON reports to `/data/reports` (default)
  - `false`: Don't save reports
  - Useful for debugging and external analysis

- **custom_integration_paths**: Custom paths to scan for integrations
  - Default: `[]` (uses built-in paths)
  - Example: `["/config/custom_components", "/share/integrations"]`
  - **Use case**: If the default paths don't work in your environment
  - The add-on will automatically suggest alternative paths in the logs if default paths are missing
  - See [Troubleshooting - Dependency Graph Issues](#dependency-graph-issues) for more details

#### Logging Settings

- **log_level**: Set the verbosity of logs
  - `"minimal"`: Only errors
  - `"standard"`: Info and errors (default)
  - `"maximal"`: Debug, info, and errors

## WebUI Access

The add-on includes a built-in **interactive WebUI** for dependency visualization and analysis. This replaces the deprecated dashboard auto-creation feature.

### How to Access the WebUI

#### Method 1: Sidebar Panel (Recommended)

1. Look for the **"Sentry"** panel in your Home Assistant sidebar (left navigation)
2. Click to open the WebUI

This is the easiest and most reliable method.

#### Method 2: Via Add-on Settings

1. Go to **Settings** → **Add-ons**
2. Find **Home Assistant Sentry**
3. Click the **Open Web UI** button

#### Method 3: Direct Ingress URL

Navigate directly to: `/api/hassio_ingress/ha_sentry`

Or click links in notifications that use this format.

### WebUI Features

The WebUI provides:

- **Dependency Visualization**: Interactive graphs showing component dependencies
- **"Where Used" Analysis**: See which components depend on any integration
- **Change Impact Reports**: Understand the impact of updating specific components
- **Component Explorer**: Browse all installed integrations and their requirements
- **Interactive Navigation**: Click to explore dependency chains

### Troubleshooting WebUI Access

**"I don't see the Sentry panel"**
- Restart the add-on
- Refresh your browser (Ctrl+F5 or Cmd+R)
- Check add-on logs for errors
- Verify `enable_web_ui: true` and `ingress: true` in configuration

**"WebUI shows no components"**
- This is normal if dependency graph building failed
- Check add-on logs for path scanning errors
- The add-on may suggest custom integration paths
- See the "Empty Dependency Graph" troubleshooting section below

**"Links in notifications don't work"**
- Use the sidebar panel instead (most reliable)
- Or use Method 2 (via add-on settings)
- Check if you're behind a reverse proxy that might interfere

### Dashboard vs WebUI

**Important**: The `auto_create_dashboard` feature is deprecated and does not work.

| Feature | Dashboard (Deprecated) | WebUI (Recommended) |
|---------|----------------------|---------------------|
| Status | ❌ Doesn't work | ✅ Fully functional |
| Access | Would be at `/lovelace/ha-sentry` | `/api/hassio_ingress/ha_sentry` |
| Visualization | Basic sensor cards | Interactive graphs |
| Dependency Analysis | Limited | Full analysis |
| Impact Reports | No | Yes |
| Where Used | No | Yes |

**Always use the WebUI** - it provides all features and more than the dashboard would have provided.

## AI Provider Setup

### Setting up Ollama

1. **Install Ollama**
   ```bash
   curl https://ollama.ai/install.sh | sh
   ```

2. **Pull a model**
   ```bash
   ollama pull llama2
   ```

3. **Configure Sentry**
   ```yaml
   ai_provider: "ollama"
   ai_endpoint: "http://localhost:11434"
   ai_model: "llama2"
   ```

### Setting up LMStudio

1. **Download LMStudio** from https://lmstudio.ai/
2. **Load a model** in LMStudio
3. **Start the server** in LMStudio (Tools → Server)
4. **Configure Sentry**
   ```yaml
   ai_provider: "lmstudio"
   ai_endpoint: "http://localhost:1234"
   ai_model: "local-model"
   ```

### Setting up OpenWebUI

1. **Install OpenWebUI** (see https://openwebui.com/)
2. **Get your API endpoint** from OpenWebUI settings
3. **Configure Sentry**
   ```yaml
   ai_provider: "openwebui"
   ai_endpoint: "http://your-server:8080"
   ai_model: "gpt-3.5-turbo"
   api_key: "your-api-key"
   ```

### Using OpenAI

1. **Get an API key** from https://platform.openai.com/
2. **Configure Sentry**
   ```yaml
   ai_provider: "openai"
   ai_endpoint: "https://api.openai.com/v1"
   ai_model: "gpt-3.5-turbo"
   api_key: "sk-your-key-here"
   ```

## Dashboard Integration

### Sensor Entities

When enabled, these sensors are created:

1. **sensor.ha_sentry_update_status**
   - States: `safe`, `review_required`, `up_to_date`
   - Shows overall update safety status

2. **sensor.ha_sentry_updates_available**
   - Numeric value showing total updates
   - Attributes include breakdown by type

3. **sensor.ha_sentry_addon_updates**
   - Count of add-on updates
   - Attributes list each add-on with versions

4. **sensor.ha_sentry_hacs_updates**
   - Count of HACS updates
   - Attributes list each integration with versions

5. **sensor.ha_sentry_issues**
   - Count of detected issues
   - Attributes include issue details and severity

6. **sensor.ha_sentry_confidence**
   - Analysis confidence score (0-1)
   - Percentage in attributes

### Dashboard Examples

#### Simple Status Card

```yaml
type: entities
title: Update Status
entities:
  - sensor.ha_sentry_update_status
  - sensor.ha_sentry_updates_available
  - sensor.ha_sentry_issues
```

#### Detailed Information Card

```yaml
type: vertical-stack
cards:
  - type: glance
    title: Sentry Status
    entities:
      - entity: sensor.ha_sentry_update_status
        name: Status
      - entity: sensor.ha_sentry_updates_available
        name: Updates
      - entity: sensor.ha_sentry_confidence
        name: Confidence
  
  - type: markdown
    content: >
      {% if states('sensor.ha_sentry_updates_available') | int > 0 %}
        ## Available Updates
        - **Add-ons**: {{ states('sensor.ha_sentry_addon_updates') }}
        - **HACS**: {{ states('sensor.ha_sentry_hacs_updates') }}
        
        {% if states('sensor.ha_sentry_issues') | int > 0 %}
        ⚠️ **{{ states('sensor.ha_sentry_issues') }} issues detected**
        {% else %}
        ✅ **Safe to update**
        {% endif %}
      {% else %}
        ✅ System is up to date
      {% endif %}
```

#### Conditional Warning Card

```yaml
type: conditional
conditions:
  - entity: sensor.ha_sentry_issues
    state_not: "0"
card:
  type: markdown
  title: "⚠️ Update Issues Detected"
  content: >
    {{ state_attr('sensor.ha_sentry_issues', 'issues_list') | length }} issues found.
    
    Check the Sentry notification for details.
```

## Understanding the Analysis

### Safety Levels

- **Safe**: No conflicts detected, confidence above threshold
- **Review Required**: Potential issues found, manual review recommended
- **Up to Date**: No updates available

### Issue Severity

- **Critical** 🔴: Major compatibility issues, data loss risk
- **High** 🟠: Significant functionality issues, service interruption likely
- **Medium** 🟡: Minor issues, workarounds available
- **Low** 🟢: Informational, no action required

### Confidence Scores

- **0.9-1.0**: Very confident in the analysis
- **0.7-0.9**: Confident, recommended for most users
- **0.5-0.7**: Moderate confidence, exercise caution
- **Below 0.5**: Low confidence, manual review strongly recommended

## Troubleshooting

### Common Issues

#### 1. No Sensors Appearing

**Problem**: Dashboard sensors not showing up

**Solutions**:
- Verify `create_dashboard_entities: true` in configuration
- Wait for the first check cycle to complete
- Check Developer Tools → States for `sensor.ha_sentry_*`
- Restart Home Assistant if needed

#### 2. AI Analysis Not Working

**Problem**: Falls back to heuristic analysis

**Solutions**:
- Verify AI service is running and accessible
- Check endpoint URL is correct
- Test endpoint connectivity: `curl http://your-endpoint/v1/models`
- Review add-on logs for connection errors
- Verify API key is correct (for OpenAI)

#### 3. HACS Updates Not Detected

**Problem**: Shows 0 HACS updates when updates exist

**Solutions**:
- Verify HACS is installed and configured
- Check HACS has update sensors enabled
- Ensure `check_hacs: true` in configuration
- Review add-on logs for API errors

#### 4. Schedule Not Working

**Problem**: Checks not running at scheduled time

**Solutions**:
- Verify time format is `HH:MM` (24-hour)
- Check add-on logs for scheduler errors
- Note: First check runs immediately on start
- Restart add-on if schedule seems stuck

#### 5. Dashboard Creation Failed (404 Not Found)

**Problem**: "Failed to create dashboard: 404 - 404: Not Found" in logs

**This is EXPECTED BEHAVIOR**: Dashboard auto-creation is deprecated and does not work.

**Why This Happens**:
- Home Assistant add-ons do not have permission to create Lovelace dashboards via the API
- The Lovelace API endpoint returns 404 or 403 errors when accessed by add-ons
- This is a limitation of Home Assistant's security architecture, not a bug

**Solution**:
1. The option has been removed - dashboard auto-creation is no longer supported
2. **Use the WebUI instead** - access via the "Sentry" panel in your sidebar
3. The WebUI provides all features and more than a dashboard would have provided
4. See the [WebUI Access](#webui-access) section for details

#### 6. Dashboard Creation Failed (401 Unauthorized)

**Problem**: "Failed to create dashboard: 401 - 401: Unauthorized" in logs (in older versions)

**This is a known limitation**: Home Assistant add-ons do not have permission to create Lovelace dashboards via the API. This functionality has been removed.

**Solution**:
- The `auto_create_dashboard` option has been removed in current versions
- Use the built-in WebUI instead (accessible via "Sentry" sidebar panel)
- See the [WebUI Access](#webui-access) section for details
- The add-on will continue to work normally and create/update sensor entities

#### 7. AI Client Initialization Error

**Problem**: "Failed to initialize AI client: Client.__init__() got an unexpected keyword argument 'proxies'"

**This was a compatibility issue** with older versions of the OpenAI library.

**Solution**:
- Update to the latest version of the add-on (v1.1.1 or later)
- The issue has been fixed by updating the OpenAI library dependency
- If you continue to see this error, try restarting the add-on

#### 7. No Update Entities Found

**Problem**: "No update.* entities found in Home Assistant" warning in logs

**This may indicate**:
- No updates are currently available (normal situation)
- Update entities are not enabled in your Home Assistant configuration
- Possible Home Assistant version compatibility issue

**Solutions**:
- Verify your Home Assistant version is **2024.11 or later** (check Settings → System → About)
- Check if update entities exist: Go to Developer Tools → States and search for `update.`
- Ensure update entity integration is enabled in Home Assistant
- If running HA 2024.11+, update entities should be available by default
- Check add-on logs for specific error messages about API endpoints

#### 8. API Endpoint Not Found (404)

**Problem**: "API endpoint not found" error in logs

**This indicates a potential Home Assistant API compatibility issue**:
- The `/api/states` endpoint should be available in all HA versions 2024.11+
- The `/api/lovelace/dashboards` endpoint is used for dashboard creation

**Solutions**:
- Verify your Home Assistant version: Settings → System → About
- Update Home Assistant to version **2024.11.0 or later**
- For dashboard creation failures: Set `auto_create_dashboard: false` and create dashboards manually
- Check Home Assistant logs for any API-related errors
- If the issue persists on a supported version, report it as a bug

#### 9. Empty Update Results with Fallback Warnings

**Problem**: "No updates found via unified API - attempting legacy fallback methods" in logs

**This is a compatibility fallback mechanism**:
- The add-on first tries the modern update entity API
- If that returns empty, it falls back to legacy Supervisor API
- This ensures compatibility across different HA versions

**Solutions**:
- If the fallback succeeds, no action needed - the add-on is working correctly
- If both methods return empty and you know updates exist, check:
  - Update entity permissions in HA configuration
  - Supervisor API access (requires `hassio_api: true` in config)
- Check Developer Tools → States for update.* entities to verify they exist
#### 7. Dependency Graph Issues

**Problem**: Logs show "Path does not exist" and "Zero integrations found when building dependency graph"

**Root Cause**: The add-on container doesn't have access to Home Assistant's integration directories.

**Symptoms**:
- Log messages: "Path does not exist: /usr/src/homeassistant/homeassistant/components"
- Log messages: "Path does not exist: /config/custom_components"
- "Dependency graph built: 0 integrations, 0 dependencies"

**Solutions**:

1. **Check the logs for suggested paths**: The add-on will automatically scan for alternative integration paths and suggest them in the logs.

2. **Configure custom paths**: Add the suggested paths to your add-on configuration:
   ```yaml
   custom_integration_paths:
     - "/config/custom_components"
     - "/usr/share/hassio/homeassistant/custom_components"
   ```

3. **Disable dependency graph** (if you don't need it):
   ```yaml
   enable_dependency_graph: false
   ```
   Note: The add-on will still work without the dependency graph, but won't be able to analyze shared dependency conflicts.

4. **Manual path discovery**: If the automatic suggestion doesn't work, you can manually explore your container:
   - Enable SSH access to your Home Assistant
   - Run: `docker exec -it addon_SLUG sh` (replace SLUG with the add-on slug)
   - Look for directories containing `manifest.json` files
   - Add those paths to `custom_integration_paths`

**What the dependency graph provides**:
- Detection of shared dependencies between integrations
- Identification of version conflicts in dependencies
- Highlighting of high-risk dependencies (e.g., aiohttp, cryptography)
- Enhanced analysis of update impacts

**Note**: The dependency graph is an optional feature. The add-on will continue to function normally without it, using update metadata analysis instead.

### Checking Logs

View add-on logs:
1. Go to Supervisor → Home Assistant Sentry
2. Click on "Log" tab
3. Look for errors or warnings

Enable debug logging by adding to configuration:
```yaml
log_level: debug
```

## Advanced Usage

### Manual Trigger

To manually trigger a check without waiting for the schedule:
1. Restart the add-on
2. The check runs immediately on startup

### Integration with Automations

Use the sensors in automations:

```yaml
automation:
  - alias: "Notify on unsafe updates"
    trigger:
      - platform: state
        entity_id: sensor.ha_sentry_update_status
        to: "review_required"
    action:
      - service: notify.mobile_app
        data:
          message: "Sentry detected issues with available updates"
          title: "⚠️ Update Review Required"
```

### Custom Safety Threshold

Adjust the safety threshold based on your risk tolerance:

- **Conservative** (0.8-0.9): Only approve very confident analyses
- **Balanced** (0.7): Recommended for most users
- **Aggressive** (0.5-0.6): Accept more uncertain analyses

### Disabling Specific Checks

Check only add-ons:
```yaml
check_addons: true
check_hacs: false
```

Check only HACS:
```yaml
check_addons: false
check_hacs: true
```

### Multiple Daily Checks

While the configuration supports one scheduled check, you can:
1. Restart the add-on to trigger an immediate check
2. Use Home Assistant automations to restart the add-on at specific times

---

For more information, visit: https://github.com/ian-morgan99/Home-Assistant-Sentry
