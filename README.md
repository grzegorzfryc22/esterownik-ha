# eSterownik dla Home Assistant

Lokalna integracja Home Assistant dla sterowników kotłów **eSterownik.pl** (ELEKTRO-SYSTEM):
**Pello** (kotły pelletowe) i **eCoal** (kotły węglowe). Działa bez chmury: łączy się
bezpośrednio ze stroną WWW sterownika w sieci lokalnej.

> Wsparcie eCoal jest na razie **eksperymentalne** — integracja korzysta z tego samego API
> co Pello, ale nie była jeszcze testowana na każdym modelu.

## Jak to działa

Sterownik udostępnia **słownik rejestrów** (`config/hardware.xml`) z polskimi nazwami,
jednostkami, zakresami, listami opcji i uprawnieniami. Integracja czyta ten słownik i sama
tworzy encje — dlatego obsługuje różne modele bez ręcznego dopisywania rejestrów.

| Rejestr w słowniku | Encja |
| --- | --- |
| Pomiar (temperatura, moc, %, kg/h…) | `sensor` ze statystykami długoterminowymi |
| Nastawa liczbowa (temperatura zadana, krzywa…) | `number` z zakresem i krokiem ze sterownika |
| Wyliczenie z zapisem (tryb Zima/Lato, tryb CWU…) | `select` |
| Wyliczenie 0/1 z zapisem (regulator pogodowy…) | `switch` |
| Alarm | `binary_sensor` (problem) z opisem alarmu |
| Wyjście mocy, wejście binarne | `binary_sensor` |
| Data (następny zasyp, ostatni zasyp) | `sensor` typu timestamp |
| Polecenie „Potwierdzenie alarmów” | `button` |

Najważniejsze encje są włączone od razu. Pozostałe rejestry (parametry, liczniki,
diagnostyka) są tworzone jako **wyłączone** — włączysz je w ustawieniach urządzenia.
Obiegi CO, bufor i moduły, których nie masz zainstalowanych, są pomijane.

## Bezpieczeństwo zapisu

Zapis jest dozwolony tylko dla nastaw użytkowych: kocioł, CWU, obiegi CO, zawór 4D,
tryb pracy, pompa cyrkulacyjna i bufor. **Nigdy nie są zapisywalne:**
strojenie palnika, typ kotła, kalibracje czujników, parametry PID i instalacyjne,
ręczne sterowanie wyjściami, restart i formatowanie karty SD.
Wartość spoza zakresu sterownik odrzuci, a Home Assistant pokaże błąd.

### Tryb ręczny

Tryb **Automatyczny / Ręczny** jest dostępny, ale domyślnie wyłączony. Tryb ręczny
**zatrzymuje palnik**, a sterownik przestaje sterować pompami, zaworem i podajnikiem —
dom i CWU przestają być grzane. Nie używaj go w automatyzacjach bez zabezpieczeń.

### Regulator pogodowy

Przy włączonym regulatorze pogodowym sterownik sam wylicza temperaturę zadaną z krzywej
grzewczej — rzeczywistą wartość pokazują sensory „Aktywna temperatura zadana …”.

## Instalacja (HACS)

1. HACS → trzy kropki → **Niestandardowe repozytoria**.
2. Repozytorium: `https://github.com/grzegorzfryc22/esterownik-ha`, kategoria **Integracja**.
3. **Pobierz**, a potem zrestartuj Home Assistant.
4. **Ustawienia → Urządzenia oraz usługi → Dodaj integrację → eSterownik**.
5. Podaj adres IP sterownika oraz login i hasło do jego strony WWW (zwykle `root`).

Częstotliwość odświeżania zmienisz w **Konfiguruj**, a adres IP — w **Zmień konfigurację**.
Wymagany Home Assistant 2026.3 lub nowszy.

## Akcja: rejestracja zasypu

`esterownik.add_fuel` zapisuje ilość wsypanego paliwa (kg). Sterownik traktuje zasobnik
jako pełny i od nowa liczy prognozę. Zakres ilości pochodzi ze sterownika.

## Przejście z pello-ha

To osobna integracja (domena `esterownik`). Aby przejść: zainstaluj ją, dodaj sterownik,
sprawdź encje, a następnie usuń integrację „Piec Pello 3.5”. Identyfikatory encji
(`entity_id`) będą inne — popraw je w automatyzacjach i na pulpitach.

## Zgłaszanie nowego sterownika

Najbardziej pomaga zrzut z Twojego sterownika: `config/hardware.xml`, `info.cgi`
i `syncvalues.cgi` (otwórz w przeglądarce po zalogowaniu i zapisz przez Ctrl+S).
**Przed wysłaniem usuń z `syncvalues.cgi` pola `auth_root`, `auth_admin` i `auth_user`**
— zawierają login i hasło zakodowane Base64 (to nie jest szyfrowanie).
W `info.cgi` zamaskuj `mac`, `sn` i `uid`.

## Licencja

[Apache 2.0](LICENSE). Projekt niezależny, niezwiązany z ELEKTRO-SYSTEM ani eSterownik.pl.
