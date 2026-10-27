"""Diagnostyka: dane do zgłoszeń błędów, bez danych logowania i identyfikatorów."""

from __future__ import annotations

from collections import Counter
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from .const import MAIN_VID
from .coordinator import EsterownikConfigEntry

TO_REDACT = {
    CONF_PASSWORD,
    CONF_USERNAME,
    CONF_HOST,
    "mac",
    "serial",
    "device_sn",
    "device_id",
    "eth_mac",
    "eth_ip",
    "eth_ip_ro",
    "eth_gate",
    "eth_gate_ro",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: EsterownikConfigEntry
) -> dict[str, Any]:
    coordinator = entry.runtime_data
    info = coordinator.info
    return {
        "entry": async_redact_data(dict(entry.data), TO_REDACT),
        "options": dict(entry.options),
        "controller": async_redact_data(
            {
                "hardware_type": info.hardware_type,
                "hardware_version": info.hardware_version,
                "software_version": info.software_version,
                "company": info.company,
                "mac": info.mac,
                "serial": info.serial,
            },
            TO_REDACT,
        ),
        "dictionary": {
            "type": coordinator.dictionary.hardware_type,
            "version": coordinator.dictionary.version,
            "registers": {
                str(vid): len(registers)
                for vid, registers in coordinator.dictionary.registers.items()
            },
        },
        "access_level": coordinator.access_level,
        "entities": dict(Counter(str(spec.platform) for spec in coordinator.specs)),
        "values": async_redact_data(coordinator.data.values(MAIN_VID), TO_REDACT),
    }
