# Quick Start Guide - Home Assistant Sentry

Get up and running with Home Assistant Sentry in 5 minutes!

> **Important Note**: This is a Home Assistant **add-on**, not a HACS integration. Follow the Supervisor add-on installation steps below. Do NOT attempt to add this to HACS.

> **✅ Compatibility**: Requires Home Assistant **2024.11 or later**. Tested with versions **2024.11.x**, **2024.12.x**, and **2025.1.x**

## Prerequisites

- Home Assistant OS or Supervised
- Home Assistant Core **2024.11+** (check Settings → System → About)
- (Optional) Ollama, LMStudio, OpenWebUI, or OpenAI API key

## Installation Steps

### 1. Add the Repository

1. Open Home Assistant
2. Navigate to **Supervisor** → **Add-on Store**
3. Click the **menu** (⋮) in the top right
4. Select **Repositories**
5. Add: `https://github.com/ian-morgan99/Home-Assistant-Sentry`
6. Click **Close**

### 2. Install the Add-on

1. Find **"Home Assistant Sentry"** in the add-on store
2. Click on it
3. Click **Install**
4. Wait for installation to complete (may take a few minutes)

### 3. Configure the Add-on

#### Option A: Basic Setup (No AI)

Go to the **Configuration** tab and use:

```yaml
ai_enabled: false
check_schedule: "02:00"
create_dashboard_entities: true
check_addons: true
check_hacs: true
```

#### Option B: With Local AI (Ollama - Recommended)

First, install and set up Ollama on your network, then:

```yaml
ai_enabled: true
ai_provider: "ollama"
ai_endpoint: "http://your-ollama-host:11434"
ai_model: "llama2"
check_schedule: "02:00"
create_dashboard_entities: true
check_addons: true
check_hacs: true
safety_threshold: 0.7
```

### 4. Start the Add-on

1. Click on the **Info** tab
2. Click **Start**
3. (Optional) Enable **Start on boot**
4. (Optional) Enable **Watchdog**

### 5. Check Notifications (Important!)

1. Click the **notification bell icon** 🔔 in Home Assistant
2. Look for the **"🚀 Home Assistant Sentry Started"** notification
3. This notification explains:
   - How to view your sensors
   - How to create dashboards
   - When the next check will run

### 6. Verify Sensors Are Created

1. Go to **Developer Tools** → **States**
2. In the filter box, type: `sensor.ha_sentry`
3. You should see **6 sensors**:
   - `sensor.ha_sentry_update_status` - Overall status
   - `sensor.ha_sentry_updates_available` - Update count
   - `sensor.ha_sentry_addon_updates` - Add-on updates
   - `sensor.ha_sentry_hacs_updates` - HACS updates
   - `sensor.ha_sentry_issues` - Issues detected
   - `sensor.ha_sentry_confidence` - Analysis confidence

**Can't find them?** Check the add-on logs and ensure `create_dashboard_entities: true` in configuration.

### 7. Check the Analysis Results and WebUI

After the first check completes (happens immediately on startup):

1. Look for a **new notification** 🔔: "🔔 Home Assistant Sentry Update Report"
2. This shows:
   - How many updates are available
   - Whether they're safe to install
   - Any detected issues
   - Recommendations
   - **Interactive links** to view dependencies for each component
   - **Change Impact Report** link to see all updates and their dependencies
   - **Open WebUI** link for full dependency visualization

3. **Access the WebUI**:
   - Click the **"Sentry"** panel in your Home Assistant sidebar (easiest method)
   - Or click any link in the notification
   - Or go to Settings → Add-ons → Home Assistant Sentry → Open Web UI
   - Or navigate directly to `http://homeassistant:8099` (or your configured port)

The WebUI provides interactive dependency visualization, "Where Used" analysis, and change impact reports.

**Note on Port Configuration**: By default, the WebUI runs on port 8099. If this port conflicts with another service, you can change it in the add-on configuration. The sidebar panel will continue to work regardless of your port setting. See [DOCS.md](DOCS.md#webui-port-configuration) for details.

## Creating a Dashboard Card

Add this to your Lovelace dashboard:

```yaml
type: entities
title: Update Monitor
entities:
  - entity: sensor.ha_sentry_update_status
    name: Status
  - entity: sensor.ha_sentry_updates_available
    name: Updates Available
  - entity: sensor.ha_sentry_confidence
    name: Confidence
```

## Troubleshooting

### No updates showing?

- Make sure you have add-ons installed and updates available
- Check that HACS is installed if checking HACS integrations
- Wait for the first scheduled check to complete

### AI not working?

- Verify your AI endpoint is accessible
- Test with `ai_enabled: false` first
- Check the logs for connection errors

### Sensors not appearing?

- Verify `create_dashboard_entities: true`
- Wait for the first check cycle to complete
- Check Developer Tools → States for `sensor.ha_sentry_*`

## Next Steps

1. **Customize the schedule**: Change `check_schedule` to your preferred time
2. **Try different AI models**: Experiment with models like `llama2`, `mistral`, or `codellama` (Ollama)
3. **Adjust safety threshold**: Tune based on your risk tolerance
4. **Add automations**: Create automations based on the sensors
5. **Read the docs**: Check out DOCS.md for advanced features

## Common Questions

**Q: When does the first check run?**  
A: Immediately when the add-on starts, then daily at the scheduled time.

**Q: Do I need AI enabled?**  
A: No! The add-on works with heuristic analysis when AI is disabled.

**Q: Can I check updates manually?**  
A: Yes! Restart the add-on to trigger an immediate check.

**Q: Is my data private?**  
A: Yes! With local AI (Ollama/LMStudio), nothing leaves your network.

**Q: Does this automatically install updates?**  
A: No! It only analyzes and reports. You install updates manually.

## Support

- **Issues**: https://github.com/ian-morgan99/Home-Assistant-Sentry/issues
- **Documentation**: See DOCS.md for detailed information
- **Examples**: See EXAMPLES.md for more configuration options

---

**You're all set!** Home Assistant Sentry is now monitoring your updates. 🎉
