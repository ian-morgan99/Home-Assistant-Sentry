# Changelog

## 2.0.13
- Fix OpenWebUI endpoint to use /api instead of /v1 OpenWebUI uses `/api/chat/completions` for its API endpoint, not `/v1/chat/completions` like other OpenAI-compatible providers. This caused 405 Method Not Allowed errors when attempting to use OpenWebUI as the AI provider.


## 2.0.12
- Make installation review timeout configurable and add progress logging Installation reviews were timing out before AI reasoning models could complete analysis. The 160s timeout was insufficient for models like `qwen3-8b-claude-sonnet-4.5-reasoning-distill@q8_0` analyzing 2500+ entities.


## 2.0.11
- Fix installation review config, log monitoring baseline, and WebUI notification access Three features were non-functional: installation review ignored config, log monitoring failed across HA restarts, and WebUI notification links redirected incorrectly.


## 2.0.10
- Fix hardcoded value in installation review disabled log message The debug log message for disabled installation review always displayed `enable_installation_review=false`, even when the feature was enabled, causing confusion during troubleshooting.


## 2.0.09
- Add diagnostic logging to installation review scheduling Users enabling `enable_installation_review` saw no log output indicating whether the feature was running or why it wasn't. The `_should_run_installation_review()` method performed all scheduling logic silently.


## 2.0.08
- Fix installation review scheduling when no updates available The installation review check was placed after the early return when no updates are found, preventing it from running when no updates are available.


## 2.0.07
- Enable user-configurable WebUI port without breaking ingress Enable web server to listen on both: 1. **Ingress Port (8099)** - Always used for HA sidebar panel 2. **Custom Port (user-configurable)** - For direct browser access


## 2.0.06
- Fix: Port is now user-configurable without breaking ingress
- Feature: Web UI listens on both ingress port (8099) and custom port simultaneously
- Sidebar panel always works regardless of port configuration
- Add comprehensive documentation for dual-port configuration options
- Remove misleading port configuration warnings
- Improve startup logging to show both access methods

## 2.0.05
- Add Installation Review feature for AI-powered Home Assistant optimization Comments 2679343988 and 2679343995 suggest adding test coverage. These are valuable suggestions for future work but are not blocking issues for the current implementation. The feature has been manually tested and all syntax checks pass.


## 2.0.04
- Add Installation Review feature for AI-powered Home Assistant optimization recommendations
- New configuration options: enable_installation_review, installation_review_schedule, installation_review_scope
- Privacy-first data collection: only metadata and counts, no sensitive values
- AI-powered analysis: comprehensive recommendations by category (security, performance, automation, etc.)
- Heuristic fallback: rule-based recommendations when AI is disabled
- Scheduled reviews: weekly, monthly, or manual trigger
- Categorized recommendations with priority levels (high/medium/low)
- JSON report saving for external analysis
- Notification with actionable insights and improvement suggestions
- Fix WebUI startup failure caused by missing environment variable exports The WebUI stopped starting in v2.0.03 due to missing environment variable exports in `run.sh` and a stale export for a removed config option.


## 2.0.03
- Add panel_admin field and fix port configuration issues Home Assistant Supervisor fails to establish ingress connection with error "Unable to fetch add-on info to start Ingress" due to missing `panel_admin` configuration field.


## 2.0.02
- Fix notification links using correct ingress URL format Notification links were redirecting to the Home Assistant dashboard instead of opening the Sentry Web UI. The code was using `/api/hassio_ingress/{slug}/` (backend proxy route) instead of `/hassio/ingress/{slug}/` (frontend navigation route).


## 2.0.01
- Fix notification links to WebUI and add per-component dependency links Notification links were redirecting to home dashboard instead of WebUI. Per-component dependency links were missing.


## 2.0.0
- **MAJOR RELEASE**: Fix notification links to WebUI and add per-component dependency links
- Fix main WebUI link by adding trailing slash to ingress URL (`/api/hassio_ingress/ha_sentry/`)
- Add "View Dependencies" link for each integration/HACS component in notifications
- Links appear in both SAFE and REVIEW REQUIRED notifications
- Add comprehensive "Available Updates" section with links for all updated components
- Change Impact Report link now works for both safe and review-required notifications
- Update all documentation (DOCS.md, README.md, QUICKSTART.md) to reflect new features
- Improve list merge efficiency using set-based deduplication
- **Breaking Change**: Notification format now includes interactive links section


## 1.3.34
- Fix WebUI ingress routing and make port user-configurable The WebUI hangs at "Preparing status..." when accessed through Home Assistant ingress because JavaScript builds absolute URLs that are missing the ingress path prefix stripped by HA's proxy. Additionally, the port was hardcoded, preventing users from changing it when port 8099 is already in use.


## 1.3.33
- Delay initial update check to prevent WebUI blocking on slow AI endpoints WebUI hung on "Preparing status..." when LMStudio accepted TCP connections but didn't respond to HTTP requests, blocking initial startup.


## 1.3.32
- Add comprehensive WebUI progress tracking and error handling to fix "Preparing status..." hang The Web UI gets stuck on "Preparing status..." when `loadComponents()` or `loadStats()` fail, because these async functions were called without `await`, causing unhandled promise rejections. This PR provides a comprehensive solution with production-grade features to address all potential failure modes.


## 1.3.31
- Major WebUI overhaul: Add real-time progress bar, comprehensive error handling, and network timeout management
- Show visual progress during dependency graph building (30-60 second process)
- Poll status API every second to display real-time progress and integration count
- Add 7 distinct error scenarios with specific troubleshooting steps
- Implement timeout handling with AbortController (8s for status, 15s for components)
- Extract all timeouts and thresholds to named constants for easy configuration
- Add step-by-step diagnostic logging for precise failure tracking
- Fix async/await in DOMContentLoaded to properly catch initialization errors


## 1.3.30
- Improve Web UI initialization diagnostics and ingress-safe API routing Web UI dependency graph remained on “Initializing” with empty component lists and non-functional “Where used” due to brittle ingress paths and lack of visible progress.


## 1.3.29
- Fix 404 handler to return JSON for API/ingress paths Home Assistant Supervisor probes `/ingress/validate_session` and other routes, receiving HTML 404s that it attempts to parse as JSON, causing "Attempt to decode JSON with unexpected mimetype: text/plain" errors in Core logs.


## 1.3.28
- Fix AI analysis blocking event loop causing timeouts and missed notifications 1. ✅ **AI Analysis Timeout** - HTTP connection to LMStudio hangs, preventing update analysis 2. ✅ **No Notifications Sent** - Notifications depend on analysis completion 3. ✅ **WebUI Status Update** - Web server becomes unresponsive when AI blocks


## 1.3.27
- Add persistent notifications for log monitoring with status indicators and debug logging - ✅ Green: No changes in log entries - ⚠️ Amber: Can't determine changes (first run or missing previous logs) - 🔴 Red: Changes detected in log entries


## 1.3.26
- Add post-update log monitoring with AI-powered error analysis All requested features have been successfully implemented and tested!


## 1.3.25
- Add log monitoring feature to check system logs after component updates
- Monitor Home Assistant logs for new errors/warnings after updates
- Compare logs between checks to identify changes (new, resolved, persistent errors)
- Support both heuristic and AI-powered analysis of log changes
- Automatically anonymize sensitive data (IPs, tokens, keys) before AI analysis
- Generate notifications with severity assessment and recommendations
- Configurable via `monitor_logs_after_update` and `log_check_lookback_hours` settings
- Helps identify issues early before they impact the system

## 1.3.24
- Fix race condition in WebUI component loading during graph initialization WebUI shows "Initializing..." or "Loading..." and never displays components, even though the dependency graph successfully builds with integrations in the background.


## 1.3.23
- Add configurable log obfuscation for sensitive data (IPs, API keys, tokens) Logs currently expose sensitive data including IP addresses, API keys, and authentication tokens. This adds automatic obfuscation enabled by default.


## 1.3.22
- Add addon dependency tracking to dependency graph and Web UI Extends dependency visibility to include Home Assistant add-ons alongside integrations, addressing the gap identified in PR #105 where addon dependencies were not tracked.


## 1.3.21
- Fixed notification links to only show for integrations and HACS components
- **CRITICAL FIX: Switched from URL fragments to query parameters for notification links**
  - URL fragments (# anchors) are not reliably preserved in Home Assistant persistent notifications
  - Now using query parameters (?mode=whereused&component=name) which work correctly
  - Web UI supports both formats for backward compatibility
- Improved error messages when clicking links to components not in dependency graph
- Added diagnostic logging for URL handling in web UI
- Fixed issue where links to addons (mosquitto, Node-RED, etc.) would fail because addons are not tracked in the dependency graph

## 1.3.20
- Enhance changelog generation with PR metadata extraction and rebuild historic entries Changelog entries were showing bare merge commit messages ("Merge pull request #101...") instead of meaningful descriptions. The workflow had logic to extract Copilot review summaries but no fallback for when reviews are unavailable.


## 1.3.19
- Extract Copilot review summaries for CHANGELOG entries. Issue #98 requested using Copilot PR review comments in CHANGELOG.md instead of raw commit messages. The workflow now extracts the summary paragraph from copilot-pull-request-reviewer[bot] reviews and uses it as the changelog entry with comprehensive test coverage for PR number extraction and review summary parsing.

## 1.3.18
- Fix WebUI hanging and add directory mappings to enable dependency graph access. The WebUI hung for 60 seconds before showing an error when the dependency graph completed with 0 integrations. Fixed the status endpoint to properly detect completion with no integrations and added directory mappings (config:ro, share:ro, homeassistant_config:ro) to provide read-only access to HACS/custom integration directories.

## 1.3.17
- Remove dashboard auto-creation option and clarify WebUI access. Dashboard auto-creation via Lovelace API fails with 404 due to Home Assistant add-on permission restrictions. Completely removed the deprecated auto_create_dashboard option and enhanced documentation to emphasize WebUI access via sidebar panel, add-on settings, or direct ingress URL.

## 1.3.16
- Fix WebUI stuck on "Loading components" by auto-detecting integration paths. The dependency graph was not finding any integrations because default paths don't exist in all HA environments. Implemented dynamic Python version detection with glob patterns, improved error messages distinguishing between empty vs non-existent paths, and added diagnostic logging for troubleshooting.

## 1.3.15
- Auto-generate meaningful changelog entries from commit messages. The automated version increment workflow was generating placeholder text instead of meaningful changelog entries. Enhanced the workflow to extract recent commits, filter bot/version commits, and generate entries based on commit count (2-5 commits: include all, 1 or 6+: most recent only).


## 1.3.14
- Version automatically incremented
- Manual update recommended: Add detailed release notes here


## 1.3.13
- Version automatically incremented
- Manual update recommended: Add detailed release notes here


## 1.3.12
- Version automatically incremented
- Manual update recommended: Add detailed release notes here


## 1.3.11
- Version automatically incremented
- Manual update recommended: Add detailed release notes here


## 1.3.10
- Version automatically incremented
- Manual update recommended: Add detailed release notes here


## 1.3.09
- Version automatically incremented
- Manual update recommended: Add detailed release notes here


## 1.3.08
- Fixed CHANGELOG.md format to match Home Assistant expectations (simple ## X.Y.Z headings)
- Added automatic CHANGELOG.md updates to version increment workflow
- Updated documentation with correct CHANGELOG.md format requirements

## 1.3.07
- Configuration Documentation Enhancement: Added comprehensive inline parameter documentation to config.yaml
- Image Asset Improvements: Converted icon.png and logo.png to RGBA format with transparent backgrounds for better appearance on different colored backgrounds
- Performance Review: Verified all code uses async/await properly with no blocking operations
- Security Review: Verified no vulnerabilities in dependencies and proper authentication handling
- Code Quality: Confirmed error handling is robust with graceful degradation
- Documentation Polish: Enhanced configuration guidance explaining when to use each parameter

## 1.2.11
- Production Readiness Improvements: Configuration, image assets, performance, security, and documentation enhancements

## 1.1.0
- Comprehensive Update Checking: Now checks ALL update entities from Settings > Updates section
  - Home Assistant Core updates
  - Supervisor updates
  - Operating System updates
  - All add-on updates
  - All integration updates (including HACS)
- New check_all_updates configuration option (default: true) for comprehensive update monitoring
- Enhanced update categorization with breakdown by type (Core/System, Add-ons, HACS/Integrations)
- Auto-update support: Add-on now supports Home Assistant's auto-update feature via auto_update configuration flag
- Auto-create dashboard feature: New auto_create_dashboard option to automatically create a Lovelace dashboard with Sentry widgets
- Dashboard will be created on add-on startup when auto_create_dashboard is enabled
- Pre-configured Sentry dashboard includes all monitoring widgets and conditional alerts
- Enhanced documentation with comprehensive update checking capabilities
- Updated notification format to show breakdown by update type
- Improved update detection using Home Assistant's native update entities
- Updated all example configurations to include new options
- Legacy check_addons and check_hacs options maintained for backward compatibility

## 1.0.0
- Initial release of Home Assistant Sentry
- Daily automated checks for add-on updates via Supervisor API
- Daily automated checks for HACS integration updates
- AI-powered conflict and dependency analysis
- Support for multiple AI providers: OpenAI (cloud), Ollama (local), LMStudio (local), OpenWebUI (local/remote)
- Fallback heuristic analysis when AI is disabled
- Dashboard sensor entities for monitoring:
  - Update status sensor
  - Updates available counter
  - Add-on updates details
  - HACS updates details
  - Issues detected sensor
  - Confidence score sensor
- Persistent notifications with detailed analysis results
- Configurable daily check schedule
- Safety threshold configuration
- Comprehensive documentation and examples
- Example dashboard cards for Lovelace
- Identifies potential dependency conflicts between updates
- Detects breaking changes in updates
- Analyzes integration compatibility issues
- Provides safety recommendations
- Creates actionable issue reports
- Supports custom AI endpoint configurations
- Privacy-focused with local AI support
- No external telemetry or data collection
