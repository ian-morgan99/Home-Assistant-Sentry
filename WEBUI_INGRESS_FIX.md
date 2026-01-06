# WebUI Ingress Routing Fix

## Problem Description

Users reported that the WebUI would get stuck on "Preparing status..." and never load when accessed through Home Assistant's ingress system (via the Sentry sidebar panel or `/api/hassio_ingress/ha_sentry`).

## Root Cause

The JavaScript `getApiUrl()` function was building **absolute URLs** by combining `window.location.origin` with `window.location.pathname`:

```javascript
// Old implementation
const pathname = window.location.pathname || '/';
const basePath = pathname.endsWith('/') ? pathname : pathname + '/';
const base = window.location.origin + basePath;
return new URL(sanitizedPath, base).toString();
```

This worked fine for direct access on port 8099, but failed with Home Assistant ingress because:

1. **Browser URL**: `http://homeassistant.local:8123/api/hassio_ingress/ha_sentry/`
2. **HA Ingress Proxy**: Strips the `/api/hassio_ingress/ha_sentry` prefix before forwarding to add-on
3. **Add-on sees**: Requests coming to `http://localhost:8099/`
4. **JavaScript sees**: `window.location.pathname = "/"` (the proxy strips the prefix)
5. **API calls built**: `http://homeassistant.local:8123/api/status` (WRONG! Missing ingress prefix)
6. **Expected**: `http://homeassistant.local:8123/api/hassio_ingress/ha_sentry/api/status`

The JavaScript had no way to know about the stripped ingress prefix, causing all API calls to 404.

## Solution

Changed `getApiUrl()` to return **relative URLs** instead of absolute URLs:

```javascript
// New implementation
const sanitizedPath = decodedPath
    .replace(/^\/+/, '')
    .replace(/\/{2,}/g, '/');
return sanitizedPath;  // Just return the relative path
```

When `fetch()` receives a relative URL, the browser automatically resolves it relative to the current page URL:

- **Direct access**: `fetch('api/status')` from `http://localhost:8099/` → `http://localhost:8099/api/status` ✓
- **Ingress access**: `fetch('api/status')` from `http://ha:8123/api/hassio_ingress/ha_sentry/` → `http://ha:8123/api/hassio_ingress/ha_sentry/api/status` ✓

## Technical Details

### How Home Assistant Ingress Works

1. **User accesses**: `http://homeassistant:8123/api/hassio_ingress/ha_sentry/`
2. **HA Supervisor**: Proxies request to add-on at `http://localhost:8099/`
3. **Proxy behavior**: Strips `/api/hassio_ingress/ha_sentry` prefix from forwarded requests
4. **Add-on response**: Returns HTML page
5. **JavaScript in browser**: Still at `http://homeassistant:8123/api/hassio_ingress/ha_sentry/`
6. **Relative fetch calls**: Browser automatically prepends the current page's path

### Why Relative URLs Work

The browser's `fetch()` API resolves relative URLs according to the **current page's URL**, not where the server thinks it is:

```javascript
// Current page: http://ha:8123/api/hassio_ingress/ha_sentry/index.html
fetch('api/status')
// Browser resolves to: http://ha:8123/api/hassio_ingress/ha_sentry/api/status
// Proxy forwards to add-on as: http://localhost:8099/api/status
```

This works identically for direct access:

```javascript
// Current page: http://localhost:8099/index.html
fetch('api/status')
// Browser resolves to: http://localhost:8099/api/status
```

## Files Changed

### 1. `ha_sentry/rootfs/app/web_server.py`

**Modified `getApiUrl()` function** (lines 1189-1225):
- Removed absolute URL construction using `new URL()`
- Now returns sanitized relative path only
- Updated function documentation to explain ingress compatibility

**Fixed syntax warning** (line 664):
- Changed HTML string from `"""` to `r"""` (raw string)
- Prevents Python from interpreting backslashes in JavaScript regex patterns

### 2. `tests/test_get_api_url.py`

**Updated test expectations**:
- Changed from expecting absolute URLs to relative URLs
- Updated Node.js test implementation to match new function
- All tests still pass with new behavior

### 3. `ha_sentry/rootfs/app/sentry_service.py`

**Added documentation** (lines 37-41):
- Clarified that `WEB_UI_PORT` must match config files
- Explained that port is NOT user-configurable

### 4. `tests/test_webui_ingress_path_resolution.py` (NEW)

**Created comprehensive test suite**:
- Tests URL resolution for multiple scenarios
- Python-based implementation for easier debugging
- Validates both direct and ingress access patterns

## Testing

### Automated Tests

All tests pass:
```bash
✓ test_get_api_url.py - Validates getApiUrl() security and path handling
✓ test_webui_ingress_path_resolution.py - Validates ingress compatibility
✓ test_basic.py - Basic functionality tests
```

### Manual Testing Scenarios

**Scenario 1: Direct Access (Port 8099)**
- URL: `http://localhost:8099/`
- Expected: WebUI loads, API calls work
- Result: ✓ Works

**Scenario 2: Ingress via Sidebar Panel**
- Access: Click "Sentry" in HA sidebar
- Expected: WebUI loads, API calls work through ingress
- Result: ✓ Should work (requires HA environment to verify)

**Scenario 3: Ingress via Direct URL**
- URL: `http://homeassistant:8123/api/hassio_ingress/ha_sentry/`
- Expected: WebUI loads, API calls work through ingress
- Result: ✓ Should work (requires HA environment to verify)

## Migration Notes

### For Users

No action required. The fix is transparent:
- Update the add-on to get the fix
- Restart the add-on
- WebUI should now work via all access methods

### For Developers

If you've been working around the ingress issue:
1. Remove any proxy or redirect workarounds
2. The fix makes ingress access work as designed
3. Both direct and ingress access now use the same code path

## Port Configuration

Note: The port (8099) is **NOT user-configurable**. This is by design:

- `ingress_port` in `config.json`/`config.yaml` is **add-on metadata**, not user config
- It tells Home Assistant Supervisor which port to proxy to
- Changing it requires code changes in multiple places:
  - `ha_sentry/config.json` → `ingress_port`
  - `ha_sentry/config.yaml` → `ingress_port`  
  - `ha_sentry/rootfs/app/sentry_service.py` → `WEB_UI_PORT`

To make the port user-configurable would require:
1. Adding a schema option in config files
2. Reading the option in `config_manager.py`
3. Passing it to `SentryService`
4. Updating `ingress_port` dynamically (not supported by HA)

This is not recommended because Home Assistant's ingress system expects a fixed port.

## Related Issues

- GitHub Issue #126: "Webui still not working - Stuck in Preparing status…"
- GitHub Issue #128: "WebUI still doesn't work after PR #127"
- GitHub PR #127: Fixed AI timeout blocking startup (secondary issue)

## References

- [Home Assistant Add-on Documentation](https://developers.home-assistant.io/docs/add-ons/)
- [Ingress Documentation](https://developers.home-assistant.io/docs/add-ons/presentation/#ingress)
- [MDN: Using Fetch - Relative URLs](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch)
