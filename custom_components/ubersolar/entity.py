"""An abstract class common to all UberSolar entities."""

from __future__ import annotations

import logging
from typing import cast

from pyubersolar import UberSmart
from pyubersolar.models import UberSmartStatus

from homeassistant.components import bluetooth
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
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
        connections: set[tuple[str, str]] = {(dr.CONNECTION_BLUETOOTH, self._address)}
        if ":" in self._address:
            # If the bluetooth address is also a mac address,
            # add this connection as well to prevent a new device
            # entry from being created when upgrading from a previous
            # version of the integration.
            connections.add((dr.CONNECTION_NETWORK_MAC, self._address))
        else:
            # MacOS Bluetooth addresses are not mac addresses
            _LOGGER.debug(
                "%s: Address lacks colon; skipping MAC connection", self._address
            )

        self._attr_device_info = DeviceInfo(
            connections=connections,
            manufacturer=MANUFACTURER,
            model=MODEL,
            name=coordinator.device_name,
        )

    @property
    def data(self) -> UberSmartStatus:
        """Return coordinator data for this entity."""
        coordinator_data = cast(
            object,
            getattr(self.coordinator, "data", None),
        )
        if isinstance(coordinator_data, dict) and self._address in coordinator_data:
            return cast(UberSmartStatus, coordinator_data[self._address])
        return cast(UberSmartStatus, self.coordinator.device.status_data[self._address])

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return super().available and bluetooth.async_address_present(
            self.hass, self._address, True
        )
