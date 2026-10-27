"""Zamiana słownika rejestrów na encje Home Assistant.

Każdy rejestr ze słownika (config/hardware.xml), który sterownik raportuje w
syncvalues.cgi, staje się encją. Typ encji wynika z typu rejestru i uprawnień konta.
Ręcznie dobrane są tylko: lista bezpiecznych zapisów, ważne encje włączone
domyślnie oraz ikony/klasy urządzeń. Wszystko inne jest tworzone jako wyłączone.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field, replace

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.number import NumberDeviceClass
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import (
    PERCENTAGE,
    REVOLUTIONS_PER_MINUTE,
    EntityCategory,
    Platform,
    UnitOfMass,
    UnitOfPower,
    UnitOfPressure,
    UnitOfTemperature,
    UnitOfTime,
)

from .const import MAIN_VID
from .models import Dictionary, RegisterDef, Snapshot, pick

KIND_NUMBER = "number"
KIND_ENUM = "enum"
KIND_TIMESTAMP = "timestamp"
KIND_DURATION = "duration"
KIND_ALARM = "alarm"
KIND_ONOFF = "onoff"
KIND_COMMAND = "command"


@dataclass(frozen=True, slots=True)
class EntitySpec:
    """Wszystko, czego platforma potrzebuje, by utworzyć encję."""

    platform: Platform
    kind: str
    vid: int
    tid: str
    register: RegisterDef
    name: str
    group: str
    enabled: bool
    # rejestr, z którego czytamy stan, gdy inny niż zapisywany (np. tryb_auto -> tryb_auto_state)
    state_tid: str | None = None
    category: EntityCategory | None = None
    device_class: str | None = None
    state_class: SensorStateClass | None = None
    unit: str | None = None
    icon: str | None = None
    precision: int | None = None
    options: dict[str, str] = field(default_factory=dict)  # wartość -> etykieta
    minimum: float | None = None
    maximum: float | None = None
    step: float | None = None


# --- Bezpieczeństwo -----------------------------------------------------------------

# Rejestry pomijane całkowicie (dane logowania, sieć, systemowe).
HIDDEN = re.compile(
    r"^(auth_|eth_|rtc_|upd_|node_|rf_|device_|pattern_|screen_|remote_|local)"
    r"|^(lang|log|accesslevel|datetime|date|time|daytime|prod_date|en_scr|lcd_hdr|panel_cd1)$"
)

# Zapis dozwolony tylko w tych grupach (angielskie nazwy grup ze słownika,
# z obiegami "CH 3", "CH3 - 4-way valve" sprowadzonymi do "CH" / "4-way valve").
WRITE_GROUPS = frozenset(
    {
        "Boiler",
        "DHW",
        "CH",
        "4-way valve",
        "Operating mode",
        "Circulation pump",
        "Buffer CH",
    }
)

# W dozwolonych grupach i tak blokujemy parametry instalacyjne i strojenie.
WRITE_BLOCKED = re.compile(
    r"_cal$|_typ$|^pl_|^mpl_|^pid_|^zaw4d_|_zaw4d_max$|_zaw4d_(open_time|hist|p|i|dir)$"
    r"|^out_|^tank_en$|^fun_cwu$|^time_to_empty$|^burner|^install_type$|^typ_spal$"
    r"|_pl_wyg$|_pump_pok$|_pomp_(on|off)$"
)

# Polecenia dostępne jako przyciski. Restart i formatowanie karty SD są pomijane.
ALLOWED_COMMANDS = frozenset({"cmd_ackalarm"})

# Rejestry ustawiane przez akcję, a nie encję (zapis zmienia stan zasobnika).
SERVICE_ONLY = frozenset({"add_fuel"})

# Zapis, którego stan raportuje osobny rejestr. Rejestr stanu jest tylko do odczytu.
STATE_REGISTERS = {"tryb_auto": "tryb_auto_state"}
STATE_ONLY = frozenset(STATE_REGISTERS.values())

# Funkcje ukrywane, gdy nie są zainstalowane: (wzorzec tid, flaga, wartość oznaczająca brak).
FEATURES: tuple[tuple[re.Pattern[str], str, str], ...] = (
    (re.compile(r"tank"), "tank_en", "0"),
    (re.compile(r"^mod1_"), "mod1", "0"),
    (re.compile(r"^mod2_"), "mod2", "0"),
    (re.compile(r"^dp_"), "dp_en", "0"),
    (re.compile(r"^zas_"), "zas_en", "0"),
    (re.compile(r"(^|_)t2(_|$)"), "ob2_typ", "0"),
    (re.compile(r"^exh_fan_speed$"), "exh_fan_mode", "0"),
)

# Tryb ręczny zatrzymuje palnik i całe sterowanie — encja wyłączona domyślnie.
DISABLED_CONTROLS = frozenset({"tryb_auto"})

# Grupy wyjść i wejść pokazywane jako binary_sensor.
BINARY_GROUPS = frozenset({"Power outputs", "Binary inputs"})

# --- Domyślnie włączone ------------------------------------------------------------

ENABLED = re.compile(
    r"^(kot_tzad|cwu_tzad|cwu_state|zima_lato|tryb_auto|tank_tzad|pog_en"
    r"|ob\d_tzad|ob\d_pok_(lo|norm|hi)|ob\d_pog_en"
    r"|tzew_value|twew_value|fuel_level|time_to_empty|next_fuel_time|add_fuel|add_fuel_time"
    r"|pl_status|tryb_auto_state|kot_status|ob\d_zaw4d_pos|act_dm_speed|mpl_dm_rpm|pl_tfire"
    r"|out_pomp1|out_pomp2|out_cwu|out_pod|out_dm|out_zaw4d|out_miesz|out_tank"
    r"|cmd_ackalarm)$"
)

# --- Prezentacja ---------------------------------------------------------------------

ICONS: dict[str, str] = {
    "tkot_value": "mdi:heating-coil",
    "tcwu_value": "mdi:water-boiler",
    "tpow_value": "mdi:thermometer-chevron-down",
    "tsp_value": "mdi:fire",
    "tzew_value": "mdi:thermometer",
    "tzew_act": "mdi:thermometer",
    "twew_value": "mdi:home-thermometer",
    "t1_value": "mdi:pipe-valve",
    "fuel_level": "mdi:barrel",
    "pl_status": "mdi:fire-circle",
    "pl_flame": "mdi:fire",
    "pl_power_kw": "mdi:lightning-bolt",
    "pl_fuel_flow": "mdi:weight",
    "tryb_auto": "mdi:state-machine",
    "tryb_auto_state": "mdi:state-machine",
    "zima_lato": "mdi:theme-light-dark",
    "zima_lato_state": "mdi:theme-light-dark",
    "cwu_state": "mdi:water-boiler",
    "next_fuel_time": "mdi:calendar-clock",
    "add_fuel_time": "mdi:calendar-check",
    "add_fuel": "mdi:basket-fill",
    "time_to_empty": "mdi:timer-sand-empty",
    "act_dm_speed": "mdi:fan",
    "mpl_dm_rpm": "mdi:fan",
    "cmd_ackalarm": "mdi:alarm-light-off",
    "pl_tfire": "mdi:counter",
}

# Nazwy nadpisane, gdy słownik ma nazwy zbyt ogólne lub powtórzone.
NAMES: dict[str, dict[str, str]] = {
    "tryb_auto": {"pl": "Tryb pracy (Automatyczny / Ręczny)", "en": "Operating mode"},
    "tryb_auto_state": {"pl": "Stan trybu pracy", "en": "Operating mode state"},
    "zima_lato_state": {"pl": "Aktywny tryb Zima/Lato", "en": "Active winter/summer mode"},
    "cwu_tzad": {"pl": "Temperatura zadana CWU", "en": "DHW set temperature"},
    "kot_tact": {"pl": "Aktywna temperatura zadana kotła", "en": "Active boiler setpoint"},
    "cwu_tact": {"pl": "Aktywna temperatura zadana CWU", "en": "Active DHW setpoint"},
    "time_to_empty": {"pl": "Czas do opróżnienia zasobnika", "en": "Time to empty hopper"},
    "add_fuel": {"pl": "Ostatni zasyp", "en": "Last refuel amount"},
    "tzew_act": {"pl": "Temperatura zewnętrzna (aktywna)", "en": "Outdoor temperature (active)"},
}
for _n in range(1, 7):
    NAMES[f"ob{_n}_tzad"] = {
        "pl": f"Temperatura zadana za zaworem CO{_n}",
        "en": f"CH{_n} valve set temperature",
    }

# Jednostki słownika -> jednostka HA, klasa urządzenia sensora, klasa urządzenia number.
UNITS: dict[str, tuple[str | None, str | None, str | None]] = {
    "°C": (UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, NumberDeviceClass.TEMPERATURE),
    "%": (PERCENTAGE, None, None),
    "kW": (UnitOfPower.KILO_WATT, SensorDeviceClass.POWER, NumberDeviceClass.POWER),
    "kg": (UnitOfMass.KILOGRAMS, SensorDeviceClass.WEIGHT, NumberDeviceClass.WEIGHT),
    "g": (UnitOfMass.GRAMS, SensorDeviceClass.WEIGHT, NumberDeviceClass.WEIGHT),
    "sek": (UnitOfTime.SECONDS, SensorDeviceClass.DURATION, NumberDeviceClass.DURATION),
    "s": (UnitOfTime.SECONDS, SensorDeviceClass.DURATION, NumberDeviceClass.DURATION),
    "min": (UnitOfTime.MINUTES, SensorDeviceClass.DURATION, NumberDeviceClass.DURATION),
    "godz": (UnitOfTime.HOURS, SensorDeviceClass.DURATION, NumberDeviceClass.DURATION),
    "h": (UnitOfTime.HOURS, SensorDeviceClass.DURATION, NumberDeviceClass.DURATION),
    "rpm": (REVOLUTIONS_PER_MINUTE, None, None),
    "obr/min": (REVOLUTIONS_PER_MINUTE, None, None),
    "Pa": (UnitOfPressure.PA, SensorDeviceClass.PRESSURE, NumberDeviceClass.PRESSURE),
}

# Pomiary chwilowe, dla których prowadzimy statystyki długoterminowe.
MEASUREMENT_UNITS = frozenset({"°C", "%", "kW", "kg/h", "rpm", "obr/min", "Pa"})

# Liczniki rosnące.
TOTAL_INCREASING = frozenset({"pl_tfire"})

_CIRCUIT = re.compile(r"^CH ?(\d)\b")
_CIRCUIT_TID = re.compile(r"^ob(\d)_")


def _group_key(register: RegisterDef) -> str:
    """Angielska nazwa grupy bez numeru obiegu: 'CH 3 - Alerts' -> 'Alerts', 'CH 2' -> 'CH'."""
    group = register.group.get("en", "")
    if " - " in group and _CIRCUIT.match(group):
        return group.split(" - ", 1)[1]
    if _CIRCUIT.match(group):
        return "CH"
    return group


def _circuit(register: RegisterDef) -> int | None:
    if match := _CIRCUIT.match(register.group.get("en", "")):
        return int(match.group(1))
    if match := _CIRCUIT_TID.match(register.tid):
        return int(match.group(1))
    return None


def _unused(register: RegisterDef, values: dict[str, str]) -> bool:
    """Obiegi CO o typie 0 i wyłączony bufor nie są zainstalowane."""
    circuit = _circuit(register)
    if circuit is not None and values.get(f"ob{circuit}_typ") == "0":
        return True
    if _group_key(register) == "Buffer CH" and values.get("tank_en") == "0":
        return True
    return any(
        pattern.search(register.tid) and values.get(flag) == off for pattern, flag, off in FEATURES
    )


def _can_write(register: RegisterDef, level: int) -> bool:
    return (
        register.writable(level)
        and _group_key(register) in WRITE_GROUPS
        and not WRITE_BLOCKED.search(register.tid)
        and register.tid not in SERVICE_ONLY
        and register.tid not in STATE_ONLY
    )


def _is_onoff(options: dict[str, str]) -> bool:
    return set(options) == {"0", "1"}


def _spec(
    register: RegisterDef,
    values: dict[str, str],
    level: int,
    language: str,
) -> EntitySpec | None:
    tid = register.tid
    rtype = register.type
    unit_text = pick(register.unit, language)
    unit, sensor_class, number_class = UNITS.get(unit_text, (unit_text or None, None, None))
    options = {value: pick(texts, language) for value, texts in register.options.items()}
    group = pick(register.group, language)
    name = pick(NAMES.get(tid, register.name), language) or tid
    has_value = tid in values and values[tid] != ""
    curated = bool(ENABLED.match(tid))
    base = {
        "vid": MAIN_VID,
        "tid": tid,
        "register": register,
        "name": name,
        "group": group,
        "icon": ICONS.get(tid),
    }

    if rtype == "cmd":
        if tid not in ALLOWED_COMMANDS or not register.executable(level):
            return None
        return EntitySpec(platform=Platform.BUTTON, kind=KIND_COMMAND, enabled=True, **base)

    # Pozostałe typy muszą być raportowane w syncvalues.cgi.
    if tid not in values and tid not in STATE_REGISTERS:
        return None
    if not register.readable(level):
        return None

    if rtype == "alarm":
        return EntitySpec(
            platform=Platform.BINARY_SENSOR,
            kind=KIND_ALARM,
            enabled=True,
            device_class=BinarySensorDeviceClass.PROBLEM,
            options=options,
            **base,
        )

    if rtype == "unixtime":
        return EntitySpec(
            platform=Platform.SENSOR,
            kind=KIND_TIMESTAMP,
            enabled=curated,
            device_class=SensorDeviceClass.TIMESTAMP,
            category=None if curated else EntityCategory.DIAGNOSTIC,
            **base,
        )

    if rtype == "interval":
        return EntitySpec(
            platform=Platform.SENSOR,
            kind=KIND_DURATION,
            enabled=curated,
            device_class=SensorDeviceClass.DURATION,
            unit=UnitOfTime.SECONDS,
            category=EntityCategory.DIAGNOSTIC,
            **base,
        )

    if rtype == "enum":
        if not options:
            return None
        if _can_write(register, level):
            enabled = curated and tid not in DISABLED_CONTROLS
            category = None if curated else EntityCategory.CONFIG
            if _is_onoff(options) and tid not in STATE_REGISTERS:
                return EntitySpec(
                    platform=Platform.SWITCH,
                    kind=KIND_ONOFF,
                    enabled=enabled,
                    category=category,
                    **base,
                )
            return EntitySpec(
                platform=Platform.SELECT,
                kind=KIND_ENUM,
                enabled=enabled,
                category=category,
                state_tid=STATE_REGISTERS.get(tid),
                options=options,
                **base,
            )
        if _group_key(register) in BINARY_GROUPS and _is_onoff(options):
            return EntitySpec(
                platform=Platform.BINARY_SENSOR,
                kind=KIND_ONOFF,
                enabled=curated,
                device_class=(
                    BinarySensorDeviceClass.RUNNING
                    if _group_key(register) == "Power outputs"
                    else None
                ),
                category=None if curated else EntityCategory.DIAGNOSTIC,
                **base,
            )
        return EntitySpec(
            platform=Platform.SENSOR,
            kind=KIND_ENUM,
            enabled=curated,
            device_class=SensorDeviceClass.ENUM,
            options=options,
            category=None if curated else EntityCategory.DIAGNOSTIC,
            **base,
        )

    if rtype in ("float", "int"):
        if _can_write(register, level):
            return EntitySpec(
                platform=Platform.NUMBER,
                kind=KIND_NUMBER,
                enabled=curated,
                category=None if curated else EntityCategory.CONFIG,
                device_class=number_class,
                unit=unit,
                precision=register.precision,
                minimum=register.minimum,
                maximum=register.maximum,
                step=register.step,
                **base,
            )
        measurement = register.has_api("chart") or unit_text in MEASUREMENT_UNITS
        state_class = None
        if tid in TOTAL_INCREASING:
            state_class = SensorStateClass.TOTAL_INCREASING
        elif measurement and sensor_class not in (SensorDeviceClass.DURATION,):
            state_class = SensorStateClass.MEASUREMENT
        enabled = curated or (register.has_api("chart") and has_value)
        return EntitySpec(
            platform=Platform.SENSOR,
            kind=KIND_NUMBER,
            enabled=enabled,
            category=None if enabled else EntityCategory.DIAGNOSTIC,
            device_class=sensor_class,
            state_class=state_class,
            unit=unit,
            precision=register.precision,
            **base,
        )

    # string, text, string.ip, string.auth, weeklytable — pomijane
    return None


def build_specs(
    dictionary: Dictionary, snapshot: Snapshot, level: int, language: str
) -> list[EntitySpec]:
    """Lista encji dla głównego urządzenia sterownika."""
    values = snapshot.values(MAIN_VID)
    specs: list[EntitySpec] = []
    for register in dictionary.for_vid(MAIN_VID).values():
        if HIDDEN.search(register.tid) or _unused(register, values):
            continue
        if spec := _spec(register, values, level, language):
            specs.append(spec)

    # Powtórzone nazwy (np. "Temperatura zadana" w CWU i w zaworze) dostają nazwę grupy.
    counts = Counter(spec.name for spec in specs)
    renamed: list[EntitySpec] = []
    for spec in specs:
        if counts[spec.name] > 1 and spec.group:
            spec = replace(spec, name=f"{spec.name} ({spec.group})")
        renamed.append(spec)
    counts = Counter(spec.name for spec in renamed)
    return [
        replace(spec, name=f"{spec.name} [{spec.tid}]") if counts[spec.name] > 1 else spec
        for spec in renamed
    ]
