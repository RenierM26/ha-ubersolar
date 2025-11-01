"""Diagnostics support for the UberSolar integration."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import format_mac

from .const import DOMAIN
from .coordinator import UbersolarDataUpdateCoordinator


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: UbersolarDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]
    status = coordinator.data or coordinator.device.status_data

    return {
        "entry": {
            "title": config_entry.title,
            "address": format_mac(config_entry.data.get(CONF_ADDRESS, "")),
        },
        "status": {
            address: {
                key: value.hex() if isinstance(value, (bytes, bytearray)) else value
                for key, value in device_status.items()
            }
            for address, device_status in status.items()
        },
    }
