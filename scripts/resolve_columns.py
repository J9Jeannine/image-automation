#!/usr/bin/env python3
"""Spalten eines Funnel-Sheet-Tabs ueber die UEBERSCHRIFT aufloesen, nicht ueber feste
Buchstaben.

Grund (Jeannine, 2026-11-14): im Tab ZA wurde die Spalte "SKU EUR Price" neu als K
eingefuegt. Dadurch ist alles ab dem alten K eine Spalte nach rechts gewandert -- die
Ad-Link-Spalte lag vorher auf M und liegt jetzt auf N. Eine Routine, die feste
Buchstaben annimmt, liest danach die falsche Zelle und findet den neuen Drive-Link
nicht. Das darf nicht noch einmal passieren: Buchstaben sind ab jetzt nur noch ein
Erwartungswert, verbindlich ist die Ueberschrift.

Aufruf (nach dem XLSX-Export des Funnel Sheets):

    python3 scripts/resolve_columns.py <funnel.xlsx>            # alle Markt-Tabs
    python3 scripts/resolve_columns.py <funnel.xlsx> ZA         # nur ein Tab
    python3 scripts/resolve_columns.py <funnel.xlsx> --json     # maschinenlesbar

Exit 0 = fuer jeden geprueften Tab wurden alle Pflichtspalten gefunden.
Exit 1 = mindestens eine Pflichtspalte nicht gefunden -> NICHT weiterarbeiten,
         Tab von Hand ansehen und diese Datei bzw. config/automation.config.json
         nachziehen.

Die Ueberschrift steht in Zeile 1 oder Zeile 2 (teils verbundene Zellen). Verglichen
wird klein geschrieben, ohne Mehrfach-Leerzeichen und ohne Zeilenumbrueche, als
Teilstring -- "Competitor Ad Link/Drive Link" wird also auch gefunden, wenn jemand
den Text leicht ergaenzt.
"""

import json
import re
import sys

try:
    import openpyxl
except ImportError:  # pragma: no cover
    print("openpyxl fehlt. Installieren mit: pip install openpyxl", file=sys.stderr)
    sys.exit(2)

from openpyxl.utils import get_column_letter

# Logischer Name -> Suchtext in der Ueberschrift (klein, normalisiert).
# Reihenfolge ist die Suchreihenfolge; der erste Treffer von links gewinnt.
MARKT_TAB_SPALTEN = {
    "competitor_url": "competitor url",
    "product_name": "new pr name",
    "price": "bundle/deal offer",
    "ad_links": "competitor ad link",        # Kommentar-Thread ODER Drive-Link
    "bearbeiter": "link to videos",          # erste Spalte dieser Ueberschrift
    "ordner_link": "link to videos",         # zweite Spalte dieser Ueberschrift
    "status": "video/images comments",
}

# Spalten, ohne die eine Zeile nicht verarbeitet werden kann.
PFLICHT = ("competitor_url", "product_name", "price", "ad_links")

WINNING_PRODUCTS_SPALTEN = {
    "product_name": "product",
    "ad_links": "drive link",
    "instructions": "instructions",
    "ordner_link": "link to videos",
    "lauf_datum": "date completed",
}

MARKT_TABS = ("FI", "FRCA", "ZA", "NLBE new", "NL/BE new")


def _norm(value):
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip().lower()


def kopfzeile(ws, max_col=40):
    """Pro Spalte den zusammengesetzten Ueberschriftstext aus Zeile 1 und 2."""
    kopf = {}
    for col in range(1, min(ws.max_column, max_col) + 1):
        teile = [_norm(ws.cell(row=row, column=col).value) for row in (1, 2)]
        kopf[get_column_letter(col)] = " | ".join(t for t in teile if t)
    return kopf


def aufloesen(ws, spalten):
    """{logischer Name: Spaltenbuchstabe}. 'link to videos' kommt zweimal vor --
    bearbeiter ist der erste Treffer, ordner_link der zweite."""
    kopf = kopfzeile(ws)
    reihenfolge = list(kopf.items())
    gefunden, verbraucht = {}, set()
    for name, suchtext in spalten.items():
        zweiter = name == "ordner_link" and "bearbeiter" in spalten
        treffer = [L for L, text in reihenfolge if suchtext in text]
        if zweiter:
            treffer = [L for L in treffer if L not in verbraucht]
        if treffer:
            gefunden[name] = treffer[0]
            if suchtext == "link to videos":
                verbraucht.add(treffer[0])
    # "Link to Videos /Images" ist in den Markt-Tabs ueber zwei Spalten verbunden:
    # die erste traegt den Bearbeiter, die zweite den Ordner-Link, und nur die erste
    # hat ueberhaupt einen Ueberschrifttext. Deshalb die Nachbarspalte ableiten.
    if "bearbeiter" in gefunden and "ordner_link" not in gefunden:
        from openpyxl.utils import column_index_from_string
        gefunden["ordner_link"] = get_column_letter(
            column_index_from_string(gefunden["bearbeiter"]) + 1)
    return gefunden


def pruefe_tab(wb, tab):
    ws = wb[tab]
    spalten = WINNING_PRODUCTS_SPALTEN if tab == "Winning Products" else MARKT_TAB_SPALTEN
    gefunden = aufloesen(ws, spalten)
    fehlend = [n for n in PFLICHT if n in spalten and n not in gefunden]
    return gefunden, fehlend


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    pfad = sys.argv[1]
    als_json = "--json" in sys.argv[2:]
    gewuenscht = [a for a in sys.argv[2:] if not a.startswith("--")]

    wb = openpyxl.load_workbook(pfad, read_only=False)
    tabs = gewuenscht or [t for t in wb.sheetnames if t in MARKT_TABS or t == "Winning Products"]

    ergebnis, fehler = {}, False
    for tab in tabs:
        if tab not in wb.sheetnames:
            print(f"FEHLT    Tab '{tab}' gibt es im Sheet nicht.")
            fehler = True
            continue
        gefunden, fehlend = pruefe_tab(wb, tab)
        ergebnis[tab] = gefunden
        if fehlend:
            fehler = True
        if not als_json:
            print(f"=== {tab}")
            reihenfolge = list(dict.fromkeys(
                list(MARKT_TAB_SPALTEN) + list(WINNING_PRODUCTS_SPALTEN)))
            for name in reihenfolge:
                if name in gefunden:
                    print(f"    {name:16s} -> Spalte {gefunden[name]}")
            for name in fehlend:
                print(f"    {name:16s} -> NICHT GEFUNDEN")

    if als_json:
        print(json.dumps(ergebnis, indent=2, ensure_ascii=False))

    if fehler:
        print("\nBLOCKIERT - mindestens eine Pflichtspalte nicht gefunden. "
              "Tab von Hand ansehen, bevor irgendetwas generiert wird.")
        sys.exit(1)
    print("\nOK - alle Pflichtspalten gefunden.")
    sys.exit(0)


if __name__ == "__main__":
    main()
