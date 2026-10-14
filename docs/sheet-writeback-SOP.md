# Sheet-Eintrag (L/N/O/P) — macht die Apps-Script-Web-App

Stand 2026-10-03. Ersetzt die Fassung vom 23.09., die einen „Trigger im Google-Konto“
behauptete, den es nie gab — deshalb blieben ab dann alle Zeilen leer (Ursache nachgewiesen:
`fillFunnelSheet()` existierte im Script, wurde aber von nichts aufgerufen).

## Wie es jetzt läuft

- Code: [`apps-script/Code.gs`](../apps-script/Code.gs) — muss im Script-Editor identisch sein.
- `doPost` lädt das Bild hoch und ruft danach `fillFunnelSheet()` auf. Antwort:
  `{"id":…,"link":…,"sheet":"ok: FI!111 FlexiVera"}` oder `"sheet":"ERROR: …"`.
- `{"action":"fill"}` an denselben Endpunkt führt nur den Sheet-Eintrag aus.
- `fillFunnelSheet()` liest die Ordner `<YYYY-MM-DD> - <Produkt>` unter
  `Translated-Ads/FI` und `Translated-Ads/FRCA`, sucht den Produktnamen in Spalte **G** des
  gleichnamigen Tabs und füllt **nur leere** Zellen: L = Datum, N = `claude`,
  O = `HYPERLINK(Ordner;Produkt)`, P = `in progress`. Neuester Ordner gewinnt.
- Netz: stündlicher Zeit-Trigger (`installTrigger()` einmal im Editor ausgeführt).

## Pflicht für die Routine

1. Nach dem letzten Upload eines Laufs: `curl -sS -L "<endpoint>" -H "Content-Type: application/json" -d '{"action":"fill"}'`
2. Den Wert von `sheet` wörtlich in den Abschlussbericht.
3. `ERROR` / fehlendes Feld → im Bericht als **nicht eingetragen** melden.
4. Die Routine selbst schreibt keine Zelle (kein Sheets-API, kein Service-Account).

Ordnername **muss** exakt dem Produktnamen in Spalte G entsprechen (Groß/klein egal),
sonst findet `fillFunnelSheet()` die Zeile nicht.


---

## Fehlerfall 2026-10-14 — Eintragung in einer Zeile ohne Quelle (BEHOBEN)

**Symptom (von Jeannine gemeldet):** `FI!123` (smokola) zeigte `L` = Datum, `N` = `claude`,
`O` = Ordner-Link, `P` = `in progress`, obwohl in Spalte **M** dieser Zeile weder
Ad-Links noch ein Ordner-Link stehen. Fuer diese Zeile wurde nie etwas generiert.

**Ursache:** Die alte Fassung von `fillFunnelSheet()` hat die Ordner unter
`Translated-Ads/<Markt>` eingelesen und jede Zeile gesucht, deren Spalte **G** denselben
Produktnamen traegt. Der Produktname ist aber nicht eindeutig: `smokola` steht im FI-Tab
in den Zeilen 6, 59 **und** 123. Ein alter Ordner `… - Smokola` aus der frueheren Zeile
hat deshalb auch die neue, unbearbeitete Zeile 123 getroffen. Dasselbe haette jede andere
Zeile getroffen, die einen schon einmal verwendeten Produktnamen wiederverwendet.

**Behebung:** `fillFunnelSheet()` raet nicht mehr. Die Routine meldet beim Upload im
JSON-Feld `row` genau die Zeile, zu der der Upload gehoert
(`"FI!120"`, `"NL/BE new!3"`). Das Script fuehrt daraus eine Registry in den
ScriptProperties und beschreibt ausschliesslich diese Zeilen. Fehlt `row`, wird gar
nichts eingetragen.

**Aufraeumen einer bereits falsch gefuellten Zeile:** `clearRows_(['FI!123'])` einmal im
Script-Editor ausfuehren (loescht `L`/`N`/`O`/`P` dieser Zeile und nimmt sie aus der
Registry), oder die vier Zellen von Hand leeren. Da `setIfEmpty_` nur leere Zellen
beschreibt, kommt die Eintragung danach nicht zurueck.

**Damit der Fix wirkt, muss `apps-script/Code.gs` in den Script-Editor uebernommen und
die Web-App neu deployed werden.** Bis dahin gilt der alte Stand im Google-Konto.


---

## WICHTIG: solange das alte Script deployed ist, kommt die falsche Zeile zurueck

Am 2026-10-14 nachgewiesen: ein Aufruf von `{"action":"fill"}` gegen den **damals
deployten** (alten) Stand antwortete mit `ok: FI!123 smokola` — das Script hat die zuvor
von Hand geleerten Zellen sofort wieder gefuellt.

Daraus folgt:

- **Die Zellen von Hand zu leeren reicht nicht.** Der stuendliche Zeit-Trigger ruft
  `fillFunnelSheet()` ohnehin weiter auf und schreibt sie erneut.
- **Erst das Deployment des neuen Stands stoppt das.** Danach raet das Script nicht mehr
  ueber den Produktnamen, sondern schreibt nur Zeilen, die ueber `row` gemeldet wurden.
- **`{"action":"fill"}` darf nicht aufgerufen werden, solange der alte Stand laeuft.**

## Reihenfolge nach dem Deployment

1. `apps-script/Code.gs` aus diesem Repo in den Script-Editor kopieren und die Web-App
   neu deployen.
2. Falsche Eintragung entfernen:

   ```bash
   curl -sS -L "$ENDPOINT" -H "Content-Type: application/json" \
     -d '{"action":"clear","rows":["FI!123"]}'
   ```

3. Zeilen nachtragen, die hochgeladen wurden, bevor das neue Script lief:

   ```bash
   curl -sS -L "$ENDPOINT" -H "Content-Type: application/json" \
     -d '{"action":"register","row":"NL/BE new!3","folderId":"<Ordner-ID>"}'
   ```

   Der Call traegt die Zeile in die Registry ein und ruft danach `fillFunnelSheet()` auf,
   schreibt also direkt L/N/O/P.
