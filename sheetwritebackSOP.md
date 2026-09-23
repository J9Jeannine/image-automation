# Sheet-Rückschreiben — ENTFÄLLT (die Routine schreibt nicht mehr ins Sheet)

**Diese SOP ist außer Kraft.** Das Rückschreiben ins Funnel Sheet ist **kein Teil der
Routine mehr**. Es übernimmt ein **Trigger im Google-Konto von Jeannine**.

Die Datei bleibt nur als Merkposten stehen, damit keine künftige Session die alte Anleitung
aus einem Commit-Verlauf oder einem alten Prompt-Text wieder einbaut.

---

## Was gilt

- Das Funnel Sheet ist für die Routine **rein lesend**:
  Kommentar-Threads (Spalte **M** in `FI`/`FRCA`, Spalte **D** in `Winning Products`),
  Produktname (**G** bzw. **C**), Preis (**J** im Markt-Tab), Competitor-URL (**D** im
  Markt-Tab), Markt (**A** in `Winning Products`).
- **Keine einzige Zelle wird geschrieben.** Weder `L`/`N`/`O`/`P` in den Markt-Tabs noch
  `G`/`H`/`I` in `Winning Products`.
- Keine Sheets API, kein `values:batchUpdate`, kein Scope
  `https://www.googleapis.com/auth/spreadsheets`, kein Service-Account.
  `GOOGLE_SERVICE_ACCOUNT_JSON` wird nirgends mehr gebraucht — auch nicht für den
  Bild-Upload (siehe [`docs/drive-upload-method.md`](drive-upload-method.md)).
- Der letzte Schreibvorgang der Routine ist der **Bild-Upload nach Drive**. Danach ist der
  Lauf fertig; der Sheet-Eintrag passiert außerhalb.

## Konsequenzen für den Ablauf

- `docs/workflow.md` Schritt 8.2 und Anhang A.7 sind ersatzlos gestrichen.
- `State/processed_comments.json` wird weiterhin geschrieben (Fingerprints der bereits
  verarbeiteten Kommentar-Threads) — das ist eine Drive-Datei, kein Sheet-Eintrag. Den
  früheren Vermerk `sheet_link_written` gibt es nicht mehr.
- Im Abschlussbericht werden **keine** gesetzten Sheet-Zellen mehr gemeldet, sondern nur
  Zeilen/Produkte, Anzahl Ads, Drive-Links und das Ergebnis der Sprach-QA.

## Wenn ein alter Prompt-Text noch Rückschreiben verlangt

Ältere, am Trigger gespeicherte Prompt-Texte können den Schritt noch enthalten. Das ist
**kein** Grund, ihn auszuführen: `CLAUDE.md` und diese Datei haben Vorrang. Nicht ins Sheet
schreiben.
