# Update Report Enhancement - Component Impact Links

## Overview

This feature enhances the Home Assistant Sentry Update Report by adding useful links to provide more detailed information about component updates and their impacts.

## What's New

### 1. Component Naming
Components that have been updated are now clearly named in the notification, making it easy to identify which specific component is affected.

### 2. "View Impact" Links for Each Component
Each component in the update report now includes a **"View Impact"** link that takes you directly to the web UI's "Where Used" view for that specific component. This shows:
- Which other integrations depend on this component
- What packages are shared with other components
- The potential blast radius of updating this component

**Example:**
```
🟠 Home Assistant Core
Major version update: 2024.1 → 2024.2
  [🔍 View Impact](/api/hassio_ingress/ha_sentry#whereused:home_assistant_core)
```

### 3. Change Impact Report Link
At the bottom of the notification, when issues are detected, a comprehensive **Change Impact Report** link is provided. This link:
- Shows ALL changed components in one view
- Displays the total number of affected dependencies
- Highlights high-risk changes
- Provides a complete picture of the update's impact

**Example:**
```
📊 Detailed Analysis:
- [⚡ Change Impact Report](/api/hassio_ingress/ha_sentry#impact:home_assistant_core,mosquitto) 
  View 2 changed components and their affected dependencies
```

### 4. Dependency Dashboard Link
A link to the main dependency visualization dashboard is always included, allowing users to:
- Explore all component dependencies
- Switch between different visualization modes
- Perform custom impact analysis

## How It Works

### URL Structure
All links use Home Assistant's ingress system for seamless integration:
- Base URL: `/api/hassio_ingress/ha_sentry`
- Where Used: `/api/hassio_ingress/ha_sentry#whereused:component_name`
- Impact Analysis: `/api/hassio_ingress/ha_sentry#impact:comp1,comp2,comp3`

### Deep Linking
The web UI automatically handles URL fragments (the `#` part) to:
1. Switch to the appropriate view mode (Dependencies, Where Used, or Impact)
2. Pre-populate the component selection
3. Automatically run the visualization

This means clicking a link in the notification takes you directly to the relevant analysis, with no manual navigation required.

## Configuration

The feature respects the existing configuration:
- Links are only shown if `enable_web_ui: true` in the add-on configuration
- Links are only shown if `enable_dependency_graph: true` (required for web UI)
- If web UI is disabled, notifications continue to work as before without links

## Example Notification

Here's an example of a complete update notification with the new features:

```markdown
⚠️ **REVIEW REQUIRED before updating**

**Confidence:** 75%

**Updates Available:** 5
- Core/System: 1
- Add-ons: 2
- HACS/Integrations: 2

**Issues Found:** 2

🟠 **Home Assistant Core**
Major version update: 2024.1 → 2024.2
  [🔍 View Impact](/api/hassio_ingress/ha_sentry#whereused:home_assistant_core)

🟡 **mosquitto**
MQTT broker update: 2.0.15 → 2.0.18
  [🔍 View Impact](/api/hassio_ingress/ha_sentry#whereused:mosquitto)

**Summary:**
Deep analysis: 5 updates available. Review required: 0 critical, 2 high-priority issues detected.

**Recommendations:**
- Backup before updating Home Assistant Core
- Review Home Assistant Core changelog for breaking changes

---
**📊 Detailed Analysis:**
- [⚡ Change Impact Report](/api/hassio_ingress/ha_sentry#impact:home_assistant_core,mosquitto) - View 2 changed components and their affected dependencies
- [🛡️ Dependency Dashboard](/api/hassio_ingress/ha_sentry) - Explore all component dependencies

*Analysis powered by: Heuristics*
*Last check: 2025-12-29 20:45:00*
```

## Technical Implementation

### Changed Files
1. **sentry_service.py**:
   - Added `ADDON_SLUG` constant
   - Added `_get_ingress_url()` method for generating ingress URLs
   - Added `_extract_component_domain()` method for sanitizing component names
   - Modified notification generation to include links

2. **web_server.py**:
   - Added `handleUrlFragment()` JavaScript function
   - Implemented automatic mode switching based on URL fragments
   - Added component pre-selection from URL parameters

### Test Coverage
New test file `test_notification_links.py` validates:
- Ingress URL generation patterns
- Component domain extraction and sanitization
- URL fragment handling in the web UI
- Notification structure requirements

## Benefits

1. **Reduced Click Navigation**: Users can jump directly to relevant analysis views
2. **Better Context**: "Where Used" links provide immediate understanding of component relationships
3. **Comprehensive Overview**: Impact report shows the big picture of what's changing
4. **Seamless UX**: Deep linking eliminates manual navigation steps
5. **Backward Compatible**: Existing functionality is preserved when web UI is disabled

## Future Enhancements

Possible future improvements:
- Add direct links to component documentation
- Include links to GitHub release notes
- Provide "recommended update order" based on dependency analysis
- Add "quick fix" links for common issues
