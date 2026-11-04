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


def test_return_protection_is_writable():
    specs = _specs()
    ochr = specs["ochr_pow"]
    assert ochr.platform is Platform.SELECT and ochr.enabled
    assert ochr.options == {
        "0": "Pompa mieszająca",
        "1": "Pompa CWU",
        "2": "Zawór 4D",
        "3": "Wyłączona",  # literówka "Wyłaczona" w słowniku sterownika
    }
    tryb = specs["tryb_ochr_pow"]
    assert tryb.platform is Platform.SELECT and tryb.enabled
    assert tryb.options["0"] == "Pompy CO i palnik"
    tpow = specs["tpow_min"]
    assert tpow.platform is Platform.NUMBER and tpow.enabled
    assert (tpow.minimum, tpow.maximum, tpow.step) == (35, 60, 1)
    # inne parametry z grupy "Zaawansowane" zostają tylko do odczytu
    assert specs["pomp_ton"].platform is Platform.SENSOR


def test_names_are_unique_and_readable():
    specs = _specs()
    assert specs["pog_krzyw1"].name == "Krzywa grzania - temp. kotła dla minus 10°C"
    assert specs["pog_krzyw2"].name == "Krzywa grzania - temp. kotła dla plus 10°C"
    assert specs["ob1_pog_krzyw1"].name == "Krzywa grzania - temp. dla minus 10°C"
    assert specs["pl_flame_b"].name == "Płomień wykryty"
    assert specs["pl_flame"].name == "Płomień"
    assert "tpod_value" not in specs  # "not use" w słowniku
    names = [spec.name for spec in specs.values()]
    assert len(names) == len(set(names))
