# Copilot Instructions for Home Assistant Sentry

## Product Overview

**Home Assistant Sentry** is a Home Assistant add-on that performs daily reviews of all available updates (Core, Supervisor, OS, add-ons, and integrations), identifies potential conflicts and dependency issues, and advises whether updates are safe to install.

### Product Goal

**Home-Assistant-Sentry exists to explain update risk before the user updates, without modifying or interfering with Home Assistant's runtime.**

### Key Principles

- **Advisory, not intrusive**: We provide information and recommendations, never taking action on behalf of the user
- **Predictive, not reactive**: We analyze before updates happen, not after
- **Read-only by default**: We observe and analyze, never modify
- **Zero-risk to HA stability**: Our add-on must never cause Home Assistant to fail or become unstable

## Architecture

This is a **Home Assistant add-on** (not a HACS integration) that runs as a separate Docker container managed by the Supervisor.

### Technology Stack

- **Language**: Python 3
- **Runtime**: Docker container
- **APIs**: Home Assistant Supervisor API, Home Assistant Core API
- **AI Integration**: OpenAI, Ollama, LMStudio, OpenWebUI (configurable)
- **Web UI**: Flask-based visualization interface

### Directory Structure

```
Home-Assistant-Sentry/
├── ha_sentry/                          # Add-on directory
│   ├── rootfs/                         # Root filesystem for the add-on container
│   │   └── app/                        # Main application code
│   │       ├── main.py                 # Entry point
│   │       ├── config_manager.py       # Configuration management
│   │       ├── ha_client.py            # Home Assistant API client
│   │       ├── ai_client.py            # AI provider integration
│   │       ├── dashboard_manager.py    # Dashboard entities manager
│   │       ├── dependency_analyzer.py  # Dependency analysis
│   │       ├── dependency_graph_builder.py  # Dependency graph building
│   │       ├── sentry_service.py       # Main service coordinator
│   │       └── web_server.py           # Web UI server
│   ├── config.yaml                     # Add-on configuration
│   ├── Dockerfile                      # Container image definition
│   └── requirements.txt                # Python dependencies
├── tests/                              # Test files
└── [documentation files]
```

## Critical Rules (Non-Negotiable)

### What Sentry NEVER Does

1. ❌ **Never changes system state**
   - No modifications to Home Assistant configuration
   - No changes to integration files
   - No database modifications
   - No file system writes except for its own logs and reports

2. ❌ **Never "fixes" issues**
   - No automatic patching
   - No automatic configuration updates
   - No automatic dependency resolution

3. ❌ **Never blocks updates**
   - We may warn and advise caution
   - We may recommend delaying
   - But we NEVER prevent the user from updating

4. ❌ **Never assumes user intent**
   - We provide information
   - The user decides what to do with it

### What Sentry NEVER Touches

1. ❌ **No pip install**
   - Never install, upgrade, or modify Python packages in HA's environment
   - Never run pip commands in HA's environment
   - Never manipulate the Python environment

2. ❌ **No writes to HA Python environment**
   - Never modify site-packages
   - Never modify installed integrations
   - Never inject code into HA's Python runtime

3. ❌ **No runtime monkey-patching**
   - Never modify HA Core at runtime
   - Never patch integration code
   - Never intercept or modify HA's execution

4. ❌ **No integration imports**
   - Never import integration code directly
   - Static inspection only (read manifest.json files)
   - Read manifest files, don't execute integration code

### What Sentry ONLY Does

✅ **Static inspection only**
- Read and parse manifest.json files
- Read configuration files (read-only)
- Analyze file metadata

✅ **Filesystem reads only**
- Read files to gather information
- Never write outside our designated directories (`/data/`)
- Never modify any HA files

✅ **Supervisor-approved APIs only**
- Use official Home Assistant APIs
- Use official Supervisor APIs
- Never circumvent API security

## Language Rules for User-Facing Messages

When writing user-facing messages, documentation, or code comments about risks:

### ✅ Use These Words
- "may", "could", "might", "possible", "potential"
- "risk of", "could affect", "may impact"

### ❌ Never Use These Words
- "will break", "will fail", "guaranteed to", "definitely", "certainly will"

### Examples

**Good:**
> ⚠️ Updating to HA 2025.1 may affect custom_component_x (requires <=2024.12)

**Bad:**
> ❌ Updating to HA 2025.1 will break custom_component_x

## Coding Standards

### Python Style
- Follow PEP 8 conventions
- Use type hints where appropriate
- Add docstrings to functions and classes
- Use descriptive variable names
- Keep functions focused and small

### Logging Levels
- `DEBUG`: Detailed diagnostic information
- `INFO`: General informational messages
- `WARNING`: Warning messages for potential issues
- `ERROR`: Error messages for failures

### Error Handling
- Handle all error cases gracefully
- No crashes on malformed manifests
- No assumptions about install type (HA OS vs. Container vs. Core)
- Graceful degradation when data is unavailable
- Clear error messages for users

## Development Workflow

### Testing
- Test files are in `/tests/` directory
- Run tests: `python3 tests/test_basic.py`
- Add unit tests for new functionality
- Test error paths and edge cases
- Verify no side effects

### Test Scenarios to Consider
1. **Clean HA OS install**: Fresh installation with no custom integrations
2. **Heavy HACS system**: System with 50+ HACS integrations
3. **Broken/partial integrations**: Malformed manifest.json files, missing fields, invalid version strings

### Performance Requirements
- **Graph build**: < 2 seconds for 200+ integrations
- **Memory footprint**: < 200MB
- **No continuous background scanning**: Only scheduled checks
- **Efficient API usage**: Minimize API calls to HA

## Building and Running

### Building the Add-on
The add-on is built by Home Assistant when installed. For manual Docker builds:
```bash
cd ha_sentry
docker build -t ha-sentry .
```

### Running Tests
```bash
# Run basic tests
python3 tests/test_basic.py

# Run specific test files
python3 tests/test_dependency_analyzer.py
python3 tests/test_ai_client.py
```

### Python Dependencies
Located in `ha_sentry/requirements.txt`. Install for local testing:
```bash
pip install -r ha_sentry/requirements.txt
```

## Adding New Features

### Checklist Before Implementation
- [ ] Does it align with the product goal?
- [ ] Is it read-only (no system state modifications)?
- [ ] Does it use only approved APIs?
- [ ] Does it handle errors gracefully?
- [ ] Have you added tests?
- [ ] Have you updated documentation?

### Adding a New AI Provider
1. Edit `ha_sentry/config.yaml`: Add provider to schema
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

## Version Management

### Version Numbers

Version numbers MUST be updated in **both** configuration files when making a release:
- `ha_sentry/config.json` - Update the `"version"` field
- `ha_sentry/config.yaml` - Update the `version:` field

**Important**: Both files must have matching version numbers.

### Semantic Versioning

Follow semantic versioning (MAJOR.MINOR.PATCH):
- **Patch increment (0.0.1)**: Bug fixes and minor changes (e.g., 1.2.0 → 1.2.1)
- **Minor increment (0.1.0)**: New features or larger changes (e.g., 1.2.0 → 1.3.0)
- **Major increment (1.0.0)**: Breaking changes (e.g., 1.2.0 → 2.0.0)

### Automated Version Updates

Versions are automatically updated via GitHub Actions when code is pushed to main. The workflow:
1. Validates the version is properly incremented
2. Updates both config.json and config.yaml
3. Adds a new entry to CHANGELOG.md
4. Commits changes to the main branch

### Changelog Format

The CHANGELOG.md follows Home Assistant Add-on standards:

**Format Requirements:**
- Version heading: `## X.Y.Z` (version number only, **no dates or suffixes**)
- List changes as bullet points with `-`
- Newest version at the top
- Keep entries clear and concise
- **CRITICAL**: Do NOT add dates, "TBD", or any other text after the version number

**Example:**
```markdown
## 1.2.0
- Added new feature X
- Fixed bug in Y component
- Improved performance of Z operation

## 1.1.0
- Added support for Home Assistant 2024.12
```

**Why This Matters:**
Home Assistant Supervisor parses CHANGELOG.md to match the version in config.yaml:
1. Reads config.yaml → gets version (e.g., "1.2.0")
2. Looks for CHANGELOG.md
3. Parses markdown headings looking for exact match: `## 1.2.0`
4. Displays the content under that heading

If the version heading includes dates or other suffixes (e.g., `## 1.2.0 - 2024-12-30` or `## 1.2.0 - TBD`), Home Assistant will not find a match and will show "No changelog found".

**Automated Updates:**
The GitHub Actions workflow automatically adds a new CHANGELOG.md entry when versions are incremented. The workflow extracts commit messages and generates meaningful changelog entries:
- Single commits: Uses the commit message as the changelog entry
- Batch merges (2-5 commits): Includes all commit messages
- Large batches (6+ commits): Uses only the most recent commit message

You can manually edit these entries to add more detailed release notes if needed. Write clear, descriptive commit messages as they will automatically appear in the CHANGELOG.

When making changes, always update CHANGELOG.md with clear, user-friendly descriptions.

## Documentation

Key documentation files:
- **README.md**: Overview, features, quick start
- **DOCS.md**: Comprehensive user documentation
- **CONTRIBUTING.md**: Detailed contributor guidelines with all rules
- **STRUCTURE.md**: Repository structure and component descriptions
- **EXAMPLES.md**: Configuration examples
- **QUICKSTART.md**: Quick start guide
- **CHANGELOG.md**: Version history

When making changes that affect user-facing functionality, update the relevant documentation files.

## Safety Validations Checklist

Before any code is merged, verify:
- [ ] ❌ No pip install commands
- [ ] ❌ No writes to HA Python environment
- [ ] ❌ No runtime monkey-patching
- [ ] ❌ No integration imports (no executing integration code)
- [ ] ✅ Static inspection only
- [ ] ✅ Filesystem reads only (within appropriate boundaries)
- [ ] ✅ Supervisor-approved APIs only
- [ ] ✅ Appropriate language ("may", "could", not "will")
- [ ] ✅ No assumptions about user intent
- [ ] ✅ No blocking of user actions

## Common Tasks

### Debugging
Set log level to maximal in `ha_sentry/config.yaml`:
```yaml
log_level: "maximal"
```

### Accessing Logs
```bash
ha addons logs ha_sentry
```

### Testing Configuration Changes
Changes to `ha_sentry/config.yaml` require rebuilding and restarting the add-on.

## Additional Resources

- **Contributing Guide**: See CONTRIBUTING.md for complete rules and guidelines
- **Best Practices**: https://gh.io/copilot-coding-agent-tips
- **Home Assistant Add-on Documentation**: https://developers.home-assistant.io/docs/add-ons/
