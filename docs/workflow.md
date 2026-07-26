# Master-Workflow

Wird bei jedem Trigger-Lauf ausgeführt. Tool-Namen beziehen sich auf die in der
Cowork-Session verfügbaren MCP-Server (`Google_Drive`, `Higgsfield`) sowie Bash für die
Playwright-Skripte in `scripts/`.

## Schritt 0 — Config-Guard

0. **`STATUS.md` lesen, bevor irgendetwas anderes passiert.** Dort steht, wie Bilder in
   Drive und Links ins Sheet kommen (Service Account, `scripts/drive_upload.py`,
   `scripts/sheet_set_link.py`). Beides geht — aber nicht über den Drive-MCP-Connector
   allein. Wer nur auf die MCP-Toolliste schaut, kommt zum falschen Schluss "geht nicht".
   Niemals dem Nutzer sagen, etwas sei unmöglich, ohne vorher `STATUS.md` gelesen und
   `env | grep -i google` geprüft zu haben.
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
4. **Zeile ohne eigenen M-Kommentar, aber gleiches Produkt im anderen Tab?** FI und FRCA
   bespielen weitgehend dieselben Produkte — nur mit eigenem Preis (EUR vs. CAD) und
   eigener Zielsprache. Hat eine Zeile keinen eigenen Thread, aber der andere Tab hat
   eine Zeile mit **demselben Competitor** (Spalte C/D), dann die dort verlinkten
   Quell-Ads wiederverwenden und neu übersetzen, statt die Zeile zu überspringen.
   Wichtig dabei:
   - Immer von den **Original-Quell-Ads** übersetzen, nie vom bereits übersetzten
     Ergebnis des anderen Marktes (sonst summieren sich Übersetzungsfehler).
   - Produktname aus Spalte G **des eigenen Tabs** nehmen — Schreibweise kann abweichen
     (FI `itzora` vs. FRCA `Itzora`). Weicht sie ab, das Produktbild neu erzeugen.
   - Preis aus Spalte J des eigenen Tabs, in Marktkonvention (Quebec: `69,99 $`).
   - Im State-Eintrag `source_from_<tab>_row` + Quell-Fingerprint vermerken.
5. Pro zu verarbeitender Zeile zusätzlich lesen:
   - Spalte `sheet.columns.competitor_url` (D) — Competitor-Funnel-/Artikel-Link.
   - Spalte `sheet.columns.product_name` (G) — unser Produktname ("new PR NAME"),
     **exakt wie im Sheet geschrieben** (inkl. ®/™).
   - Spalte `sheet.columns.price_column` (J, "Bundle/deal offer") — die korrekte(n)
     Preisstufe(n) in der Marktwährung (EUR für FI, CAD für FRCA). Fließt in die
     übersetzte Ad-Copy ein, wo der Preis genannt wird.

## Schritt 3 — EIN Produktbild pro Zeile/Produkt erzeugen (nicht pro Ad!)

**Wichtig:** Dieser Schritt läuft genau **einmal pro Zeile/Produkt**, nicht einmal pro
Ad. Das Ergebnis (ein Bild) wird in Schritt 5 für alle Ads dieser Zeile wiederverwendet
— es wird nie neu generiert, nur referenziert.

1. Competitor-Funnel-Seite aus Spalte D per `curl` herunterladen (kein Playwright/Browser
   nötig — in dieser Sandbox funktioniert Chromium über den Proxy ohnehin nicht
   zuverlässig für HTTPS, siehe Caveat in der README) und das größte/Produkt-Bild aus dem
   HTML extrahieren (z. B. per Bildgrößen-Query-Parameter die volle Auflösung anfordern,
   nicht die Thumbnail-Variante).
2. Dieses Competitor-Produktfoto **einmalig** per `Higgsfield.generate_image` bearbeiten:
   Produktform/-design/Farben/Licht/Winkel exakt beibehalten, nur den sichtbaren
   Produktnamen durch `product_name` (Spalte G) ersetzen (inkl. ®/™-Handling).
3. Das Ergebnis ist DAS Produktbild-Asset für diese Zeile — merken (media_id/Job-ID) für
   Schritt 5. Bei mehreren Ads derselben Zeile wird dieses eine Bild wiederverwendet,
   nicht neu erzeugt.

## Schritt 4 — Ad-Links öffnen

Für jeden in Schritt 2 gesammelten Ad-Library-Permalink (Anzahl variiert pro Zeile — so
viele wie im Kommentar-Thread stehen, kein fester Wert):

1. **Zuerst prüfen, ob im M-Kommentar-Thread selbst schon eine direkte
   `fbcdn.net`-Bild-/Video-URL als Reply steht** (der Nutzer kann jederzeit auf den
   Kommentar mit dem direkten Link antworten — das ist der Standardweg, kein Sonderfall).
   Falls ja: direkt per curl herunterladen, fertig.
2. Steht nur der `facebook.com/ads/library/?id=...`-Permalink da (noch keine
   fbcdn.net-Reply): versuchen, ihn per curl zu öffnen.
3. **Bekannte Einschränkung:** `facebook.com` selbst ist in dieser Sandbox durch die
   Netzwerk-Policy blockiert (403 vom Proxy) — das betrifft nur die Permalink-**Seite**.
   Das dahinterliegende Bild-/Video-CDN (`scontent.*.fbcdn.net`) ist normal per curl
   erreichbar (bestätigt: mehrere echte Downloads erfolgreich). Der Permalink lässt sich
   in dieser Sandbox nur nicht zur fbcdn.net-URL auflösen, weil genau das ein Laden der
   blockierten Seite erfordern würde.
4. Schlägt Schritt 2 fehl: **den Nutzer aktiv fragen** (oder darauf hinweisen, dass er
   direkt im Sheet-Kommentar antworten kann), ob er die direkte fbcdn.net-Bild-/Video-URL
   zu diesem Permalink schicken kann (Browser: Rechtsklick auf die Anzeige →
   "Bildadresse kopieren"), statt den Lauf stumm abzubrechen oder es wiederholt zu
   versuchen.
5. **Dedup-Check:** Vor jeder Higgsfield-Generierung den MD5/Hash der heruntergeladenen
   Ad-Bilder innerhalb derselben Zeile vergleichen. Sind zwei Ad-Links bildidentisch
   (kommt vor — Meta zeigt dieselbe Creative unter mehreren Ad-IDs), nur einmal
   generieren und das Ergebnis für beide verwenden, nicht doppelt rendern.
4. Ergebnis: pro Ad ein lokales Bild (per curl heruntergeladen) plus, falls erkennbar,
   Headline/Primary Text der Anzeige.

## Schritt 5 — Übersetzung/Lokalisierung (Translation Mode)

**Quelle der Wahrheit ist der reale, im Account aktivierte Skill `image-ad-prompt-generator`
— nicht die lokale Kopie in `docs/skills/image-ad-prompt-generator.md`.** Diese Datei ist
nur eine Referenz-Zusammenfassung für den Fall, dass der Skill in der ausführenden
Session einmal nicht geladen ist.

Für **jede einzelne Ad** aus Schritt 4 (nicht gebündelt):

1. Prüfen, ob die Quell-Anzeige überhaupt ein Produkt zeigt.
   - **Zeigt sie ein Produkt:** das EINE Produktbild-Asset aus Schritt 3 (wiederverwendet,
     nicht neu erzeugt) als Referenz einsetzen — Maßstab/Winkel/Licht an die Ad-Szene
     anpassen.
   - **Zeigt sie kein Produkt:** die Anzeige visuell unverändert lassen, nur den Text
     übersetzen.
2. Den `Skill`-Tool mit `skill: "image-ad-prompt-generator"` aufrufen (steht der
   ausführenden Session zur Verfügung, da der Trigger in die reguläre Chat-Session
   zurückspielt) und dabei übergeben: die eine Quell-Ad-Referenz, ggf. die
   Produktbild-Referenz aus Schritt 3 (nur wenn Produkt vorhanden), exakter Produktname
   aus Spalte G, korrekter Preis aus Spalte J, Zielsprache aus dem Tab (`FI` → Finnisch,
   `FRCA` → Quebec-Französisch, siehe `sheet.tabs.*.language`).
3. Ist der Skill in der Session ausnahmsweise nicht auffindbar: ersatzweise nach den
   Regeln in `docs/skills/image-ad-prompt-generator.md` selbst vorgehen und das im
   Abschlussbericht (Schritt 8) vermerken.
4. **Wichtig:** Dieser Skill wird ausschließlich für Übersetzungen (diese Ads) verwendet
   — niemals für Varianten/Iterationen/New Concepts. Das ist Aufgabe der separaten,
   aktuell inaktiven Foundation-Phase (Schritt 6, `docs/skills/foundation-to-higgsfield.md`),
   die einen anderen Skill/Ablauf nutzt. Pro Ad wird **genau ein** Ergebnisbild erzeugt,
   nicht mehrere Varianten.
5. Output (übersetzte Headline + Primary Text inkl. korrektem Preis, Liste der
   verarbeiteten Ad-Permalinks) als Markdown nach
   `<Projektordner>/<market_code>/translated-ads/<product_name>/<Lauf-Datum>.md`
   schreiben (`Google_Drive.create_file`, `contentMimeType: text/markdown`).

## Schritt 6 — Foundation-Phase (optional, aktuell inaktiv)

Nur wenn `foundation_phase.mode` ungleich `translation_only`. Regeln:
`docs/skills/foundation-to-higgsfield.md`. Aktuell nicht konfiguriert (keine
Foundation-Dokumente hinterlegt) — Schritt wird übersprungen.

## Schritt 7 — Rendering-Output

Die eigentliche Higgsfield-Generierung passiert bereits in Schritt 5 (ein Call pro Ad,
über den `image-ad-prompt-generator`-Skill). Dieser Schritt betrifft nur die Ablage:

1. **Seitenverhältnis:** Jedes generierte Bild muss exakt das Seitenverhältnis/die Maße
   der jeweiligen Quell-Anzeige haben (z. B. `1:1`, `4:5`, `9:16` — je nachdem, wie die
   Ad in der Ad Library aussieht), nicht ein Standard-Format. Vor dem Higgsfield-Call die
   Maße der Quell-Anzeige bestimmen und als `aspect_ratio` übergeben.
2. **Die Bilddateien selbst gehören in Drive** — in voller Auflösung, nicht nur als
   CDN-Link. Ablauf (Details und Begründung: `STATUS.md` Abschnitt 2a):
   a. Die Higgsfield-Ergebnisse per `curl` lokal ablegen, benannt nach dem Schema
      `<product_name>_ad<N>_<market_code>.jpg` (plus `<product_name>_<market_code>_produktbild.png`).
   b. Pro Datei einen 630-Byte-Platzhalter per Drive-MCP `create_file` im Zielordner
      anlegen (Konstante `PLACEHOLDER_JPEG_B64` in `scripts/drive_upload.py`,
      `disableConversionToGoogleType: true`, Dateiname exakt wie lokal).
   c. `python3 scripts/drive_upload.py <folder_id> <local_dir>` — ersetzt den Inhalt
      byte-genau über den Service Account und verifiziert die Größe.
   Der Service Account kann Dateien nicht selbst *anlegen* (keine Speicherquota), nur
   *überschreiben* — deshalb der Platzhalter-Schritt. Kein Grund, hier aufzugeben.
3. Zusätzlich pro Zeile/Produkt/Lauf-Datum ein Markdown-Dokument im selben Ordner
   ablegen: übersetzte Headline + Primary Text, per-Ad-Overlay-Text, die
   Higgsfield-CDN-URLs und alle Review-Flags.
4. Ist kein Higgsfield-MCP verfügbar: nur die Prompt-Texte ausgeben, Rendering
   überspringen.

## Schritt 8 — Ablage, Sheet-Eintrag & Abschluss

1. Alle Text-/Bild-Outputs liegen bereits in Drive (Schritte 5/7).
2. **Den Drive-Ordnerlink in das Sheet schreiben** — Spalte `O`
   (`[merged] Link to Videos /Images`) der verarbeiteten Zeile, Label = Produktname aus
   Spalte G, genau wie es die FI-Zeilen vormachen:
   `python3 scripts/sheet_set_link.py <TAB> O<Zeile> <folder_id> <Produktname>`
   Das Skript wählt den Formel-Trenner passend zur Sheet-Locale (`nl_NL` → Semikolon;
   ein Komma ergibt `#ERROR!`) und prüft danach, dass die Zelle sauber rendert.
   Das ist ein fester Teil des Laufs, keine Hausaufgabe für den Nutzer.
3. `<Projektordner>/<market_code>/State/processed_comments.json` mit den neuen
   Fingerprints aus Schritt 2 aktualisieren. Hat die Zeile keinen eigenen M-Thread,
   sondern nutzt die Quell-Ads des anderen Tabs (siehe Schritt 2.4), dann
   `source_from_<tab>_row` und die Fingerprints der Quellzeile mitschreiben.
4. Kurze Zusammenfassung an den Nutzer: welche Zeilen/Produkte verarbeitet wurden, wie
   viele Ads pro Zeile, Drive-Links zu den neuen Dateien, ob gerendert wurde oder nur
   Prompt-Texte erzeugt wurden. Bei "nichts Neues" keine Nachricht (siehe Schritt 2.2).
