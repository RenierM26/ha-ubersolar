"""Support for UberSolar."""
from __future__ import annotations

from datetime import datetime
import logging

from homeassistant.components.datetime import DateTimeEntity, DateTimeEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity import EntityCategory
from homeassistant.util import dt as dt_util
import ubersolar

from .const import DOMAIN
from .coordinator import UbersolarDataUpdateCoordinator
from .entity import UbersolarEntity

# Initialize the logger
_LOGGER = logging.getLogger(__name__)
PARALLEL_UPDATES = 0

DATETIME_TYPE = DateTimeEntityDescription(
    key="lluTime",
    name="Device Time",
    entity_category=EntityCategory.DIAGNOSTIC,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: entity_platform.AddEntitiesCallback,
) -> None:
    """Set up UberSolar based on a config entry."""
    coordinator: UbersolarDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(UbersmartDateTime(coordinator))


class UbersmartDateTime(UbersolarEntity, DateTimeEntity):
    """Representation of a UberSolar DateTimeEntity."""

    _device: ubersolar.UberSmart
    _attr_has_entity_name = True

    def __init__(self, coordinator: UbersolarDataUpdateCoordinator) -> None:
        """Initialize the UberSmart device."""
        super().__init__(coordinator)
        self.entity_description = DATETIME_TYPE
        self._attr_unique_id = f"{coordinator.base_unique_id}-{DATETIME_TYPE.key}"

    @property
    def native_value(self) -> datetime | None:
        """Return the value reported by the datetime."""
        return dt_util.parse_datetime(self.data["lluTime"])

    async def async_set_value(self, value: datetime) -> None:
        """Change the date/time."""
        await self._device.set_current_time()
