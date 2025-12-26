# Example Configuration for Home Assistant Sentry

## Minimal Configuration (No AI)

```yaml
ai_enabled: false
check_schedule: "02:00"
create_dashboard_entities: true
check_addons: true
check_hacs: true
```

## Ollama Configuration (Recommended for Local AI)

```yaml
ai_enabled: true
ai_provider: "ollama"
ai_endpoint: "http://localhost:11434"
ai_model: "llama2"
api_key: ""
check_schedule: "02:00"
create_dashboard_entities: true
check_addons: true
check_hacs: true
safety_threshold: 0.7
```

## LMStudio Configuration

```yaml
ai_enabled: true
ai_provider: "lmstudio"
ai_endpoint: "http://localhost:1234"
ai_model: "local-model"
api_key: ""
check_schedule: "02:00"
create_dashboard_entities: true
check_addons: true
check_hacs: true
safety_threshold: 0.7
```

## OpenAI Configuration

```yaml
ai_enabled: true
ai_provider: "openai"
ai_endpoint: "https://api.openai.com/v1"
ai_model: "gpt-3.5-turbo"
api_key: "sk-your-openai-api-key-here"
check_schedule: "02:00"
create_dashboard_entities: true
check_addons: true
check_hacs: true
safety_threshold: 0.7
```

## OpenWebUI Configuration

```yaml
ai_enabled: true
ai_provider: "openwebui"
ai_endpoint: "http://your-openwebui-host:8080"
ai_model: "gpt-3.5-turbo"
api_key: "your-api-key"
check_schedule: "02:00"
create_dashboard_entities: true
check_addons: true
check_hacs: true
safety_threshold: 0.7
```

## Advanced Configuration

### Only Check Add-ons (Skip HACS)

```yaml
ai_enabled: true
ai_provider: "ollama"
ai_endpoint: "http://localhost:11434"
ai_model: "llama2"
api_key: ""
check_schedule: "02:00"
create_dashboard_entities: true
check_addons: true
check_hacs: false  # Disable HACS checking
safety_threshold: 0.7
```

### Only Check HACS (Skip Add-ons)

```yaml
ai_enabled: true
ai_provider: "ollama"
ai_endpoint: "http://localhost:11434"
ai_model: "llama2"
api_key: ""
check_schedule: "02:00"
create_dashboard_entities: true
check_addons: false  # Disable add-on checking
check_hacs: true
safety_threshold: 0.7
```

### Different Check Times

```yaml
# Run at 3:30 AM
check_schedule: "03:30"

# Run at 2:00 PM (14:00)
check_schedule: "14:00"

# Run at midnight
check_schedule: "00:00"
```

### Conservative Safety Settings

For users who want to be very cautious:

```yaml
ai_enabled: true
ai_provider: "ollama"
ai_endpoint: "http://localhost:11434"
ai_model: "llama2"
api_key: ""
check_schedule: "02:00"
create_dashboard_entities: true
check_addons: true
check_hacs: true
safety_threshold: 0.85  # Higher threshold = more conservative
```

### Without Dashboard Entities (Notifications Only)

```yaml
ai_enabled: true
ai_provider: "ollama"
ai_endpoint: "http://localhost:11434"
ai_model: "llama2"
api_key: ""
check_schedule: "02:00"
create_dashboard_entities: false  # Only notifications, no sensors
check_addons: true
check_hacs: true
safety_threshold: 0.7
```

## Configuration Tips

1. **Start Simple**: Begin with AI disabled to test basic functionality
2. **Use Local AI**: Ollama or LMStudio for privacy and no API costs
3. **Test Schedule**: Use a time when you're awake for initial testing
4. **Adjust Threshold**: Start with 0.7 and adjust based on your comfort level
5. **Enable Logging**: Check the add-on logs to see what's happening

## Troubleshooting Configuration

If the add-on isn't working:

1. Check the logs in Supervisor → Home Assistant Sentry → Log
2. Verify your AI endpoint is accessible
3. Test with `ai_enabled: false` first
4. Ensure the time format is correct (HH:MM, 24-hour)
5. Restart the add-on after configuration changes
