# Repository Structure

This document describes the structure of the Home Assistant Sentry add-on repository.

## Directory Structure

```
Home-Assistant-Sentry/
├── rootfs/                      # Root filesystem for the add-on container
│   ├── app/                     # Main application code
│   │   ├── main.py              # Entry point for the application
│   │   ├── config_manager.py   # Configuration management
│   │   ├── ha_client.py         # Home Assistant API client
│   │   ├── ai_client.py         # AI provider integration
│   │   ├── dashboard_manager.py # Dashboard entities manager
│   │   └── sentry_service.py    # Main service coordinator
│   └── usr/
│       └── bin/
│           └── run.sh           # Add-on startup script
├── tests/                       # Test files
│   └── test_basic.py            # Basic module tests
├── config.yaml                  # Add-on configuration (Home Assistant)
├── config.json                  # Add-on configuration (JSON format)
├── build.json                   # Build configuration for multi-arch
├── Dockerfile                   # Container image definition
├── requirements.txt             # Python dependencies
├── README.md                    # Main documentation
├── DOCS.md                      # Detailed user documentation
├── EXAMPLES.md                  # Configuration examples
├── CHANGELOG.md                 # Version history
├── LICENSE                      # MIT License
└── .gitignore                   # Git ignore rules
```

## Key Files

### Configuration Files

- **config.yaml**: Home Assistant add-on metadata and options schema
- **config.json**: Alternative JSON format for add-on configuration
- **build.json**: Build configuration for multi-architecture support
- **Dockerfile**: Container image build instructions

### Application Code

- **main.py**: Application entry point, starts the service
- **config_manager.py**: Loads and manages configuration from environment
- **ha_client.py**: Client for Home Assistant Supervisor and Core APIs
- **ai_client.py**: Client for AI providers (OpenAI, Ollama, LMStudio, etc.)
- **dashboard_manager.py**: Creates and updates sensor entities
- **sentry_service.py**: Main service that coordinates update checks and analysis

### Scripts

- **run.sh**: Startup script that loads configuration and starts Python app

### Documentation

- **README.md**: Overview, features, quick start
- **DOCS.md**: Comprehensive user documentation
- **EXAMPLES.md**: Configuration examples
- **CHANGELOG.md**: Version history and changes

## Data Flow

1. **Startup**: run.sh loads config → starts main.py
2. **Initialization**: main.py → config_manager → sentry_service
3. **Scheduled Check**: sentry_service → ha_client (get updates)
4. **Analysis**: sentry_service → ai_client (analyze conflicts)
5. **Reporting**: sentry_service → dashboard_manager → ha_client (update sensors)
6. **Notification**: sentry_service → ha_client (create notification)

## Key Components

### ConfigManager (config_manager.py)
- Loads configuration from environment variables
- Provides settings to other components
- Manages API credentials

### HomeAssistantClient (ha_client.py)
- Communicates with Supervisor API for add-on info
- Communicates with Core API for HACS info
- Creates notifications and sensor states

### AIClient (ai_client.py)
- Supports multiple AI providers
- Analyzes updates for conflicts
- Falls back to heuristic analysis if AI unavailable

### DashboardManager (dashboard_manager.py)
- Creates sensor entities
- Updates sensor states with analysis results

### SentryService (sentry_service.py)
- Coordinates all components
- Manages scheduling
- Runs update checks
- Reports results

## Adding Features

### Adding a New AI Provider

1. Edit `config.yaml`: Add provider to schema
2. Edit `ai_client.py`: Add provider initialization in `_initialize_client()`
3. Test with new provider configuration

### Adding New Sensors

1. Edit `dashboard_manager.py`: Add new sensor in `update_sensors()`
2. Use `ha_client.set_sensor_state()` to create/update
3. Document new sensor in README.md

### Adding New Analysis Rules

1. Edit `ai_client.py`: Update `_fallback_analysis()` for heuristics
2. Edit `_get_system_prompt()` to guide AI analysis
3. Test with various update scenarios

## Development Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set environment variables for testing
4. Run tests: `python3 tests/test_basic.py`

## Building

The add-on is built by Home Assistant when installed. For manual builds:

```bash
docker build -t ha-sentry .
```

## Contributing

See CONTRIBUTING.md for guidelines on contributing to this project.
