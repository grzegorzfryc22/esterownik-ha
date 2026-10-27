"""Koordynator odświeżania i zapisu rejestrów."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_SCAN_INTERVAL, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import EsterownikClient
from .catalog import EntitySpec
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN, MAIN_VID
from .errors import AuthError, EsterownikError, WriteError
from .models import ControllerInfo, Dictionary, Snapshot

_LOGGER = logging.getLogger(__name__)

type EsterownikConfigEntry = ConfigEntry[EsterownikCoordinator]


class EsterownikCoordinator(DataUpdateCoordinator[Snapshot]):
    """Odczytuje syncvalues.cgi; trzyma informacje o sterowniku i słownik rejestrów."""

    config_entry: EsterownikConfigEntry
    info: ControllerInfo
    dictionary: Dictionary
    specs: list[EntitySpec]

    def __init__(self, hass: HomeAssistant, entry: EsterownikConfigEntry) -> None:
        interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=int(interval)),
        )
        self.client = EsterownikClient(
            async_get_clientsession(hass),
            entry.data[CONF_HOST],
            entry.data.get(CONF_USERNAME, ""),
            entry.data.get(CONF_PASSWORD, ""),
        )

    async def _async_setup(self) -> None:
        """Jednorazowo: informacje o urządzeniu i słownik rejestrów."""
        try:
            self.info = await self.client.async_get_info()
            self.dictionary = await self.client.async_get_dictionary()
        except AuthError as err:
            raise ConfigEntryAuthFailed("Sterownik odrzucił login lub hasło") from err
        except EsterownikError as err:
            raise UpdateFailed(f"Nie udało się pobrać słownika sterownika: {err}") from err

    async def _async_update_data(self) -> Snapshot:
        try:
            return await self.client.async_get_snapshot()
        except AuthError as err:
            raise ConfigEntryAuthFailed("Sterownik odrzucił login lub hasło") from err
        except EsterownikError as err:
            raise UpdateFailed(f"Brak połączenia ze sterownikiem: {err}") from err

    @property
    def access_level(self) -> int:
        """Poziom dostępu konta (0 = root), raportowany przez sterownik."""
        raw = self.data.value(MAIN_VID, "accesslevel") if self.data else None
        try:
            return int(raw) if raw is not None else 0
        except ValueError:
            return 0

    def value(self, tid: str, vid: int = MAIN_VID) -> str | None:
        return self.data.value(vid, tid) if self.data else None

    async def async_write(self, tid: str, value: str, vid: int = MAIN_VID) -> None:
        """Zapisuje rejestr i odświeża dane. Błąd zgłasza w interfejsie HA."""
        try:
            await self.client.async_set_register(vid, tid, value)
        except AuthError as err:
            raise HomeAssistantError("Sterownik odrzucił login lub hasło") from err
        except WriteError as err:
            raise HomeAssistantError(str(err)) from err
        except EsterownikError as err:
            raise HomeAssistantError(f"Nie udało się zapisać {tid}: {err}") from err
        _LOGGER.debug("Zapisano %s=%s", tid, value)
        await self.async_request_refresh()

    @property
    def device_info(self) -> DeviceInfo:
        info = self.info
        model = " ".join(part for part in (info.hardware_type, info.hardware_version) if part)
        return DeviceInfo(
            identifiers={(DOMAIN, info.mac)},
            connections={
                (CONNECTION_NETWORK_MAC, ":".join(info.mac[i : i + 2] for i in range(0, 12, 2)))
            },
            name=info.name or info.hardware_type or "eSterownik",
            manufacturer=info.company or "eSterownik.pl",
            model=model or None,
            sw_version=info.software_version or None,
            hw_version=info.hardware_version or None,
            serial_number=info.serial or None,
            configuration_url=self.client.base_url,
        )
