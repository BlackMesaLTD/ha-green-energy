"""Binary sensor platform for Green Energy integration."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, VERSION, CONF_INSTANCE_ID
from .coordinator import GreenEnergyCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Green Energy binary sensors."""
    coordinator: GreenEnergyCoordinator = config_entry.runtime_data

    async_add_entities([GreenEnergyConnectedSensor(coordinator, config_entry)])


class GreenEnergyConnectedSensor(
    CoordinatorEntity[GreenEnergyCoordinator], BinarySensorEntity
):
    """Binary sensor for cloud connection status."""

    _attr_has_entity_name = True
    _attr_translation_key = "connected"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self, coordinator: GreenEnergyCoordinator, config_entry: ConfigEntry
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{config_entry.data[CONF_INSTANCE_ID]}_connected"
        self._config_entry = config_entry

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._config_entry.data[CONF_INSTANCE_ID])},
            name="Green Energy",
            manufacturer="Green Energy Ltd",
            model="Cloud Integration",
            configuration_url="https://green-energy-topaz.vercel.app/dashboard",
            sw_version=VERSION,
        )

    @property
    def is_on(self) -> bool:
        """Return True if connected to cloud."""
        if self.coordinator.data is None:
            return False
        return self.coordinator.data.get("connected", False)
