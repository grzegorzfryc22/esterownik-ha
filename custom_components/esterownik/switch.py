"""Przełączniki 0/1 eSterownik."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
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
        EsterownikSwitch(coordinator, spec)
        for spec in coordinator.specs
        if spec.platform is Platform.SWITCH
    )


class EsterownikSwitch(EsterownikEntity, SwitchEntity):
    """Rejestr 0/1 z zapisem przez setregister.cgi."""

    @property
    def is_on(self) -> bool | None:
        raw = self.raw
        return None if raw is None else raw == "1"

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_write(self.spec.tid, "1", self.spec.vid)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_write(self.spec.tid, "0", self.spec.vid)
