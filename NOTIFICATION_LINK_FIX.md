# Notification Link Fix Summary

## Issue
Notification links to the Sentry Web UI were redirecting users to the Home Assistant dashboard (`/lovelace/default_view`) instead of opening the Sentry add-on Web UI.

## Root Cause
The code was generating ingress URLs using the **backend proxy route** format `/api/hassio_ingress/{addon_slug}/` instead of the **frontend navigation route** format `/hassio/ingress/{addon_slug}/`.

### Home Assistant Ingress URL Formats

Home Assistant uses two different ingress URL formats:

1. **Frontend Navigation Route**: `/hassio/ingress/{addon_slug}/`
   - Used for: Notification links, frontend navigation, sidebar panels
   - Keeps the Home Assistant interface chrome (header, sidebar)
   - Opens in the existing Home Assistant interface
   - **This is what notification markdown links need to use**

2. **Backend Proxy Route**: `/api/hassio_ingress/{token}/`
   - Used for: Backend API requests, internal proxying
   - The frontend router uses this internally after routing
   - Not reliable for direct user-facing links

## The Fix

### Code Changes

**File: `ha_sentry/rootfs/app/sentry_service.py`**

Changed the `_get_ingress_url()` method from:
```python
base_url = f"/api/hassio_ingress/{self.ADDON_SLUG}/"
```

To:
```python
base_url = f"/hassio/ingress/{self.ADDON_SLUG}/"
```

### Before and After

**Before:**
```markdown
[🛡️ Open WebUI](/api/hassio_ingress/ha_sentry/)
[🔍 View Dependencies](/api/hassio_ingress/ha_sentry/?mode=whereused&component=mosquitto)
```

**After:**
```markdown
[🛡️ Open WebUI](/hassio/ingress/ha_sentry/)
[🔍 View Dependencies](/hassio/ingress/ha_sentry/?mode=whereused&component=mosquitto)
```

## Files Modified

1. **ha_sentry/rootfs/app/sentry_service.py**
   - Updated `_get_ingress_url()` to use frontend navigation format
   - Updated startup notification with correct URL
   - Added detailed comments explaining the URL format differences

2. **tests/test_notification_links.py**
   - Updated expected URL patterns
   - Verified frontend navigation format is used

3. **tests/test_ingress_url.py**
   - Updated mock URL generation
   - Updated test expectations

4. **tests/test_notification_url_format.py** (NEW)
   - Comprehensive tests for URL generation
   - Markdown link format verification
   - Code verification to ensure correct format

5. **INGRESS_URL_INFO.md**
   - Clarified frontend vs backend URL formats
   - Updated all examples
   - Added detailed explanations

## Testing

All tests pass:
- ✅ `test_notification_links.py` - 4 tests passed
- ✅ `test_ingress_url.py` - 3 tests passed
- ✅ `test_notification_url_format.py` - 3 tests passed
- ✅ Code review completed - 1 minor issue addressed
- ✅ CodeQL security scan - 0 alerts

## Impact

### User Experience
- Clicking notification links now opens the Sentry Web UI correctly
- No more redirects to the Home Assistant dashboard
- Maintains Home Assistant interface chrome (sidebar, header)

### Backward Compatibility
- The fix only affects notification markdown links
- The Web UI continues to work via all existing access methods:
  - Sidebar panel ("Sentry" panel)
  - Add-on settings page ("Open Web UI" button)
  - Direct URL navigation

### URL Parameters
Query parameters are still supported for deep linking:
- Basic: `/hassio/ingress/ha_sentry/`
- Where-used: `/hassio/ingress/ha_sentry/?mode=whereused&component=mosquitto`
- Impact: `/hassio/ingress/ha_sentry/?mode=impact&component=comp1,comp2`

## Deployment

Users should:
1. Update to the new version of the add-on
2. Restart the add-on
3. Test notification links - they should now work correctly

If issues persist, users can still access the Web UI via:
- Sidebar panel: Look for "Sentry" in the sidebar
- Add-on page: Settings → Add-ons → Home Assistant Sentry → Open Web UI

## References

- Home Assistant Ingress Documentation: https://developers.home-assistant.io/docs/add-ons/presentation/#ingress
- GitHub Issue: "Webui links still don't work from notification bar"
- Related discussions: https://github.com/home-assistant/frontend/issues/28041

## Verification

To verify the fix works:
1. Trigger an update check that finds updates
2. Wait for notification to appear
3. Click any link in the notification (e.g., "Open WebUI", "View Dependencies")
4. Verify: Should open Sentry Web UI, not Home Assistant dashboard
5. Verify: URL bar should show `/hassio/ingress/ha_sentry/`

## Technical Notes

### Why This Matters
- Home Assistant's persistent notification markdown links require frontend navigation URLs
- The backend API proxy URLs (`/api/hassio_ingress/`) may not have proper session/routing context when clicked from notifications
- Frontend URLs (`/hassio/ingress/`) are handled by HA's router and properly maintain session state

### URL Format Deep Dive
When you click a sidebar panel, HA's frontend router:
1. Receives click on frontend URL: `/hassio/ingress/ha_sentry/`
2. Internally routes to backend proxy: `/api/hassio_ingress/{session_token}/`
3. Backend proxy forwards to add-on on port 8099

When you click a notification link with backend URL:
1. Browser navigates to: `/api/hassio_ingress/ha_sentry/`
2. No frontend router context - may cause redirect
3. Session/auth may not be properly established

When you click a notification link with frontend URL:
1. Browser navigates to: `/hassio/ingress/ha_sentry/`
2. Frontend router handles routing ✅
3. Properly establishes session and loads add-on UI ✅
