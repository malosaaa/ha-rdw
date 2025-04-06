"""Diagnostics support for RDW Vehicle Information."""
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntry # Not strictly needed but good practice

from .const import DOMAIN, DIAG_CONFIG_ENTRY, DIAG_COORDINATOR_DATA, DIAG_OPTIONS
from .coordinator import RdwDataUpdateCoordinator


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: RdwDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    diagnostics_data = {
        DIAG_CONFIG_ENTRY: {
             "entry_id": entry.entry_id,
             "title": entry.title,
             "data": dict(entry.data), # Make serializable copy
             "options": dict(entry.options), # Make serializable copy
             "unique_id": entry.unique_id,
        },
        DIAG_OPTIONS: dict(entry.options), # Explicitly include options again for clarity
        DIAG_COORDINATOR_DATA: {
            "license_plate": coordinator.license_plate,
            "last_update_success": coordinator.last_update_success,
            "last_update_error": coordinator.last_update_error,
            "last_update_timestamp": coordinator.last_update_success_timestamp.isoformat() if coordinator.last_update_success_timestamp else None,
            "update_interval": coordinator.update_interval.total_seconds() if coordinator.update_interval else None,
            "consecutive_errors": coordinator.error_count,
            "data": coordinator.data, # Include the last fetched data
        }
    }

    return diagnostics_data

