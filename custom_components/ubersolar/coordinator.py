"""Provides the UberSolar DataUpdateCoordinator."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import TYPE_CHECKING

from ubersolar import UberSmart

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN

if TYPE_CHECKING:
    from bleak.backends.device import BLEDevice

_LOGGER = logging.getLogger(__name__)


class UbersolarDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching ubersolar data."""

    def __init__(
        self,
        hass: HomeAssistant,
        logger: logging.Logger,
        ble_device: BLEDevice,
        device: UberSmart,
        base_unique_id: str,
        device_name: str,
    ) -> None:
        """Initialize global ubersolar data updater."""

        self.ble_device = ble_device
        self.device = device
        self.device_name = device_name
        self.address = device.get_address()
        self.base_unique_id = base_unique_id
        super().__init__(
            hass=hass,
            logger=logger,
            name=DOMAIN,
            update_interval=timedelta(seconds=60),
            update_method=device.update,
        )
