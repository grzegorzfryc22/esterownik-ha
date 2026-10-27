"""Parsowanie odpowiedzi sterownika."""

import pytest

from custom_components.esterownik.errors import ParseError, WriteError
from custom_components.esterownik.parser import (
    parse_dictionary,
    parse_info,
    parse_snapshot,
    parse_write_result,
)

from .conftest import fixture


def test_info():
    info = parse_info(fixture("pello", "info.xml"))
    assert info.hardware_type == "pello"
    assert info.hardware_version == "3.5"
    assert info.mac == "aabbccddeeff"


def test_dictionary_merges_base_and_device_types():
    dictionary = parse_dictionary(fixture("pello", "hardware.xml"))
    main = dictionary.for_vid(0)
    assert "cmd_ackalarm" in main  # z typu "base"
    assert "tkot_value" in main  # z typu "Pello1.4"
    kot = main["kot_tzad"]
    assert (kot.minimum, kot.maximum, kot.step) == (42, 80, 1)
    assert kot.writable(0)
    assert main["tryb_auto"].options["0"]["pl"] == "Ręczny"
    # zepsuta lista opcji (wszystkie id="0") jest ignorowana
    assert main["fuel_level_enum"].options == {}


def test_snapshot_drops_credentials_and_decodes_values():
    snapshot = parse_snapshot(fixture("pello", "syncvalues.txt"))
    values = snapshot.values(0)
    assert not any(key.startswith("auth_") for key in values)
    assert values["pod_run_time_str"] == "396m 34s"
    assert snapshot.value(0, "t2_value") is None  # pusty = brak czujnika
    assert snapshot.value(0, "t1_value") == "29.97"


def test_snapshot_without_main_device_fails():
    with pytest.raises(ParseError):
        parse_snapshot("1;0;s:0;\n")


def test_write_result():
    parse_write_result('<cmd status="ok"><device><reg tid="a" status="ok"/></device></cmd>', "a")
    parse_write_result("OK", "a")  # nie-XML: przyjmujemy
    with pytest.raises(WriteError, match="out_of_range"):
        parse_write_result(
            '<cmd status="ok"><device><reg tid="a" status="out_of_range"/></device></cmd>', "a"
        )
