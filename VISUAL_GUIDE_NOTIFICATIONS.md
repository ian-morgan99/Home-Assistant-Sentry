# Visual Guide: Log Monitoring Notifications

## What Users Will See in Home Assistant

This guide shows the three notification states users will receive from the log monitoring feature.

---

## 🟢 GREEN - All Clear

**Scenario:** No changes in logs since last check

**Notification:**
```
✅ Home Assistant Log Monitor - All Clear

Log Monitoring Status: GREEN

✅ No changes in log entries since last check.

Your Home Assistant system logs are stable with no new errors or warnings.

Summary:
No changes in error logs since last check.

---
Analysis powered by: Heuristics
Check time: 2024-12-30 14:30:00 UTC
Log lookback period: 24 hours
```

**What it means:**
- Your system is stable
- No new problems detected
- Everything is working as expected

---

## 🟡 AMBER - Cannot Determine

**Scenario:** First run or no previous baseline available

**Notification:**
```
⚠️ Home Assistant Log Monitor - Unable to Compare

Log Monitoring Status: AMBER

⚠️ Unable to determine if log entries have changed.

This is the first log check, or previous log data is unavailable. Starting fresh baseline.

Current Status:
- Errors/warnings found: 3
- Previous baseline: None available

What This Means:
This is expected on first run or after clearing log history. The next check will be able to compare against this baseline.

---
Analysis powered by: Heuristics
Check time: 2024-12-30 14:30:00 UTC
Log lookback period: 24 hours
```

**What it means:**
- First time monitoring is running
- Establishing a baseline for future comparisons
- Next check will show green or red status
- No action needed - this is normal

---

## 🔴 RED - Changes Detected

**Scenario:** Changes detected in logs (severity varies)

### Example 1: Low Severity
```
🔴 Home Assistant Log Monitor - Changes Detected

Log Monitoring Status: RED

🔴 Changes detected in log entries since last check.

Severity: LOW

Summary:
1 new error/warning message detected.

Changes:
- New errors/warnings: 1
- Resolved errors: 0

Recommendations:
- Review the new error messages when convenient.

---
Analysis powered by: Heuristics
Check time: 2024-12-30 14:30:00 UTC
Log lookback period: 24 hours

Next Steps:
1. Review the error messages in your Home Assistant logs
2. Check if any integrations or add-ons are failing to load
3. Consider rolling back recent updates if errors are critical
```

### Example 2: Critical Severity
```
🔴 Home Assistant Log Monitor - Changes Detected

Log Monitoring Status: RED

🔴 Changes detected in log entries since last check.

Severity: CRITICAL

Summary:
8 new error/warning messages detected. 5 errors may require attention.

Changes:
- New errors/warnings: 8
- Resolved errors: 2

Significant Errors Detected:
1. `2024-12-30 14:25:00 ERROR homeassistant.components.mqtt: Setup of mqtt is taking longer than 60 seconds. Startup will proceed without it.`
2. `2024-12-30 14:20:00 ERROR homeassistant.components.zwave: Integration zwave could not be set up. Configuration is invalid.`
3. `2024-12-30 14:18:00 ERROR homeassistant.loader: Cannot import component test_integration`
4. `2024-12-30 14:15:00 ERROR homeassistant.components.sensor: Setup failed for platform: mqtt`
5. `2024-12-30 14:10:00 CRITICAL homeassistant.core: Failed to start Home Assistant after 60 seconds`

Recommendations:
- Review the new error messages immediately.
- Check if any integrations or add-ons are failing to load.
- Consider reporting issues to component maintainers if errors persist.
- Good news: Some previous errors have been resolved.

---
Analysis powered by: AI
Check time: 2024-12-30 14:30:00 UTC
Log lookback period: 24 hours

Next Steps:
1. Review the error messages in your Home Assistant logs
2. Check if any integrations or add-ons are failing to load
3. Consider rolling back recent updates if errors are critical
```

**What it means:**
- Something has changed in your system logs
- Severity indicates how serious the changes are
- Review the listed errors and take action if needed
- Critical errors need immediate attention

---

## Debug Logging (When Enabled)

When log level is set to "maximal" in add-on configuration, administrators see detailed comparison information in the logs:

```
============================================================
LOG COMPARISON DETAILS
============================================================
Current check time: 2024-12-30 14:30:00
Lookback period: 24 hours
Comparing logs from: 2024-12-29 14:30:00 to 2024-12-30 14:30:00
Current errors found: 5
Previous errors loaded: 3
Previous log data available - can determine changes

Sample of current error entries (up to 5):
  1. 2024-12-30 14:25:00 ERROR homeassistant.components.mqtt: Connection failed to broker at 192.168.1.100...
  2. 2024-12-30 14:20:00 WARNING homeassistant.loader: Integration deprecated: This integration will be removed...
  3. 2024-12-30 14:15:00 ERROR homeassistant.components.sensor: Setup failed for platform: mqtt...
  4. 2024-12-30 14:10:00 ERROR homeassistant.components.zwave: Integration could not be set up...
  5. 2024-12-30 14:05:00 WARNING homeassistant.core: Detected blocking call to sleep...

Sample of previous error entries (up to 5):
  1. 2024-12-29 16:30:00 ERROR homeassistant.components.mqtt: Connection failed to broker at 192.168.1.100...
  2. 2024-12-29 16:20:00 WARNING homeassistant.loader: Integration deprecated: This integration will be removed...
  3. 2024-12-29 16:15:00 WARNING homeassistant.core: Detected blocking call to sleep...
============================================================

Comparison results:
  New errors: 2
  Resolved errors: 0
  Persistent errors: 3
```

**What debug logs show:**
- Exact time ranges being compared
- How many entries found
- Sample of actual log entries
- Detailed comparison results
- Helps troubleshoot issues

---

## Configuration

Enable log monitoring in add-on configuration:

```yaml
monitor_logs_after_update: true
log_check_lookback_hours: 24
log_level: "maximal"  # For debug output
```

---

## Summary

| Status | Emoji | When | Action Needed |
|--------|-------|------|---------------|
| GREEN | ✅ | No log changes | None - all is well |
| AMBER | ⚠️ | First run or no baseline | None - establishing baseline |
| RED | 🔴 | Changes detected | Review errors based on severity |

**Key Benefits:**
- ✅ Always get a notification (no silent monitoring)
- ✅ Clear status at a glance
- ✅ Detailed information when needed
- ✅ Debug logging for troubleshooting
