"""Karta Lovelace dostarczana razem z integracją.

Integracja serwuje plik karty i rejestruje go we frontendzie, a karcie podaje
mapę "element schematu -> aktualne entity_id" dla wybranego urządzenia. Mapa
opiera się na unique_id (stałe klucze rejestrów), więc działa także po zmianie
nazw encji przez użytkownika.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import voluptuous as vol
from homeassistant.components import frontend, websocket_api
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from .catalog import KIND_ALARM
from .const import CARD_FILE, CARD_URL_BASE, DOMAIN, MAIN_VID

# Element schematu karty -> rejestr sterownika (tid) na głównym urządzeniu.
CARD_REGISTERS: dict[str, str] = {
    "status": "pl_status",
    "tryb_pracy": "tryb_auto_state",
    "zima_lato": "zima_lato",
    "t_zewn": "tzew_value",
    "kasuj_alarmy": "cmd_ackalarm",
    "t_kotla": "tkot_value",
    "zad_kotla": "kot_tzad",
    "t_powrotu": "tpow_value",
    "t_spalin": "tsp_value",
    "reg_pog_kociol": "pog_en",
    "moc": "pl_power_kw",
    "plomien": "pl_flame",
    "poziom": "fuel_level",
    "czas_do_oproznienia": "time_to_empty",
    "kolejny_zasyp": "next_fuel_time",
    "strumien": "pl_fuel_flow",
    "rozpalenia": "pl_tfire",
    "t_podajnika": "mpl_temp",
    "podajnik": "out_pod",
    "dmuchawa": "out_dm",
    "moc_dmuchawy": "act_dm_speed",
    "t_cwu": "tcwu_value",
    "zad_cwu": "cwu_tzad",
    "tryb_cwu": "cwu_state",
    "pompa_cwu": "out_cwu",
    "t_za_zaworem": "t1_value",
    "zad_za_zaworem": "ob1_tzad",
    "poz_zaworu": "ob1_zaw4d_pos",
    "stan_zaworu": "out_zaw4d",
    "reg_pog_zawor": "ob1_pog_en",
    "pompa_co": "out_pomp1",
    "t_wewn": "twew_value",
    "zad_wewn": "ob1_pok_tzad",
    "wewn_komfortowa": "ob1_pok_hi",
    "wewn_normalna": "ob1_pok_norm",
    "wewn_niska": "ob1_pok_lo",
}

WS_CARD_ENTITIES = f"{DOMAIN}/card_entities"


async def async_register_card(hass: HomeAssistant, version: str) -> None:
    """Serwuje plik karty i dodaje go do frontendu (raz na uruchomienie HA)."""
    websocket_api.async_register_command(hass, ws_card_entities)
    if hass.http is None or "frontend" not in hass.config.components:
        return  # np. w testach bez interfejsu
    url = f"{CARD_URL_BASE}/{CARD_FILE}"
    path = Path(__file__).parent / "www" / CARD_FILE
    await hass.http.async_register_static_paths([StaticPathConfig(url, str(path), True)])
    # Wersja w adresie wymusza pobranie nowej karty po aktualizacji integracji.
    frontend.add_extra_js_url(hass, f"{url}?v={version}")


@websocket_api.websocket_command(
    {vol.Required("type"): WS_CARD_ENTITIES, vol.Required("device_id"): str}
)
@callback
def ws_card_entities(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Zwraca encje sterownika dla elementów schematu karty."""
    device = dr.async_get(hass).async_get(msg["device_id"])
    if device is None:
        connection.send_error(msg["id"], "not_found", "Nie znaleziono urządzenia")
        return

    coordinator = None
    for entry_id in device.config_entries:
        entry = hass.config_entries.async_get_entry(entry_id)
        if entry and entry.domain == DOMAIN and entry.state is ConfigEntryState.LOADED:
            coordinator = entry.runtime_data
            break
    if coordinator is None:
        connection.send_error(
            msg["id"], "not_loaded", "Urządzenie nie należy do załadowanej integracji eSterownik"
        )
        return

    registry = er.async_get(hass)
    by_unique_id = {
        entity.unique_id: entity.entity_id
        for entity in er.async_entries_for_device(
            registry, device.id, include_disabled_entities=True
        )
        if entity.platform == DOMAIN
    }
    prefix = f"{coordinator.info.mac}_{MAIN_VID}_"

    entities = {
        key: by_unique_id[prefix + tid]
        for key, tid in CARD_REGISTERS.items()
        if prefix + tid in by_unique_id
    }
    alarms = sorted(
        by_unique_id[f"{coordinator.info.mac}_{spec.vid}_{spec.tid}"]
        for spec in coordinator.specs
        if spec.kind == KIND_ALARM
        and f"{coordinator.info.mac}_{spec.vid}_{spec.tid}" in by_unique_id
    )
    connection.send_result(
        msg["id"],
        {
            "model": (coordinator.info.hardware_type or "").lower(),
            "entities": entities,
            "alarms": alarms,
        },
    )
