"""An abstract class common to all UberSolar entities."""
from __future__ import annotations

import logging
from typing import Any

from ubersolar import UberSmart

from homeassistant.components import bluetooth
from homeassistant.const import ATTR_CONNECTIONS
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import DeviceInfo, Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import MANUFACTURER, MODEL
from .coordinator import UbersolarDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


class UbersolarEntity(CoordinatorEntity[UbersolarDataUpdateCoordinator], Entity):
    """Generic entity encapsulating common features of UberSolar device."""

    coordinator: UbersolarDataUpdateCoordinator
    _device: UberSmart
    _attr_has_entity_name = True

    def __init__(self, coordinator: UbersolarDataUpdateCoordinator) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._device = coordinator.device
        self._address = coordinator.address
        self._attr_unique_id = coordinator.base_unique_id
        self._attr_device_info = DeviceInfo(
            connections={(dr.CONNECTION_BLUETOOTH, self._address)},
            manufacturer=MANUFACTURER,
            model=MODEL,
            name=coordinator.device_name,
        )
        if ":" not in self._address:
            # MacOS Bluetooth addresses are not mac addresses
            return
        # If the bluetooth address is also a mac address,
        # add this connection as well to prevent a new device
        # entry from being created when upgrading from a previous
        # version of the integration.
        self._attr_device_info[ATTR_CONNECTIONS].add(
            (dr.CONNECTION_NETWORK_MAC, self._address)
        )

    @property
    def data(self) -> dict[str, Any]:
        """Return coordinator data for this entity."""
        return self.coordinator.device.status_data[self._address]

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return super().available and bluetooth.async_address_present(
            self.hass, self._address, True
        )
