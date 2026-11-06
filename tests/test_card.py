"""Mapa encji dla karty Lovelace (polecenie websocket esterownik/card_entities)."""

from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from custom_components.esterownik.card import CARD_REGISTERS
from custom_components.esterownik.const import DOMAIN


async def _setup(hass, entry):
    hass.config.language = "pl"
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED


def _device(hass, mac="aabbccddeeff"):
    return dr.async_get(hass).async_get_device(identifiers={(DOMAIN, mac)})


async def test_card_entities_pello(hass, entry, mock_pello, hass_ws_client):
    await _setup(hass, entry)
    registry = er.async_get(hass)
    # Użytkownik zmienił nazwę encji: mapa ma podać nową.
    old = registry.async_get_entity_id("sensor", DOMAIN, "aabbccddeeff_0_tkot_value")
    registry.async_update_entity(old, new_entity_id="sensor.moj_kociol")

    client = await hass_ws_client(hass)
    await client.send_json(
        {"id": 1, "type": "esterownik/card_entities", "device_id": _device(hass).id}
    )
    msg = await client.receive_json()
    assert msg["success"], msg
    result = msg["result"]

    assert result["model"] == "pello"
    entities = result["entities"]
    assert entities["t_kotla"] == "sensor.moj_kociol"
    assert entities["status"].startswith("sensor.")
    assert entities["zad_kotla"].startswith("number.")
    assert entities["tryb_cwu"].startswith("select.")
    assert entities["reg_pog_zawor"].startswith("switch.")
    assert entities["pompa_cwu"].startswith("binary_sensor.")
    assert entities["kasuj_alarmy"].startswith("button.")
    # Każdy element schematu Pello ma swoją encję na zrzucie z prawdziwego sterownika.
    assert set(entities) == set(CARD_REGISTERS)

    alarm = registry.async_get_entity_id("binary_sensor", DOMAIN, "aabbccddeeff_0_alarm_rozp")
    assert alarm in result["alarms"]
    assert entities["pompa_cwu"] not in result["alarms"]


async def test_card_entities_unknown_device(hass, entry, mock_pello, hass_ws_client):
    await _setup(hass, entry)
    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": "esterownik/card_entities", "device_id": "brak"})
    msg = await client.receive_json()
    assert not msg["success"]
    assert msg["error"]["code"] == "not_found"


async def test_card_file_is_bundled():
    from pathlib import Path

    import custom_components.esterownik as integration

    card = Path(integration.__file__).parent / "www" / "esterownik-card.js"
    text = card.read_text(encoding="utf-8")
    assert "esterownik/card_entities" in text
    assert "def('esterownik-pello-card', EsterownikPelloCard)" in text
    # Rejestracja dopiero po starcie aplikacji HA (podmiana rejestru komponentów).
    assert "customElements.whenDefined('home-assistant')" in text
