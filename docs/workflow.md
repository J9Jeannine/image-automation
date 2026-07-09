# Master-Workflow

Wird bei jedem Trigger-Lauf ausgeführt. Tool-Namen beziehen sich auf die in der
Cowork-Session verfügbaren MCP-Server (`Google_Drive`, `Higgsfield`) sowie Bash für die
Playwright-Skripte in `scripts/`.

## Schritt 0 — Config-Guard

1. `config/automation.config.json` aus diesem Repo lesen.
2. Bleibt ein Pflichtfeld unklar (z. B. `foundation_documents.*` fehlt, obwohl
   `foundation_phase.mode` das braucht) → Lauf für die betroffene Teil-Phase überspringen
   und das im Abschlussbericht (Schritt 8) vermerken, statt hart abzubrechen — die
   Kernübersetzung (Schritte 1-5) ist unabhängig von der Foundation-Phase lauffähig.
3. Sonst weiter mit Schritt 1.

## Schritt 1 — Trigger

Erfolgt automatisch durch die Routine (siehe `automation/trigger-prompt.md`), Cadence
laut `config/automation.config.json` → `cadence` (Default: täglich).

## Schritt 2 — Sheet lesen & neue Ad-Links finden

Datenquelle ist **kein** freies Ad-Library-Suchergebnis, sondern das bestehende
`config/automation.config.json` → `sheet.id` ("Funnel Sheet").

1. Für jeden Tab in `sheet.tabs` (`FI`, `FRCA`):
   a. `Google_Drive.read_file_content` mit `includeComments: true` auf `sheet.id`
      aufrufen (bzw. den entsprechenden Tab, falls das Tool Tab-Auswahl unterstützt).
   b. Zeilen ab `tabs.<TAB>.start_row` bis zur letzten befüllten Zeile durchgehen.
   c. Pro Zeile: existiert an der Zelle in Spalte `sheet.columns.ad_library_links_comment_column`
      (M) ein Kommentar-Thread? Falls ja: **Head-Post-Inhalt UND alle Replies** als
      Ad-Library-Permalinks sammeln (mehrere Team-Mitglieder posten oft in derselben
      Zelle nacheinander — nichts davon verwerfen).
2. Gegen `<Projektordner>/<market_code>/State/processed_comments.json` in Drive
   abgleichen: pro Zeile einen Hash/Fingerprint des kompletten Kommentar-Threads
   (Head-Post + alle Reply-Inhalte) speichern. Nur Zeilen mit einem **neuen oder
   geänderten** Fingerprint gegenüber dem letzten Lauf weiterverarbeiten. Ist nichts neu:
   Lauf beenden, keine weiteren Schritte, keine Chat-Nachricht nötig (kein Spam).
3. Pro zu verarbeitender Zeile zusätzlich lesen:
   - Spalte `sheet.columns.competitor_url` (D) — Competitor-Funnel-/Artikel-Link.
   - Spalte `sheet.columns.product_name` (G) — unser Produktname ("new PR NAME"),
     **exakt wie im Sheet geschrieben** (inkl. ®/™).

## Schritt 3 — Produktbild besorgen (Competitor-Funnel-Screenshot)

Für jede zu verarbeitende Zeile:

1. `python3 scripts/screenshot_page.py --url "<Competitor-URL aus Spalte D>" --out
   <tmp>/<row>-product.png` ausführen — screenshottet die Funnel-/Artikelseite des
   Competitors. Enthält die Seite mehrere Bilder, das Hero-/Produktbild bevorzugen
   (größtes Bild oberhalb des Falzes).
2. Dieses Bild ist die Referenz für den Produktbild-Swap in Schritt 5 — visuell bleibt
   es wie beim Competitor, nur der Produktname wird auf `product_name` (Spalte G)
   geändert (siehe `docs/skills/image-ad-prompt-generator.md`).

## Schritt 4 — Ad-Links öffnen, herunterladen/screenshotten

Für jeden in Schritt 2 gesammelten Ad-Library-Permalink:

1. `python3 scripts/fetch_ad_permalink.py --url "<permalink>" --out <tmp>/<ad_id>`
   ausführen. Das Skript öffnet die Ad-Detailseite (Playwright), versucht die
   Bild-/Video-URL direkt zu extrahieren und herunterzuladen; gelingt das nicht
   (abgelaufene signierte URL, Video-Player ohne direkten Src, etc.), macht es
   stattdessen einen Screenshot der Anzeige.
2. Ergebnis: pro Ad ein lokales Bild (Download oder Screenshot) plus, falls auf der
   Detailseite sichtbar, Headline/Primary Text der Anzeige.

## Schritt 5 — Übersetzung/Lokalisierung (Translation Mode)

Regeln: `docs/skills/image-ad-prompt-generator.md`. Zielsprache ergibt sich aus dem Tab:
`FI` → Finnisch, `FRCA` → Quebec-Französisch (siehe `sheet.tabs.*.language`).

1. Batch-Prompt pro Zeile/Produkt aus der Vorlage befüllen: Quell-Ad-Referenzen aus
   Schritt 4, Produktbild-Referenz aus Schritt 3, exakter Produktname aus Spalte G,
   Zielsprache aus dem Tab.
2. Gemeinsame übersetzte Headline + Primary Text für diese Zeile ableiten (idiomatisch,
   nicht wörtlich; Basis: die On-Image-Texte der gesammelten Ads).
3. Output als Markdown nach
   `<Projektordner>/<market_code>/translated-ads/<product_name>/<Lauf-Datum>.md`
   schreiben (`Google_Drive.create_file`, `contentMimeType: text/markdown`), inkl.
   Liste der verarbeiteten Ad-Permalinks.

## Schritt 6 — Foundation-Phase (optional, aktuell inaktiv)

Nur wenn `foundation_phase.mode` ungleich `translation_only`. Regeln:
`docs/skills/foundation-to-higgsfield.md`. Aktuell nicht konfiguriert (keine
Foundation-Dokumente hinterlegt) — Schritt wird übersprungen.

## Schritt 7 — Rendering

1. Prüfen, ob ein `Higgsfield`-MCP-Tool in der Session verfügbar ist (`ToolSearch`).
2. Falls ja: für jeden Batch-Prompt aus Schritt 5 `Higgsfield.generate_image` aufrufen
   (Referenzbilder vorher per `Higgsfield.media_upload`/`media_import_url` aus den in
   Schritt 3/4 erzeugten lokalen Dateien hochladen). Ergebnisse inline zeigen und in
   `<Projektordner>/<market_code>/renders/<product_name>/` als Referenz-Link
   dokumentieren.
3. Falls kein Higgsfield-MCP verfügbar: nur die Prompt-Texte ausgeben, Rendering
   überspringen.

## Schritt 8 — Ablage & Abschluss

1. Alle Text-/Bild-Outputs liegen bereits in Drive (Schritte 5/7).
2. `<Projektordner>/<market_code>/State/processed_comments.json` mit den neuen
   Fingerprints aus Schritt 2 aktualisieren.
3. Kurze Zusammenfassung an den Nutzer: welche Zeilen/Produkte verarbeitet wurden, wie
   viele Ads pro Zeile, Drive-Links zu den neuen Dateien, ob gerendert wurde oder nur
   Prompt-Texte erzeugt wurden. Bei "nichts Neues" keine Nachricht (siehe Schritt 2.2).
