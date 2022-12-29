"""Support for UberSolar."""
from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity, SelectEntityDescription
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


SELECT_METHODS_LIST: dict[str, list] = {
    "eSolenoidMode": ["set_solinoid_off", "set_solinoid_on", "set_solinoid_auto"],
}

SELECT_TYPES: dict[str, SelectEntityDescription] = {
    "eSolenoidMode": SelectEntityDescription(
        key="eSolenoidMode",
        name="Solenoid Mode",
        icon="mdi:electric-switch",
        entity_category=EntityCategory.CONFIG,
        options=[0, 1, 2],
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
        UbersmartSelect(
            coordinator,
            selector,
        )
        for selector in coordinator.device.status_data[coordinator.address]
        if selector in SELECT_TYPES
    ]

    async_add_entities(entities)


class UbersmartSelect(UbersolarEntity, SelectEntity):
    """Representation of a UberSolar Selector."""

    _device: ubersolar.UberSmart
    _attr_has_entity_name = True

    def __init__(
        self, coordinator: UbersolarDataUpdateCoordinator, selector: str
    ) -> None:
        """Initialize the UberSmart device."""
        super().__init__(coordinator)
        self._selector = selector
        self._attr_unique_id = f"{coordinator.base_unique_id}-{selector}"
        self.entity_description = SELECT_TYPES[selector]

    @property
    def current_option(self) -> str | None:
        """Return the selected entity option to represent the entity state."""
        return self.data[self._selector]

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        _LOGGER.info(
            "Set %s value to %s for device %s", self._selector, option, self._address
        )

        switch_method = getattr(
            self._device, SELECT_METHODS_LIST[self._selector][option]
        )

        await switch_method()
        await self.coordinator.async_request_refresh()
