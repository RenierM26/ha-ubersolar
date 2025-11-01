"""Provides the UberSolar DataUpdateCoordinator."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from datetime import timedelta
import logging
import time

from bleak.backends.device import BLEDevice
from pyubersolar import UberSmart
from pyubersolar.models import UberSmartStatus

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class UbersolarDataUpdateCoordinator(DataUpdateCoordinator[dict[str, UberSmartStatus]]):
    """Class to manage fetching ubersolar data."""

    def __init__(
        self,
        hass: HomeAssistant,
        ble_device: BLEDevice,
        device: UberSmart,
        base_unique_id: str,
        device_name: str,
    ) -> None:
        """Initialize global ubersolar data updater."""

        self.ble_device = ble_device
        self.device: UberSmart = device
        self.device_name = device_name
        self.address = device.get_address()
        self.base_unique_id = base_unique_id
        self._last_poll_monotonic: float | None = None
        self._last_push_state: dict[str, UberSmartStatus] = {}
        self._initial_push_event: asyncio.Event = asyncio.Event()
        self._unsubscribe_device: Callable[[], None] | None = self.device.subscribe(
            self._handle_device_push
        )
        super().__init__(
            hass=hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=60),
            update_method=self._async_update_data,
        )

    def _handle_device_push(self) -> None:
        """Handle push updates from the device while connected."""

        snapshot = self._status_snapshot()
        current_state = snapshot.get(self.address, {})
        previous_state = self._last_push_state.get(self.address, {})

        changed_keys = sorted(
            key
            for key, value in current_state.items()
            if previous_state.get(key) != value
        )

        if changed_keys:
            _LOGGER.debug(
                "%s: Received push update; changed fields: %s",
                self.device.name,
                ", ".join(changed_keys),
            )
            self._last_push_state = {
                addr: state.copy() for addr, state in snapshot.items()
            }
            if not self._initial_push_event.is_set():
                self._initial_push_event.set()
            self.async_set_updated_data(snapshot)
            return

        if not self._last_push_state:
            _LOGGER.debug(
                "%s: Received initial push payload; forwarding to coordinator",
                self.device.name,
            )
            self._last_push_state = {
                addr: state.copy() for addr, state in snapshot.items()
            }
            if not self._initial_push_event.is_set():
                self._initial_push_event.set()
            self.async_set_updated_data(snapshot)
            return

        _LOGGER.debug(
            "%s: Received identical push payload; skipping coordinator update",
            self.device.name,
        )

    async def async_shutdown(self) -> None:
        """Clean up coordinator resources."""
        if self._unsubscribe_device:
            self._unsubscribe_device()
            self._unsubscribe_device = None
        await self.device.async_disconnect()
        await super().async_shutdown()

    async def _async_update_data(self) -> dict[str, UberSmartStatus]:
        """Fetch data from the device, polling only when needed."""
        seconds_since_last_poll: float | None = None
        if self._last_poll_monotonic is not None:
            seconds_since_last_poll = time.monotonic() - self._last_poll_monotonic

        if not self.device.poll_needed(seconds_since_last_poll):
            _LOGGER.debug(
                "%s: Skipping poll; using push data (last poll %.1fs ago)",
                self.device.name,
                seconds_since_last_poll or -1.0,
            )
            return self._status_snapshot()

        if not self._last_push_state:
            _LOGGER.debug(
                "%s: Awaiting initial push payload before polling",
                self.device.name,
            )
            try:
                await asyncio.wait_for(self._initial_push_event.wait(), timeout=5)
                self._initial_push_event.clear()
                return self._status_snapshot()
            except TimeoutError:
                _LOGGER.debug(
                    "%s: Initial push timeout expired; falling back to poll",
                    self.device.name,
                )

        _LOGGER.debug(
            "%s: Polling device for fresh data (last poll %.1fs ago)",
            self.device.name,
            seconds_since_last_poll or -1.0,
        )
        await self.device.update()
        self._last_poll_monotonic = time.monotonic()
        return self._status_snapshot()

    def _status_snapshot(self) -> dict[str, UberSmartStatus]:
        """Return a snapshot of the latest device status."""
        return {
            address: data.copy() for address, data in self.device.status_data.items()
        }
