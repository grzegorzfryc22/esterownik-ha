"""Integracja Home Assistant dla sterowników eSterownik.pl (Pello, eCoal)."""

from __future__ import annotations

import voluptuous as vol
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .catalog import build_specs
from .const import ATTR_AMOUNT, ATTR_CONFIG_ENTRY_ID, DOMAIN, MAIN_VID, SERVICE_ADD_FUEL
from .coordinator import EsterownikConfigEntry, EsterownikCoordinator

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

ADD_FUEL_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_AMOUNT): vol.All(vol.Coerce(int), vol.Range(min=1)),
        vol.Optional(ATTR_CONFIG_ENTRY_ID): cv.string,
    }
)


def _loaded_coordinator(hass: HomeAssistant, entry_id: str | None) -> EsterownikCoordinator:
    entries = [
        entry
        for entry in hass.config_entries.async_entries(DOMAIN)
        if entry.state is ConfigEntryState.LOADED
        and (entry_id is None or entry.entry_id == entry_id)
    ]
    if len(entries) != 1:
        raise ServiceValidationError(
            "Wskaż config_entry_id sterownika (brak lub więcej niż jeden sterownik)"
        )
    return entries[0].runtime_data


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Rejestruje akcje integracji."""

    async def _async_add_fuel(call: ServiceCall) -> None:
        coordinator = _loaded_coordinator(hass, call.data.get(ATTR_CONFIG_ENTRY_ID))
        register = coordinator.dictionary.for_vid(MAIN_VID).get("add_fuel")
        if register is None or not register.writable(coordinator.access_level):
            raise ServiceValidationError("Ten sterownik nie obsługuje rejestracji zasypu")
        amount: int = call.data[ATTR_AMOUNT]
        low, high = register.minimum, register.maximum
        if low is not None and high is not None and not low <= amount <= high:
            raise ServiceValidationError(f"Ilość {amount} kg spoza zakresu {low:g}–{high:g} kg")
        # Sterownik traktuje zapis ilości jak pełny zasyp i ustawia datę zasypu.
        await coordinator.async_write("add_fuel", str(amount))

    hass.services.async_register(DOMAIN, SERVICE_ADD_FUEL, _async_add_fuel, ADD_FUEL_SCHEMA)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: EsterownikConfigEntry) -> bool:
    """Uruchamia wpis: informacje, słownik, pierwszy odczyt, encje."""
    coordinator = EsterownikCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    coordinator.specs = build_specs(
        coordinator.dictionary,
        coordinator.data,
        coordinator.access_level,
        (hass.config.language or "pl").split("-")[0],
    )
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: EsterownikConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_reload(hass: HomeAssistant, entry: EsterownikConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
