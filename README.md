# Image Automation — Competitor Ad Localization Pipeline

Wiederkehrende Automatisierung: holt Konkurrenz-Anzeigen aus der **Meta Ad Library**,
lokalisiert sie anhand hinterlegter Produktinfos aus **Google Drive** und erzeugt daraus
fertige **Higgsfield (Nano Banana)** Prompts/JSON-Configs für die Bildgenerierung.

Läuft als wiederkehrende Routine (Trigger), nicht als einmaliger Task. Siehe
`automation/trigger-prompt.md` für den Prompt, der bei jedem Lauf ausgeführt wird, und
`docs/workflow.md` für die vollständige Schritt-für-Schritt-Logik.

## Status: Setup unvollständig

Diese Automatisierung wurde ohne Live-Rückfrage angelegt (nicht-interaktive Session).
Der wiederkehrende Trigger ist bereits erstellt, aber **deaktiviert**, bis die
Pflichtfelder in `config/automation.config.json` ausgefüllt sind:

- `advertiser.search_term` — welcher Advertiser/welche Marke in der Meta Ad Library beobachtet wird
- `target_markets` — Zielmarkt/-sprache(n) für die Lokalisierung
- `foundation_phase.mode` — ob/wie die foundation-to-higgsfield-Wochenproduktion mitläuft

Solange diese Felder `"TODO"` enthalten, bricht der Lauf sofort mit einer Erinnerung ab,
anstatt mit Platzhalterdaten zu arbeiten. Sobald die Config ausgefüllt ist, den Trigger
mit `update_trigger(enabled: true)` aktivieren (oder den Nutzer bitten, das zu tun).

## Ordnerstruktur

```
config/automation.config.json   Alle veränderlichen Parameter (Advertiser, Märkte, Cadence, Foundation-Modus, Drive-Ordner-ID)
docs/skills/image-ad-prompt-generator.md   Regeln für Translation Mode (1:1 übernommen)
docs/skills/foundation-to-higgsfield.md    Regeln für Foundation-Dokumente + wöchentliche Higgsfield-Produktion
docs/workflow.md                 Master-Playbook: die 8 Schritte im Detail, inkl. Tool-Zuordnung
automation/trigger-prompt.md     Der Prompt-Text, den die Routine bei jedem Lauf bekommt
scripts/scrape_ad_library.py     Playwright-Scraper für die öffentliche Meta Ad Library
```

## Google Drive

Basis-Ordner (vom Nutzer vorgegeben):
`https://drive.google.com/drive/folders/1RH4nagTulPEPXPp5fSwTeccvL-GlMI5-`

**Wichtiger Hinweis:** Dieser Ordner wird bereits von einer anderen, unabhängigen
Automatisierung genutzt ("Claude Cowork Automation" — FI & FRCA Funnel/Ads Monitor,
Winning Products Ads Monitor, Daily SLA Check; siehe die "Notes — How This Automation
Works" Docs darin). Diese Pipeline legt **einen zusätzlichen Projekt-Unterordner** pro
Produkt an (Namensschema: `<Produktname>/`) und rührt die bestehenden Unterordner
(`State/`, `Funnel-PDFs/`, `QA-Reports/`) nicht an. Innerhalb des neuen Projektordners
werden angelegt:

```
<Produktname>/
  foundation/          Kopien/Links der Foundation-Dokumente (falls vorhanden)
  translated-ads/      Batch-Prompt + Headline/Primary Text pro Zielmarkt, pro Lauf-Datum
  higgsfield-json/      (nur wenn foundation_phase.mode aktiviert ist) wöchentliche 48+12 Konzepte
  renders/             Generierte Bilder, falls Higgsfield-MCP verfügbar
```

## Meta Ad Library

Kein Login nötig, aber die Seite ist eine JS-SPA — ein einfacher HTTP-Fetch liefert keine
Ad-Daten. `scripts/scrape_ad_library.py` nutzt das im Environment vorinstallierte
Playwright/Chromium, öffnet die öffentliche Such-URL für `advertiser.search_term` (+
optional `advertiser.page_id`) und extrahiert je Anzeige: Bild-/Video-URL, Headline,
Primary Text, Anzeigen-Permalink. Ergebnis wird als JSON ausgegeben und von der Routine
weiterverarbeitet.

Bitte moderate Cadence/Ad-Limits einhalten (siehe Config) — es handelt sich um
öffentliche, aber automatisiert abgerufene Daten von einer Meta-Property.

**Caveat:** Die CSS-Selektoren im Scraper (`div[role='article']` etc.) basieren auf dem
aktuell öffentlich sichtbaren Markup der Ad Library und können nach einem Meta-Redesign
brechen. Der Trigger-Lauf sollte einen leeren/fehlerhaften Scraper-Output erkennen und
den Nutzer statt stiller Fehlschläge informieren.

## Higgsfield

Falls der Higgsfield-MCP-Server in der ausführenden Session verfügbar ist, rendert die
Routine die erzeugten Prompts direkt (`generate_image`, Model z.B. `nano_banana_pro`,
Referenzbilder über `media_import_url`/`media_upload`). Ist kein Higgsfield-MCP
verfügbar, werden nur die Prompt-Texte erzeugt und in Drive abgelegt.

## Setup-Schritte für den Nutzer

1. `config/automation.config.json` ausfüllen (Advertiser, Zielmärkte, Cadence, Foundation-Modus).
2. Google-Drive-Connector in dieser Cowork-Umgebung autorisiert lassen (bereits der Fall,
   da der Basis-Ordner oben lesbar war).
3. Trigger aktivieren: den Nutzer bitten "aktiviere die image-automation Routine" —
   dann wird `update_trigger(trigger_id, enabled: true)` aufgerufen.
4. Ersten Lauf beobachten (Drive-Projektordner + ggf. Chat-Nachricht prüfen).
