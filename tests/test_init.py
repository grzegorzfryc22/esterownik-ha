"""Uruchomienie integracji na zrzutach z Pello v3.5, zapisy i błędy."""

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from custom_components.esterownik.const import DOMAIN

from .conftest import HOST, OK


def _eid(hass, platform, tid):
    return er.async_get(hass).async_get_entity_id(platform, DOMAIN, f"aabbccddeeff_0_{tid}")


async def _setup(hass, entry, language="pl"):
    hass.config.language = language
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED


async def test_setup_creates_entities(hass, entry, mock_pello):
    await _setup(hass, entry)
    assert hass.states.get(_eid(hass, "sensor", "t1_value")).state == "29.97"
    assert hass.states.get(_eid(hass, "sensor", "pl_status")).state == "STOP"
    assert hass.states.get(_eid(hass, "sensor", "next_fuel_time")).state.startswith("2026-11")
    assert hass.states.get(_eid(hass, "number", "kot_tzad")).state == "67.0"
    assert hass.states.get(_eid(hass, "number", "ob1_pok_norm")).state == "21.3"
    assert hass.states.get(_eid(hass, "select", "zima_lato")).state == "Zima"
    assert hass.states.get(_eid(hass, "switch", "ob1_pog_en")).state == "on"
    assert hass.states.get(_eid(hass, "binary_sensor", "out_cwu")).state == "on"
    assert hass.states.get(_eid(hass, "binary_sensor", "alarm_rozp")).state == "off"
    # tryb ręczny istnieje, ale jest wyłączony domyślnie
    entity = er.async_get(hass).async_get(_eid(hass, "select", "tryb_auto"))
    assert entity.disabled_by is er.RegistryEntryDisabler.INTEGRATION

    device = dr.async_get(hass).async_get_device(identifiers={(DOMAIN, "aabbccddeeff")})
    assert device.sw_version == "1.1.39.4"
    assert device.model == "pello 3.5"


async def test_writes(hass, entry, mock_pello):
    await _setup(hass, entry)
    mock_pello.get(f"http://{HOST}/setregister.cgi", text=OK.format(tid="x"))

    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": _eid(hass, "number", "ob1_tzad"), "value": 45},
        blocking=True,
    )
    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": _eid(hass, "number", "ob1_pok_norm"), "value": 21.5},
        blocking=True,
    )
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": _eid(hass, "select", "zima_lato"), "option": "Auto-Lato"},
        blocking=True,
    )
    await hass.services.async_call(
        "switch", "turn_off", {"entity_id": _eid(hass, "switch", "pog_en")}, blocking=True
    )
    await hass.services.async_call(
        "button", "press", {"entity_id": _eid(hass, "button", "cmd_ackalarm")}, blocking=True
    )
    await hass.services.async_call(DOMAIN, "add_fuel", {"amount": 60}, blocking=True)

    writes = [str(call[1]) for call in mock_pello.mock_calls if "setregister" in str(call[1])]
    assert writes == [
        f"http://{HOST}/setregister.cgi?device=0&ob1_tzad=45",
        f"http://{HOST}/setregister.cgi?device=0&ob1_pok_norm=21.5",
        f"http://{HOST}/setregister.cgi?device=0&zima_lato=2",
        f"http://{HOST}/setregister.cgi?device=0&pog_en=0",
        f"http://{HOST}/setregister.cgi?device=0&cmd_ackalarm=1",
        f"http://{HOST}/setregister.cgi?device=0&add_fuel=60",
    ]


async def test_add_fuel_range_from_dictionary(hass, entry, mock_pello):
    await _setup(hass, entry)
    with pytest.raises(HomeAssistantError, match="spoza zakresu"):
        await hass.services.async_call(DOMAIN, "add_fuel", {"amount": 900}, blocking=True)


async def test_refused_write_raises(hass, entry, mock_pello):
    await _setup(hass, entry)
    mock_pello.get(
        f"http://{HOST}/setregister.cgi",
        text=(
            '<cmd status="ok"><device id="0">'
            '<reg vid="0" tid="kot_tzad" status="out_of_range"/></device></cmd>'
        ),
    )
    with pytest.raises(HomeAssistantError, match="out_of_range"):
        await hass.services.async_call(
            "number",
            "set_value",
            {"entity_id": _eid(hass, "number", "kot_tzad"), "value": 60},
            blocking=True,
        )


async def test_auth_failure_starts_reauth(hass, entry, aioclient_mock):
    aioclient_mock.get(f"http://{HOST}/info.cgi", status=401)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.SETUP_ERROR
    assert any(
        flow["context"]["source"] == "reauth" for flow in hass.config_entries.flow.async_progress()
    )


async def test_diagnostics_redacts(hass, entry, mock_pello):
    from custom_components.esterownik.diagnostics import async_get_config_entry_diagnostics

    await _setup(hass, entry)
    diag = await async_get_config_entry_diagnostics(hass, entry)
    text = str(diag)
    assert "secret" not in text and "aabbccddeeff" not in text
    assert diag["controller"]["hardware_type"] == "pello"


async def test_english_names(hass, entry, mock_pello):
    await _setup(hass, entry, language="en")
    state = hass.states.get(_eid(hass, "select", "zima_lato"))
    assert state.state == "Winter"
    assert state.attributes["friendly_name"] == "pello Winter/Summer Mode"
