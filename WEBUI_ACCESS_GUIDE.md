# WebUI Access Guide

## Issue Resolution Summary

This document explains the changes made to address WebUI access issues and clarify the deprecation of dashboard auto-creation.

## What Was Fixed

### 1. Dashboard Auto-Creation Deprecated

**Problem**: Users were confused about dashboard creation failing with 404 errors, even though this is expected behavior.

**Solution**: Added prominent warnings throughout the codebase:
- **config.yaml**: Clear deprecation notice explaining dashboard creation doesn't work
- **sentry_service.py**: Warning box displayed when dashboard creation is attempted
- **dashboard_manager.py**: Deprecation warning in the method itself
- **ha_client.py**: Prominent warning before attempting API call

**Result**: Users now understand dashboard creation is deprecated and should use WebUI instead.

### 2. Improved WebUI Access Instructions

**Problem**: Users were unclear on how to access the WebUI.

**Solution**: Enhanced startup notification with three clear access methods:
1. **Sidebar Panel** (preferred): Look for "Sentry" in the Home Assistant sidebar
2. **Add-on Settings**: Settings → Add-ons → Home Assistant Sentry → Open Web UI
3. **Direct Ingress URL**: `/hassio/ingress/ha_sentry/`

**Result**: Clear, step-by-step instructions for accessing the WebUI.

### 3. Clarified Notification Links

**Problem**: Notification links were not clearly explained.

**Solution**: 
- All notification links use ingress URL format: `/hassio/ingress/ha_sentry/`
- Added "Alternative Access Methods" section in notifications
- Emphasized sidebar panel as the easiest access method

**Result**: Users understand all links point to WebUI, not a dashboard.

## How to Access the WebUI

### Method 1: Sidebar Panel (Easiest)
1. Open your Home Assistant
2. Look for the **"Sentry"** panel in the left sidebar
3. Click to open the WebUI

### Method 2: Via Add-on Settings
1. Go to **Settings** → **Add-ons**
2. Find **Home Assistant Sentry**
3. Click **Open Web UI** button

### Method 3: Direct Browser Access
Navigate to: `http://your-home-assistant-address:PORT`

Default PORT is 8099. This can be customized in the add-on configuration.

### Method 4: Direct Ingress URL
Navigate to: `/hassio/ingress/ha_sentry/`

Or click links in notifications that look like:
- `[🛡️ Open WebUI](/hassio/ingress/ha_sentry/)`
- `[🔍 View Impact](/hassio/ingress/ha_sentry/?mode=whereused&component=component_name)`

## WebUI Port Configuration

The WebUI supports flexible port configuration with dual-port mode:

### Understanding Dual-Port Mode

The add-on can listen on two ports simultaneously to support both Home Assistant ingress and direct browser access:

1. **Ingress Port (8099)** - Always Active
   - Required for Home Assistant sidebar panel integration
   - Used by Methods 1, 2, and 4 above
   - Fixed at port 8099 (HA Supervisor requirement)
   - Cannot be changed

2. **Direct Access Port** - User Configurable
   - Used for Method 3 (direct browser access)
   - Default: 8099 (single port mode)
   - Can be changed to any port 1024-65535
   - Useful if port 8099 conflicts with another service

### Configuration Examples

**Default (Single Port Mode):**
```yaml
port: 8099
```
- Sidebar panel works ✅
- Direct access: `http://homeassistant:8099` ✅
- Single web server instance

**Custom Port (Dual Port Mode):**
```yaml
port: 8098
```
- Sidebar panel **still works** ✅ (uses port 8099 internally)
- Direct access: `http://homeassistant:8098` ✅
- Two web server instances running

### When to Use Custom Port

Change the default port if:
- Port 8099 is already in use by another service
- You want direct browser access on a different port
- You need to avoid port conflicts on your system

**Important**: The sidebar panel (Method 1) and add-on "Open Web UI" button (Method 2) will always work regardless of your `port` setting, as they use Home Assistant's internal ingress routing on port 8099.

## Configuration Changes Required

### Disable Dashboard Auto-Creation

The configuration is correct - no changes needed:

```yaml
enable_web_ui: true  # Keep enabled for WebUI access
```

Note: The `auto_create_dashboard` option has been removed as it never worked.

### Why Dashboard Creation Doesn't Work

Home Assistant add-ons do not have permission to create Lovelace dashboards via the API. This is a limitation of the Home Assistant architecture, not a bug in the add-on.

The API endpoint `/api/lovelace/dashboards` returns 404 or 403 errors when accessed from add-ons.

**Workaround**: Use the built-in WebUI which provides:
- Full dependency visualization
- Interactive graphs
- "Where Used" analysis
- Change impact reports
- All features that the dashboard would have provided

## Verification

### Confirm Ingress is Working

Run the test to verify ingress configuration:

```bash
python3 tests/test_ingress_url.py
```

Expected output:
```
✓ Ingress URL generation test passed
  Base URL: /hassio/ingress/ha_sentry/
✓ Addon slug consistency test passed
✓ Ingress configuration test passed
```

### Check Your Configuration

Verify your `config.json` has:
```json
{
  "slug": "ha_sentry",
  "ingress": true,
  "ingress_port": 8099,
  "panel_icon": "mdi:family-tree",
  "panel_title": "Sentry"
}
```

## Troubleshooting

### "I don't see the Sentry panel in my sidebar"

1. Restart the add-on
2. Refresh your browser (Ctrl+F5)
3. Check add-on logs for errors
4. Verify `ingress: true` in config.json

### "The WebUI link doesn't work"

1. Try the sidebar panel instead (most reliable)
2. Try: Settings → Add-ons → Home Assistant Sentry → Open Web UI
3. Check if you're using a reverse proxy that might interfere
4. Verify the add-on is running and port 8099 is accessible

### "I see dashboard creation errors in old logs"

The `auto_create_dashboard` option has been removed. If you're seeing these errors in old logs, they can be safely ignored. Update to the latest version and the errors will no longer occur.

## Technical Details

### Ingress URL Format

The add-on uses the standard Home Assistant ingress format for frontend navigation:
```
/hassio/ingress/{addon_slug}/
```

For this add-on:
```
/hassio/ingress/ha_sentry/
```

Note: The backend proxy route `/api/hassio_ingress/ha_sentry` is used internally by Home Assistant but should not be used directly for navigation.

### URL Parameters

The WebUI supports URL fragments for direct navigation:
- `#whereused:component_name` - Show "Where Used" view for a component
- `#impact:comp1,comp2` - Show impact report for multiple components

Example:
```
/hassio/ingress/ha_sentry/?mode=whereused&component=powercalc
```

### Addon Slug

The addon slug `ha_sentry` is consistent across:
- config.json (`"slug": "ha_sentry"`)
- config.yaml (`slug: ha_sentry`)
- Python code (`ADDON_SLUG = 'ha_sentry'`)

## Summary

**Bottom Line**: 
1. The `auto_create_dashboard` option has been removed
2. Access WebUI via sidebar panel labeled "Sentry"
3. All functionality is available in the WebUI
4. Dashboard auto-creation never worked and is no longer an option

The WebUI provides all features and more than a dashboard would have provided.
