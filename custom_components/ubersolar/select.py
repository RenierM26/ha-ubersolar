"""Support for UberSolar."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import cast

from homeassistant.components.select import SelectEntity, SelectEntityDescription
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


@dataclass(frozen=True, kw_only=True)
class UbersmartSelectEntityDescriptionMixin:
    """Mixin values for Ubersmart select entities."""

    method: list[str]


@dataclass(frozen=True, kw_only=True)
class UbersmartSelectEntityDescription(
    SelectEntityDescription, UbersmartSelectEntityDescriptionMixin
):
    """Describe a Ubersmart select entity."""


SELECT_TYPE = UbersmartSelectEntityDescription(
    key="eSolenoidMode",
    translation_key="solenoid_mode",
    icon="mdi:electric-switch",
    entity_category=EntityCategory.CONFIG,
    options=["off", "on", "auto"],
    method=["set_solinoid_off", "set_solinoid_on", "set_solinoid_auto"],
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: entity_platform.AddEntitiesCallback,
) -> None:
    """Set up UberSolar based on a config entry."""
    coordinator: UbersolarDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([UbersmartSelect(coordinator)])


class UbersmartSelect(UbersolarEntity, SelectEntity):
    """Representation of a UberSolar Selector."""

    def __init__(self, coordinator: UbersolarDataUpdateCoordinator) -> None:
        """Initialize the UberSmart device."""
        super().__init__(coordinator)
        self._selector = SELECT_TYPE.key
        self._attr_unique_id = f"{coordinator.base_unique_id}-{SELECT_TYPE.key}"
        self.entity_description = SELECT_TYPE
        options = cast("list[str]", SELECT_TYPE.options)
        current_index = cast(int, self.data.get(self._selector, 0))
        self._attr_current_option = options[current_index]

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        _LOGGER.debug(
            "Set %s value to %s for device %s", self._selector, option, self._address
        )

        options = cast("list[str]", SELECT_TYPE.options)
        switch_method = getattr(self._device, SELECT_TYPE.method[options.index(option)])

        await switch_method()
        self._attr_current_option = option
        self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        options = cast("list[str]", SELECT_TYPE.options)
        current_index = cast(int, self.data.get(self._selector, 0))
        self._attr_current_option = options[current_index]
        super()._handle_coordinator_update()
