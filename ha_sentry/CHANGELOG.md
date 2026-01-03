# Changelog

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
