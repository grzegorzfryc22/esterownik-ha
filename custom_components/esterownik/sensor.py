"""Sensory eSterownik."""

from __future__ import annotations

from datetime import UTC, datetime

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .catalog import KIND_DURATION, KIND_ENUM, KIND_TIMESTAMP, EntitySpec
from .coordinator import EsterownikConfigEntry, EsterownikCoordinator
from .entity import EsterownikEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EsterownikConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        EsterownikSensor(coordinator, spec)
        for spec in entry.runtime_data.specs
        if spec.platform is Platform.SENSOR
    )


class EsterownikSensor(EsterownikEntity, SensorEntity):
    """Odczyt rejestru."""

    def __init__(self, coordinator: EsterownikCoordinator, spec: EntitySpec) -> None:
        super().__init__(coordinator, spec)
        self._attr_native_unit_of_measurement = spec.unit
        self._attr_state_class = spec.state_class
        self._attr_suggested_display_precision = spec.precision
        if spec.kind == KIND_ENUM:
            self._attr_options = list(dict.fromkeys(spec.options.values()))

    @property
    def native_value(self) -> str | int | float | datetime | None:
        kind = self.spec.kind
        if kind == KIND_ENUM:
            raw = self.raw
            return self.spec.options.get(raw) if raw is not None else None
        value = self.raw_float
        if value is None:
            return None
        if kind == KIND_TIMESTAMP:
            return datetime.fromtimestamp(value, tz=UTC) if value > 0 else None
        if kind == KIND_DURATION or self.spec.device_class == SensorDeviceClass.DURATION:
            return int(value)
        return int(value) if value.is_integer() and not self.spec.precision else value
