# Image Automation — Competitor Ad Localization Pipeline

Wiederkehrende Automatisierung: liest kuratierte Meta-Ad-Library-Links aus dem
bestehenden **"Funnel Sheet"** (Google Sheets), holt die referenzierten
Konkurrenz-Anzeigen, lokalisiert sie und erzeugt daraus fertige **Higgsfield (Nano
Banana)** Prompts für die Bildgenerierung.

Läuft als wiederkehrende Routine (Trigger), nicht als einmaliger Task. Siehe
`automation/trigger-prompt.md` für den Prompt, der bei jedem Lauf ausgeführt wird, und
`docs/workflow.md` für die vollständige Schritt-für-Schritt-Logik.

## Wie die Daten fließen (Kurzfassung)

Quelle ist **nicht** eine freie Ad-Library-Suche, sondern das bestehende Sheet
[`Funnel Sheet`](https://docs.google.com/spreadsheets/d/1SkD7jrC-othtbwTYyz1VCK1HPIkEKHxc_hSAvRp2iL8/edit),
Tabs `FI` (ab Zeile 52) und `FRCA` (ab Zeile 33):

- **Spalte D** (`Competitor URL / Content`) — Link zum Competitor-Funnel/-Artikel.
- **Spalte G** (`new PR NAME`) — unser eigener Produktname, exakt inkl. ®/™.
- **Spalte M** (`Competitor Ad Link/Drive Link`) — die eigentlichen Meta-Ad-Library-Links
  stehen hier **als Zell-Kommentar** (Kopf-Kommentar + alle Replies verschiedener
  Teammitglieder), nicht als Zellwert.

Pro Zeile mit einem neuen/unverarbeiteten Kommentar-Thread:

1. Alle Ad-Library-Permalinks aus dem Kommentar-Thread öffnen, Anzeige herunterladen
   oder screenshotten (`scripts/fetch_ad_permalink.py`).
2. Die Competitor-Funnel-Seite aus Spalte D screenshotten, um das Produktbild als
   Referenz zu bekommen (`scripts/screenshot_page.py`) — das Foto bleibt visuell wie
   beim Competitor, nur der Produktname wird auf Spalte G geändert.
3. Nach Translation-Mode-Regeln (`docs/skills/image-ad-prompt-generator.md`)
   lokalisieren: Layout/Szene/Gesichter beibehalten, Overlay-Text idiomatisch in die
   Zielsprache des Tabs übersetzen (`FI` → Finnisch, `FRCA` → Quebec-Französisch),
   Produktname/-bild tauschen.
4. Output (Batch-Prompt + Headline/Primary Text, ggf. Renders) in den Drive-Projektordner
   ablegen.

Details und Randfälle: `docs/workflow.md`.

## Offene Annahme

Die Spaltenbelegung (D/G/M) wurde am `FRCA`-Tab verifiziert (inkl. Kommentar-Anker
`FRCA!M33` etc.). Der `FI`-Tab wird als strukturell identisch angenommen (laut Sheet
selbst per Kommentar aus einer "FRCA Template" hervorgegangen) — bitte kurz
gegenchecken und melden, falls die Spalten dort abweichen.

## Status: Trigger noch NICHT angelegt

Die Config (`config/automation.config.json`) ist vollständig ausgefüllt (Sheet-ID,
Spalten, Start-Zeilen, Zielsprachen, Cadence = täglich). Was noch fehlt: der eigentliche
wiederkehrende Trigger wurde noch nicht erstellt. In einer interaktiven Session einfach
sagen "lege die image-automation Routine an" — dann wird `create_trigger` mit dem Prompt
aus `automation/trigger-prompt.md` und dem Cron-Ausdruck aus der Config aufgerufen.

Die Foundation-Phase (`docs/skills/foundation-to-higgsfield.md`, wöchentliche
48+12-Konzept-Produktion) ist bewusst noch nicht aktiv (`foundation_phase.mode:
"translation_only"`) — dafür fehlen noch die Foundation-Dokumente pro Produkt. Kann
später ergänzt werden, ohne die Kernübersetzung anzufassen.

## Ordnerstruktur

```
config/automation.config.json      Sheet-ID, Spalten, Tabs/Start-Zeilen, Cadence, Foundation-Modus
docs/skills/image-ad-prompt-generator.md   Regeln für Translation Mode (1:1 übernommen)
docs/skills/foundation-to-higgsfield.md    Regeln für Foundation-Dokumente + wöchentliche Higgsfield-Produktion
docs/workflow.md                   Master-Playbook: die 8 Schritte im Detail, inkl. Tool-Zuordnung
automation/trigger-prompt.md       Der Prompt-Text, den die Routine bei jedem Lauf bekommt
scripts/fetch_ad_permalink.py      Öffnet einen bekannten Ad-Library-Permalink, lädt Creative herunter oder screenshottet
scripts/screenshot_page.py         Screenshottet eine beliebige URL (Competitor-Funnel) + versucht das Hero-/Produktbild zu isolieren
scripts/scrape_ad_library.py       Optional: freie Ad-Library-Suche nach Suchbegriff (nicht Teil des Kern-Workflows, nützlich für manuelle Recherche)
```

## Google Drive — Ablage

Basis-Ordner (vom Nutzer vorgegeben):
`https://drive.google.com/drive/folders/1RH4nagTulPEPXPp5fSwTeccvL-GlMI5-`

**Wichtiger Hinweis:** Dieser Ordner wird bereits von einer anderen, unabhängigen
Automatisierung genutzt ("Claude Cowork Automation" — FI & FRCA Funnel/Ads Monitor,
Winning Products Ads Monitor, Daily SLA Check). Diese Pipeline legt eigene
Unterordner an und rührt `State/`, `Funnel-PDFs/`, `QA-Reports/` nicht an:

```
<market_code>/                     FI oder FRCA
  State/processed_comments.json    Fingerprints bereits verarbeiteter Kommentar-Threads
  translated-ads/<product_name>/   Batch-Prompt + Headline/Primary Text, pro Lauf-Datum
  renders/<product_name>/          Generierte Bilder, falls Higgsfield-MCP verfügbar
  higgsfield-json/                 (nur wenn foundation_phase.mode aktiviert ist)
```

## Meta Ad Library — Zugriff auf bekannte Permalinks

Kein Login nötig, aber die Seite ist eine JS-SPA — ein einfacher HTTP-Fetch liefert keine
Ad-Daten. `scripts/fetch_ad_permalink.py` nutzt das im Environment vorinstallierte
Playwright/Chromium, öffnet den konkreten, aus dem Sheet-Kommentar bekannten Permalink
und lädt die Anzeige herunter oder screenshottet sie als Fallback.

**Caveat:** Die CSS-Selektoren (`div[role='article']` etc.) basieren auf dem aktuell
öffentlich sichtbaren Markup der Ad Library und können nach einem Meta-Redesign brechen
— das Skript screenshottet in diesem Fall die ganze Seite als Fallback, damit der Lauf
trotzdem etwas Verwertbares liefert, statt still zu scheitern.

## Higgsfield

Falls der Higgsfield-MCP-Server in der ausführenden Session verfügbar ist, rendert die
Routine die erzeugten Prompts direkt (`generate_image`, Model z.B. `nano_banana_pro`,
Referenzbilder über `media_upload`/`media_import_url`). Ist kein Higgsfield-MCP
verfügbar, werden nur die Prompt-Texte erzeugt und in Drive abgelegt.

## Setup-Schritte für den Nutzer

1. Kurz gegenchecken, ob der `FI`-Tab im Funnel Sheet dieselbe Spaltenbelegung hat wie
   `FRCA` (siehe "Offene Annahme" oben).
2. In einer interaktiven Session sagen "lege die image-automation Routine an" —
   dann wird `create_trigger` mit dem Prompt aus `automation/trigger-prompt.md` und dem
   Cron-Ausdruck aus der Config aufgerufen (der Trigger existiert vorher nicht).
3. Ersten Lauf beobachten (Drive-Projektordner + Chat-Nachricht prüfen).
