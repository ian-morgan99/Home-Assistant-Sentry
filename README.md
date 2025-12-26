# Home Assistant Sentry

A Home Assistant add-on that performs daily reviews of all available updates to installed add-ons and HACS integrations, identifies potential conflicts and dependency issues, and advises whether updates are safe to install.

## Features

- 🔍 **Automated Update Monitoring**: Daily checks for add-on and HACS integration updates
- 🤖 **AI-Powered Analysis**: Uses configurable AI endpoints to analyze update conflicts and dependencies
- 🛡️ **Safety Assessment**: Provides confidence scores and safety recommendations
- 📊 **Dashboard Integration**: Creates Home Assistant sensors for easy monitoring
- 🔔 **Notification System**: Sends persistent notifications with analysis results
- ⚙️ **Flexible Configuration**: Supports multiple AI providers (OpenAI, Ollama, LMStudio, OpenWebUI)

## Installation

1. Add this repository to your Home Assistant add-on store
2. Install the "Home Assistant Sentry" add-on
3. Configure the add-on (see Configuration section)
4. Start the add-on

## Configuration

### Basic Configuration

```yaml
ai_enabled: true
ai_provider: "ollama"
ai_endpoint: "http://localhost:11434"
ai_model: "llama2"
check_schedule: "02:00"
create_dashboard_entities: true
check_addons: true
check_hacs: true
safety_threshold: 0.7
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
| `check_addons` | Check add-on updates | `true` |
| `check_hacs` | Check HACS updates | `true` |
| `safety_threshold` | Confidence threshold for safety (0.0-1.0) | `0.7` |

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

#### Without AI (Heuristic Analysis)

```yaml
ai_enabled: false
check_schedule: "02:00"
create_dashboard_entities: true
check_addons: true
check_hacs: true
```

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
2. **Data Collection**: Gathers information about add-on and HACS updates via Home Assistant APIs
3. **AI Analysis**: Sends update information to the configured AI endpoint for conflict analysis
4. **Safety Assessment**: AI analyzes dependencies, breaking changes, and potential conflicts
5. **Results Reporting**: Creates/updates dashboard sensors and sends a detailed notification
6. **Issue Tracking**: If issues are found, provides specific recommendations for resolution

## Analysis Features

The AI analysis checks for:

- **Dependency Conflicts**: Incompatible version requirements between components
- **Breaking Changes**: Updates that may break existing functionality
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

## Troubleshooting

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

## Support

For issues, feature requests, or contributions:
- GitHub: https://github.com/ian-morgan99/Home-Assistant-Sentry

## License

MIT License - See LICENSE file for details

## Credits

Created for the Home Assistant community to make update management safer and more automated. 
