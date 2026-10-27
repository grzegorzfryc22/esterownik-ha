"""Nastawy liczbowe eSterownik."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .catalog import EntitySpec
from .coordinator import EsterownikConfigEntry, EsterownikCoordinator
from .entity import EsterownikEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EsterownikConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        EsterownikNumber(coordinator, spec)
        for spec in coordinator.specs
        if spec.platform is Platform.NUMBER
    )


def _decimals(step: float | None, precision: int | None) -> int:
    if precision is not None:
        return precision
    if step is None or float(step).is_integer():
        return 0
    return len(f"{step:g}".split(".")[1])


class EsterownikNumber(EsterownikEntity, NumberEntity):
    """Rejestr liczbowy z zapisem przez setregister.cgi."""

    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator: EsterownikCoordinator, spec: EntitySpec) -> None:
        super().__init__(coordinator, spec)
        self._attr_native_unit_of_measurement = spec.unit
        self._decimals = _decimals(spec.step, spec.precision)
        if spec.minimum is not None:
            self._attr_native_min_value = spec.minimum
        if spec.maximum is not None:
            self._attr_native_max_value = spec.maximum
        self._attr_native_step = spec.step or (10**-self._decimals)
        if (
            spec.minimum is not None
            and spec.maximum is not None
            and spec.maximum - spec.minimum <= 100
        ):
            self._attr_mode = NumberMode.SLIDER if self._decimals == 0 else NumberMode.BOX

    @property
    def native_value(self) -> float | None:
        return self.raw_float

    async def async_set_native_value(self, value: float) -> None:
        text = f"{value:.{self._decimals}f}"
        await self.coordinator.async_write(self.spec.tid, text, self.spec.vid)
