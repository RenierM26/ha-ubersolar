"""Support for UberSolar."""
from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_platform

from .const import DOMAIN
from .coordinator import UbersolarDataUpdateCoordinator
from .entity import UbersolarEntity

# Initialize the logger
_LOGGER = logging.getLogger(__name__)
PARALLEL_UPDATES = 0


@dataclass
class UbersmartSwitchEntityDescriptionMixin:
    """Mixin values for Ubersmart switch entities."""

    method: list


@dataclass
class UbersmartSwitchEntityDescription(
    SwitchEntityDescription, UbersmartSwitchEntityDescriptionMixin
):
    """Describe a Ubersmart switch entity."""


SWITCH_TYPES: dict[str, UbersmartSwitchEntityDescription] = {
    "bElementOn": UbersmartSwitchEntityDescription(
        key="bElementOn",
        name="Element",
        icon="mdi:heating-coil",
        entity_category=EntityCategory.CONFIG,
        method=["turn_on_element", "turn_off_element"],
    ),
    "bPumpOn": UbersmartSwitchEntityDescription(
        key="bPumpOn",
        name="Pump",
        icon="mdi:water-pump",
        entity_category=EntityCategory.CONFIG,
        method=["turn_on_pump", "turn_off_pump"],
    ),
    "bHolidayMode": UbersmartSwitchEntityDescription(
        key="bHolidayMode",
        name="Holiday Mode",
        icon="mdi:beach",
        entity_category=EntityCategory.CONFIG,
        method=["turn_on_holiday", "turn_off_holiday"],
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

    entity_description: UbersmartSwitchEntityDescription

    def __init__(
        self, coordinator: UbersolarDataUpdateCoordinator, switch: str
    ) -> None:
        """Initialize the UberSmart device."""
        super().__init__(coordinator)
        self._switch = switch
        self._attr_unique_id = f"{coordinator.base_unique_id}-{switch}"
        self.entity_description = SWITCH_TYPES[switch]
        self._attr_is_on = self.data[switch]

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn device on."""
        _LOGGER.debug("Turn %s on for device %s", self._switch, self._address)

        switch_method = getattr(self._device, self.entity_description.method[0])

        await switch_method()
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn device off."""
        _LOGGER.debug("Turn %s off for device %s", self._switch, self._address)

        switch_method = getattr(self._device, self.entity_description.method[1])

        await switch_method()
        self._attr_is_on = False
        self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_is_on = self.data[self._switch]
        super()._handle_coordinator_update()
