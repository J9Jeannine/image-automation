# Image Automation — Competitor Ad Localization Pipeline

Wiederkehrende Automatisierung: liest kuratierte Meta-Ad-Library-Links aus dem
bestehenden **"Funnel Sheet"** (Google Sheets), holt die referenzierten
Konkurrenz-Anzeigen, lokalisiert sie und erzeugt daraus fertige **Higgsfield (Nano
Banana)** Bilder in der passenden Zielsprache.

Läuft als wiederkehrende Routine (Trigger), nicht als einmaliger Task. Siehe
`automation/trigger-prompt.md` für den Prompt, der bei jedem Lauf ausgeführt wird, und
`docs/workflow.md` für die vollständige Schritt-für-Schritt-Logik.

## Wie die Daten fließen (Kurzfassung)

Quelle ist **nicht** eine freie Ad-Library-Suche, sondern das bestehende Sheet
[`Funnel Sheet`](https://docs.google.com/spreadsheets/d/1SkD7jrC-othtbwTYyz1VCK1HPIkEKHxc_hSAvRp2iL8/edit),
Tabs `FI` (ab Zeile 52) und `FRCA` (ab Zeile 33) — Spaltenbelegung an **beiden** Tabs
verifiziert:

- **Spalte D** (`Competitor URL / Content`) — Link zum Competitor-Funnel/-Artikel.
- **Spalte G** (`new PR NAME`) — unser eigener Produktname, exakt inkl. ®/™.
- **Spalte J** (`Bundle/deal offer`) — Preisstufen in Marktwährung (EUR für FI, CAD für FRCA).
- **Spalte M** (`Competitor Ad Link/Drive Link`) — die eigentlichen Meta-Ad-Library-Links
  stehen hier **als Zell-Kommentar** (Kopf-Kommentar + alle Replies verschiedener
  Teammitglieder), nicht als Zellwert.

Pro Zeile mit einem neuen/unverarbeiteten Kommentar-Thread:

1. **Einmal pro Zeile** (nicht pro Ad!): Produktfoto von der Competitor-Funnel-Seite
   (Spalte D) laden, per Higgsfield den Produktnamen darauf auf Spalte G ändern. Dieses
   eine Bild wird für alle Ads dieser Zeile wiederverwendet.
2. Für jede Ad aus dem M-Kommentar-Thread: über den echten, im Account aktivierten Skill
   **`image-ad-prompt-generator`** (per `Skill`-Tool, nicht die lokale Doku-Kopie in
   `docs/skills/`) lokalisieren — Layout/Szene/Gesichter beibehalten, Text idiomatisch in
   die Zielsprache des Tabs übersetzen (`FI` → Finnisch, `FRCA` → Quebec-Französisch),
   korrekten Preis aus Spalte J verwenden, das eine Produktbild aus Schritt 1 **nur**
   einsetzen, wenn die Quell-Ad tatsächlich ein Produkt zeigt, sonst Ad visuell
   unverändert lassen. Output exakt im Seitenverhältnis der Quell-Anzeige. Dieser Skill
   ist ausschließlich für Übersetzungen da, nie für Varianten/Iterationen/New Concepts.
3. Ergebnis (Bilder + übersetzte Headline/Primary Text) in den Drive-Projektordner
   ablegen.

Details und Randfälle: `docs/workflow.md`.

## Bekannte Einschränkung: Ad-Library-Permalink nicht direkt auflösbar

In der Sandbox, in der diese Automatisierung läuft, ist `facebook.com` (die
Permalink-**Seite** `facebook.com/ads/library/?id=...`) durch die Netzwerk-Policy
blockiert (403 direkt vom Proxy — bestätigt, kein Retry-Fall). Das dahinterliegende
Bild-/Video-CDN **`scontent.*.fbcdn.net` ist dagegen normal per `curl` erreichbar**
(bestätigt: 600×600-JPEG erfolgreich geladen). Fehlt ist also nur die Auflösung
Permalink → fbcdn.net-URL, nicht der Download selbst. Zusätzlich funktioniert
Playwright/Chromium in dieser Sandbox unabhängig davon bei **jeder** HTTPS-Seite nicht
(Connection Reset über den Proxy) — deshalb holt die Pipeline Bilder ausschließlich per
`curl`, nie per Screenshot.

**Praktische Konsequenz — und Standardweg:** Der Nutzer kann direkt im
Sheet-Kommentar-Thread (Spalte M) mit der fbcdn.net-Bild-/Video-URL antworten (Browser:
Rechtsklick auf die Anzeige → "Bildadresse kopieren") — das wird beim normalen
Comment-Read ohnehin mitgelesen (Replies gehören zum Thread). Steht noch keine
fbcdn.net-URL im Thread und der Permalink lässt sich nicht auflösen: aktiv danach fragen,
nicht stumm überspringen oder wiederholt versuchen. Details:
`config/automation.config.json` → `network_access`.

**Bild-Upload nach Drive (gelöst — verbindliche Methode):** Der Drive-MCP-`create_file`
schleust Base64 durch den Modell-Kontext und schneidet lange Werte ab (~15 000 Zeichen ≈
11 KB) → für echte Bilder unbrauchbar. Der Service-Account hat kein Storage-Quota, kann
also keine Inhalts-Dateien **anlegen** (`403 storageQuotaExceeded`). Lösung (kanonisch,
kein Markdown-Links-Workaround mehr): **(1)** die Zieldatei als winzigen Platzhalter über
die Drive-Verbindung anlegen (User-owned), **(2)** der Service-Account
(`GOOGLE_SERVICE_ACCOUNT_JSON`) überschreibt sie mit den vollen Bytes von der Disk via
`files.update` (`PATCH …/upload/drive/v3/files/{id}?uploadType=media`). Da der Speicher dem
**Owner** (User) berechnet wird, funktioniert das in voller Qualität — Ergebnis:
`owner=User`, `lastModifyingUser=Service-Account`. Vollständige Schritte + Begründung:
`config/automation.config.json` → `upload_method` und `docs/workflow.md` Schritt 7. Echte
Bilddateien landen als `<N>_<product>_<market>.jpg` (Zahl zuerst, z. B. `1_Pawox_FI.jpg`)
im Tages-/Produkt-Ordner
`Translated-Ads/<market>/<YYYY-MM-DD> - <product>/`.

**Beobachtete Instabilität bei automatischen (Trigger-)Läufen:** Im zweiten,
Trigger-ausgelösten Lauf (2026-07-10) sind MCP-Tool-Verbindungen wiederholt
disconnected/reconnected, und Google-Drive-**Schreib**-Aufrufe (`create_file`) sind
mehrfach mit "Tool permission request failed" fehlgeschlagen, obwohl Lesezugriffe
(`read_file_content`, `download_file_content`) und Higgsfield-Aufrufe im selben Lauf
funktionierten. Ergebnis: die Higgsfield-Bilder wurden erzeugt, konnten aber in diesem
Lauf nicht in Drive abgelegt werden — sie wurden stattdessen direkt an den Nutzer
geschickt (`SendUserFile`) und die CDN-Links im Chat mitgeteilt. `State/processed_comments.json`
wurde aus demselben Grund noch nicht angelegt. Nächster Schritt: Drive-Ablage erneut
versuchen, sobald die Verbindung stabil ist (z. B. im nächsten Lauf oder interaktiv).

## Status: Trigger ist aktiv, erster End-to-End-Testlauf erfolgreich abgeschlossen

Trigger `trig_013rHHhQkPL2Zfrne2M3xkaY` ("image-automation: Competitor Ad Localization
(Funnel Sheet)") läuft **täglich um 6:00 Uhr Lisbon-Zeit** (Cron `0 5 * * *` UTC —
Annahme: Sommerzeit/DST, im Winterhalbjahr ggf. auf `0 6 * * *` per `update_trigger`
nachjustieren) und feuert in diese Chat-Session zurück
(`persistent_session_id: session_01F8Bw6DQR4mk9S5WZHAcPZH`).

**Test durchgeführt mit dem letzten FI-Produkt (Zeile 52: Competitor "variclex" →
unser Produkt "vanix"), alle 3 Ads aus dem M-Kommentar abgeschlossen:**
- Produktbild von `sunuris.com` (Spalte D) per curl geladen (1080×1080 PNG,
  "VariClex™ Solo Product Image"), per Higgsfield einmalig auf "vanix" umbenannt
  (2 Credits) — wird für alle Ads dieser Zeile wiederverwendet (aber in diesem Test
  nicht gebraucht, da keine der 3 Ads ein Produktfoto zeigte).
- Ad 1 (`?id=1692362565352629`) und Ad 2 (`?id=1045373708000500`) sind bildidentisch
  (gleicher MD5-Hash) — nur einmal generiert, Dedup-Check funktioniert.
- Ad 1/2 (Beinfoto, Krampfadern) und Ad 3 (3-Panel-Infografik) erfolgreich ins
  Finnische übersetzt: Layout/Farben/Icons beibehalten, Text idiomatisch übersetzt,
  Markenname "VariClex™" → "vanix" wo vorhanden.
- Ergebnis-Dokument in Drive: `Translated-Ads/FI/vanix/2026-07-09-vanix-fi` (Google Doc
  mit CDN-Links + Ad-Copy, siehe Ordnerstruktur unten).

Die Foundation-Phase (`docs/skills/foundation-to-higgsfield.md`, wöchentliche
48+12-Konzept-Produktion) ist bewusst noch nicht aktiv (`foundation_phase.mode:
"translation_only"`).

## Ordnerstruktur

```
config/automation.config.json      Sheet-ID, Spalten, Tabs/Start-Zeilen, Cadence, network_access, Foundation-Modus
docs/skills/image-ad-prompt-generator.md   Referenz-Zusammenfassung (Fallback) für den echten Account-Skill
docs/skills/foundation-to-higgsfield.md    Regeln für Foundation-Dokumente + wöchentliche Higgsfield-Produktion
docs/workflow.md                   Master-Playbook: die 8 Schritte im Detail, inkl. Tool-Zuordnung
automation/trigger-prompt.md       Der Prompt-Text, den die Routine bei jedem Lauf bekommt
scripts/fetch_ad_permalink.py      Öffnet einen bekannten Ad-Library-Permalink (funktioniert aktuell NICHT in dieser Sandbox, siehe oben)
scripts/screenshot_page.py         Playwright-Screenshot einer beliebigen URL (funktioniert aktuell NICHT in dieser Sandbox, siehe oben)
scripts/scrape_ad_library.py       Optional: freie Ad-Library-Suche nach Suchbegriff (nicht Teil des Kern-Workflows)
```

## Google Drive — Ablage

Basis-Ordner (vom Nutzer vorgegeben):
`https://drive.google.com/drive/folders/1RH4nagTulPEPXPp5fSwTeccvL-GlMI5-`

**Wichtiger Hinweis:** Dieser Ordner wird bereits von einer anderen, unabhängigen
Automatisierung genutzt ("Claude Cowork Automation" — FI & FRCA Funnel/Ads Monitor,
Winning Products Ads Monitor, Daily SLA Check). Diese Pipeline legt einen eigenen
Unterordner an und rührt `State/`, `Funnel-PDFs/`, `QA-Reports/` nicht an. Tatsächlich
angelegte Struktur (Stand jetzt):

```
Translated-Ads/                    (id: 1JWHztpl2Z6mE9WtcRTObRgwBRp1OsHCb)
  FI/                               (id: 1Ey4aVRrpzrzolETnzKVxVCZQGZjm0P5K)
    2026-09-03 - Cervi/             echte Bilddateien: 1_Cervi_FI.jpg .. 8_Cervi_FI.jpg, Cervi_FI_produktbild.jpg, Cervi_FI_ad_copy.md
    2026-07-25 - itzora/            aelterer Lauf, noch im alten Namensschema (itzora_FI_ad1..8.jpg)
    vanix/                          (id: 1TwCfnOts6cXmiLJFCLbsPNW4HkTlQKaJ)
      2026-07-09-vanix-fi           Google Doc: CDN-Links + übersetzte Ad-Copy (alter Lauf, vor Upload-Fix)
  FRCA/                             (id: 1ZeW7nKHrCMNOBH6jIKZrzNYjJWXPvQDW)
```

Ordner-Namensschema pro Lauf: `<YYYY-MM-DD> - <product_name>` (Produktname MUSS im
Ordnernamen stehen, nicht nur das Datum). Darin liegen die **echten** JPG-Dateien (per
`upload_method`, siehe oben), nicht nur CDN-Links. `State/processed_comments.json` je Markt
für Kommentar-Fingerprints.

## Higgsfield

Verbindung bestätigt und funktionsfähig (Account-Guthaben abgefragt: 260 Credits,
Starter-Plan, Testbild kostete 2 Credits). `generate_image` mit Model `nano_banana_pro`
für Produktbild-Rename und Ad-Übersetzung, Referenzbilder über `media_upload`.

## Verbleibende Punkte für den Nutzer

1. FI-Zeile-52-Testlauf ist komplett (alle 3 Ads verarbeitet). Für zukünftige Zeilen:
   fbcdn.net-Links wie gehabt direkt als Reply auf den M-Kommentar posten.
2. Bei Bedarf Cadence prüfen/anpassen (aktuell angenommen: Lisbon-Zeit, Sommerzeit).
3. Ersten automatischen Lauf (morgen 05:00 UTC) beobachten.
4. Bild-Upload nach Drive ist gelöst: echte JPG-Dateien werden über `upload_method`
   (Platzhalter via Drive-Verbindung + Service-Account `files.update`) in voller Qualität
   abgelegt — kein Markdown-Links-Workaround mehr. Details: `config/automation.config.json`
   → `upload_method`, `docs/workflow.md` Schritt 7.
