# Home Assistant Sentry

> **🔔 This is a Home Assistant Add-on Repository**  
> This repository provides a Home Assistant add-on, not a HACS integration. Please install it through the **Supervisor Add-on Store**, not HACS. See [Installation Instructions](#installation) below.

## Product Goal

**Home-Assistant-Sentry exists to explain update risk before the user updates, without modifying or interfering with Home Assistant's runtime.**

### Key Principles
- **Advisory, not intrusive**: We provide information, never taking action
- **Predictive, not reactive**: Analyze before updates, not after
- **Read-only by default**: Observe and analyze, never modify
- **Zero-risk to HA stability**: Never cause Home Assistant to fail

---

A Home Assistant add-on that performs daily reviews of **all available updates** (Core, Supervisor, OS, add-ons, and integrations), identifies potential conflicts and dependency issues, and advises whether updates are safe to install.

## Features

- 🔍 **Comprehensive Update Monitoring**: Daily checks for **all** system updates including:
  - Home Assistant Core
  - Supervisor
  - Operating System
  - Add-ons
  - Integrations (including HACS)
- 🤖 **AI-Powered Analysis**: Uses configurable AI endpoints to analyze update conflicts and dependencies
- 🔬 **Deep Dependency Analysis**: Advanced heuristic analysis without AI, checking version changes, pre-releases, and known conflicts
- 🛡️ **Safety Assessment**: Provides confidence scores and safety recommendations
- 📊 **Dashboard Integration**: Creates Home Assistant sensors for easy monitoring
- 🎨 **Auto-Dashboard Creation**: Optionally auto-creates a pre-configured Lovelace dashboard
- 🔄 **Auto-Update Support**: Supports Home Assistant's auto-update feature
- 🔔 **Notification System**: Sends persistent notifications with analysis results
- ⚙️ **Flexible Configuration**: Supports multiple AI providers (OpenAI, Ollama, LMStudio, OpenWebUI)

## Installation

> **Important**: This is a Home Assistant **add-on** repository, not a HACS integration. Add-ons must be installed through the Home Assistant Supervisor, not through HACS.

### Step-by-Step Installation

1. **Add the repository to Home Assistant Supervisor**:
   - Go to **Settings** → **Add-ons** → **Add-on Store**
   - Click the **three dots menu** (⋮) in the top right corner
   - Select **Repositories**
   - Add this URL: `https://github.com/ian-morgan99/Home-Assistant-Sentry`
   - Click **Add**

2. **Install the add-on**:
   - The "Home Assistant Sentry" add-on should now appear in your add-on store
   - Click on it and select **Install**

3. **Configure the add-on**:
   - Go to the **Configuration** tab
   - Adjust settings as needed (see Configuration section below)

4. **Start the add-on**:
   - Go to the **Info** tab
   - Click **Start**
   - Optionally enable **Start on boot** and **Watchdog**

### Note about HACS

This is NOT a HACS integration. If you try to add this repository to HACS, you will receive an error. HACS is for custom integrations, plugins, and themes, while this is a Home Assistant add-on that runs as a separate Docker container managed by the Supervisor.

## Configuration

### Basic Configuration

```yaml
ai_enabled: true
ai_provider: "ollama"
ai_endpoint: "http://localhost:11434"
ai_model: "llama2"
check_schedule: "02:00"
create_dashboard_entities: true
auto_create_dashboard: false
check_all_updates: true
check_addons: true
check_hacs: true
safety_threshold: 0.7
log_level: "standard"
```

### Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `ai_enabled` | Enable AI-powered analysis | `true` |
| `ai_provider` | AI provider: `openai`, `ollama`, `lmstudio`, `openwebui` | `openai` |
| `ai_endpoint` | API endpoint URL | `http://localhost:11434` |
| `ai_model` | Model name to use | `gpt-3.5-turbo` |
| `api_key` | API key (required for OpenAI) | `""` |
| `check_schedule` | Daily check time in HH:MM format (24h) | `02:00` |
| `create_dashboard_entities` | Create sensor entities for dashboard | `true` |
| `auto_create_dashboard` | Automatically create a Sentry dashboard in Lovelace | `false` |
| `check_all_updates` | Check all update entities (Core, Supervisor, OS, Add-ons, Integrations) | `true` |
| `check_addons` | Check add-on updates (legacy, use `check_all_updates` instead) | `true` |
| `check_hacs` | Check HACS updates (legacy, use `check_all_updates` instead) | `true` |
| `safety_threshold` | Confidence threshold for safety (0.0-1.0) | `0.7` |
| `log_level` | Logging verbosity: `minimal` (errors only), `standard` (info), `maximal` (debug) | `standard` |

### AI Provider Examples

#### Using Ollama (Local)

```yaml
ai_enabled: true
ai_provider: "ollama"
ai_endpoint: "http://localhost:11434"
ai_model: "llama2"
api_key: ""  # Not required for Ollama
```

#### Using LMStudio (Local)

```yaml
ai_enabled: true
ai_provider: "lmstudio"
ai_endpoint: "http://localhost:1234"
ai_model: "local-model"
api_key: ""  # Not required for LMStudio
```

#### Using OpenWebUI

```yaml
ai_enabled: true
ai_provider: "openwebui"
ai_endpoint: "http://your-openwebui-instance:8080"
ai_model: "gpt-3.5-turbo"
api_key: "your-api-key"
```

#### Using OpenAI

```yaml
ai_enabled: true
ai_provider: "openai"
ai_endpoint: "https://api.openai.com/v1"
ai_model: "gpt-3.5-turbo"
api_key: "sk-your-api-key-here"
```

#### Without AI (Deep Dependency Analysis)

When AI is disabled, the add-on uses advanced heuristic analysis that checks:
- **Version changes**: Detects major version updates that may break compatibility
- **Pre-release versions**: Identifies beta/RC releases and warns about instability
- **Critical service updates**: Flags database/broker updates requiring special care
- **Simultaneous updates**: Detects multiple critical services updating at once
- **Update volume**: Warns when too many updates are available at once
- **Version jumps**: Identifies large version jumps that may skip migration steps

```yaml
ai_enabled: false
check_schedule: "02:00"
create_dashboard_entities: true
check_addons: true
check_hacs: true
```

This mode provides deeper analysis than basic pattern matching, though not as comprehensive as AI-powered analysis.

## Dashboard Sensors

When `create_dashboard_entities` is enabled, the add-on creates the following sensors:

- **sensor.ha_sentry_update_status**: Overall update status (`safe` or `review_required`)
- **sensor.ha_sentry_updates_available**: Total number of updates available
- **sensor.ha_sentry_addon_updates**: Number of add-on updates with details
- **sensor.ha_sentry_hacs_updates**: Number of HACS updates with details
- **sensor.ha_sentry_issues**: Number and details of detected issues
- **sensor.ha_sentry_confidence**: Analysis confidence score

### Example Dashboard Card

Add this to your Lovelace dashboard:

```yaml
type: vertical-stack
cards:
  - type: entities
    title: Home Assistant Sentry
    entities:
      - entity: sensor.ha_sentry_update_status
        name: Status
      - entity: sensor.ha_sentry_updates_available
        name: Updates Available
      - entity: sensor.ha_sentry_confidence
        name: Confidence
      - entity: sensor.ha_sentry_issues
        name: Issues Detected
  
  - type: conditional
    conditions:
      - entity: sensor.ha_sentry_issues
        state_not: "0"
    card:
      type: markdown
      content: >
        ## ⚠️ Issues Detected
        
        Review the persistent notification for details.
  
  - type: entities
    title: Update Details
    entities:
      - entity: sensor.ha_sentry_addon_updates
        name: Add-on Updates
      - entity: sensor.ha_sentry_hacs_updates
        name: HACS Updates
```

## How It Works

1. **Scheduled Check**: At the configured time each day, the add-on checks for available updates
2. **Data Collection**: Gathers information about **all system updates** (Core, Supervisor, OS, Add-ons, and Integrations) via Home Assistant APIs
3. **AI Analysis**: Sends update information to the configured AI endpoint for conflict analysis
4. **Safety Assessment**: AI analyzes dependencies, breaking changes, and potential conflicts
5. **Results Reporting**: Creates/updates dashboard sensors and sends a detailed notification
6. **Issue Tracking**: If issues are found, provides specific recommendations for resolution

## Analysis Features

The AI analysis checks for:

- **Dependency Conflicts**: Incompatible version requirements between components
- **Breaking Changes**: Updates that may break existing functionality
- **System Update Safety**: Critical updates to Core, Supervisor, and OS
- **Integration Compatibility**: Conflicts between HACS integrations and add-ons
- **Security Concerns**: Known vulnerabilities or security issues
- **Installation Order**: Recommended sequence for applying updates
- **System Impact**: Potential system stability issues

## Notifications

The add-on creates persistent notifications with:

- ✅ Safety status (safe/review required)
- 📊 Confidence score
- 📦 List of available updates
- ⚠️ Identified issues with severity levels
- 💡 Actionable recommendations
- 🕐 Timestamp of analysis

## Logging

The add-on provides configurable logging levels to help with troubleshooting and monitoring:

### Log Levels

- **`minimal`**: Only logs errors and critical issues. Use this for production environments where you only want to be notified of problems.
- **`standard`** (default): Logs informational messages including:
  - Service startup and configuration
  - Update check cycles and results
  - API interactions with Home Assistant
  - Analysis summaries
- **`maximal`**: Enables debug logging with detailed information including:
  - All API requests and responses
  - Detailed configuration values
  - AI model interactions and responses
  - Sensor update operations
  - Scheduler operations

### Configuration Example

```yaml
log_level: "maximal"  # Enable debug logging for troubleshooting
```

### Viewing Logs

To view add-on logs:
1. Go to **Settings** → **Add-ons** → **Home Assistant Sentry**
2. Click on the **Log** tab
3. Or use the command line: `ha addons logs ha_sentry`

## Troubleshooting

### Add-on won't start

- Check the add-on logs for specific error messages
- Verify that your configuration is valid YAML
- Ensure required parameters (like `api_key` for OpenAI) are set correctly
- Try setting `log_level: "maximal"` to get more detailed error information

### No updates detected

- Ensure add-ons are installed and check for updates in the Supervisor
- Verify HACS is installed and configured
- Check add-on logs for API errors

### AI analysis not working

- Verify the AI endpoint is accessible from the add-on
- Check that the API key is correct (for OpenAI)
- Ensure the AI service is running (for Ollama/LMStudio)
- Review logs for connection errors
- Test with `ai_enabled: false` to use heuristic analysis

### Sensors not appearing

- Enable `create_dashboard_entities: true`
- Wait for the first check cycle to complete
- Check Home Assistant Developer Tools > States for sensors starting with `sensor.ha_sentry_`

### Schedule not working

- Ensure time format is `HH:MM` in 24-hour format (e.g., `02:00`, `14:30`)
- Check add-on logs for scheduler errors
- The first check runs immediately on add-on start

## Privacy & Security

- All data stays within your Home Assistant instance by default
- When using local AI (Ollama, LMStudio), no data leaves your network
- API keys are stored securely in Home Assistant
- No telemetry or external reporting

## Development & Contributing

For information about creating releases and the automated version update process, see [RELEASING.md](RELEASING.md).

**For contributors:** Please read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting changes. It contains critical information about our principles, rules, and guidelines that all contributors must follow.

## Support

For issues, feature requests, or contributions:
- GitHub: https://github.com/ian-morgan99/Home-Assistant-Sentry

## License

MIT License - See LICENSE file for details

## Credits

Created for the Home Assistant community to make update management safer and more automated. 
