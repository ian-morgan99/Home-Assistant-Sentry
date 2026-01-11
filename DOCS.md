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
   - The web UI is accessible via the ingress URL: `/api/hassio_ingress/ha_sentry/`
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

- **obfuscate_logs**: Obfuscate sensitive data in log files (default: `true`, recommended)
  - `true`: IP addresses, API keys, tokens, and passwords are obfuscated in logs
  - `false`: Log all data in plain text (not recommended except for debugging)
  - What is obfuscated:
    - IP addresses: `192.168.1.100` → `192.***.***.100`
    - API keys/tokens: `api_key=secret123456` → `api_key=sec***456`
    - Authorization headers: `Bearer token123` → `Bearer tok***23`
    - URL parameters: `?token=secret` → `?token=sec***et`

#### Log Monitoring Settings

- **monitor_logs_after_update**: Monitor Home Assistant logs for errors after updates (default: `false`)
  - `true`: Check logs after components are updated and report unexpected failures
  - `false`: Don't monitor logs
  - **Use case**: Get notified about new error messages that appear after updates
  - **How it works**: 
    - Compares current error logs with previous check to identify changes
    - In heuristics mode: Lists changes in log entries
    - In AI mode: Analyzes and summarizes consequential errors
    - Automatically anonymizes sensitive data before AI analysis
  - **Example**: After a component update, you'll be notified if new integration setup failures appear

- **log_check_lookback_hours**: How many hours of logs to analyze (default: `24`, range: `1-168`)
  - Controls how far back to check for error messages
  - **Recommendation**: 
    - Daily updates: 24 hours is sufficient
    - Weekly updates: Consider 48-72 hours
    - Monthly updates: Consider 168 hours (7 days)
  - Lower values = faster analysis, but may miss errors
  - Higher values = more comprehensive, but may include unrelated errors

#### Installation Review Settings

- **enable_installation_review**: Enable AI-powered installation review (default: `false`)
  - `true`: Periodically review your entire Home Assistant installation
  - `false`: Disable installation review feature
  - **Use case**: Get AI-powered recommendations to optimize your setup
  - **Privacy-first**: Only collects metadata and counts, no sensitive data
  - **What gets reviewed**: Integrations, devices, automations, helpers, dashboards
  - **Output**: Categorized recommendations (security, performance, automation, etc.)

- **installation_review_schedule**: When to run installation reviews (default: `"weekly"`)
  - `"weekly"`: Run once per week (recommended for most users)
  - `"monthly"`: Run once per month (for stable installations)
  - `"manual"`: Only run when manually triggered (future feature)
  - **Note**: Reviews run automatically based on schedule, separate from daily update checks
  - **First run**: Runs on first update check after enabling

- **installation_review_scope**: What aspects to review (default: `"full"`)
  - `"full"`: Review integrations, devices, automations, helpers, and dashboards (recommended)
  - `"integrations"`: Only review integrations and their configuration
  - `"automations"`: Only review automations and scripts
  - **Use case**: Use specific scopes if you only want targeted advice
  - **Performance**: Full scope may take longer but provides comprehensive analysis

**Installation Review Example Notification:**
```
🏠 Home Assistant Installation Review

Installation Review Complete

Your installation has 450 entities across 32 integrations and 15 devices.

📊 Key Insights:
- Large installation with 450 entities - consider using performance optimization techniques
- Diverse device ecosystem with 5 different manufacturers

💡 Recommendations:

🔒 Security:
❗ Keep System Updated
   Regularly update Home Assistant Core, Supervisor, OS, and all integrations

⚡ Performance:
❗ Recorder Optimization for Sensors
   You have 250 sensors. Configure recorder to exclude sensors that don't need history

🤖 Automation:
➡️ Consider Using Input Helpers
   Input helpers can make automations more flexible and easier to manage
```

- **obfuscate_logs**: Obfuscate sensitive data in log files (default: `true`, recommended)
  - `true`: Automatically obfuscate IP addresses, API keys, tokens, and passwords in logs
  - `false`: Log all data in plain text (not recommended - use only for specific debugging scenarios)
  
  **What gets obfuscated:**
  - IP addresses: `192.168.1.100` → `192.***.***.100`
  - API keys/tokens: `api_key=secret123456` → `api_key=sec***456`
  - Authorization headers: `Bearer token123` → `Bearer tok***23`
  - URL parameters: `?token=secret` → `?token=sec***et`
  
  **When to disable:** Only disable obfuscation if you need to see full data for specific debugging purposes, and re-enable it immediately after. Leaving it disabled may expose sensitive information in log files.

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

#### Method 3: Direct Browser Access

Navigate directly to: `http://your-home-assistant-address:PORT`

Default PORT is 8099. This can be configured in the add-on settings.

#### Method 4: Direct Ingress URL

Navigate directly to: `/hassio/ingress/ha_sentry/`

Or click links in notifications that use this format.

### WebUI Port Configuration

The WebUI supports flexible port configuration with two access methods:

#### Understanding Dual-Port Mode

The add-on can listen on two ports simultaneously:

1. **Ingress Port (8099)** - Required for Home Assistant integration
   - Used by the sidebar panel (Method 1)
   - Used by the add-on "Open Web UI" button (Method 2)
   - Always port 8099 (required by HA Supervisor)
   - Cannot be changed

2. **Direct Access Port** - Configurable for direct browser access
   - Used for direct HTTP access (Method 3)
   - Default: 8099 (same as ingress)
   - Can be changed to any port (1024-65535)
   - Useful if port 8099 conflicts with another service

#### Configuration

In the add-on configuration tab:

```yaml
port: 8099  # Default - single port mode
```

Or for custom port:

```yaml
port: 8098  # Custom - dual port mode
```

**How it works:**

- `port: 8099`: Web server listens only on port 8099
  - Sidebar panel works ✅
  - Direct access: `http://homeassistant:8099` ✅
  
- `port: 8098`: Web server listens on BOTH 8099 and 8098
  - Sidebar panel works ✅ (uses port 8099 internally)
  - Direct access: `http://homeassistant:8098` ✅
  - Ingress still uses port 8099 in the background

**When to use a custom port:**
- Port 8099 is already in use by another service
- You want to access the UI via a different port for bookmarking
- You need to avoid port conflicts

**Important:** The sidebar panel always works regardless of your `port` setting, because it uses Home Assistant's internal ingress system on port 8099.

### WebUI Features

The WebUI provides:

- **Dependency Visualization**: Interactive graphs showing component dependencies (integrations and add-ons)
- **Add-on Tracking**: View add-on metadata and Home Assistant version requirements
- **"Where Used" Analysis**: See which components depend on any integration or package
- **Change Impact Reports**: Understand the impact of updating specific components
- **Component Explorer**: Browse all installed integrations, add-ons, and their requirements
- **Interactive Navigation**: Click to explore dependency chains
- **Real-time Statistics**: View counts for integrations, add-ons, dependencies, and high-risk packages

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
- Links in notifications now properly route to the WebUI with a trailing slash
- Each updated component (integration/HACS) has a "View Dependencies" link that opens the WebUI in "Where Used" mode for that component
- A "Change Impact Report" link shows all updated components and their dependencies
- If links still don't work, use the sidebar panel instead (most reliable)
- Or use Method 2 (via add-on settings)
- Check if you're behind a reverse proxy that might interfere

**"Installation review is not running"**
- Check add-on logs to understand why the review is or isn't running
- At standard log level (`log_level: "standard"`), you'll see INFO messages when:
  - The review is scheduled to run (first time or when schedule is due)
  - The review completes with recommendations
- Set `log_level: "maximal"` to see DEBUG messages explaining:
  - Why the review is not running (schedule not due, feature disabled, manual mode)
  - Schedule details (last run time, days since last run, schedule type)
  - Configuration details (schedule mode, review scope)
- Common reasons review doesn't run:
  - `enable_installation_review: false` - Feature is disabled
  - `installation_review_schedule: "manual"` - Automatic reviews are disabled
  - Review ran recently (less than 7 days for weekly, less than 30 days for monthly)
- First run: The review will run on the first update check after enabling the feature

### Notification Links

Since version 2.0.0, notifications include interactive links to help you understand update impacts:

**Per-Component Links**: Each integration or HACS component in the "Available Updates" section includes a "🔍 View Dependencies" link that:
- Opens the WebUI in "Where Used" mode for that specific component
- Shows which other integrations depend on it
- Displays shared packages and potential conflicts
- Only appears for integrations and HACS (not add-ons, core, or OS)

**Change Impact Report Link**: When multiple components are being updated, a "⚡ Change Impact Report" link shows:
- All updated components in one view
- Total number of affected dependencies
- High-risk changes highlighted
- Complete picture of the update's impact

**Open WebUI Link**: Always available link to access the full WebUI for:
- Exploring all component dependencies
- Switching between different visualization modes
- Performing custom dependency analysis

### Dashboard vs WebUI

**Important**: The `auto_create_dashboard` feature is deprecated and does not work.

| Feature | Dashboard (Deprecated) | WebUI (Recommended) |
|---------|----------------------|---------------------|
| Status | ❌ Doesn't work | ✅ Fully functional |
| Access | Would be at `/lovelace/ha-sentry` | `/api/hassio_ingress/ha_sentry/` |
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

**Problem**: WebUI shows "Loading components..." forever or "No integrations found", or logs show "NO INTEGRATION PATHS FOUND"

**Root Cause**: The add-on can't find your Home Assistant integration directories because:
- Default paths don't exist in your environment
- Permissions issue preventing access
- Non-standard Home Assistant installation

**Symptoms**:
- WebUI stuck on "Loading components..."
- WebUI shows error: "No integrations found"
- Log messages: "⚠️  NO INTEGRATION PATHS FOUND!"
- Log messages: "⚠️  DEPENDENCY GRAPH IS EMPTY!"
- "Dependency graph built: 0 integrations, 0 dependencies"

**Solution (Step-by-Step)**:

1. **Check the add-on logs** (Settings → Add-ons → Home Assistant Sentry → Log tab)
   - Look for the section: "BUILDING DEPENDENCY GRAPH"
   - The logs will show which paths were checked and which ones don't exist
   - **Important**: Look for "✓ FOUND ALTERNATIVE INTEGRATION PATHS" - the add-on automatically scans and suggests working paths!

2. **Use the auto-detected paths**: If the logs show alternative paths (most common case):
   ```yaml
   custom_integration_paths:
     - "/path/shown/in/logs"
     - "/another/path/from/logs"
   ```
   Example from real logs:
   ```yaml
   custom_integration_paths:
     - "/config/custom_components"
     - "/usr/src/homeassistant/homeassistant/components"
   ```

3. **Restart the add-on** after configuring custom paths

4. **Refresh the WebUI** - Click the "🔄 Refresh Page" button or reload your browser

5. **Verify it works**: Check the logs for:
   ```
   ✅ DEPENDENCY GRAPH BUILD COMPLETE
     Total integrations: [number]
   ```

**Alternative: Disable dependency graph** (if you don't need the WebUI):
   ```yaml
   enable_dependency_graph: false
   enable_web_ui: false
   ```
   Note: The add-on will still work for update analysis without the dependency graph, but you won't have the visual dependency tree and impact analysis features.

**Manual path discovery** (only if auto-detection fails):
   - Enable SSH access to your Home Assistant
   - Run: `docker exec -it addon_ha_sentry sh`
   - Run: `find / -name "manifest.json" -type f 2>/dev/null | head -20`
   - Look for paths containing many manifest.json files
   - Add the parent directory to `custom_integration_paths`

**What the dependency graph provides**:
- 📊 Visual dependency tree in the WebUI
- 🔍 "Where used" analysis for any package or component
- ⚡ Change impact analysis for updates
- Detection of shared dependencies between integrations
- Identification of version conflicts in dependencies
- Highlighting of high-risk dependencies (e.g., aiohttp, cryptography)
- Enhanced analysis of update impacts

**Note**: The dependency graph and WebUI are optional features. The add-on will continue to function normally for update monitoring and analysis even without them.

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

### Log Monitoring After Updates

The add-on can monitor your Home Assistant logs for errors that appear after component updates. This helps catch issues early before they impact your system.

#### How It Works

1. **First Run**: The add-on captures the current error/warning logs as a baseline
2. **Subsequent Checks**: After each daily check, it compares current logs with the baseline
3. **Change Detection**: Identifies new errors, resolved errors, and persistent issues
4. **Analysis**: 
   - **Heuristics Mode**: Lists all changes and flags significant error patterns
   - **AI Mode**: Analyzes changes and provides actionable recommendations
5. **Notification**: Sends a report with severity assessment and recommendations

#### Configuration Example

```yaml
monitor_logs_after_update: true
log_check_lookback_hours: 24
ai_enabled: true  # Optional: for AI-powered analysis
```

#### What Gets Reported

**New Errors**: Error messages that weren't present in the previous check
- Integration setup failures
- Import errors
- Configuration issues
- Breaking changes from updates

**Resolved Errors**: Previous errors that are no longer appearing
- Shows improvement after updates

**Severity Assessment**: 
- **Critical**: Multiple integration failures or critical errors
- **High**: Significant errors that may affect functionality
- **Medium**: Multiple warnings or minor errors
- **Low**: Few new warnings
- **None**: No changes detected

#### Example Notification

```
🟠 Home Assistant Log Monitor Report

Severity: HIGH

Summary:
3 new error/warning messages detected.
1 error may require attention.

Significant Errors Detected:
1. ERROR homeassistant.components.mqtt: Setup of mqtt is taking longer than 60 seconds
2. ERROR homeassistant.components.zwave: Integration zwave could not be set up
3. WARNING homeassistant.loader: Cannot import component test

Recommendations:
- Review the new error messages immediately.
- Check if any integrations or add-ons are failing to load.
- Consider reporting issues to component maintainers if errors persist.
```

#### Privacy & Security

All sensitive data is automatically obfuscated before AI analysis:
- IP addresses: `192.168.1.100` → `192.***.***.100`
- Tokens: `token=abc123` → `token=abc***23`
- API keys: `api_key=secret` → `api_key=sec***et`

This ensures your private information never leaves your network if using cloud AI services.

#### Best Practices

1. **Enable After Setup**: Let your system run for a few days before enabling to establish a stable baseline
2. **Adjust Lookback Period**: 
   - Daily updates: 24 hours
   - Weekly updates: 48-72 hours
3. **Review Notifications**: Act on critical/high severity reports promptly
4. **Use AI Mode**: If available, AI analysis provides better context and recommendations

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
