"""eCoal v4.0 (oprogramowanie 1.1.36.14) — ten sam kod co Pello, inne rejestry."""

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import Platform
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from custom_components.esterownik.catalog import build_specs
from custom_components.esterownik.const import DOMAIN
from custom_components.esterownik.parser import parse_dictionary, parse_info, parse_snapshot

from .conftest import HOST, OK, fixture


def _specs():
    dictionary = parse_dictionary(fixture("ecoal", "hardware.xml"))
    snapshot = parse_snapshot(fixture("ecoal", "syncvalues.txt"))
    return {spec.tid: spec for spec in build_specs(dictionary, snapshot, 0, "pl")}


def test_info_decodes_name():
    info = parse_info(fixture("ecoal", "info.xml"))
    assert (info.hardware_type, info.hardware_version) == ("eCoal", "4.0")
    assert info.name == "Kachlok 2.0"


def test_circuits_named_by_type():
    specs = _specs()
    # obieg 1 z zaworem 4D, obieg 2 bezpośredni
    assert specs["ob1_tzad"].name == "Temperatura zadana za zaworem CO1"
    assert specs["ob2_tzad"].name == "Temperatura zadana obiegu CO2"
    assert "ob3_tzad" not in specs  # obieg 3 nie zainstalowany


def test_ecoal_controls_and_safety():
    specs = _specs()
    assert specs["kot_tzad"].platform is Platform.NUMBER and specs["kot_tzad"].enabled
    assert specs["kot_status"].platform is Platform.SENSOR and specs["kot_status"].enabled
    assert specs["stats_pwr"].enabled
    writable = {
        tid
        for tid, s in specs.items()
        if s.platform in (Platform.NUMBER, Platform.SELECT, Platform.SWITCH)
    }
    for tid in writable:
        assert not tid.startswith(("ec_", "gr_", "p_", "rr_", "zas_", "out_", "pod_")), tid
        assert not tid.endswith(("_cal", "_typ")), tid
    names = [s.name for s in specs.values()]
    assert len(names) == len(set(names))


async def test_ecoal_setup_and_write(hass, entry_ecoal, mock_ecoal):
    hass.config.language = "pl"
    assert await hass.config_entries.async_setup(entry_ecoal.entry_id)
    await hass.async_block_till_done()
    assert entry_ecoal.state is ConfigEntryState.LOADED

    reg = er.async_get(hass)

    def eid(platform, tid):
        return reg.async_get_entity_id(platform, DOMAIN, f"112233445566_0_{tid}")

    assert hass.states.get(eid("sensor", "kot_status")).state == "Podtrzymanie"
    assert hass.states.get(eid("sensor", "tpod_value")).state == "38.57"
    assert hass.states.get(eid("select", "zima_lato")).state == "Auto-Lato"
    device = dr.async_get(hass).async_get_device(identifiers={(DOMAIN, "112233445566")})
    assert device.name == "Kachlok 2.0"
    assert device.model == "eCoal 4.0"

    mock_ecoal.get(f"http://{HOST}/setregister.cgi", text=OK.format(tid="x"))
    await hass.services.async_call(
        "number", "set_value", {"entity_id": eid("number", "ob2_tzad"), "value": 33}, blocking=True
    )
    writes = [str(c[1]) for c in mock_ecoal.mock_calls if "setregister" in str(c[1])]
    assert writes == [f"http://{HOST}/setregister.cgi?device=0&ob2_tzad=33"]
