"""Diagnostics support for Green Energy integration."""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_TOKEN, CONF_INSTANCE_ID
from .coordinator import GreenEnergyCoordinator

TO_REDACT = {CONF_TOKEN}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: GreenEnergyCoordinator = config_entry.runtime_data

    return {
        "config_entry": async_redact_data(dict(config_entry.data), TO_REDACT),
        "options": dict(config_entry.options),
        "coordinator_data": coordinator.data,
        "monitored_entities": coordinator.monitored_entities,
        "last_update_success": coordinator.last_update_success,
    }
