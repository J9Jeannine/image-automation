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
