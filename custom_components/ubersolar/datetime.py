"""Support for UberSolar."""

from __future__ import annotations

from datetime import datetime, tzinfo
import logging
from typing import cast

from homeassistant.components.datetime import DateTimeEntity, DateTimeEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_platform
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .coordinator import UbersolarDataUpdateCoordinator
from .entity import UbersolarEntity

# Initialize the logger
_LOGGER = logging.getLogger(__name__)
PARALLEL_UPDATES = 0

DATETIME_TYPE = DateTimeEntityDescription(
    key="lluTime",
    translation_key="device_time",
    entity_category=EntityCategory.CONFIG,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: entity_platform.AddEntitiesCallback,
) -> None:
    """Set up UberSolar based on a config entry."""
    coordinator: UbersolarDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([UbersmartDateTime(coordinator)])


class UbersmartDateTime(UbersolarEntity, DateTimeEntity):
    """Representation of a UberSolar DateTimeEntity."""

    def __init__(self, coordinator: UbersolarDataUpdateCoordinator) -> None:
        """Initialize the UberSmart device."""
        super().__init__(coordinator)
        self.entity_description = DATETIME_TYPE
        self._attr_unique_id = f"{coordinator.base_unique_id}-{DATETIME_TYPE.key}"

    @property
    def native_value(self) -> datetime | None:
        """Return the value reported by the datetime."""
        raw_value = self.data.get(DATETIME_TYPE.key)
        if raw_value is None:
            return None

        parsed = dt_util.parse_datetime(cast(str, raw_value))
        if parsed is None:
            return None

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt_util.UTC)

        return dt_util.as_local(parsed)

    async def async_set_value(self, value: datetime) -> None:
        """Change the date/time."""
        if value.tzinfo is None:
            tzinfo_value: tzinfo = dt_util.UTC
            if self.hass and self.hass.config and self.hass.config.time_zone:
                hass_tz = dt_util.get_time_zone(self.hass.config.time_zone)
                if hass_tz is not None:
                    tzinfo_value = hass_tz
            value = value.replace(tzinfo=tzinfo_value)

        await self._device.set_time(value.astimezone(dt_util.UTC))
