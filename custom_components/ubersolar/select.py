"""Support for UberSolar."""
from __future__ import annotations

from dataclasses import dataclass
import logging

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


@dataclass
class UbersmartSelectEntityDescriptionMixin:
    """Mixin values for Ubersmart select entities."""

    method: list


@dataclass
class UbersmartSelectEntityDescription(
    SelectEntityDescription, UbersmartSelectEntityDescriptionMixin
):
    """Describe a Ubersmart select entity."""


SELECT_TYPE = UbersmartSelectEntityDescription(
    key="eSolenoidMode",
    name="Solenoid Mode",
    icon="mdi:electric-switch",
    entity_category=EntityCategory.CONFIG,
    options=["Off", "On", "Auto"],
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
        self._attr_current_option = SELECT_TYPE.options[self.data[self._selector]]

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        _LOGGER.debug(
            "Set %s value to %s for device %s", self._selector, option, self._address
        )

        switch_method = getattr(
            self._device, SELECT_TYPE.method[SELECT_TYPE.options.index(option)]
        )

        await switch_method()
        self._attr_current_option = option
        self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_current_option = SELECT_TYPE.options[self.data[self._selector]]
        super()._handle_coordinator_update()
