"""Polecenia eSterownik."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import EsterownikConfigEntry
from .entity import EsterownikEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EsterownikConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        EsterownikButton(coordinator, spec)
        for spec in coordinator.specs
        if spec.platform is Platform.BUTTON
    )


class EsterownikButton(EsterownikEntity, ButtonEntity):
    """Polecenie sterownika (np. potwierdzenie alarmów)."""

    async def async_press(self) -> None:
        await self.coordinator.async_write(self.spec.tid, "1", self.spec.vid)
