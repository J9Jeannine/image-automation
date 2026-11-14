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
    python3 scripts/resolve_columns.py <funnel.xlsx> --offen    # offene Zeilen listen

`--offen` listet je Tab die Zeilen, in denen die Ad-/Drive-Link-Spalte einen Link traegt
und die Ordner-Link-Spalte noch leer ist -- also die Zeilen, die dieser Lauf abarbeiten
muss. Ein Link zaehlt in DREI Formen, und alle drei muessen geprueft werden:

  a) Zellwert `=HYPERLINK("https://...";"Text")`  -- Formel
  b) an den Zelltext gehaengter Hyperlink        -- `cell.hyperlink`, der Zellwert ist
     dann nur sichtbarer Text wie "Set 1-Dens"
  c) blanke URL als Zellwert

Form (b) hat am 2026-11-14 ZA!17 (Jointiva) durchrutschen lassen: die Zelle sah leer von
Links aus, weil nur nach `=HYPERLINK(` gesucht wurde. Deshalb jetzt alle drei Formen.

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


def zell_link(cell):
    """Link einer Zelle in allen drei Formen, sonst None.

    (a) `=HYPERLINK("...";"...")` als Zellwert, (b) an den Zelltext gehaengter
    Hyperlink (`cell.hyperlink`), (c) blanke URL als Zellwert. Wer nur (a) prueft,
    uebersieht Zeilen -- siehe Modulkopf."""
    ziel = getattr(cell, "hyperlink", None)
    if ziel is not None:
        ziel = getattr(ziel, "target", None) or str(ziel)
        if ziel:
            return ziel
    wert = cell.value
    if not isinstance(wert, str):
        return None
    treffer = re.search(r'HYPERLINK\s*\(\s*"([^"]+)"', wert, re.IGNORECASE)
    if treffer:
        return treffer.group(1)
    if wert.strip().lower().startswith(("http://", "https://")):
        return wert.strip()
    return None


def zelle_leer(cell):
    if zell_link(cell):
        return False
    return not str(cell.value or "").strip()


def offene_zeilen(ws, gefunden, ab_zeile=2):
    """Zeilen mit Link in der Ad-/Drive-Link-Spalte und noch leerer Ordner-Link-Spalte."""
    quelle = gefunden.get("ad_links")
    ziel = gefunden.get("ordner_link")
    name = gefunden.get("product_name")
    if not quelle or not ziel:
        return []
    offen = []
    for r in range(ab_zeile, ws.max_row + 1):
        link = zell_link(ws[quelle + str(r)])
        if not link:
            continue
        if not zelle_leer(ws[ziel + str(r)]):
            continue
        offen.append({
            "zeile": r,
            "produkt": str(ws[name + str(r)].value or "").strip() if name else "",
            "quelle": link,
            "quelle_text": str(ws[quelle + str(r)].value or "").strip(),
        })
    return offen


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
    zeige_offen = "--offen" in sys.argv[2:]
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
        ergebnis[tab] = dict(gefunden)
        if zeige_offen:
            offen = offene_zeilen(wb[tab], gefunden)
            ergebnis[tab] = {"spalten": gefunden, "offene_zeilen": offen}
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
            if zeige_offen:
                offen = ergebnis[tab]["offene_zeilen"]
                if offen:
                    for eintrag in offen:
                        print(f"    OFFEN  Zeile {eintrag['zeile']:>3}  "
                              f"{eintrag['produkt'] or '(ohne Produktnamen)'}  "
                              f"<- {eintrag['quelle_text'] or eintrag['quelle']}")
                else:
                    print("    OFFEN  keine")

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
