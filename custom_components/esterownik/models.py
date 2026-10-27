"""Model danych sterownika eSterownik: informacje, słownik rejestrów i odczyty."""

from __future__ import annotations

from dataclasses import dataclass, field

ACCESS_NONE = "-"
ACCESS_READ = "r"
ACCESS_WRITE = "w"
ACCESS_EXECUTE = "x"


def pick(texts: dict[str, str], language: str) -> str:
    """Tekst w danym języku, z awarią na polski, angielski albo dowolny."""
    for lang in (language, "pl", "en"):
        if texts.get(lang):
            return texts[lang]
    return next((text for text in texts.values() if text), "")


@dataclass(frozen=True, slots=True)
class ControllerInfo:
    """Odpowiedź info.cgi."""

    hardware_type: str
    hardware_version: str
    software_version: str
    company: str
    mac: str
    serial: str
    name: str


@dataclass(frozen=True, slots=True)
class RegisterDef:
    """Opis jednego rejestru ze słownika config/hardware.xml."""

    tid: str
    type: str
    priv: str
    api: str
    group: dict[str, str] = field(default_factory=dict)
    name: dict[str, str] = field(default_factory=dict)
    unit: dict[str, str] = field(default_factory=dict)
    minimum: float | None = None
    maximum: float | None = None
    step: float | None = None
    precision: int | None = None
    # wartość -> etykiety w językach; puste, gdy rejestr nie jest wyliczeniem
    options: dict[str, dict[str, str]] = field(default_factory=dict)

    def access(self, level: int) -> str:
        """Uprawnienie konta o danym poziomie: '-', 'r', 'w' albo 'x'."""
        if 0 <= level < len(self.priv):
            return self.priv[level]
        return ACCESS_NONE

    def readable(self, level: int) -> bool:
        return self.access(level) in (ACCESS_READ, ACCESS_WRITE)

    def writable(self, level: int) -> bool:
        return self.access(level) == ACCESS_WRITE

    def executable(self, level: int) -> bool:
        return self.access(level) == ACCESS_EXECUTE

    def has_api(self, flag: str) -> bool:
        return f"|{flag}|" in (self.api or "")

    def option_label(self, value: str, language: str) -> str | None:
        texts = self.options.get(value)
        return pick(texts, language) if texts else None


@dataclass(frozen=True, slots=True)
class Dictionary:
    """Słownik rejestrów pogrupowany według urządzeń wirtualnych (vid)."""

    hardware_type: str
    version: str
    registers: dict[int, dict[str, RegisterDef]]

    def for_vid(self, vid: int) -> dict[str, RegisterDef]:
        return self.registers.get(vid, {})


@dataclass(frozen=True, slots=True)
class DeviceValues:
    """Jedna linia syncvalues.cgi."""

    vid: int
    active: bool
    values: dict[str, str]


@dataclass(frozen=True, slots=True)
class Snapshot:
    """Wszystkie linie syncvalues.cgi."""

    devices: dict[int, DeviceValues]

    def values(self, vid: int) -> dict[str, str]:
        device = self.devices.get(vid)
        return device.values if device else {}

    def value(self, vid: int, tid: str) -> str | None:
        """Wartość rejestru albo None, gdy brak lub pusta (np. niepodłączony czujnik)."""
        value = self.values(vid).get(tid)
        return value if value not in (None, "") else None
