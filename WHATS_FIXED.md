# What's Fixed in This Update

Three important features that weren't working correctly have been fixed. Here's what changed and what you need to know:

## 🔗 Issue #1: WebUI Links in Notifications

### What was broken?
When you clicked links in update notifications to view the WebUI, you were taken to the wrong screen (the add-on selection screen).

### What's fixed?
Notifications now provide clear, step-by-step instructions for accessing the WebUI instead of relying on clickable links that don't always work.

### What you'll see now:
```
📊 Interactive WebUI - Detailed Analysis:

How to Access WebUI:
1. Via Sidebar Panel (Recommended): Look for the 'Sentry' panel in your Home Assistant sidebar
2. Via Add-on Settings: Settings → Add-ons → Home Assistant Sentry → Open Web UI
```

### Action required:
✅ None - this works automatically

---

## 🏠 Issue #2: Installation Review Feature

### What was broken?
Even when you enabled `enable_installation_review: true` in the configuration, the feature didn't work. The logs showed it was still disabled.

### What's fixed?
The add-on now correctly reads your installation review configuration and activates the feature when you enable it.

### What you'll see now:
When you enable installation review, you'll see this in the logs:
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

### Action required:
✅ If you want to use this feature:
1. Open add-on configuration
2. Set `enable_installation_review: true`
3. Choose a schedule: `weekly` or `monthly`
4. Choose a scope: `full`, `integrations`, or `automations`
5. Restart the add-on

The add-on will then periodically review your Home Assistant setup and provide recommendations for improvements.

---

## 📋 Issue #3: Log Comparison After Updates

### What was broken?
The add-on couldn't compare logs before and after updates because Home Assistant clears its logs when it restarts (which happens after most updates).

### What's fixed?
The add-on now saves a "baseline" snapshot of your logs that survives Home Assistant restarts. This means it can:
- Compare logs before and after updates (even when HA restarts)
- Detect new error messages that appear after updates
- Alert you to issues that might have been introduced by updates

### What you'll see now:
**First time it runs:**
```
============================================================
ESTABLISHING BASELINE
============================================================
No previous log data available - this may be first run
Creating baseline snapshot for future comparisons
Future checks will compare against this baseline to detect new errors
============================================================
```

**After Home Assistant restarts:**
```
Loaded 15 baseline error lines from 2026-01-11T22:30:00
Using baseline for comparison (helps detect issues across HA restarts)
```

### Action required:
✅ If you want to use this feature:
1. Open add-on configuration
2. Set `monitor_logs_after_update: true`
3. Optionally adjust `log_check_lookback_hours` (default: 24)
4. Restart the add-on

The add-on will then monitor your logs and alert you to new errors that appear after updates.

---

## 🎉 Summary

All three features now work as intended:
- ✅ WebUI is easier to access with clear instructions
- ✅ Installation review works when you enable it
- ✅ Log monitoring works across Home Assistant restarts

No configuration changes are required unless you want to enable the new features. If these features were previously enabled but not working, they will start working automatically after you update to this version.

---

## Need Help?

If you encounter any issues:
1. Check the add-on logs for detailed information
2. Look for the enhanced logging messages shown above
3. Open an issue on GitHub with:
   - Your configuration settings
   - Relevant log excerpts
   - Description of what's not working

The enhanced logging will make it much easier to diagnose any remaining issues!
