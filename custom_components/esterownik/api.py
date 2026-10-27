"""Klient HTTP lokalnego API sterowników eSterownik (Pello, eCoal)."""

from __future__ import annotations

import re

import aiohttp
from yarl import URL

from .const import PATH_DICTIONARY, PATH_INFO, PATH_VALUES, PATH_WRITE, REQUEST_TIMEOUT
from .errors import AuthError, ConnectionFailed, ParseError, WriteError
from .models import ControllerInfo, Dictionary, Snapshot
from .parser import (
    REGISTER_ID,
    parse_dictionary,
    parse_info,
    parse_snapshot,
    parse_write_result,
)

# Słownik rejestrów ma ok. 300 kB; limit chroni przed nieoczekiwanie dużą odpowiedzią.
MAX_RESPONSE_BYTES = 4 * 1024 * 1024
_VALUE = re.compile(r"^-?\d+(\.\d+)?$")


class EsterownikClient:
    """Odczyt i zapis rejestrów przez lokalny serwer WWW sterownika."""

    def __init__(
        self, session: aiohttp.ClientSession, host: str, username: str, password: str
    ) -> None:
        try:
            self._base = URL.build(scheme="http", host=host.strip())
        except ValueError as err:
            raise ConnectionFailed("Niepoprawny adres sterownika") from err
        self._session = session
        self._auth = aiohttp.BasicAuth(username, password or "") if username else None
        self._timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)

    @property
    def base_url(self) -> str:
        return str(self._base)

    async def _get(self, path: str, query: dict[str, str | int] | None = None) -> str:
        url = self._base / path
        if query is not None:
            url = url.with_query(query)
        try:
            async with self._session.get(
                url, auth=self._auth, timeout=self._timeout, allow_redirects=False
            ) as response:
                if response.status in (401, 403):
                    raise AuthError
                if response.status != 200:
                    raise ConnectionFailed(f"{path}: HTTP {response.status}")
                chunks: list[bytes] = []
                size = 0
                async for chunk in response.content.iter_chunked(64 * 1024):
                    size += len(chunk)
                    if size > MAX_RESPONSE_BYTES:
                        raise ParseError(f"{path}: odpowiedź jest zbyt duża")
                    chunks.append(chunk)
        except (aiohttp.ClientError, TimeoutError) as err:
            raise ConnectionFailed(f"{path}: {err}") from err
        return b"".join(chunks).decode("utf-8", errors="replace")

    async def async_get_info(self) -> ControllerInfo:
        return parse_info(await self._get(PATH_INFO))

    async def async_get_dictionary(self) -> Dictionary:
        return parse_dictionary(await self._get(PATH_DICTIONARY))

    async def async_get_snapshot(self) -> Snapshot:
        return parse_snapshot(await self._get(PATH_VALUES))

    async def async_set_register(self, vid: int, tid: str, value: str) -> None:
        """Zmienia jeden rejestr. Rzuca WriteError, gdy sterownik odmówi."""
        # Inne znaki pozwoliłyby dokleić do żądania drugi rejestr.
        if not REGISTER_ID.match(tid) or not _VALUE.match(value):
            raise WriteError(f"Odmowa zapisu nieoczekiwanej wartości do {tid}")
        # Sterownik wymaga kolejności: najpierw device, potem rejestr.
        text = await self._get(PATH_WRITE, {"device": vid, tid: value})
        parse_write_result(text, tid)
