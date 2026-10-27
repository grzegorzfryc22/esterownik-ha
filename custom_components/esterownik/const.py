"""Stałe integracji eSterownik."""

from typing import Final

DOMAIN: Final = "esterownik"

DEFAULT_SCAN_INTERVAL: Final = 30
MIN_SCAN_INTERVAL: Final = 10
MAX_SCAN_INTERVAL: Final = 600
REQUEST_TIMEOUT: Final = 15

# Główne urządzenie sterownika: pierwsza linia syncvalues.cgi i device=0 w setregister.cgi.
MAIN_VID: Final = 0

PATH_INFO: Final = "info.cgi"
PATH_DICTIONARY: Final = "config/hardware.xml"
PATH_VALUES: Final = "syncvalues.cgi"
PATH_WRITE: Final = "setregister.cgi"

DEFAULT_USERNAME: Final = "root"

SERVICE_ADD_FUEL: Final = "add_fuel"
ATTR_AMOUNT: Final = "amount"
ATTR_CONFIG_ENTRY_ID: Final = "config_entry_id"
