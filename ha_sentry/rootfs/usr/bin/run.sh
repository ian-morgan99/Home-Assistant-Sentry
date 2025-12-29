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
export CHECK_ADDONS=$(bashio::config 'check_addons')
export CHECK_HACS=$(bashio::config 'check_hacs')
export SAFETY_THRESHOLD=$(bashio::config 'safety_threshold')
export LOG_LEVEL=$(bashio::config 'log_level')
export SUPERVISOR_TOKEN="${SUPERVISOR_TOKEN}"

bashio::log.info "Configuration loaded"
bashio::log.info "AI Enabled: ${AI_ENABLED}"
bashio::log.info "AI Provider: ${AI_PROVIDER}"
bashio::log.info "Check Schedule: ${CHECK_SCHEDULE}"
bashio::log.info "Log Level: ${LOG_LEVEL}"

# Start the Python application
cd /app
exec python3 -u /app/main.py
