"""Wspólne fixture'y: sterownik udawany przez zrzuty z prawdziwego urządzenia."""

from __future__ import annotations

from pathlib import Path

import pytest
import pytest_homeassistant_custom_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.esterownik.const import DOMAIN

pytest_plugins = ["pytest_homeassistant_custom_component"]

# Testowy katalog konfiguracji HA ma własny pakiet custom_components, który przesłania
# katalog z repozytorium. Podpinamy tam integrację, żeby loader HA ją znalazł.
_TESTING = (
    Path(pytest_homeassistant_custom_component.__file__).parent
    / "testing_config"
    / "custom_components"
    / "esterownik"
)
if not _TESTING.exists():
    _TESTING.symlink_to(
        Path(__file__).parents[1] / "custom_components" / "esterownik",
        target_is_directory=True,
    )

HOST = "192.0.2.10"
FIXTURES = Path(__file__).parent / "fixtures"
OK = '<cmd status="ok"><device id="0"><reg vid="0" tid="{tid}" status="ok"/></device></cmd>'


def fixture(device: str, name: str) -> str:
    return (FIXTURES / device / name).read_text(encoding="utf-8")


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture
def mock_pello(aioclient_mock):
    aioclient_mock.get(f"http://{HOST}/info.cgi", text=fixture("pello", "info.xml"))
    aioclient_mock.get(f"http://{HOST}/config/hardware.xml", text=fixture("pello", "hardware.xml"))
    aioclient_mock.get(f"http://{HOST}/syncvalues.cgi", text=fixture("pello", "syncvalues.txt"))
    return aioclient_mock


@pytest.fixture
def entry(hass) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="pello",
        unique_id="aabbccddeeff",
        data={"host": HOST, "username": "root", "password": "secret"},
    )
    entry.add_to_hass(hass)
    return entry


@pytest.fixture
def mock_ecoal(aioclient_mock):
    aioclient_mock.get(f"http://{HOST}/info.cgi", text=fixture("ecoal", "info.xml"))
    aioclient_mock.get(f"http://{HOST}/config/hardware.xml", text=fixture("ecoal", "hardware.xml"))
    aioclient_mock.get(f"http://{HOST}/syncvalues.cgi", text=fixture("ecoal", "syncvalues.txt"))
    return aioclient_mock


@pytest.fixture
def entry_ecoal(hass) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="eCoal",
        unique_id="112233445566",
        data={"host": HOST, "username": "root", "password": "secret"},
    )
    entry.add_to_hass(hass)
    return entry
