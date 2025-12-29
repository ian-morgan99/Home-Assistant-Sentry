# Home Assistant Sentry Add-on

A Home Assistant add-on that performs daily reviews of **all available updates** (Core, Supervisor, OS, Add-ons, and Integrations), identifies potential conflicts and dependency issues, and advises whether updates are safe to install.

## 🎯 What This Add-on Does

After starting, this add-on will:

1. **Check for all updates** in your Home Assistant installation
2. **Analyze them** for conflicts and compatibility issues  
3. **Create sensor entities** you can view in Home Assistant
4. **Send notifications** with detailed analysis results
5. **Run daily** at your configured schedule

## 📊 How to View Your Results

### Sensors Created

When you start this add-on with `create_dashboard_entities: true` (the default), it creates **6 sensors**:

- `sensor.ha_sentry_update_status` - Overall safety status
- `sensor.ha_sentry_updates_available` - Total updates count
- `sensor.ha_sentry_addon_updates` - Add-on updates
- `sensor.ha_sentry_hacs_updates` - HACS/Integration updates
- `sensor.ha_sentry_issues` - Issues detected
- `sensor.ha_sentry_confidence` - Analysis confidence score

### Where to Find Them

**Step 1:** Go to **Developer Tools** → **States**  
**Step 2:** Search for `sensor.ha_sentry`  
**Step 3:** You'll see all 6 sensors with their current values

### Notifications

Look for the **notification bell icon** 🔔 in Home Assistant. You'll receive:
- A startup notification (once) explaining how to use the add-on
- Update analysis notifications (daily or when updates are detected)

### Create a Dashboard

Add this to any dashboard to see your sensors:

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

See [more examples](https://github.com/ian-morgan99/Home-Assistant-Sentry/blob/main/README.md#example-dashboard-card) in the documentation.

## ⚙️ Configuration

### Basic Setup (No AI Required)

```yaml
ai_enabled: false
check_schedule: "02:00"
create_dashboard_entities: true
check_all_updates: true
```

### With Local AI (Ollama)

```yaml
ai_enabled: true
ai_provider: "ollama"
ai_endpoint: "http://localhost:11434"
ai_model: "llama2"
check_schedule: "02:00"
create_dashboard_entities: true
```

## 🚀 Quick Start

1. **Configure** the add-on (see Configuration tab)
2. **Start** the add-on (see Info tab)
3. **Check notifications** 🔔 for the startup guide
4. **View sensors** at Developer Tools → States → Search `ha_sentry`
5. **Add to dashboard** using the example above

## 📖 Documentation

- **Full Documentation**: [DOCS.md](https://github.com/ian-morgan99/Home-Assistant-Sentry/blob/main/DOCS.md)
- **Quick Start Guide**: [QUICKSTART.md](https://github.com/ian-morgan99/Home-Assistant-Sentry/blob/main/QUICKSTART.md)
- **Examples**: [EXAMPLES.md](https://github.com/ian-morgan99/Home-Assistant-Sentry/blob/main/EXAMPLES.md)

## 🔧 Troubleshooting

### Not seeing sensors?

**Check the logs first!** Go to the add-on **Log** tab and look for errors.

**Common Issue: 401 Authentication Error**

If you see `Failed to update sensor: 401` in the logs:

1. The add-on cannot authenticate with Home Assistant
2. This prevents sensor creation and updates
3. **Solution**: Restart the add-on. If that doesn't work, restart Home Assistant.
4. The add-on requires `homeassistant_api: true` in config.json (already set by default)

**Other checks:**

1. Verify `create_dashboard_entities: true` in configuration
2. Wait for the first check cycle to complete (runs immediately on start)
3. Go to Developer Tools → States → Search for `sensor.ha_sentry`
4. Check the add-on logs for any other errors

### Not seeing dashboard?

The add-on **does NOT automatically create dashboard cards**. You need to manually add sensors to your dashboard using the YAML examples above. Set `auto_create_dashboard: false` (the default) as automatic dashboard creation has API permission limitations.

## 🆘 Support

- **GitHub Issues**: [Report a problem](https://github.com/ian-morgan99/Home-Assistant-Sentry/issues)
- **Documentation**: [Full docs](https://github.com/ian-morgan99/Home-Assistant-Sentry)
- **Logs**: Check the Log tab in this add-on for debugging
