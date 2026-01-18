"""Sensor platform for Green Energy integration."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfTime
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
    """Set up Green Energy sensors."""
    coordinator: GreenEnergyCoordinator = config_entry.runtime_data

    entities = [
        GreenEnergySyncStatusSensor(coordinator, config_entry),
        GreenEnergyLastSyncSensor(coordinator, config_entry),
        GreenEnergyReadingsTodaySensor(coordinator, config_entry),
        GreenEnergyRecommendationSensor(coordinator, config_entry),
        GreenEnergySavingsSensor(coordinator, config_entry),
        GreenEnergyTariffRateSensor(coordinator, config_entry),
    ]

    async_add_entities(entities)


class GreenEnergyBaseSensor(CoordinatorEntity[GreenEnergyCoordinator], SensorEntity):
    """Base class for Green Energy sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: GreenEnergyCoordinator,
        config_entry: ConfigEntry,
        key: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{config_entry.data[CONF_INSTANCE_ID]}_{key}"
        self._attr_translation_key = key
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


class GreenEnergySyncStatusSensor(GreenEnergyBaseSensor):
    """Sensor for sync status."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self, coordinator: GreenEnergyCoordinator, config_entry: ConfigEntry
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry, "sync_status")

    @property
    def native_value(self) -> str:
        """Return the current sync status."""
        if self.coordinator.data is None:
            return "unknown"
        return self.coordinator.data.get("sync_status", "unknown")

    @property
    def icon(self) -> str:
        """Return the icon based on status."""
        status = self.native_value
        if status == "synced":
            return "mdi:cloud-check"
        if status == "syncing":
            return "mdi:cloud-sync"
        if status == "error":
            return "mdi:cloud-alert"
        return "mdi:cloud-question"


class GreenEnergyLastSyncSensor(GreenEnergyBaseSensor):
    """Sensor for last sync timestamp."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self, coordinator: GreenEnergyCoordinator, config_entry: ConfigEntry
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry, "last_sync")

    @property
    def native_value(self) -> datetime | None:
        """Return the last sync time."""
        if self.coordinator.data is None:
            return None
        last_sync = self.coordinator.data.get("last_sync")
        if last_sync:
            return datetime.fromisoformat(last_sync)
        return None


class GreenEnergyReadingsTodaySensor(GreenEnergyBaseSensor):
    """Sensor for readings uploaded today."""

    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:counter"

    def __init__(
        self, coordinator: GreenEnergyCoordinator, config_entry: ConfigEntry
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry, "readings_today")

    @property
    def native_value(self) -> int:
        """Return the number of readings uploaded today."""
        if self.coordinator.data is None:
            return 0
        return self.coordinator.data.get("readings_today", 0)


class GreenEnergyRecommendationSensor(GreenEnergyBaseSensor):
    """Sensor for current optimization recommendation."""

    _attr_icon = "mdi:lightbulb-on"

    def __init__(
        self, coordinator: GreenEnergyCoordinator, config_entry: ConfigEntry
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry, "recommendation")

    @property
    def native_value(self) -> str:
        """Return the current recommendation."""
        if self.coordinator.data is None:
            return "No data"
        return self.coordinator.data.get("recommendation", "No action needed")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        if self.coordinator.data is None:
            return {}
        return {
            "reason": self.coordinator.data.get("recommendation_reason"),
            "valid_until": self.coordinator.data.get("recommendation_expires"),
        }


class GreenEnergySavingsSensor(GreenEnergyBaseSensor):
    """Sensor for estimated savings today."""

    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.TOTAL
    _attr_native_unit_of_measurement = "GBP"
    _attr_suggested_display_precision = 2
    _attr_icon = "mdi:piggy-bank"

    def __init__(
        self, coordinator: GreenEnergyCoordinator, config_entry: ConfigEntry
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry, "savings_today")

    @property
    def native_value(self) -> float:
        """Return the savings in pounds."""
        if self.coordinator.data is None:
            return 0.0
        # API returns pence, convert to pounds
        pence = self.coordinator.data.get("savings_today", 0)
        return pence / 100


class GreenEnergyTariffRateSensor(GreenEnergyBaseSensor):
    """Sensor for current tariff rate."""

    _attr_native_unit_of_measurement = "p/kWh"
    _attr_suggested_display_precision = 2
    _attr_icon = "mdi:lightning-bolt"

    def __init__(
        self, coordinator: GreenEnergyCoordinator, config_entry: ConfigEntry
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry, "tariff_rate")

    @property
    def native_value(self) -> float | None:
        """Return the current tariff rate in pence per kWh."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("tariff_rate")
