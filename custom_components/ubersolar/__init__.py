"""Support for UberSolar devices."""

import logging

import ubersolar

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, CONF_NAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import CONF_RETRY_COUNT, DEFAULT_RETRY_COUNT, DOMAIN
from .coordinator import UbersolarDataUpdateCoordinator

PLATFORMS: list[Platform] = [
    Platform.DATETIME,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up UberSolar from a config entry."""
    assert entry.unique_id is not None
    hass.data.setdefault(DOMAIN, {})

    if not entry.options:
        hass.config_entries.async_update_entry(
            entry,
            options={CONF_RETRY_COUNT: DEFAULT_RETRY_COUNT},
        )

    address: str = entry.data[CONF_ADDRESS]
    ble_device = bluetooth.async_ble_device_from_address(hass, address.upper(), True)
    if not ble_device:
        raise ConfigEntryNotReady(
            f"Could not find UberSolar device with address {address}"
        )

    await ubersolar.close_stale_connections(ble_device)

    device = ubersolar.UberSmart(
        device=ble_device, retry_count=entry.options[CONF_RETRY_COUNT]
    )

    coordinator = hass.data[DOMAIN][entry.entry_id] = UbersolarDataUpdateCoordinator(
        hass=hass,
        logger=_LOGGER,
        ble_device=ble_device,
        device=device,
        base_unique_id=entry.unique_id,
        device_name=entry.data.get(CONF_NAME, entry.title),
    )

    await coordinator.async_config_entry_first_refresh()

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.config_entries.async_entries(DOMAIN):
            hass.data.pop(DOMAIN)

    return unload_ok
