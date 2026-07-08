# Master-Workflow

Wird bei jedem Trigger-Lauf ausgeführt. Tool-Namen beziehen sich auf die in der
Cowork-Session verfügbaren MCP-Server (`Google_Drive`, `Higgsfield`) sowie Bash für den
Playwright-Scraper.

## Schritt 0 — Config-Guard

1. `config/automation.config.json` aus diesem Repo lesen.
2. Enthält eines der Pflichtfelder (`advertiser.search_term`, `advertiser.country`,
   `target_markets[].market_code`/`language`, `product.exact_name`,
   `product.product_image_drive_file_id`, `drive.project_folder_name`) noch `"TODO"` (als
   String oder Teilstring) → **Lauf sofort abbrechen**, keine weiteren Schritte
   ausführen, stattdessen kurze Erinnerung ausgeben ("Setup unvollständig, bitte
   config/automation.config.json ausfüllen") und den Lauf beenden. Kein Drive-Zugriff,
   kein Scraping, kein Higgsfield-Aufruf in diesem Fall.
3. Sonst weiter mit Schritt 1.

## Schritt 1 — Trigger

Erfolgt automatisch durch die Routine (siehe `automation/trigger-prompt.md`). Keine
manuelle Aktion nötig.

## Schritt 2 — Ad-Links holen (Meta Ad Library)

1. `python3 scripts/scrape_ad_library.py --search-term "<advertiser.search_term>" --country
   "<advertiser.country>" [--page-id <advertiser.page_id>] --max-ads
   <advertiser.max_ads_per_run>` ausführen (Bash).
2. Ergebnis ist eine JSON-Liste: `[{ "ad_id", "permalink", "media_type", "media_url",
   "headline", "primary_text" }, ...]`.
3. Gegen `<Projektordner>/State/seen_ads.json` (in Drive, falls vorhanden) abgleichen —
   nur wirklich neue `ad_id`s weiterverarbeiten, wenn `cadence.mode == "on_new_ads"`. Bei
   `"weekly"`/`"daily"` werden alle im Fenster gefundenen Ads verarbeitet.

## Schritt 3 — Produktinfos laden (Google Drive)

1. `Google_Drive.search_files` mit `parentId = '<drive.base_folder_id>'`, um zu prüfen,
   ob bereits ein Projektordner `<drive.project_folder_name>` existiert.
2. Produktname, Zielmarkt/-sprache, Winning-Ad-Copy kommen primär aus
   `config/automation.config.json` (`product.*`, `target_markets`). Falls ein
   Foundation-Set existiert (`foundation_documents.*`), zusätzlich mit
   `Google_Drive.read_file_content` laden und als Kontext für Schritt 5/6 verwenden.

## Schritt 4 — Projektordner anlegen

1. Existiert der Ordner aus Schritt 3.1 nicht: `Google_Drive.create_file` mit
   `mimeType: application/vnd.google-apps.folder`, `parentId:
   <drive.base_folder_id>`, `title: <drive.project_folder_name>`.
2. Unterordner `foundation/`, `translated-ads/`, `renders/` anlegen (und
   `higgsfield-json/`, falls `foundation_phase.mode != "translation_only"`).
3. Bestehende Ordner `State/`, `Funnel-PDFs/`, `QA-Reports/` im Basisordner **nicht**
   anfassen — die gehören zu einer anderen Automatisierung.

## Schritt 5 — Übersetzung/Lokalisierung (Translation Mode)

Regeln: `docs/skills/image-ad-prompt-generator.md`.

Für jeden Zielmarkt in `target_markets`:

1. Batch-Prompt aus der Vorlage befüllen (Quell-Ad-Referenzen aus Schritt 2, Produktbild
   aus `product.product_image_drive_file_id`, exakter Produktname, Zielsprache).
2. Gemeinsame übersetzte Headline + Primary Text aus `product.winning_ad_copy` ableiten
   (idiomatisch, nicht wörtlich).
3. Output als Markdown nach
   `<Projektordner>/translated-ads/<market_code>/<Lauf-Datum>.md` schreiben
   (`Google_Drive.create_file`, `contentMimeType: text/markdown`).

## Schritt 6 — Foundation-Phase (optional)

Nur wenn `foundation_phase.mode` `combined` oder `foundation_once_then_weekly_json` ist.
Regeln: `docs/skills/foundation-to-higgsfield.md`. Output nach
`<Projektordner>/higgsfield-json/<Lauf-Datum>.json`.

## Schritt 7 — Rendering

1. Prüfen, ob ein `Higgsfield`-MCP-Tool in der Session verfügbar ist (`ToolSearch`).
2. Falls ja: für jeden Batch-Prompt bzw. jedes Konzept aus Schritt 5/6
   `Higgsfield.generate_image` aufrufen (Referenzbilder vorher per
   `Higgsfield.media_import_url` aus den Drive-Bild-URLs importieren). Ergebnisse
   (Bild-URLs) inline zeigen und in `<Projektordner>/renders/` als Referenz-Link
   dokumentieren.
3. Falls kein Higgsfield-MCP verfügbar: nur die Prompt-Texte ausgeben, Rendering
   überspringen.

## Schritt 8 — Ablage & Abschluss

1. Alle Text-Outputs liegen bereits in Drive (Schritte 5/6).
2. `<Projektordner>/State/seen_ads.json` mit den in Schritt 2 verarbeiteten `ad_id`s
   aktualisieren (für `on_new_ads`-Modus).
3. Kurze Zusammenfassung an den Nutzer: Anzahl verarbeiteter Ads, Zielmärkte, Drive-Links
   zu den neuen Dateien, ggf. Render-Ergebnisse.
