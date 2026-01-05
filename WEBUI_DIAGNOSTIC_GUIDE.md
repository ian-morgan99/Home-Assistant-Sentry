# Web UI Diagnostic Guide

## Issue: Web UI Stuck on "Preparing status..."

This guide explains how to use the new diagnostic features to identify why the Web UI gets stuck.

## What We Added

### 1. Immediate JavaScript Execution Test
As soon as the script loads (before the page is fully ready), it will try to update the status text to:
```
JavaScript is executing... waiting for DOM ready
```

**What this tells us:**
- ✅ If you see this text: JavaScript IS executing in your browser
- ❌ If you still see "Preparing status...": JavaScript is NOT executing (browser blocking it)

### 2. Console Logging
Open your browser's Developer Tools (F12) and check the Console tab for messages:

#### Expected Console Messages (if everything works):
```
[INIT] Script block executing immediately
[INIT] Successfully updated status-detail element
Web UI loaded
  URL: <your url>
  Path: <your path>
  Hash: <any fragment>
[API] Fetching status from: <status api url>
[API] Status response received: 200 OK
[API] Fetching components from: <components api url>
[API] Components response received: 200 OK
```

#### Error Messages to Look For:
- `CRITICAL: DOMContentLoaded handler failed` - JavaScript error during initialization
- `CRITICAL: Failed to attach DOMContentLoaded listener` - Browser security blocking JavaScript
- `Unsafe API path detected` - URL generation problem
- `Failed to load components: <error>` - API call failed

### 3. Diagnostic Panel
If errors occur, a diagnostic panel will appear automatically showing:
- Timestamp of each step
- Error messages with details
- Suggestions for fixing the issue

You can also manually show/hide the diagnostic panel by clicking the toggle button.

### 4. Network Tab Inspection
In Developer Tools, go to the Network tab and look for:
- `GET /api/status` - Should return 200 with JSON containing `status`, `components_count`, `ready`
- `GET /api/components` - Should return 200 with JSON containing array of components

**If these requests don't appear:** JavaScript is not making API calls (could be URL issue or execution problem)

## How to Test

### Step 1: Deploy Updated Add-on
1. Pull the latest changes from the `copilot/analyse-webui-logs` branch
2. Restart the Home Assistant Sentry add-on
3. Wait for it to fully start (check add-on logs)

### Step 2: Open Web UI
Access the Web UI via any method:
- ✅ Local: `http://homeassistant.local:8123/936f27fd_ha_sentry` (via HA ingress)
- ✅ Direct: `http://<ha-ip>:8099` (direct to add-on)
- ✅ Remote: Via Nabu Casa Cloud URL

### Step 3: Immediately Check Status Text
Look at the status text under the "Home Assistant Sentry" heading. Within 1 second, it should change from:
```
Preparing status...
```
to:
```
JavaScript is executing... waiting for DOM ready
```

### Step 4: Open Developer Tools
Press F12 (or Cmd+Option+I on Mac) to open Developer Tools

#### Check Console Tab:
1. Look for `[INIT]` messages
2. Look for `[API]` messages  
3. Look for any error messages (red text)
4. Copy ALL console output

#### Check Network Tab:
1. Refresh the page if needed
2. Look for requests to `/api/status` and `/api/components`
3. Click on each request to see:
   - Status code (should be 200)
   - Response body (should be JSON)
   - Any error messages

### Step 5: Check Add-on Logs
In Home Assistant:
1. Go to Settings → Add-ons → Home Assistant Sentry
2. Click the "Log" tab
3. Look for lines containing:
   ```
   web_server - DEBUG - Web UI accessed from:
   web_server - DEBUG - Request path: /
   web_server - DEBUG - Request path: /api/status
   web_server - DEBUG - Request path: /api/components
   ```

### Step 6: Report Back
Please provide:
1. **What status text you see** (exact text)
2. **Full console output** (copy/paste)
3. **Network tab screenshot** showing API requests (or lack thereof)
4. **Add-on logs** showing web server access (last 50 lines)
5. **How you accessed the UI** (local ingress, direct, or Nabu Casa)

## Expected Behavior vs. Issues

### ✅ Working Correctly
- Status text changes immediately to "JavaScript is executing..."
- Console shows `[INIT]` and `[API]` messages
- Network tab shows `/api/status` and `/api/components` requests
- Add-on logs show corresponding requests
- Eventually shows "X components loaded" status

### ❌ JavaScript Not Executing
- Status text stays "Preparing status..."
- No console messages
- No network requests
- Possible causes:
  - Content Security Policy blocking JavaScript
  - Browser security settings
  - Ad blocker interfering
  - Proxy/ingress stripping JavaScript

### ❌ JavaScript Executes but API Fails
- Status text changes to "JavaScript is executing..."
- Console shows `[INIT]` messages
- Console shows `[API]` messages with errors
- Network tab may show failed requests or no requests
- Possible causes:
  - Incorrect URL generation (ingress path issue)
  - CORS blocking requests
  - Proxy not forwarding API requests

### ❌ API Works but Components Empty
- Status text progresses through initialization
- Console and network show successful API calls
- Status shows "No integrations found" or "0 components"
- Possible causes:
  - Dependency graph build failed
  - Integration paths incorrect
  - Race condition during graph building

## Common Fixes

### Fix 1: JavaScript Blocked
**Symptoms:** Status never changes from "Preparing status...", no console messages

**Solutions:**
1. Disable ad blockers for Home Assistant domain
2. Check browser console for security errors
3. Try a different browser
4. Access via local ingress instead of Nabu Casa

### Fix 2: API Calls Blocked
**Symptoms:** JavaScript runs but no API requests appear

**Solutions:**
1. Check Home Assistant ingress configuration
2. Verify add-on is running on correct port (8099)
3. Check for proxy/reverse proxy configuration issues
4. Try direct access on port 8099

### Fix 3: Components Not Loading
**Symptoms:** API works but shows 0 components

**Solutions:**
1. Check add-on logs for dependency graph build errors
2. Verify `enable_dependency_graph: true` in configuration
3. Check custom_integration_paths if configured
4. See "No Integrations Found" error message in UI for specific guidance

## Need More Help?

If diagnostics show something unexpected, please open a GitHub issue with:
1. All information from Step 6 above
2. Screenshots of browser console and network tab
3. Add-on configuration (sanitize any sensitive data)
4. Home Assistant version and installation type (OS, Container, Core, Supervised)

The diagnostic information will help us quickly identify and fix the root cause!
