"""DataUpdateCoordinator for Green Energy integration."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback, Event
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.debounce import Debouncer
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    GreenEnergyApiClient,
    CannotConnect,
    AuthenticationError,
    GreenEnergyApiError,
)
from .const import (
    DOMAIN,
    CONF_TOKEN,
    CONF_INSTANCE_ID,
    CONF_API_URL,
    CONF_SOLAR_ENTITY,
    CONF_BATTERY_ENTITY,
    CONF_GRID_ENTITY,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_API_URL,
)

_LOGGER = logging.getLogger(__name__)

REQUEST_REFRESH_DEBOUNCER_COOLDOWN = 5.0


class GreenEnergyCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for Green Energy data sync."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        api_url = config_entry.data.get(CONF_API_URL, DEFAULT_API_URL)
        self._api_client = GreenEnergyApiClient(
            session=async_get_clientsession(hass),
            api_url=api_url,
            token=config_entry.data[CONF_TOKEN],
            instance_id=config_entry.data[CONF_INSTANCE_ID],
        )
        self._data_buffer: list[dict[str, Any]] = []
        self._unsub_listeners: list[callable] = []
        self._upload_task: asyncio.Task | None = None
        self._last_upload: datetime | None = None
        self._readings_today: int = 0
        self._readings_today_date: str | None = None

        scan_interval = config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
            request_refresh_debouncer=Debouncer(
                hass,
                _LOGGER,
                cooldown=REQUEST_REFRESH_DEBOUNCER_COOLDOWN,
                immediate=False,
            ),
        )

    @property
    def instance_id(self) -> str:
        """Return the instance ID."""
        return self.config_entry.data[CONF_INSTANCE_ID]

    @property
    def monitored_entities(self) -> list[str]:
        """Return list of monitored entity IDs."""
        entities = []
        for key in (CONF_SOLAR_ENTITY, CONF_BATTERY_ENTITY, CONF_GRID_ENTITY):
            entity_id = self.config_entry.options.get(key)
            if entity_id:
                entities.append(entity_id)
        return entities

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API and upload buffered readings."""
        # Upload any buffered data
        await self._async_upload_buffered_data()

        # Fetch current status from cloud
        try:
            status = await self._api_client.async_get_status()
        except AuthenticationError as err:
            raise UpdateFailed(f"Authentication failed: {err}") from err
        except CannotConnect as err:
            raise UpdateFailed(f"Cannot connect: {err}") from err
        except GreenEnergyApiError as err:
            raise UpdateFailed(f"API error: {err}") from err

        # Track readings count per day
        today = datetime.now().date().isoformat()
        if self._readings_today_date != today:
            self._readings_today = 0
            self._readings_today_date = today

        return {
            "connected": True,
            "sync_status": "synced",
            "last_sync": datetime.now().isoformat(),
            "readings_today": self._readings_today,
            "recommendation": status.get("recommendation", "No action needed"),
            "recommendation_reason": status.get("recommendation_reason"),
            "recommendation_expires": status.get("recommendation_expires"),
            "savings_today": status.get("savings_today_pence", 0),
            "tariff_rate": status.get("current_rate_pence"),
        }

    async def async_start_listeners(self) -> None:
        """Start listening for state changes on monitored entities."""
        entities = self.monitored_entities
        if not entities:
            _LOGGER.debug("No entities configured to monitor")
            return

        _LOGGER.debug("Starting state listeners for: %s", entities)

        unsub = async_track_state_change_event(
            self.hass,
            entities,
            self._handle_state_change,
        )
        self._unsub_listeners.append(unsub)

    async def async_stop_listeners(self) -> None:
        """Stop all state listeners."""
        for unsub in self._unsub_listeners:
            unsub()
        self._unsub_listeners.clear()

        # Cancel any pending upload task
        if self._upload_task and not self._upload_task.done():
            self._upload_task.cancel()

    @callback
    def _handle_state_change(self, event: Event) -> None:
        """Handle state change events for monitored entities."""
        entity_id = event.data["entity_id"]
        new_state = event.data.get("new_state")

        if new_state is None:
            return

        # Buffer the reading
        reading = {
            "entity_id": entity_id,
            "state": new_state.state,
            "attributes": {
                k: v
                for k, v in new_state.attributes.items()
                if k in ("unit_of_measurement", "device_class", "state_class", "friendly_name")
            },
            "timestamp": new_state.last_updated.isoformat(),
        }
        self._data_buffer.append(reading)

        _LOGGER.debug("Buffered reading for %s: %s", entity_id, new_state.state)

        # Schedule debounced upload
        self._schedule_upload()

    def _schedule_upload(self) -> None:
        """Schedule an upload task with debouncing."""
        if self._upload_task and not self._upload_task.done():
            return  # Upload already scheduled

        self._upload_task = self.hass.async_create_task(
            self._async_debounced_upload()
        )

    async def _async_debounced_upload(self) -> None:
        """Wait for debounce period then upload."""
        await asyncio.sleep(5.0)  # 5 second debounce
        await self._async_upload_buffered_data()
        await self.async_request_refresh()

    async def _async_upload_buffered_data(self) -> None:
        """Upload buffered readings to cloud."""
        if not self._data_buffer:
            return

        readings = self._data_buffer.copy()
        self._data_buffer.clear()

        try:
            _LOGGER.debug("Uploading %d readings", len(readings))
            await self._api_client.async_post_readings(readings)
            self._last_upload = datetime.now()
            self._readings_today += len(readings)
        except GreenEnergyApiError as err:
            _LOGGER.error("Failed to upload readings: %s", err)
            # Put readings back in buffer for retry
            self._data_buffer.extend(readings)
