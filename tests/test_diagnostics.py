"""Diagnostyka nie może zawierać danych logowania ani danych identyfikujących."""

from pytest_homeassistant_custom_component.components.diagnostics import (
    get_diagnostics_for_config_entry,
)

from .conftest import HOST, fixture

REDACTED = "**REDACTED**"
PRIVATE = (
    "device_sn",
    "device_id",
    "device_name",
    "device_location",
    "eth_mac",
    "eth_ip",
    "eth_ip_ro",
    "eth_gate",
    "eth_gate_ro",
    "eth_mask",
    "eth_mask_ro",
)


async def test_diagnostics_redacts_private_data(hass, hass_client, entry, aioclient_mock):
    # lokalizację użytkownik wpisuje sam na stronie sterownika
    values = fixture("pello", "syncvalues.txt").replace(
        "device_location:;", "device_location:Kot%C5%82ownia%20ul.%20Prywatna%201;", 1
    )
    assert "Prywatna" in values
    aioclient_mock.get(f"http://{HOST}/info.cgi", text=fixture("pello", "info.xml"))
    aioclient_mock.get(f"http://{HOST}/config/hardware.xml", text=fixture("pello", "hardware.xml"))
    aioclient_mock.get(f"http://{HOST}/syncvalues.cgi", text=values)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    diag = await get_diagnostics_for_config_entry(hass, hass_client, entry)

    assert diag["entry"] == {"host": REDACTED, "username": REDACTED, "password": REDACTED}
    assert diag["controller"]["mac"] == REDACTED
    assert diag["controller"]["serial"] == REDACTED
    values = diag["values"]
    for key in PRIVATE:
        assert values[key] == REDACTED, key
    assert not any(key.startswith("auth_") for key in values)
    text = str(diag)
    for secret in ("secret", HOST, "aabbccddeeff", "AABBCCDDEEFF", "Prywatna"):
        assert secret not in text, secret
    # wartości użytkowe zostają, żeby diagnostyka była przydatna
    assert values["t1_value"] == "29.97"
