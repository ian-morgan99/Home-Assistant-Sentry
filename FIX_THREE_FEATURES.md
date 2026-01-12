# Fix Summary: Three Non-Working Features

**Issue Date:** 2026-01-12  
**Affected Versions:** 2.0.10 and earlier  
**Fixed in:** 2.0.11+

## Issues Fixed

### 1. WebUI Links from Notifications Not Working

**Problem:**  
When users clicked links in notifications to access the WebUI, they were redirected to the add-on selection screen instead of the Sentry WebUI.

**Root Cause:**  
Home Assistant's persistent notification system doesn't always handle markdown links reliably, especially:
- Relative URLs may not navigate correctly
- Link behavior varies between HA versions
- Some mobile apps don't handle ingress links in notifications

**Solution:**  
- Removed reliance on clickable markdown links
- Provided clear step-by-step access instructions in notification text
- Emphasized sidebar panel access (most reliable)
- Added fallback method via Settings → Add-ons

**Before:**
```markdown
- [🛡️ Open WebUI](/hassio/ingress/ha_sentry/) - Full dependency visualization
```

**After:**
```markdown
How to Access WebUI:
1. Via Sidebar Panel (Recommended): Look for the 'Sentry' panel in your sidebar
2. Via Add-on Settings: Settings → Add-ons → Home Assistant Sentry → Open Web UI
```

---

### 2. Installation Review Feature Not Being Presented

**Problem:**  
When users enabled `enable_installation_review: true` in the add-on configuration, the logs still showed the feature as disabled.

**Root Cause:**  
The `run.sh` script was missing the environment variable exports for the three installation review configuration options:
- `ENABLE_INSTALLATION_REVIEW`
- `INSTALLATION_REVIEW_SCHEDULE`
- `INSTALLATION_REVIEW_SCOPE`

Without these exports, the Python code always saw the default values (disabled).

**Solution:**  
Added the missing environment variable exports to `run.sh`:

```bash
export ENABLE_INSTALLATION_REVIEW=$(bashio::config 'enable_installation_review')
export INSTALLATION_REVIEW_SCHEDULE=$(bashio::config 'installation_review_schedule')
export INSTALLATION_REVIEW_SCOPE=$(bashio::config 'installation_review_scope')
```

Also added enhanced logging:

**When Enabled:**
```
============================================================
INSTALLATION REVIEW FEATURE ENABLED
============================================================
  Schedule: weekly
  Scope: full
  AI-powered: true
Installation reviews will analyze your HA setup and provide recommendations
============================================================
```

**When Disabled:**
```
Installation review feature is disabled in configuration
  enable_installation_review: False
  To enable: Set 'enable_installation_review: true' in add-on config
```

---

### 3. Log Comparison Doesn't Work After HA Restarts

**Problem:**  
Home Assistant clears its logs on restart, and many updates require a restart. This meant that after updating and restarting, the "old" logs were gone, making before/after comparison impossible.

**Root Cause:**  
The log monitor only saved `previous_logs.json` which was overwritten on each check. When HA restarted and cleared its logs, the new check would have very few or no error logs, making comparison meaningless.

**Solution:**  
Implemented a dual log storage system:

1. **`previous_logs.json`** - Short-term storage of the most recent check
2. **`baseline_logs.json`** - Long-term stable baseline that persists across HA restarts

**How It Works:**

```python
# Saving logs
- Always save to previous_logs.json
- Update baseline_logs.json only when system is stable (< 20 errors)
- Baseline provides a stable reference point across restarts

# Loading logs
- Try to load previous_logs.json first
- If previous logs are empty (post-restart), fall back to baseline_logs.json
- This ensures we always have something to compare against
```

**Enhanced Logging:**

**First Run (Establishing Baseline):**
```
============================================================
ESTABLISHING BASELINE
============================================================
No previous log data available - this may be first run
Creating baseline snapshot for future comparisons
Future checks will compare against this baseline to detect new errors
============================================================
```

**Normal Operation:**
```
============================================================
LOG MONITORING CHECK
============================================================
Comparing current logs against baseline to detect new errors
Note: Baseline persists across HA restarts for accurate comparison
```

**After HA Restart:**
```
Previous logs appear empty (possible HA restart), trying baseline logs
Loaded 15 baseline error lines from 2026-01-11T22:30:00
Using baseline for comparison (helps detect issues across HA restarts)
```

---

## Verification Steps

### For Issue #1 (WebUI Links):
1. Enable the add-on with `enable_web_ui: true`
2. Wait for an update check to complete
3. Open the notification
4. Verify the notification contains clear instructions (not just links)
5. Follow the instructions to access the WebUI via sidebar panel
6. ✅ WebUI should open correctly

### For Issue #2 (Installation Review):
1. Set `enable_installation_review: true` in add-on config
2. Restart the add-on
3. Check the add-on logs
4. ✅ You should see the "INSTALLATION REVIEW FEATURE ENABLED" banner
5. ✅ Logs should show schedule and scope
6. Wait for the scheduled review (or trigger manually if implemented)
7. ✅ You should receive an installation review notification

### For Issue #3 (Log Monitoring):
1. Enable `monitor_logs_after_update: true` in add-on config
2. Wait for first check to complete (establishes baseline)
3. Check logs for "ESTABLISHING BASELINE" message
4. Restart Home Assistant (simulating post-update restart)
5. Wait for next log check
6. Check logs for "Using baseline for comparison" message
7. ✅ Log comparison should work despite HA restart

---

## Files Changed

1. **`ha_sentry/rootfs/usr/bin/run.sh`**
   - Added 3 missing environment variable exports

2. **`ha_sentry/rootfs/app/sentry_service.py`**
   - Enhanced installation review initialization logging
   - Updated notification format to provide clear access instructions
   - Removed reliance on markdown links

3. **`ha_sentry/rootfs/app/log_monitor.py`**
   - Added `BASELINE_LOGS_FILE` constant
   - Enhanced `save_current_logs()` to maintain baseline
   - Enhanced `load_previous_logs()` to fall back to baseline
   - Added comprehensive logging for baseline operations
   - Updated `check_logs()` with enhanced documentation

4. **`tests/test_three_feature_fixes.py`** (new)
   - Comprehensive test suite for all three fixes
   - Validates environment variable exports
   - Validates notification improvements
   - Validates baseline log persistence

---

## Impact

### Benefits:
- ✅ Installation review feature now works as expected
- ✅ Users can reliably access WebUI from notifications
- ✅ Log monitoring now works across HA restarts (most update scenarios)
- ✅ Better user experience with clear instructions
- ✅ Enhanced logging makes troubleshooting easier

### Backward Compatibility:
- ✅ All changes are backward compatible
- ✅ Existing log files continue to work
- ✅ No configuration changes required
- ✅ No breaking changes to APIs or behavior

### Upgrade Notes:
- No action required from users
- Baseline log file will be created automatically on first run after upgrade
- Installation review will start working if already enabled in config

---

## Testing

### Automated Tests:
```bash
python3 tests/test_three_feature_fixes.py
```

Expected output:
```
Tests completed: 5 passed, 0 failed
```

### Manual Testing Checklist:
- [ ] Verify installation review logs show "ENABLED" when configured
- [ ] Verify installation review notification appears on schedule
- [ ] Verify WebUI accessible via sidebar panel
- [ ] Verify WebUI accessible via Add-on Settings
- [ ] Verify notification provides clear access instructions
- [ ] Verify log monitoring establishes baseline on first run
- [ ] Verify log monitoring uses baseline after HA restart
- [ ] Verify log comparison reports work with baseline

---

## Related Issues

- Original issue: "New Features Not Working" (2026-01-12)
- Related: Notification link fix (previous iterations)
- Related: Log monitoring enhancements

---

## Future Improvements

### Potential Enhancements:
1. Add manual trigger for installation review
2. Add WebUI deep linking support via intent:// URLs for mobile
3. Add pre-update log snapshot API for integration with update process
4. Add baseline health check and auto-refresh mechanism

### Known Limitations:
1. Markdown links in notifications still may not work in some HA versions/apps
2. Baseline is updated only in stable states (may not capture all scenarios)
3. Installation review requires AI to be enabled for best results
