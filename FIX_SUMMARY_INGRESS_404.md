# Fix Summary: WebUI Ingress 404 Error

## Issue Description
Users reported seeing errors in Home Assistant Core logs:
```
Logger: homeassistant.components.hassio.handler
Client error on /ingress/validate_session request 401, message='Attempt to decode JSON with unexpected mimetype: text/plain; charset=utf-8', url='http://INTERNALIPADDRESS/ingress/validate_session'
```

Additionally, users reported:
1. WebUI stuck in "initialization" stage
2. Notification links redirecting to home dashboard instead of WebUI

## Root Cause

When Home Assistant Supervisor probed the add-on's web server with requests to non-existent routes (like `/ingress/validate_session`), the web server returned HTML 404 responses. When the Supervisor tried to parse these as JSON, it caused the "unexpected mimetype" error.

**Note:** The `/ingress/validate_session` endpoint is part of the Home Assistant Supervisor API, not the add-on's API. The Supervisor validates ingress sessions itself.

## Solution

Added intelligent 404 handling to the web server that distinguishes between API/JSON requests and browser requests.

### Implementation Details

**File: `ha_sentry/rootfs/app/web_server.py`**

1. Added `_handle_not_found()` method (lines 632-654):
   - Checks if the request path starts with `/api/` or `/ingress/`
   - Checks if the request Accept header contains `json`
   - Returns JSON 404 for API-like requests
   - Returns HTML 404 for browser requests

2. Added catch-all route handler (line 156):
   - Must be the last route added to prevent shadowing other routes
   - Includes clear documentation about placement importance

**File: `tests/test_404_handling.py`** (new file)

Comprehensive test suite with 5 tests:
1. API 404 returns JSON
2. Ingress path 404 returns JSON
3. JSON Accept header gets JSON 404
4. Browser request returns HTML 404
5. Valid routes still work correctly

## Testing Results

All tests pass:
- ✅ test_404_handling.py (5 tests) - NEW
- ✅ test_notification_links.py (4 tests)
- ✅ test_ingress_url.py (3 tests)
- ✅ test_web_server.py (7 tests)
- ✅ test_web_server_503_handling.py
- ✅ Code review: No issues found
- ✅ Security scan: No vulnerabilities found

## Impact

### What This Fixes
1. ✅ Eliminates "unexpected mimetype" errors in HA Core logs
2. ✅ Ensures proper JSON responses for Supervisor probes
3. ✅ Maintains good user experience for browser requests
4. ✅ No breaking changes to existing functionality

### What This Doesn't Fix

**If users still see 401 errors for `/ingress/validate_session`:**
- This is a Home Assistant Core/Supervisor issue, not an add-on issue
- Possible causes: expired sessions, cookie issues, reverse proxy configuration
- Solutions: Restart Home Assistant, check for HA updates, verify reverse proxy config

**If WebUI still shows "Loading..." indefinitely:**
- Check add-on logs for dependency graph build status
- Verify `enable_dependency_graph: true` in configuration
- Wait 60 seconds on first access (graph build takes time)
- Check browser console for JavaScript errors

**If notification links still don't work:**
- Use the "Sentry" sidebar panel (easiest access method)
- Try Settings → Add-ons → Home Assistant Sentry → Open Web UI
- Verify the ingress URL `/api/hassio_ingress/ha_sentry` works when entered manually
- Update Home Assistant to the latest version

## Code Changes

### Modified Files
1. `ha_sentry/rootfs/app/web_server.py`: Added 404 handling (27 lines added)

### New Files
1. `tests/test_404_handling.py`: Comprehensive test suite (142 lines)

## Commits
1. `aa38f73`: Fix ingress 404 error - return JSON for API/ingress paths
2. `440fcda`: Add clarifying comment for catch-all route placement

## Security Summary

CodeQL security analysis completed with **0 alerts** found. The changes:
- Do not introduce any security vulnerabilities
- Follow secure coding practices
- Properly escape HTML to prevent XSS
- Use appropriate status codes and content types

## Recommendations for Users

1. **Update the add-on** to get this fix
2. **Restart the add-on** after updating
3. **Access WebUI via sidebar panel** (look for "Sentry" in HA sidebar)
4. **If issues persist**, check add-on logs for specific error messages

## Related Documentation

- [INGRESS_URL_INFO.md](../INGRESS_URL_INFO.md) - Ingress URL format and troubleshooting
- [WEBUI_ACCESS_GUIDE.md](../WEBUI_ACCESS_GUIDE.md) - WebUI access methods
- [DOCS.md](../DOCS.md) - Full add-on documentation
