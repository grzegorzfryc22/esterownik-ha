"""Parsowanie odpowiedzi sterownika: info.cgi, hardware.xml, syncvalues.cgi, setregister.cgi."""

from __future__ import annotations

import re
from urllib.parse import unquote
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

from .errors import ParseError, WriteError
from .models import ControllerInfo, DeviceValues, Dictionary, RegisterDef, Snapshot

# syncvalues.cgi zwraca dane logowania wszystkich poziomów dostępu (Base64 "login:hasło").
SECRET_PREFIXES = ("auth_",)

# Identyfikatory rejestrów trafiają do adresów URL i unique_id.
REGISTER_ID = re.compile(r"^[A-Za-z0-9_]+$")
_MAC = re.compile(r"^[0-9a-f]{12}$")
_DECIMALS = re.compile(r"^0(?:[.,](0+))?$")
_STATUS = re.compile(r"^[A-Za-z0-9_]{1,40}$")


def _xml(text: str) -> Element:
    try:
        return ElementTree.fromstring(text.lstrip("﻿").strip())
    except ElementTree.ParseError as err:
        raise ParseError(f"Niepoprawny XML: {err}") from err


def _float(text: str | None) -> float | None:
    if text is None or text.strip() == "":
        return None
    try:
        return float(text.replace(",", "."))
    except ValueError:
        return None


def _texts(node: Element | None) -> dict[str, str]:
    if node is None:
        return {}
    return {lang: value.strip() for lang, value in node.attrib.items() if len(lang) == 2}


def parse_info(text: str) -> ControllerInfo:
    """Parsuje info.cgi."""
    root = _xml(text)
    hardware = root if root.tag == "hardware" else root.find("hardware")
    if hardware is None:
        raise ParseError("Brak węzła hardware w info.cgi")
    mac = hardware.get("mac", "").lower().replace(":", "")
    if not _MAC.match(mac):
        raise ParseError("info.cgi nie zawiera poprawnego adresu MAC")
    return ControllerInfo(
        hardware_type=hardware.get("type", ""),
        hardware_version=hardware.get("hardwareversion", ""),
        software_version=hardware.get("softwareversion", ""),
        company=hardware.get("company", ""),
        mac=mac,
        serial=hardware.get("sn", ""),
        name=hardware.get("device_name", ""),
    )


def _parse_register(node: Element) -> RegisterDef:
    config = node.find("config")
    values = config.find("values") if config is not None else None

    minimum = _float(values.get("min")) if values is not None else None
    maximum = _float(values.get("max")) if values is not None else None
    if minimum is not None and maximum is not None and minimum >= maximum:
        # np. min="0" max="0" — sterownik nie deklaruje zakresu
        minimum = maximum = None
    step = _float(values.get("step")) if values is not None else None
    if step is not None and step <= 0:
        step = None

    precision = None
    if config is not None and (fmt := config.find("format")) is not None:
        if match := _DECIMALS.match(fmt.get("pl") or fmt.get("en") or ""):
            precision = len(match.group(1) or "")

    options: dict[str, dict[str, str]] = {}
    if values is not None:
        ids = [val.get("id") for val in values.findall("val")]
        # Niektóre słowniki mają zepsute listy (wszystkie id="0") — wtedy ignorujemy opcje.
        if ids and len(set(ids)) == len(ids) and all(i is not None for i in ids):
            for val in values.findall("val"):
                options[val.get("id", "")] = _texts(val)

    return RegisterDef(
        tid=node.get("tid", ""),
        type=node.get("type", ""),
        priv=node.get("priv", ""),
        api=node.get("api", "") or "",
        group=_texts(config.find("group")) if config is not None else {},
        name=_texts(config.find("name")) if config is not None else {},
        unit=_texts(config.find("unit")) if config is not None else {},
        minimum=minimum,
        maximum=maximum,
        step=step,
        precision=precision,
        options=options,
    )


def parse_dictionary(text: str) -> Dictionary:
    """Parsuje config/hardware.xml.

    Urządzenie wirtualne (vdev) o danym vid może składać się z kilku typów (idt),
    np. vid 0 = "base" (idt 1) + "Pello1.4" (idt 29). Rejestry są łączone.
    """
    root = _xml(text)
    by_idt: dict[str, dict[str, RegisterDef]] = {}
    for device in root.findall("devices/device"):
        registers = by_idt.setdefault(device.get("idt", ""), {})
        for node in device.findall("register"):
            register = _parse_register(node)
            if REGISTER_ID.match(register.tid):
                registers[register.tid] = register

    registers: dict[int, dict[str, RegisterDef]] = {}
    for vdev in root.findall("vdevs/vdev"):
        try:
            vid = int(vdev.get("vid", ""))
        except ValueError:
            continue
        registers.setdefault(vid, {}).update(by_idt.get(vdev.get("idt", ""), {}))

    if not registers.get(0):
        raise ParseError("Słownik nie zawiera rejestrów głównego urządzenia")
    return Dictionary(
        hardware_type=root.get("type", ""),
        version=root.get("sv", ""),
        registers=registers,
    )


def parse_snapshot(text: str) -> Snapshot:
    """Parsuje syncvalues.cgi: linie ``vid;czas;s:1;klucz:wartość;...``."""
    devices: dict[int, DeviceValues] = {}
    for line in text.lstrip("﻿").splitlines():
        parts = line.strip().split(";")
        if len(parts) < 3:
            continue
        try:
            vid = int(parts[0])
        except ValueError:
            continue
        values: dict[str, str] = {}
        active = False
        for item in parts[2:]:
            if ":" not in item:
                continue
            key, raw = item.split(":", 1)
            if key == "s":
                active = raw == "1"
                continue
            if not REGISTER_ID.match(key) or key.startswith(SECRET_PREFIXES):
                continue
            values[key] = unquote(raw)
        devices[vid] = DeviceValues(vid=vid, active=active, values=values)

    main = devices.get(0)
    if main is None or not main.values:
        raise ParseError("syncvalues.cgi nie zawiera danych głównego urządzenia")
    return Snapshot(devices=devices)


def _status(node: Element) -> str:
    status = node.get("status") or "ok"
    return status if _STATUS.match(status) else "unknown"


def parse_write_result(text: str, tid: str) -> None:
    """Sprawdza odpowiedź setregister.cgi.

    Oczekiwany format: ``<cmd status="ok"><device id="0"><reg tid="x" status="ok"/>``.
    Jeśli odpowiedź nie jest XML-em (inne oprogramowanie), zapis uznajemy za
    przyjęty — o wyniku i tak przesądza kolejny odczyt.
    """
    try:
        root = _xml(text)
    except ParseError:
        return
    if _status(root) != "ok":
        raise WriteError(f"Sterownik odrzucił polecenie (status: {_status(root)})")
    for reg in root.iter("reg"):
        if reg.get("tid") == tid:
            if _status(reg) != "ok":
                raise WriteError(f"Sterownik nie zmienił {tid} (status: {_status(reg)})")
            return
