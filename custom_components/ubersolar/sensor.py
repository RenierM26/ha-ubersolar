"""Support for UberSolar sensors."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import cast

from homeassistant.components.bluetooth import async_last_service_info
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    LIGHT_LUX,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    EntityCategory,
    UnitOfElectricPotential,
    UnitOfTemperature,
    UnitOfTime,
    UnitOfVolume,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import UbersolarDataUpdateCoordinator
from .entity import UbersolarEntity

PARALLEL_UPDATES = 0

ValueFn = Callable[["UbersolarSensor"], float | int | str | None]


@dataclass(frozen=True, kw_only=True)
class UbersolarSensorEntityDescription(SensorEntityDescription):
    """Describe a Ubersolar sensor with a value extractor."""

    value_fn: ValueFn


def _data_getter(key: str) -> ValueFn:
    return lambda entity: entity.data.get(key)


def _rssi_getter(entity: UbersolarSensor) -> int | None:
    device_rssi = entity.data.get("wRSSI")
    if isinstance(device_rssi, int) and device_rssi != 0:
        return device_rssi

    address = entity.coordinator.address
    if service_info := async_last_service_info(entity.hass, address, True):
        return service_info.rssi

    if device_rssi == 0:
        return None

    return cast(int | None, device_rssi)


SENSOR_TYPES: dict[str, UbersolarSensorEntityDescription] = {
    "rssi": UbersolarSensorEntityDescription(
        key="rssi",
        translation_key="rssi",
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_rssi_getter,
    ),
    "fWaterTemperature": UbersolarSensorEntityDescription(
        key="fWaterTemperature",
        translation_key="water_temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_data_getter("fWaterTemperature"),
    ),
    "fManifoldTemperature": UbersolarSensorEntityDescription(
        key="fManifoldTemperature",
        translation_key="manifold_temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_data_getter("fManifoldTemperature"),
    ),
    "fStoredWater": UbersolarSensorEntityDescription(
        key="fStoredWater",
        translation_key="stored_water",
        native_unit_of_measurement=UnitOfVolume.LITERS,
        device_class=SensorDeviceClass.VOLUME_STORAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_data_getter("fStoredWater"),
    ),
    "fSolenoidState": UbersolarSensorEntityDescription(
        key="fSolenoidState",
        translation_key="solenoid_state",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=_data_getter("fSolenoidState"),
    ),
    "lluTime": UbersolarSensorEntityDescription(
        key="lluTime",
        translation_key="device_time_sensor",
        state_class=None,
        entity_registry_enabled_default=False,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_data_getter("lluTime"),
    ),
    "fHours": UbersolarSensorEntityDescription(
        key="fHours",
        translation_key="power_on_hours",
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_data_getter("fHours"),
    ),
    "wLux": UbersolarSensorEntityDescription(
        key="wLux",
        translation_key="light_level",
        native_unit_of_measurement=LIGHT_LUX,
        device_class=SensorDeviceClass.ILLUMINANCE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_data_getter("wLux"),
    ),
    "fPanelVoltage": UbersolarSensorEntityDescription(
        key="fPanelVoltage",
        translation_key="solar_panel_voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_data_getter("fPanelVoltage"),
    ),
    "fChipTemp": UbersolarSensorEntityDescription(
        key="fChipTemp",
        translation_key="controller_temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_data_getter("fChipTemp"),
    ),
    "fWaterLevel": UbersolarSensorEntityDescription(
        key="fWaterLevel",
        translation_key="water_level",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=_data_getter("fWaterLevel"),
    ),
    "fTankSize": UbersolarSensorEntityDescription(
        key="fTankSize",
        translation_key="tank_size",
        native_unit_of_measurement=UnitOfVolume.LITERS,
        device_class=SensorDeviceClass.VOLUME,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=_data_getter("fTankSize"),
    ),
    "bPanelFaultCode": UbersolarSensorEntityDescription(
        key="bPanelFaultCode",
        translation_key="panel_fault_code",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=_data_getter("bPanelFaultCode"),
    ),
    "bElementFaultCode": UbersolarSensorEntityDescription(
        key="bElementFaultCode",
        translation_key="element_fault_code",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=_data_getter("bElementFaultCode"),
    ),
    "bPumpFultCode": UbersolarSensorEntityDescription(
        key="bPumpFultCode",
        translation_key="pump_fault_code",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=_data_getter("bPumpFultCode"),
    ),
    "bSolenoidFaultCode": UbersolarSensorEntityDescription(
        key="bSolenoidFaultCode",
        translation_key="solenoid_fault_code",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=_data_getter("bSolenoidFaultCode"),
    ),
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Ubersolar sensors based on a config entry."""
    coordinator: UbersolarDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [UbersolarSensor(coordinator=coordinator, sensor=key) for key in SENSOR_TYPES],
        update_before_add=False,
    )


class UbersolarSensor(UbersolarEntity, SensorEntity):
    """Representation of a Ubersolar sensor."""

    entity_description: UbersolarSensorEntityDescription

    def __init__(
        self,
        coordinator: UbersolarDataUpdateCoordinator,
        sensor: str,
    ) -> None:
        """Initialize the Ubersolar sensor."""
        super().__init__(coordinator)
        self._sensor = sensor
        self._attr_unique_id = f"{coordinator.base_unique_id}-{sensor}"
        self.entity_description = SENSOR_TYPES[sensor]

    @property
    def native_value(self) -> float | int | str | None:
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self)
