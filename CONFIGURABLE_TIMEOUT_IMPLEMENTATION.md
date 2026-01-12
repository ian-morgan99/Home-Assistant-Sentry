# Configurable Installation Review Timeout - Implementation Summary

## User Request

User requested making the installation review timeout configurable instead of hardcoded, with a default of 20 minutes. The rationale:
- Local AI can be slow
- AI may have queued requests  
- Reviews run overnight, so urgency is not a concern
- The app doesn't need results immediately

## Implementation

### 1. Configuration Parameter Added

**Parameter**: `installation_review_timeout`
- **Default**: 1200 seconds (20 minutes)
- **Range**: 60-3600 seconds (1 minute to 1 hour)
- **Type**: Integer

### 2. Files Modified

#### ha_sentry/config.yaml
- Added `installation_review_timeout` to options with default of 1200
- Added schema validation: `int(60,3600)`
- Added comprehensive documentation explaining:
  - When to increase (slow AI, reasoning models, queued requests)
  - When to decrease (fast AI, quick failure detection)
  - That reviews run overnight so longer timeouts are acceptable
  - Example values for different scenarios

#### ha_sentry/rootfs/app/config_manager.py
- Added `self.installation_review_timeout` configuration property
- Reads from `INSTALLATION_REVIEW_TIMEOUT` environment variable
- Default: 1200 seconds if not specified
- Added validation in `_validate_config()`:
  - Ensures value is between 60 and 3600 seconds
  - Resets to default (1200) if out of range
  - Logs error if invalid

#### ha_sentry/rootfs/app/installation_reviewer.py
- Changed from hardcoded `timeout_seconds = 300.0` 
- Now uses `timeout_seconds = float(self.config.installation_review_timeout)`
- Updated comments to reflect configurability
- Removed TODO comment about making it configurable

#### tests/test_installation_review_timeout.py
- Renamed test from `test_timeout_value_is_300_seconds` to `test_timeout_is_configurable`
- Verifies timeout is read from config, not hardcoded
- Verifies config.yaml has the parameter
- Verifies default value is 1200 seconds
- All assertions updated for new behavior

## Testing Results

All tests pass (9/9):
- ✅ Timeout configurability test (4/4)
- ✅ Log message tests (2/2)
- ✅ Scheduling tests (3/3)
- ✅ Python syntax validation passed

## Backward Compatibility

**Fully backward compatible**:
- Existing installations will use default of 1200 seconds (20 minutes)
- Previous hardcoded 300 seconds was too short; new 1200 default is better
- No configuration changes required for existing users
- Optional configuration for users who want to customize

## Configuration Examples

### Default (Recommended)
```yaml
installation_review_timeout: 1200  # 20 minutes
```

### For Slow AI or Queued Systems
```yaml
installation_review_timeout: 1800  # 30 minutes
installation_review_timeout: 2400  # 40 minutes
```

### For Fast Local AI
```yaml
installation_review_timeout: 600   # 10 minutes
installation_review_timeout: 900   # 15 minutes
```

### Maximum Allowed
```yaml
installation_review_timeout: 3600  # 1 hour
```

## Benefits

1. **Flexibility**: Users can adjust based on their specific AI provider and hardware
2. **Better Default**: 20 minutes (vs previous 5 minutes) accommodates reasoning models
3. **Queue-Friendly**: Long enough for local AI with request queues
4. **No Urgency**: Since reviews run overnight, longer timeouts don't impact UX
5. **Validation**: Ensures timeout stays within reasonable bounds (1 min to 1 hour)

## User Communication

Replied to user's comment (ID: 3649430639) confirming:
- Timeout is now configurable
- Default is 20 minutes as requested
- Range is 60-3600 seconds
- Accommodates slow/queued local AI
- Commit hash: 95ed825

## Commit Details

**Commit**: 95ed825
**Message**: Make installation review timeout configurable with 20 minute default
**Changes**:
- Configuration parameter added with validation
- Documentation added to config.yaml
- Implementation updated to use configured value
- Tests updated to verify configurability
- All tests pass

## Documentation

Configuration documentation added to `ha_sentry/config.yaml` includes:
- Parameter description and purpose
- Default value and range
- When to increase timeout (slow AI, reasoning models, queues)
- When to decrease timeout (fast AI, quick failure detection)
- Examples for different scenarios
- Explanation that reviews run overnight so longer timeouts are acceptable
