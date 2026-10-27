"""Konfiguracja integracji eSterownik z interfejsu."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_SCAN_INTERVAL, CONF_USERNAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import EsterownikClient
from .const import (
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_USERNAME,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)
from .errors import AuthError, EsterownikError
from .models import ControllerInfo

PASSWORD = TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD))


def _credentials_schema(username: str = DEFAULT_USERNAME) -> dict:
    return {
        vol.Required(CONF_USERNAME, default=username): str,
        vol.Optional(CONF_PASSWORD, default=""): PASSWORD,
    }


async def _validate(hass: HomeAssistant, data: Mapping[str, Any]) -> ControllerInfo:
    """Łączy się ze sterownikiem; rzuca AuthError / EsterownikError."""
    client = EsterownikClient(
        async_get_clientsession(hass),
        data[CONF_HOST],
        data.get(CONF_USERNAME, ""),
        data.get(CONF_PASSWORD, ""),
    )
    info = await client.async_get_info()
    await client.async_get_snapshot()
    return info


async def _errors(
    hass: HomeAssistant, data: Mapping[str, Any]
) -> tuple[ControllerInfo | None, dict]:
    try:
        return await _validate(hass, data), {}
    except AuthError:
        return None, {"base": "invalid_auth"}
    except EsterownikError:
        return None, {"base": "cannot_connect"}


class EsterownikConfigFlow(ConfigFlow, domain=DOMAIN):
    """Dodawanie sterownika."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            user_input[CONF_HOST] = user_input[CONF_HOST].strip()
            info, errors = await _errors(self.hass, user_input)
            if info is not None:
                await self.async_set_unique_id(info.mac)
                self._abort_if_unique_id_configured(updates={CONF_HOST: user_input[CONF_HOST]})
                title = info.name or info.hardware_type or "eSterownik"
                return self.async_create_entry(
                    title=f"{title} ({user_input[CONF_HOST]})", data=user_input
                )

        schema = vol.Schema({vol.Required(CONF_HOST): str, **_credentials_schema()})
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(schema, user_input),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            data = {**entry.data, **user_input, CONF_HOST: user_input[CONF_HOST].strip()}
            info, errors = await _errors(self.hass, data)
            if info is not None:
                await self.async_set_unique_id(info.mac)
                self._abort_if_unique_id_mismatch(reason="wrong_device")
                return self.async_update_reload_and_abort(entry, data=data)

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=entry.data[CONF_HOST]): str,
                **_credentials_schema(entry.data.get(CONF_USERNAME, DEFAULT_USERNAME)),
            }
        )
        return self.async_show_form(step_id="reconfigure", data_schema=schema, errors=errors)

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        entry = self._get_reauth_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            data = {**entry.data, **user_input}
            info, errors = await _errors(self.hass, data)
            if info is not None:
                return self.async_update_reload_and_abort(entry, data=data)

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                _credentials_schema(entry.data.get(CONF_USERNAME, DEFAULT_USERNAME))
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> EsterownikOptionsFlow:
        return EsterownikOptionsFlow()


class EsterownikOptionsFlow(OptionsFlow):
    """Opcje: częstotliwość odświeżania."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        current = self.config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SCAN_INTERVAL, default=current): vol.All(
                        vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL)
                    )
                }
            ),
        )
