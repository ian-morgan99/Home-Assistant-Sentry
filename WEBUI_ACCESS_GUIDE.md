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
3. **Direct Ingress URL**: `/api/hassio_ingress/ha_sentry`

**Result**: Clear, step-by-step instructions for accessing the WebUI.

### 3. Clarified Notification Links

**Problem**: Notification links were not clearly explained.

**Solution**: 
- All notification links use ingress URL format: `/api/hassio_ingress/ha_sentry`
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

### Method 3: Direct URL
Navigate to: `/api/hassio_ingress/ha_sentry`

Or click links in notifications that look like:
- `[🛡️ Open WebUI](/api/hassio_ingress/ha_sentry)`
- `[🔍 View Impact](/api/hassio_ingress/ha_sentry#whereused:component_name)`

## Configuration Changes Required

### Disable Dashboard Auto-Creation

Edit your add-on configuration and set:

```yaml
auto_create_dashboard: false  # REQUIRED - dashboard creation doesn't work
enable_web_ui: true           # Keep enabled for WebUI access
```

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
  Base URL: /api/hassio_ingress/ha_sentry
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

### "I still see dashboard creation errors"

This is expected if you have `auto_create_dashboard: true`. To stop seeing these errors:

1. Set `auto_create_dashboard: false` in add-on configuration
2. Restart the add-on
3. Use the WebUI instead

## Technical Details

### Ingress URL Format

The add-on uses the standard Home Assistant ingress format:
```
/api/hassio_ingress/{addon_slug}
```

For this add-on:
```
/api/hassio_ingress/ha_sentry
```

### URL Parameters

The WebUI supports URL fragments for direct navigation:
- `#whereused:component_name` - Show "Where Used" view for a component
- `#impact:comp1,comp2` - Show impact report for multiple components

Example:
```
/api/hassio_ingress/ha_sentry#whereused:powercalc
```

### Addon Slug

The addon slug `ha_sentry` is consistent across:
- config.json (`"slug": "ha_sentry"`)
- config.yaml (`slug: ha_sentry`)
- Python code (`ADDON_SLUG = 'ha_sentry'`)

## Summary

**Bottom Line**: 
1. Set `auto_create_dashboard: false`
2. Access WebUI via sidebar panel labeled "Sentry"
3. All functionality is available in the WebUI
4. Dashboard creation is deprecated and will not work

The WebUI provides all features and more than the dashboard would have provided.
