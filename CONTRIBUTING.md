# Contributing to Home Assistant Sentry

Thank you for your interest in contributing to Home Assistant Sentry! This document outlines the principles, rules, and guidelines that all contributors must follow.

## Product Goal

**Home-Assistant-Sentry exists to explain update risk before the user updates, without modifying or interfering with Home Assistant's runtime.**

### Key Principles

- **Advisory, not intrusive**: We provide information and recommendations, never taking action on behalf of the user
- **Predictive, not reactive**: We analyze before updates happen, not after
- **Read-only by default**: We observe and analyze, never modify
- **Zero-risk to HA stability**: Our add-on must never cause Home Assistant to fail or become unstable

## Hard Rules (Non-Negotiable)

All contributors must adhere to these fundamental rules:

### What Sentry NEVER Does

1. ❌ **Sentry never changes system state**
   - No modifications to Home Assistant configuration
   - No changes to integration files
   - No database modifications
   - No file system writes except for its own logs and reports

2. ❌ **Sentry never "fixes" issues**
   - No automatic patching
   - No automatic configuration updates
   - No automatic dependency resolution
   - If you're tempted to "auto-fix" something → stop and reconsider

3. ❌ **Sentry never blocks updates**
   - We may warn and advise caution
   - We may recommend delaying
   - But we NEVER prevent the user from updating

4. ❌ **Sentry never assumes user intent**
   - We provide information
   - The user decides what to do with it
   - No "smart" automatic actions based on preferences

### What Sentry NEVER Touches

1. ❌ **No pip install**
   - Never install, upgrade, or modify Python packages in HA's environment
   - Never run pip commands
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
   - Static inspection only
   - Read manifest files, don't execute integration code

### What Sentry ONLY Does

✅ **Static inspection only**
- Read and parse manifest.json files
- Read configuration files (read-only)
- Analyze file metadata

✅ **Filesystem reads only**
- Read files to gather information
- Never write outside our designated directories
- Never modify any HA files

✅ **Supervisor-approved APIs only**
- Use official Home Assistant APIs
- Use official Supervisor APIs
- Never circumvent API security

## Language Rules

When writing user-facing messages, documentation, or code comments about risks:

### ✅ Use These Words
- "may"
- "could"
- "might"
- "possible"
- "potential"
- "risk of"
- "could affect"
- "may impact"

### ❌ Never Use These Words
- "will break"
- "will fail"
- "guaranteed to"
- "definitely"
- "certainly will"

### Examples

**Good:**
> ⚠️ Updating to HA 2025.1 may affect custom_component_x (requires <=2024.12)

**Bad:**
> ❌ Updating to HA 2025.1 will break custom_component_x

**Good:**
> This update could cause compatibility issues with 3 integrations.

**Bad:**
> ❌ This update will break 3 integrations.

## Safety Validations (Critical)

Before any code is merged, it must prove:

### Code Review Checklist

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

## Accuracy Validations

Before releasing new features, test against:

### Test Scenarios

1. **Clean HA OS install**
   - Fresh installation with no custom integrations
   - Verify basic functionality

2. **Heavy HACS system**
   - System with 50+ HACS integrations
   - Verify performance and accuracy

3. **Broken / partial integrations**
   - Malformed manifest.json files
   - Missing required fields
   - Invalid version strings
   - Verify graceful handling without crashes

### Expected Behaviors

- ✅ No crashes on malformed manifests
- ✅ No assumptions about install type (HA OS vs. Container vs. Core)
- ✅ Graceful degradation when data is unavailable
- ✅ Clear error messages for users

## Performance Validations

All features must meet these performance targets:

- **Graph build**: < 2 seconds for 200+ integrations
- **Memory footprint**: < 200MB
- **No continuous background scanning**: Only scheduled checks
- **Efficient API usage**: Minimize API calls to HA

### Performance Testing

Test with:
- Small systems (< 20 integrations)
- Medium systems (20-100 integrations)
- Large systems (100-200+ integrations)

## Development Guidelines

### Adding New Features

1. **Design First**: Ensure the feature aligns with product goal
2. **Read-Only Check**: Verify feature doesn't modify system state
3. **API Usage**: Use only approved APIs
4. **Error Handling**: Handle all error cases gracefully
5. **Testing**: Add tests for normal and edge cases
6. **Documentation**: Update relevant docs

### Code Style

- Follow PEP 8 for Python code
- Use type hints where appropriate
- Add docstrings to functions and classes
- Use descriptive variable names
- Keep functions focused and small

### Logging

- Use appropriate log levels:
  - `DEBUG`: Detailed diagnostic information
  - `INFO`: General informational messages
  - `WARNING`: Warning messages for potential issues
  - `ERROR`: Error messages for failures

### Testing

- Add unit tests for new functionality
- Test error paths and edge cases
- Verify no side effects
- Test with various system configurations

## What "Brilliant" Looks Like

✅ A user opens Sentry and immediately understands:
- What depends on what
- What's fragile
- Whether today is a good day to update

✅ A cautious user delays fewer updates (more confidence)

✅ A confident user updates faster (better information)

✅ Nothing ever breaks because of Sentry

## Submitting Changes

### Pull Request Guidelines

1. **Clear Description**: Explain what changes and why
2. **Testing Evidence**: Show that you've tested the changes
3. **Documentation Updates**: Update docs if needed
4. **Safety Checklist**: Confirm all safety validations pass
5. **No Breaking Changes**: Ensure backward compatibility

### PR Checklist

Before submitting a PR, verify:

- [ ] Code follows all hard rules
- [ ] Appropriate language used in user-facing text
- [ ] Tests added for new functionality
- [ ] Tests pass
- [ ] Documentation updated
- [ ] Performance targets met
- [ ] No system state modifications
- [ ] Graceful error handling

## Questions?

If you're unsure whether something aligns with our principles:

1. Ask yourself: "Does this modify Home Assistant's state?"
   - If yes → don't do it
2. Ask yourself: "Does this assume user intent?"
   - If yes → don't do it
3. Ask yourself: "Could this break Home Assistant?"
   - If yes → don't do it

When in doubt, open an issue to discuss before implementing.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
