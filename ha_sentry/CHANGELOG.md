# Changelog

## 1.3.19
- Merge pull request #101 from ian-morgan99/copilot/reopen-changelog-issue


## 1.3.18
- Merge pull request #97 from ian-morgan99/copilot/fix-webui-initialising-hang


## 1.3.17
- Merge pull request #95 from ian-morgan99/copilot/fix-webui-functionality-issue


## 1.3.16
- Merge pull request #94 from ian-morgan99/copilot/fix-webui-loading-issues


## 1.3.15
- Merge pull request #92 from ian-morgan99/copilot/update-changelog-commentary


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
