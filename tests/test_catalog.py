"""Zamiana słownika na encje — reguły bezpieczeństwa."""

from homeassistant.const import Platform

from custom_components.esterownik.catalog import build_specs
from custom_components.esterownik.parser import parse_dictionary, parse_snapshot

from .conftest import fixture


def _specs():
    dictionary = parse_dictionary(fixture("pello", "hardware.xml"))
    snapshot = parse_snapshot(fixture("pello", "syncvalues.txt"))
    return {spec.tid: spec for spec in build_specs(dictionary, snapshot, 0, "pl")}


def test_controls_are_curated():
    specs = _specs()
    assert specs["kot_tzad"].platform is Platform.NUMBER and specs["kot_tzad"].enabled
    assert specs["ob1_tzad"].platform is Platform.NUMBER
    assert specs["zima_lato"].platform is Platform.SELECT
    assert specs["pog_en"].platform is Platform.SWITCH


def test_manual_mode_is_disabled_and_reads_state_register():
    spec = _specs()["tryb_auto"]
    assert spec.platform is Platform.SELECT
    assert spec.state_tid == "tryb_auto_state"
    assert not spec.enabled


def test_risky_registers_are_never_writable():
    specs = _specs()
    writable = {
        tid
        for tid, s in specs.items()
        if s.platform in (Platform.NUMBER, Platform.SELECT, Platform.SWITCH)
    }
    for tid in writable:
        assert not tid.startswith(("pl_", "mpl_", "pid_", "out_", "auth_", "eth_")), tid
        assert not tid.endswith(("_cal", "_typ")), tid
    assert "burner_type" not in writable
    assert "cmd_reset" not in specs
    assert "cmd_formatsdcard" not in specs
    # wyjścia mocy tylko do odczytu
    assert specs["out_pomp1"].platform is Platform.BINARY_SENSOR


def test_secrets_and_unused_features_hidden():
    specs = _specs()
    assert not any(tid.startswith(("auth_", "eth_")) for tid in specs)
    assert not any(tid.startswith("ob2_") for tid in specs)  # obieg CO2 nie zainstalowany
    assert "alarm_tank_hi" not in specs  # brak bufora
    assert "mod2_power" not in specs  # brak licznika energii


def test_names_are_unique():
    names = [spec.name for spec in _specs().values()]
    assert len(names) == len(set(names))
