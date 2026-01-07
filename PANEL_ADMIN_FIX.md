# WebUI Ingress Fix: Adding panel_admin Configuration

## Issue Description

Users reported that the WebUI would not work when accessed through Home Assistant's ingress system, with the Supervisor showing the error:

> "Unable to fetch add-on info to start Ingress"

## Root Cause

The add-on configuration was missing the `panel_admin` field, which is recommended by Home Assistant for add-ons using ingress. While this field is optional, its absence can cause ambiguity in the Supervisor's handling of the add-on panel, potentially leading to connection issues when setting up ingress.

## Solution

Added `panel_admin: true` to both configuration files:

### Changes Made

1. **ha_sentry/config.json**
   - Added `"panel_admin": true` after `panel_title`
   - This restricts the panel to admin users only

2. **ha_sentry/config.yaml**
   - Added `panel_admin: true` after `panel_title`
   - Matches the JSON configuration

### Why panel_admin: true?

Home Assistant Sentry is an administrative tool that:
- Analyzes system updates (Core, Supervisor, OS)
- Reviews add-on and integration updates
- Provides AI-powered conflict detection
- Recommends whether updates are safe to install

Since this tool provides administrative insights and recommendations, it's appropriate to restrict access to administrators only.

## Configuration Reference

### Before
```json
{
  "ingress": true,
  "ingress_port": 8099,
  "panel_icon": "mdi:family-tree",
  "panel_title": "Sentry",
  "ports": {
    "8099/tcp": 8099
  }
}
```

### After
```json
{
  "ingress": true,
  "ingress_port": 8099,
  "panel_icon": "mdi:family-tree",
  "panel_title": "Sentry",
  "panel_admin": true,
  "ports": {
    "8099/tcp": 8099
  }
}
```

## What is panel_admin?

According to Home Assistant add-on documentation:

- **`panel_admin: true`**: The sidebar panel is only visible to users with admin privileges
- **`panel_admin: false`**: The panel is visible to all users
- **Not specified (default)**: Behavior may be ambiguous, potentially causing Supervisor issues

## Testing

### Automated Tests

Created `tests/test_panel_admin_config.py` which verifies:
- `panel_admin` field exists in config.json
- `panel_admin` field exists in config.yaml
- Both files have consistent values
- All ingress-related fields are properly configured

Test results:
```
✓ panel_admin configuration test passed for config.json
✓ panel_admin configuration test passed for config.yaml
✓ Configuration consistency test passed
```

### Existing Tests

All existing tests continue to pass:
```
✓ test_ingress_url.py - Ingress URL generation
✓ test_basic.py - Basic functionality (except aiohttp import)
```

## Expected Behavior After Fix

1. **For Administrators:**
   - "Sentry" panel appears in Home Assistant sidebar
   - Clicking the panel opens the WebUI through ingress
   - All API calls work correctly through ingress proxy
   - No "Unable to fetch add-on info" errors

2. **For Non-Admin Users:**
   - "Sentry" panel does NOT appear in sidebar (restricted to admins)
   - Users can still access via direct port 8099 if exposed

## Migration Notes

### For Users

**No action required** - the fix is transparent:
1. Update the add-on to the version with this fix
2. Restart the add-on
3. The "Sentry" panel should now work correctly in the sidebar

### For Developers

This change is backward compatible:
- No code changes required
- No API changes
- Only add-on metadata updated
- Users who already have working setups will see no change

## Related Files

- `ha_sentry/config.json` - JSON configuration with panel_admin
- `ha_sentry/config.yaml` - YAML configuration with panel_admin
- `tests/test_panel_admin_config.py` - New test for panel_admin validation
- `tests/test_ingress_url.py` - Existing test for ingress URL generation

## References

- [Home Assistant Add-on Configuration Docs](https://developers.home-assistant.io/docs/add-ons/configuration/)
- [Home Assistant Ingress Documentation](https://developers.home-assistant.io/docs/add-ons/presentation/#ingress)
- Previous fix: Relative URLs for ingress compatibility (already implemented)

## Summary

Adding the `panel_admin: true` field provides explicit configuration for Home Assistant Supervisor about how to handle the add-on's panel. This resolves ambiguity that could cause the "Unable to fetch add-on info to start Ingress" error and ensures the panel is only shown to administrators, which is appropriate for this administrative tool.

The fix is minimal, well-tested, and maintains backward compatibility while resolving the ingress connectivity issue.
