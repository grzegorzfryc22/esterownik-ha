"""Alarmy, wyjścia i wejścia eSterownik."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .catalog import KIND_ALARM
from .coordinator import EsterownikConfigEntry
from .entity import EsterownikEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EsterownikConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        EsterownikBinarySensor(coordinator, spec)
        for spec in coordinator.specs
        if spec.platform is Platform.BINARY_SENSOR
    )


class EsterownikBinarySensor(EsterownikEntity, BinarySensorEntity):
    """Alarm (aktywny, gdy wartość ≠ 0) albo wyjście/wejście 0/1."""

    @property
    def is_on(self) -> bool | None:
        raw = self.raw
        if raw is None:
            return None
        if self.spec.kind == KIND_ALARM:
            return raw != "0"
        return raw == "1"

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        attributes = super().extra_state_attributes
        raw = self.raw
        if self.spec.kind == KIND_ALARM and raw not in (None, "0"):
            attributes["opis"] = self.spec.options.get(raw, raw)
        return attributes
