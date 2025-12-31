# Home Assistant Ingress URL Information

## Correct URL Format

The **correct** ingress URL format for Home Assistant add-ons is:

```
/api/hassio_ingress/<addon_slug>
```

For Home Assistant Sentry, this is:

```
/api/hassio_ingress/ha_sentry
```

## Common Misconceptions

### ❌ Incorrect Format
Some users may expect URLs like:
- `/936f27fd_ha_sentry/ingress` (older/different format)
- `/ha_sentry/ingress` (missing API prefix)

These are **NOT** the correct format for modern Home Assistant add-ons with ingress enabled.

### ✅ Correct Usage

The add-on uses the standard Home Assistant ingress URL format everywhere:

1. **In notification links**: `/api/hassio_ingress/ha_sentry#whereused:component`
2. **In web UI access**: Accessible via the "Sentry" panel in the sidebar
3. **Direct access**: Settings → Add-ons → Home Assistant Sentry → Open Web UI

## How to Access the Web UI

### Method 1: Sidebar Panel (Recommended)
1. Look for the **"Sentry"** panel in your Home Assistant sidebar
2. Click it to open the dependency visualization interface
3. The dependency graph may take up to 60 seconds to build on first access

### Method 2: Add-on Page
1. Go to **Settings** → **Add-ons** → **Home Assistant Sentry**
2. Click the **Open Web UI** button
3. This opens the same interface as the sidebar panel

### Method 3: Direct URL (Advanced)
Navigate to: `http://your-homeassistant.local:8123/api/hassio_ingress/ha_sentry`

Replace `your-homeassistant.local:8123` with your Home Assistant URL.

## Troubleshooting

### "Loading components..." Never Finishes

If the web UI shows "Loading components..." for more than 60 seconds:

1. **Check Add-on Logs**:
   - Go to Settings → Add-ons → Home Assistant Sentry → Log
   - Look for "Dependency graph built successfully" message
   - If not present, look for error messages

2. **Common Causes**:
   - Dependency graph is still building (can take 60+ seconds on first run)
   - Integration paths are not accessible
   - File system permissions issues

3. **Solutions**:
   - Wait 60 seconds and refresh the page
   - Check that `enable_dependency_graph: true` in configuration
   - Review add-on logs for specific error messages

### 404 Error When Accessing Web UI

If you get a 404 error:

1. **Verify Add-on is Running**:
   - Check that the add-on is started
   - Verify logs show "Dependency tree visualization started successfully"

2. **Verify Configuration**:
   - Check that `enable_web_ui: true` in configuration
   - Ensure `ingress: true` in config.yaml (should be default)

3. **Try Alternative Access Methods**:
   - Use the sidebar panel instead of direct URL
   - Use "Open Web UI" button from add-on page

## Technical Details

### Why This URL Format?

Home Assistant's ingress system provides secure, authenticated access to add-on web interfaces without exposing additional ports. The `/api/hassio_ingress/<slug>` format:

- Routes through Home Assistant's authentication
- Works with SSL/TLS if configured
- No additional port forwarding needed
- Consistent across all add-ons

### URL Fragment Support

The web UI supports deep linking via URL fragments:

- **Dependencies**: `/api/hassio_ingress/ha_sentry#dependency:component_name`
- **Where Used**: `/api/hassio_ingress/ha_sentry#whereused:component_name`
- **Impact Analysis**: `/api/hassio_ingress/ha_sentry#impact:comp1,comp2,comp3`

These are used in notification links to provide direct navigation to specific components.

## Related Documentation

- [DOCS.md](DOCS.md) - Full configuration and usage documentation
- [FEATURE_NOTIFICATION_LINKS.md](FEATURE_NOTIFICATION_LINKS.md) - Deep linking feature details
- [QUICKSTART.md](QUICKSTART.md) - Quick start guide
