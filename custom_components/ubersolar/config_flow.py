"""Config flow for UberSolar."""

from __future__ import annotations

import logging
from typing import Any, cast

from pyubersolar import UberSolarAdvertisement
import voluptuous as vol

from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithReload,
)
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import callback
from homeassistant.data_entry_flow import AbortFlow

from .const import CONF_RETRY_COUNT, DEFAULT_NAME, DEFAULT_RETRY_COUNT, DOMAIN

_LOGGER = logging.getLogger(__name__)
ConfigFlowAny = cast(Any, ConfigFlow)


def format_unique_id(address: str) -> str:
    """Format the unique ID for a UberSolar."""
    return address.replace(":", "").lower()


def short_address(address: str) -> str:
    """Convert a Bluetooth address to a short address."""
    results = address.replace("-", ":").split(":")
    return f"{results[-2].upper()}{results[-1].upper()}"[-4:]


class UbersolarConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for UberSolar."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> UbersolarOptionsFlowHandler:
        """Get the options flow for this handler."""
        return UbersolarOptionsFlowHandler()

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovered_adv: UberSolarAdvertisement | None = None
        self._discovered_advs: dict[str, UberSolarAdvertisement] = {}

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> ConfigFlowResult:
        """Handle the bluetooth discovery step."""
        _LOGGER.debug("Discovered bluetooth device: %s", discovery_info.as_dict())
        device_name = discovery_info.name or discovery_info.device.name or DEFAULT_NAME
        await self.async_set_unique_id(format_unique_id(discovery_info.address))
        self._abort_if_unique_id_configured()
        self._discovered_adv = UberSolarAdvertisement(
            discovery_info.device.address,
            device_name,
            discovery_info.device,
            discovery_info.advertisement.rssi,
            True,
        )
        self.context["title_placeholders"] = {
            "name": self._discovered_adv.name,
            "address": short_address(self._discovered_adv.address),
        }
        return await self.async_step_confirm()

    async def _async_create_entry_from_discovery(
        self, user_input: dict[str, Any]
    ) -> ConfigFlowResult:
        """Create an entry from a discovery."""
        assert self._discovered_adv is not None

        return self.async_create_entry(
            title=self._discovered_adv.name,
            data={
                **user_input,
                CONF_ADDRESS: self._discovered_adv.address,
            },
        )

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm a single device."""
        assert self._discovered_adv is not None
        if user_input is not None:
            return await self._async_create_entry_from_discovery(user_input)

        self._set_confirm_only()
        return self.async_show_form(
            step_id="confirm",
            data_schema=vol.Schema({}),
            description_placeholders={"name": self._discovered_adv.name},
        )

    @callback
    def _async_discover_devices(self) -> None:
        current_addresses = self._async_current_ids()
        for discovery_info in async_discovered_service_info(self.hass, True):
            address = discovery_info.address
            if (
                format_unique_id(address) in current_addresses
                or address in self._discovered_advs
            ):
                continue
            device_name = (
                discovery_info.name or discovery_info.device.name or DEFAULT_NAME
            )
            parsed = UberSolarAdvertisement(
                discovery_info.device.address,
                device_name,
                discovery_info.device,
                discovery_info.advertisement.rssi,
                True,
            )
            if not parsed:
                continue
            self._discovered_advs[address] = parsed

        if not self._discovered_advs:
            raise AbortFlow("no_unconfigured_devices")

    async def _async_set_device(self, discovery: UberSolarAdvertisement) -> None:
        """Set the device to work with."""
        self._discovered_adv = discovery
        address = discovery.address
        await self.async_set_unique_id(
            format_unique_id(address), raise_on_progress=False
        )
        self._abort_if_unique_id_configured()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the user step to pick discovered device."""
        errors: dict[str, str] = {}
        device_adv: UberSolarAdvertisement | None = None
        if user_input is not None:
            device_adv = self._discovered_advs[user_input[CONF_ADDRESS]]
            await self._async_set_device(device_adv)
            return await self._async_create_entry_from_discovery(user_input)

        self._async_discover_devices()
        if len(self._discovered_advs) == 1:
            # If there is only one device we can ask for a password
            # or simply confirm it
            device_adv = next(iter(self._discovered_advs.values()))
            await self._async_set_device(device_adv)
            return await self.async_step_confirm()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADDRESS): vol.In(
                        {
                            address: parsed.address
                            for address, parsed in self._discovered_advs.items()
                        }
                    ),
                }
            ),
            errors=errors,
        )


class UbersolarOptionsFlowHandler(OptionsFlowWithReload):
    """Handle UberSolar options."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage UberSolar options."""
        if user_input is not None:
            # Update common entity options for all other entities.
            return self.async_create_entry(title="", data=user_input)

        base_schema = vol.Schema({vol.Required(CONF_RETRY_COUNT): int})
        suggested_values = {
            CONF_RETRY_COUNT: self.config_entry.options.get(
                CONF_RETRY_COUNT, DEFAULT_RETRY_COUNT
            )
        }

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                base_schema, suggested_values
            ),
        )
