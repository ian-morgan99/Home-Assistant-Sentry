# Changelog

All notable changes to Home Assistant Sentry will be documented in this file.

## [1.1.0] - TBD

### Added
- Auto-update support: Add-on now supports Home Assistant's auto-update feature via `auto_update` configuration flag
- Auto-create dashboard feature: New `auto_create_dashboard` option to automatically create a Lovelace dashboard with Sentry widgets
- Dashboard will be created on add-on startup when `auto_create_dashboard` is enabled
- Pre-configured Sentry dashboard includes all monitoring widgets and conditional alerts

### Changed
- Enhanced documentation with new configuration options
- Updated all example configurations to include new options

## [1.0.0] - 2024-12-26

### Added
- Initial release of Home Assistant Sentry
- Daily automated checks for add-on updates via Supervisor API
- Daily automated checks for HACS integration updates
- AI-powered conflict and dependency analysis
- Support for multiple AI providers:
  - OpenAI (cloud)
  - Ollama (local)
  - LMStudio (local)
  - OpenWebUI (local/remote)
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

### Features
- Identifies potential dependency conflicts between updates
- Detects breaking changes in updates
- Analyzes integration compatibility issues
- Provides safety recommendations
- Creates actionable issue reports
- Supports custom AI endpoint configurations
- Privacy-focused with local AI support
- No external telemetry or data collection
