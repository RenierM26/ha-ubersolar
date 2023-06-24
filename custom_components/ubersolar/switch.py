"""Support for UberSolar."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity import EntityCategory
import ubersolar

from .const import DOMAIN
from .coordinator import UbersolarDataUpdateCoordinator
from .entity import UbersolarEntity

# Initialize the logger
_LOGGER = logging.getLogger(__name__)
PARALLEL_UPDATES = 0


SWITCH_METHODS_LIST: dict[str, list] = {
    "bElementOn": ["turn_on_element", "turn_off_element"],
    "bPumpOn": ["turn_on_pump", "turn_off_pump"],
    "bHolidayMode": ["turn_on_holiday", "turn_off_holiday"],
}

SWITCH_TYPES: dict[str, SwitchEntityDescription] = {
    "bElementOn": SwitchEntityDescription(
        key="bElementOn",
        name="Element",
        icon="mdi:heating-coil",
        entity_category=EntityCategory.CONFIG,
    ),
    "bPumpOn": SwitchEntityDescription(
        key="bPumpOn",
        name="Pump",
        icon="mdi:water-pump",
        entity_category=EntityCategory.CONFIG,
    ),
    "bHolidayMode": SwitchEntityDescription(
        key="bHolidayMode",
        name="Holiday Mode",
        icon="mdi:beach",
        entity_category=EntityCategory.CONFIG,
    ),
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: entity_platform.AddEntitiesCallback,
) -> None:
    """Set up UberSolar based on a config entry."""
    coordinator: UbersolarDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [
        UbersmartSwitch(
            coordinator,
            switch,
        )
        for switch in coordinator.device.status_data[coordinator.address]
        if switch in SWITCH_TYPES
    ]

    async_add_entities(entities)


class UbersmartSwitch(UbersolarEntity, SwitchEntity):
    """Representation of a UberSolar switch."""

    _device: ubersolar.UberSmart
    _attr_has_entity_name = True

    def __init__(
        self, coordinator: UbersolarDataUpdateCoordinator, switch: str
    ) -> None:
        """Initialize the UberSmart device."""
        super().__init__(coordinator)
        self._switch = switch
        self._attr_unique_id = f"{coordinator.base_unique_id}-{switch}"
        self.entity_description = SWITCH_TYPES[switch]

    @property
    def is_on(self) -> bool | None:
        """Return true if device is on."""
        return self.data[self._switch]

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn device on."""
        _LOGGER.info("Turn %s on for device %s", self._switch, self._address)

        switch_method = getattr(self._device, SWITCH_METHODS_LIST[self._switch][0])

        await switch_method()
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn device off."""
        _LOGGER.info("Turn %s off for device %s", self._switch, self._address)

        switch_method = getattr(self._device, SWITCH_METHODS_LIST[self._switch][1])

        await switch_method()
        self.async_write_ha_state()
