"""Green Energy integration for Home Assistant."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS
from .coordinator import GreenEnergyCoordinator

_LOGGER = logging.getLogger(__name__)

type GreenEnergyConfigEntry = ConfigEntry[GreenEnergyCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: GreenEnergyConfigEntry) -> bool:
    """Set up Green Energy from a config entry."""
    coordinator = GreenEnergyCoordinator(hass, entry)

    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Start state listeners for monitored entities
    await coordinator.async_start_listeners()

    entry.async_on_unload(entry.add_update_listener(async_update_options))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: GreenEnergyConfigEntry) -> bool:
    """Unload a config entry."""
    coordinator: GreenEnergyCoordinator = entry.runtime_data

    # Stop state listeners
    await coordinator.async_stop_listeners()

    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_update_options(hass: HomeAssistant, entry: GreenEnergyConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)
