"""
Orphaned and broken entity analyzer for Home Assistant Sentry.

Identifies:
  - Orphaned entities: entity registry entries whose `config_entry_id` no
    longer resolves to a loaded config entry. These typically occur when a
    HACS integration or a manual integration is removed without the user
    removing the entities/devices/helpers it created.
  - Ghost entities: entities present in the entity registry but absent from
    /api/states. The platform exists in the registry, but the entity is not
    currently instantiated.
  - Broken config entries: config entries whose `state` is `not_loaded`,
    `setup_error`, `setup_retry`, `migration_error`, or `failed_unload`.
    These cause entities (and possibly devices/helpers) to malfunction.
  - Orphaned devices: devices whose `config_entries` list contains
    `entry_id` values that no longer resolve to a config entry.
  - Stale entities: entities whose `last_updated` (or, for helpers without
    last_updated, `created_at`) is older than a configured threshold and
    which are not associated with a currently-loaded config entry.

The analyzer is intentionally pure (no I/O). Callers (ha_client wrapper,
sentry_service) supply the registries. This makes the logic testable with
plain dict fixtures.

Safety: This module never modifies Home Assistant state. It only reads
registries and produces advisory information. All suggested resolutions
require explicit user action in Home Assistant.
"""
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Set

logger = logging.getLogger(__name__)

# Integrations whose config entries typically create helper entities.
# Used to identify helpers in the entity registry.
HELPER_DOMAINS: Set[str] = {
    "input_boolean",
    "input_number",
    "input_text",
    "input_select",
    "input_datetime",
    "input_button",
    "counter",
    "timer",
    "schedule",
    "template",
    "group",
}

# Config entry states that indicate a problem. Loaded is the healthy state.
BROKEN_CONFIG_ENTRY_STATES: Set[str] = {
    "not_loaded",
    "setup_error",
    "setup_retry",
    "migration_error",
    "failed_unload",
}


def _parse_iso8601(value):
    """Best-effort parse of an ISO 8601 timestamp. Returns None on failure."""
    if not value or not isinstance(value, str):
        return None
    candidate = value.strip()
    if not candidate:
        return None
    if candidate.endswith("Z"):
        candidate = candidate[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _now_utc():
    return datetime.now(timezone.utc)


def _is_helper(entity):
    """Return True if the entity appears to be a helper-style entity."""
    platform = entity.get("platform") or entity.get("config_entry_domain")
    if isinstance(platform, str) and platform in HELPER_DOMAINS:
        return True
    entity_id = entity.get("entity_id") or ""
    if isinstance(entity_id, str):
        for domain in HELPER_DOMAINS:
            if entity_id.startswith(f"{domain}."):
                return True
    return False


def _resolve_origin(entity, config_entries_by_id):
    """Return the owning config entry or None if the owner is missing."""
    entry_id = entity.get("config_entry_id")
    if not entry_id:
        return None
    if entry_id not in config_entries_by_id:
        return None
    return config_entries_by_id[entry_id]


def _build_config_entry_index(config_entries):
    """Index config entries by entry_id for O(1) lookup."""
    index = {}
    for entry in config_entries or []:
        entry_id = entry.get("entry_id")
        if entry_id:
            index[entry_id] = entry
    return index


def _build_states_index(states):
    """Return the set of entity_ids currently exposed via /api/states."""
    return {s.get("entity_id") for s in (states or []) if s.get("entity_id")}


def _suggest_orphan_entity_fixes(entity):
    """Generate user-actionable suggestions for an orphaned entity."""
    suggestions = []
    entity_id = entity.get("entity_id") or "this entity"
    is_helper = _is_helper(entity)

    if is_helper:
        suggestions.append(
            "This appears to be a helper owned by a removed integration. "
            "In Home Assistant, open Settings -> Devices & Services -> Entities, "
            f"locate '{entity_id}', and delete it if no longer needed."
        )
        suggestions.append(
            "If the entity is referenced by automations, scripts, or dashboards, "
            "update or remove those references before deleting the entity."
        )
    else:
        suggestions.append(
            "The integration that created this entity appears to have been "
            "removed or disabled. Reinstall or re-enable the integration via "
            "Settings -> Devices & Services to restore the entity."
        )
        suggestions.append(
            "If you no longer want this entity, remove it from "
            "Settings -> Devices & Services -> Entities."
        )

    if entity.get("disabled_by"):
        suggestions.append(
            f"Entity is currently disabled in the registry "
            f"({entity.get('disabled_by')}); enable it once the underlying "
            "integration is restored."
        )
    return suggestions


def _suggest_ghost_entity_fixes(entity, owner):
    """Generate suggestions for an entity registered but not in /api/states."""
    suggestions = [
        "The entity is in the registry but not currently exposed by Home "
        "Assistant. This may be transient (e.g. integration is still "
        f"starting). The owning config entry state is '{owner.get('state')}'."
    ]
    if owner.get("state") and owner.get("state") != "loaded":
        suggestions.append(
            "The owning config entry is not in the 'loaded' state. "
            "Check the Home Assistant logs for errors related to the "
            f"'{owner.get('domain')}' integration."
        )
    suggestions.append(
        "If the entity is no longer required, remove it via "
        "Settings -> Devices & Services -> Entities."
    )
    return suggestions


def _suggest_config_entry_fixes(entry):
    """Generate suggestions for a broken config entry."""
    domain = entry.get("domain") or "this integration"
    state = entry.get("state")
    suggestions = [
        f"Config entry for '{domain}' is in state '{state}'. Check the "
        "Home Assistant logs for details on why it failed to set up."
    ]
    if state == "setup_retry":
        suggestions.append(
            "Setup retry is in progress. If the entry remains in this state "
            "after the next restart, the integration may have a "
            "configuration issue that needs manual correction."
        )
    if state == "setup_error":
        suggestions.append(
            "Review the configuration options for this integration. "
            "Re-authentication or updated credentials may be required."
        )
    if state == "migration_error":
        suggestions.append(
            "A data migration failed. Reloading the integration after "
            "backing up its data may be required."
        )
    suggestions.append(
        "If the integration is no longer needed, remove it via "
        "Settings -> Devices & Services."
    )
    return suggestions


def _suggest_orphan_device_fixes(device, missing_entry_ids):
    """Generate suggestions for a device whose owning entry is missing."""
    suggestions = [
        f"Device '{device.get('name') or device.get('id')}' is still "
        "registered but its owning config entry has been removed."
    ]
    suggestions.append(
        "If the integration has been reinstalled, re-configuring it may "
        "re-link the device. Otherwise, remove the device from "
        "Settings -> Devices & Services -> Devices."
    )
    if missing_entry_ids:
        suggestions.append(
            f"Missing config entry IDs: {', '.join(missing_entry_ids)}"
        )
    return suggestions


def _suggest_stale_entity_fixes(entity, age_seconds):
    """Generate suggestions for a stale entity (no recent update)."""
    days = int(age_seconds // 86400)
    suggestions = [
        f"This entity has not been updated for {days} days. This may "
        "indicate a malfunctioning device or an integration that has "
        "stopped polling."
    ]
    suggestions.append(
        "Check the integration's status in Settings -> Devices & Services "
        "and review the Home Assistant logs for related errors."
    )
    suggestions.append(
        "If the device is no longer present, remove the entity to keep "
        "your registry tidy."
    )
    return suggestions


def analyze(
    *,
    entities=None,
    devices=None,
    config_entries=None,
    states=None,
    stale_threshold_days=30,
):
    """
    Run the orphan/broken analysis and return a structured report.

    Args:
        entities: Output of `config/entity_registry/list`.
        devices: Output of `config/device_registry/list`.
        config_entries: Output of `config/config_entries/get`.
        states: Output of `/api/states`.
        stale_threshold_days: Number of days without update before an
            entity is flagged as stale.

    Returns:
        Dict with summary counters and per-category advisory lists.
    """
    entities = entities or []
    devices = devices or []
    config_entries = config_entries or []
    states = states or []

    config_entries_by_id = _build_config_entry_index(config_entries)
    states_by_entity_id = _build_states_index(states)

    broken_config_entries = []
    for entry in config_entries:
        state = entry.get("state")
        if state in BROKEN_CONFIG_ENTRY_STATES:
            broken_config_entries.append({
                "entry_id": entry.get("entry_id"),
                "title": entry.get("title") or entry.get("domain"),
                "domain": entry.get("domain"),
                "state": state,
                "reason": entry.get("reason"),
                "suggestions": _suggest_config_entry_fixes(entry),
            })

    orphaned_entities = []
    ghost_entities = []
    for entity in entities:
        entry_id = entity.get("config_entry_id")
        if not entry_id:
            continue
        owner = _resolve_origin(entity, config_entries_by_id)
        if owner is None:
            orphaned_entities.append({
                "entity_id": entity.get("entity_id"),
                "name": entity.get("name") or entity.get("original_name"),
                "platform": entity.get("platform"),
                "config_entry_id": entry_id,
                "disabled_by": entity.get("disabled_by"),
                "is_helper": _is_helper(entity),
                "device_id": entity.get("device_id"),
                "area_id": entity.get("area_id"),
                "suggestions": _suggest_orphan_entity_fixes(entity),
            })
            continue
        if entity.get("entity_id") not in states_by_entity_id:
            ghost_entities.append({
                "entity_id": entity.get("entity_id"),
                "name": entity.get("name") or entity.get("original_name"),
                "platform": entity.get("platform"),
                "config_entry_id": entry_id,
                "config_entry_domain": owner.get("domain"),
                "config_entry_state": owner.get("state"),
                "is_helper": _is_helper(entity),
                "suggestions": _suggest_ghost_entity_fixes(entity, owner),
            })

    orphaned_devices = []
    for device in devices:
        device_entry_ids = device.get("config_entries") or []
        if not device_entry_ids:
            continue
        missing = [
            eid for eid in device_entry_ids if eid not in config_entries_by_id
        ]
        if not missing:
            continue
        orphaned_devices.append({
            "device_id": device.get("id"),
            "name": device.get("name") or device.get("name_by_user"),
            "manufacturer": device.get("manufacturer"),
            "model": device.get("model"),
            "missing_config_entry_ids": missing,
            "suggestions": _suggest_orphan_device_fixes(device, missing),
        })

    stale_entities = []
    threshold_seconds = max(stale_threshold_days, 0) * 24 * 3600
    now = _now_utc()
    if threshold_seconds > 0:
        for entity in entities:
            entry_id = entity.get("config_entry_id")
            if not entry_id or entry_id not in config_entries_by_id:
                continue
            owner = config_entries_by_id[entry_id]
            if owner.get("state") != "loaded":
                continue
            last_updated = _parse_iso8601(entity.get("last_updated"))
            if last_updated is None:
                last_updated = _parse_iso8601(entity.get("created_at"))
            if last_updated is None:
                continue
            age = (now - last_updated).total_seconds()
            if age < threshold_seconds:
                continue
            stale_entities.append({
                "entity_id": entity.get("entity_id"),
                "name": entity.get("name") or entity.get("original_name"),
                "platform": entity.get("platform"),
                "config_entry_domain": owner.get("domain"),
                "last_updated": entity.get("last_updated")
                or entity.get("created_at"),
                "days_since_update": int(age // 86400),
                "is_helper": _is_helper(entity),
                "suggestions": _suggest_stale_entity_fixes(entity, age),
            })

    return {
        "summary": {
            "total_entities": len(entities),
            "total_devices": len(devices),
            "total_config_entries": len(config_entries),
            "orphaned_entities": len(orphaned_entities),
            "ghost_entities": len(ghost_entities),
            "broken_config_entries": len(broken_config_entries),
            "orphaned_devices": len(orphaned_devices),
            "stale_entities": len(stale_entities),
        },
        "orphaned_entities": orphaned_entities,
        "ghost_entities": ghost_entities,
        "broken_config_entries": broken_config_entries,
        "orphaned_devices": orphaned_devices,
        "stale_entities": stale_entities,
    }
