#!/usr/bin/with-contenv bashio

bashio::log.info "Starting Home Assistant Sentry..."

# Load configuration
CONFIG_PATH=/data/options.json
export AI_ENABLED=$(bashio::config 'ai_enabled')
export AI_PROVIDER=$(bashio::config 'ai_provider')
export AI_ENDPOINT=$(bashio::config 'ai_endpoint')
export AI_MODEL=$(bashio::config 'ai_model')
export API_KEY=$(bashio::config 'api_key')
export CHECK_SCHEDULE=$(bashio::config 'check_schedule')
export CREATE_DASHBOARD_ENTITIES=$(bashio::config 'create_dashboard_entities')
export CHECK_ALL_UPDATES=$(bashio::config 'check_all_updates')
export CHECK_ADDONS=$(bashio::config 'check_addons')
export CHECK_HACS=$(bashio::config 'check_hacs')
export SAFETY_THRESHOLD=$(bashio::config 'safety_threshold')
export LOG_LEVEL=$(bashio::config 'log_level')
export OBFUSCATE_LOGS=$(bashio::config 'obfuscate_logs')
export ENABLE_DEPENDENCY_GRAPH=$(bashio::config 'enable_dependency_graph')
export SAVE_REPORTS=$(bashio::config 'save_reports')
export ENABLE_WEB_UI=$(bashio::config 'enable_web_ui')
export PORT=$(bashio::config 'port')
export MONITOR_LOGS_AFTER_UPDATE=$(bashio::config 'monitor_logs_after_update')
export LOG_CHECK_LOOKBACK_HOURS=$(bashio::config 'log_check_lookback_hours')

# Parse custom integration paths with proper error handling
if CUSTOM_PATHS=$(bashio::config 'custom_integration_paths' | jq -c '.' 2>/dev/null); then
    export CUSTOM_INTEGRATION_PATHS="${CUSTOM_PATHS}"
else
    bashio::log.warning "Failed to parse custom_integration_paths, using empty array"
    export CUSTOM_INTEGRATION_PATHS="[]"
fi

export SUPERVISOR_TOKEN="${SUPERVISOR_TOKEN}"

bashio::log.info "Configuration loaded"
bashio::log.info "AI Enabled: ${AI_ENABLED}"
bashio::log.info "AI Provider: ${AI_PROVIDER}"
bashio::log.info "Check Schedule: ${CHECK_SCHEDULE}"
bashio::log.info "Check All Updates: ${CHECK_ALL_UPDATES}"
bashio::log.info "Log Level: ${LOG_LEVEL}"

# Start the Python application
cd /app
exec python3 -u /app/main.py
