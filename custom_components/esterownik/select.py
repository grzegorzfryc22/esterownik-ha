"""Tryby pracy eSterownik."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
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
        EsterownikSelect(coordinator, spec)
        for spec in coordinator.specs
        if spec.platform is Platform.SELECT
    )


class EsterownikSelect(EsterownikEntity, SelectEntity):
    """Wyliczenie z zapisem przez setregister.cgi."""

    def __init__(self, coordinator: EsterownikCoordinator, spec: EntitySpec) -> None:
        super().__init__(coordinator, spec)
        self._attr_options = list(dict.fromkeys(spec.options.values()))

    @property
    def current_option(self) -> str | None:
        raw = self.raw
        if raw is None:
            return None
        label = self.spec.options.get(raw)
        # Rejestr stanu może mieć więcej wartości niż zapis (np. "Alarmowy").
        return label if label in self._attr_options else None

    async def async_select_option(self, option: str) -> None:
        value = next((raw for raw, label in self.spec.options.items() if label == option), None)
        if value is None:
            raise ServiceValidationError(f"Nieznana opcja: {option}")
        await self.coordinator.async_write(self.spec.tid, value, self.spec.vid)
