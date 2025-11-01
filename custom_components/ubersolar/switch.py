"""Support for UberSolar."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

from homeassistant.components.switch import (
    SwitchDeviceClass,
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_platform

from .const import DOMAIN
from .coordinator import UbersolarDataUpdateCoordinator
from .entity import UbersolarEntity

# Initialize the logger
_LOGGER = logging.getLogger(__name__)
PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class UbersmartSwitchEntityDescriptionMixin:
    """Mixin values for Ubersmart switch entities."""

    method: list[str]


@dataclass(frozen=True, kw_only=True)
class UbersmartSwitchEntityDescription(
    SwitchEntityDescription, UbersmartSwitchEntityDescriptionMixin
):
    """Describe a Ubersmart switch entity."""


SWITCH_TYPES: dict[str, UbersmartSwitchEntityDescription] = {
    "bElementOn": UbersmartSwitchEntityDescription(
        key="bElementOn",
        translation_key="element",
        entity_category=EntityCategory.CONFIG,
        device_class=SwitchDeviceClass.SWITCH,
        method=["turn_on_element", "turn_off_element"],
    ),
    "bPumpOn": UbersmartSwitchEntityDescription(
        key="bPumpOn",
        translation_key="pump",
        entity_category=EntityCategory.CONFIG,
        device_class=SwitchDeviceClass.SWITCH,
        method=["turn_on_pump", "turn_off_pump"],
    ),
    "bHolidayMode": UbersmartSwitchEntityDescription(
        key="bHolidayMode",
        translation_key="holiday_mode",
        entity_category=EntityCategory.CONFIG,
        device_class=SwitchDeviceClass.SWITCH,
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

    async_add_entities(
        [
            UbersmartSwitch(
                coordinator=coordinator,
                switch=key,
            )
            for key in SWITCH_TYPES
        ],
        update_before_add=False,
    )


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

    @property
    def is_on(self) -> bool:
        """Return if the switch is on."""
        return bool(self.data.get(self._switch))

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn device on."""
        _LOGGER.debug("Turn %s on for device %s", self._switch, self._address)

        switch_method = getattr(self._device, self.entity_description.method[0])

        await switch_method()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn device off."""
        _LOGGER.debug("Turn %s off for device %s", self._switch, self._address)

        switch_method = getattr(self._device, self.entity_description.method[1])

        await switch_method()
