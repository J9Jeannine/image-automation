# Master-Workflow

Wird bei jedem Trigger-Lauf ausgeführt. Tool-Namen beziehen sich auf die in der
Cowork-Session verfügbaren MCP-Server (`Google_Drive`, `Higgsfield`) sowie Bash für die
Playwright-Skripte in `scripts/`.

> **Bild-Upload nach Drive:** Die verbindliche, einzig zulässige Methode zum Hochladen
> echter Bilddateien (Platzhalter via Drive-Verbindung → Service-Account `files.update`,
> inkl. Begründung und Copy/Paste-Befehlen) steht in
> **[`docs/drive-upload-method.md`](drive-upload-method.md)**. Niemals auf einen
> Markdown-Links-Workaround zurückfallen. Kurzfassung in Schritt 7 unten.
>
> **Falls eine künftige Session behauptet, das ginge nicht:** die bewiesene Schritt-für-
> Schritt-SOP mit echten Datei-IDs/Größen (atriso 2026-07-23, itzora 2026-07-25) und
> Gegenargumenten steht in **[`docs/drive-upload-SOP.md`](drive-upload-SOP.md)** — es
> funktioniert nachweislich, einfach ausführen.

> **Sprache der Bilder (blockierend):** Die verbindlichen Regeln stehen in
> **[`docs/language-rules.md`](language-rules.md)** und sind in **jedem** Lauf vor
> Schritt 5 zu lesen. Kernprinzip: der fertige Bildtext (LOCKED STRING) steht **vor**
> dem Bildprompt fest und wird wörtlich übernommen — das Bildmodell übersetzt nie
> selbst. `FRCA` = Québec-Französisch (`tu`-Anrede), `FI` = natürliches Finnisch.
> Erfundene Wörter und Frankreich-Französisch sind Ablehnungsgründe, keine Schönheits-
> fehler.

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
2a. **Zeilen-Sperre — verpflichtend, bevor irgendetwas für eine Zeile generiert wird.**
   Grund: zwei gleichzeitig laufende Sessions (z. B. der tägliche 6-Uhr-Trigger und ein
   manueller "Jetzt ausführen"-Lauf) haben bereits einmal dieselbe Zeile parallel
   bearbeitet — Ergebnis: ein kompletter doppelter Bildersatz (12 Bilder), der danach
   wieder überschrieben/gelöscht wurde. Reine Higgsfield-Credits verbrannt, für nichts.
   Dagegen:
   - `<Projektordner>/<market_code>/State/row_locks.json` lesen (existiert die Datei
     nicht, als `{}` behandeln). Schlüssel: `<market_code>!<Zeilennummer>`
     (z. B. `FRCA!56`).
   - Existiert für diese Zeile ein Eintrag **und** ist dessen `locked_at` jünger als
     **30 Minuten**: diese Zeile in diesem Lauf **überspringen**, nichts generieren,
     im Abschlussbericht (Schritt 8) vermerken ("Zeile X übersprungen — durch andere
     Session gesperrt seit HH:MM").
   - Sonst (kein Eintrag, oder Eintrag älter als 30 Minuten = vermutlich abgestürzte/
     hängengebliebene Session): Eintrag mit aktuellem Zeitstempel und Session-Kennung
     schreiben, dann erst mit Schritt 3 für diese Zeile fortfahren.
   - Nach Abschluss dieser Zeile (egal ob erfolgreich, übersprungen wegen Blockierung,
     oder fehlgeschlagen) den Lock-Eintrag für diese Zeile wieder **entfernen**.
   - Diese Sperre ist pro Zeile, nicht global — andere Zeilen im selben Lauf sind davon
     unberührt.

2b. **Resume — nur Fehlendes oder als falsch Markiertes generieren, niemals die ganze
   Zeile neu.** Grund: bricht ein Lauf mitten in einer Zeile ab (Credits alle,
   Absturz, Fehler), soll der nächste Lauf nicht bereits fertige, korrekte Bilder ein
   zweites Mal erzeugen — das verbrennt Credits ohne Nutzen. Vor **jeder** Generierung
   (Schritt 3 Produktbild UND jede einzelne Ad in Schritt 5):
   - Zielordner `Translated-Ads/<market_code>/<Lauf-Datum> - <product_name>/` in Drive
     auflisten (existiert er noch nicht, gilt als leer).
   - `<Projektordner>/<market_code>/State/flagged_for_regeneration.json` lesen
     (existiert die Datei nicht, als `{}` behandeln). Schlüssel:
     `<market_code>!<Zeilennummer>!ad<N>` (Produktbild: `...!produktbild`).
   - Existiert `<product_name>_<market_code>_ad<N>.jpg` (bzw. `_produktbild.jpg`)
     bereits im Zielordner **und** ihr Schlüssel steht **nicht** in
     `flagged_for_regeneration.json`: **nicht neu generieren.** Datei unangetastet
     lassen, für Schritt 8 als bereits erledigt zählen.
   - Fehlt die Datei **oder** ihr Schlüssel steht in `flagged_for_regeneration.json`:
     generieren (bzw. neu generieren). Nach erfolgreichem Upload und bestandener
     Sprach-QA (Schritt 7.5) den Schlüssel aus `flagged_for_regeneration.json`
     entfernen.
   - Erzeugt eine Ad-QA (Schritt 7.5) einen Treffer (falscher Text): den Schlüssel
     dieses Bildes in `flagged_for_regeneration.json` **eintragen**, statt es nur im
     Abschlussbericht zu vermerken — sonst weiß ein späterer Lauf nicht, dass genau
     dieses eine Bild nachgeholt werden muss.
   - Das gilt unabhängig von Schritt 2a: eine durch Zeilen-Sperre übersprungene Zeile
     wird beim nächsten Lauf ganz normal nach dieser Resume-Logik behandelt (nicht
     alles neu, nur was fehlt).
3. Pro zu verarbeitender Zeile zusätzlich lesen:
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
2. **Vor dem Higgsfield-Call: jeden sichtbaren Text auf der Verpackung/dem Etikett des
   Competitor-Fotos erfassen** — nicht nur den Produktnamen, auch Zusatzzeilen wie
   Produktkategorie, Pflegehinweis, Siegel/Badges (z. B. "SOIN MÉDICAL", "MEDICAL",
   "NATURAL FORMULA"). Für jede dieser Zusatzzeilen einen LOCKED STRING in der
   Zielsprache der Zeile festlegen (siehe `docs/language-rules.md`) — genau wie für den
   Ad-Overlay-Text in Schritt 5. **Dieses Produktbild wird für ALLE Ads der Zeile
   wiederverwendet — steht hier noch fremdsprachiger Verpackungstext, taucht er in jedem
   einzelnen Ad dieser Zeile wieder auf.** Beobachteter Fehler: ein Competitor-Foto mit
   französischem "SOIN MÉDICAL" auf der Tube wurde für eine FI-Zeile wiederverwendet —
   das französische Etikett erschien dadurch unübersetzt in mehreren fertigen
   Finnisch-Ads.
3. Dieses Competitor-Produktfoto **einmalig** per `Higgsfield.generate_image` bearbeiten:
   Produktform/-design/Farben/Licht/Winkel exakt beibehalten, sichtbaren Produktnamen
   durch `product_name` (Spalte G) ersetzen (inkl. ®/™-Handling) und **jede in Punkt 2
   erfasste Verpackungszeile durch ihren LOCKED STRING in der Zielsprache ersetzen** —
   der Prompt bekommt denselben "render exactly, do not translate"-Block wie in
   `docs/language-rules.md` Abschnitt 1. Keine fremdsprachige Verpackungszeile darf
   unverändert durchgereicht werden, auch wenn nur der Produktname als "zu ändern"
   erscheint. **Modell-Parameter `model` immer und direkt `nano_banana_pro`** (siehe
   `config/automation.config.json` → `image_model`) — kein Versuch mit einem anderen
   Modell zuerst.
4. Ergebnis mit dem `Read`-Tool ansehen und jede Verpackungszeile gegen ihren LOCKED
   STRING prüfen (wie in Schritt 7.5), bevor das Bild als Asset gilt.
5. Das Ergebnis ist DAS Produktbild-Asset für diese Zeile — merken (media_id/Job-ID) für
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

> **VORGESCHALTET UND BLOCKIEREND — Sprachregeln:** `docs/language-rules.md` ist vor
> diesem Schritt zu lesen, in **jedem** Lauf. Kein Higgsfield-Call ohne LOCKED STRING.
> Kurzfassung: der komplette sichtbare Bildtext wird **vorher** in der Zielsprache
> ausformuliert (`FRCA` = Québec-Französisch mit `tu`-Anrede, `FI` = natürliches
> Finnisch), als LOCKED STRING in der `ad_copy.md` festgehalten und wörtlich in den
> Prompt gesetzt. Das Bildmodell übersetzt nichts, ergänzt nichts, korrigiert nichts.
> Kein Wort aus der Quell-Ad geht in den Prompt.

0. **LOCKED STRING erzeugen** (vor allem anderen): jeden sichtbaren Text der Ziel-Ad
   ausformulieren — Headline, Banner, Badge, Störer, CTA, Preisschild,
   Verpackungsaufdruck. Zielsprache aus dem Tab (`FI` → Finnisch, `FRCA` →
   Québec-Französisch, siehe `sheet.tabs.*.language` und
   `language_rules.<market_code>` in der Config). Max. 6 Wörter pro Textelement.
   Gegen die Verbots-/Pflichtliste in `docs/language-rules.md` Abschnitt 4 prüfen,
   **bevor** gerendert wird. Der LOCKED STRING wandert unverändert in die
   `<product_name>_<market_code>_ad_copy.md` aus Punkt 5.

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
   aus Spalte G, korrekter Preis aus Spalte J (Format nach `docs/language-rules.md`
   Abschnitt 4: `49,99 $` für FRCA, `49,99 €` für FI) und **den LOCKED STRING aus
   Punkt 0** — nicht die Zielsprache als Auftrag, sondern den fertigen Text als Vorgabe.
   Jeder Prompt endet zwingend mit:

   ```
   Render this text EXACTLY as written, character for character, including every accent
   and special character. Do NOT translate it. Do NOT rephrase it. Do NOT correct it.
   Do NOT add any other words, labels, packaging text, price tags, or background signage.
   The image must contain no text other than the strings quoted above.
   Ignore all text visible in the reference image.
   ```

   **Modell-Parameter `model` immer und direkt `nano_banana_pro`** (siehe
   `config/automation.config.json` → `image_model`) — nicht erst ein Standard-/
   Default-Modell versuchen und bei Misserfolg oder schlechtem Ergebnis auf ein anderes
   wechseln. Das direkte Anfordern des Zielmodells verhindert verbrannte Credits durch
   verworfene Zwischenversuche.
3. Ist der Skill in der Session ausnahmsweise nicht auffindbar: ersatzweise nach den
   Regeln in `docs/skills/image-ad-prompt-generator.md` selbst vorgehen und das im
   Abschlussbericht (Schritt 8) vermerken.
4. **Wichtig:** Dieser Skill wird ausschließlich für Übersetzungen (diese Ads) verwendet
   — niemals für Varianten/Iterationen/New Concepts. Das ist Aufgabe der separaten,
   aktuell inaktiven Foundation-Phase (Schritt 6, `docs/skills/foundation-to-higgsfield.md`),
   die einen anderen Skill/Ablauf nutzt. Pro Ad wird **genau ein** Ergebnisbild erzeugt,
   nicht mehrere Varianten.
5. Output (übersetzte Headline + Primary Text inkl. korrektem Preis, Liste der
   verarbeiteten Ad-Permalinks) als Markdown `<product_name>_<market_code>_ad_copy.md`
   in den Tages-/Produkt-Ordner aus Schritt 7 schreiben (`Google_Drive.create_file`,
   `contentMimeType: text/markdown`, `textContent` — klein genug, keine Truncation).

## Schritt 6 — Foundation-Phase (optional, aktuell inaktiv)

Nur wenn `foundation_phase.mode` ungleich `translation_only`. Regeln:
`docs/skills/foundation-to-higgsfield.md`. Aktuell nicht konfiguriert (keine
Foundation-Dokumente hinterlegt) — Schritt wird übersprungen.

## Schritt 7 — Rendering-Output & Drive-Upload (echte Bilddateien)

Die eigentliche Higgsfield-Generierung passiert bereits in Schritt 5 (ein Call pro Ad,
über den `image-ad-prompt-generator`-Skill). Dieser Schritt betrifft die Maße und die
**verbindliche** Ablage der echten Bilddateien in Drive.

1. **Seitenverhältnis:** Jedes generierte Bild muss exakt das Seitenverhältnis/die Maße
   der jeweiligen Quell-Anzeige haben (z. B. `1:1`, `4:5`, `9:16` — je nachdem, wie die
   Ad in der Ad Library aussieht), nicht ein Standard-Format. Vor dem Higgsfield-Call die
   Maße der Quell-Anzeige bestimmen und als `aspect_ratio` übergeben.

2. **Tages-/Produkt-Ordner anlegen:** Pro Lauf einen Ordner
   `<Lauf-Datum YYYY-MM-DD> - <product_name>` (z. B. `2026-07-25 - itzora`) unter
   `Translated-Ads/<market_code>/` erstellen (`Google_Drive.create_file`,
   `mimeType: application/vnd.google-apps.folder`, `parentId` = `drive.translated_ads_subfolders.<market_code>`
   aus der Config). Der Produktname MUSS im Ordnernamen stehen (nicht nur das Datum), damit
   mehrere Produkte am selben Tag unterscheidbar sind.

3. **Bild-Upload — ZWINGEND diese Methode, kein Markdown-Links-Workaround.**
   Higgsfield-Ergebnisse per `curl` von der CDN-URL auf die lokale Disk laden, dann jede
   echte JPG-Datei nach Drive hochladen. Der Upload läuft **immer** in zwei Schritten
   (Details + Begründung: `config/automation.config.json` → `upload_method`):
   a. **Platzhalter als User-Datei anlegen:** `Google_Drive.create_file` mit
      `contentMimeType: image/jpeg`, `disableConversionToGoogleType: true`,
      `base64Content` = winziges 1×1-JPEG, `parentId` = Tages-/Produkt-Ordner. Die
      zurückgegebene `id` merken. (Die Datei gehört jetzt dem User.)
   b. **Service-Account überschreibt mit den vollen Bytes:** Access-Token aus
      `GOOGLE_SERVICE_ACCOUNT_JSON` minten (JWT RS256, Scope `.../auth/drive`, Signatur per
      `openssl`, weil das `cryptography`-Python-Modul in der Sandbox defekt ist; Token 1 h
      gültig → bei `401 ACCESS_TOKEN_EXPIRED` neu minten), dann
      `curl -X PATCH 'https://www.googleapis.com/upload/drive/v3/files/{ID}?uploadType=media&supportsAllDrives=true'`
      `-H 'Authorization: Bearer <SA_TOKEN>' -H 'Content-Type: image/jpeg' --data-binary @<datei.jpg>`.
   Warum so: Der Service-Account hat **kein** Storage-Quota → `files.create` mit Bytes gibt
   `403 storageQuotaExceeded`, aber `files.update` auf eine **User-owned** Datei bucht den
   Speicher dem User → funktioniert (Ergebnis: `owner=User`, `lastModifyingUser=Service-Account`,
   volle Qualität). Der Drive-MCP-Base64-Kanal schneidet lange Werte ab (~15 000 base64-Zeichen
   ≈ 11 KB) → für echte Bilder (100–260 KB) unbrauchbar, deshalb nur für den Platzhalter.
   Dateibenennung: `<product_name>_<market_code>_ad<N>.jpg`, Produktbild
   `<product_name>_<market_code>_produktbild.jpg`.

4. **Verifizieren:** Nach jedem Upload prüfen, dass die zurückgegebene `size` der
   Quell-Dateigröße entspricht UND das Bild vollständig dekodiert (`PIL im.load()`). Bei
   Abweichung (Truncation/Korruption) erneut hochladen — niemals eine korrupte oder nur
   verlinkte Datei als Ergebnis stehen lassen.

5. **Sprach-QA — verpflichtend, vor jedem Upload, für JEDES einzelne Bild.**
   Vollständige Regeln: `docs/language-rules.md` Abschnitt 5. Kurzfassung:
   - Ergebnisbild mit dem `Read`-Tool ansehen (nicht auf OCR-Snippets der Drive-Suche
     verlassen), jedes sichtbare Wort abtippen und Zeichen für Zeichen gegen den
     LOCKED STRING aus Schritt 5 Punkt 0 diffen — inklusive Akzente, `ä`/`ö` und
     Zahlenformat.
   - Zusätzlich gegen die Verbotsliste der Landesvariante prüfen (FRCA u. a. `SOLDES`,
     `vous`-Anrede, fehlende Akzente; FI u. a. erfundene Komposita, `a` statt `ä`).
   - Jedes Wort im Bild, das nicht im LOCKED STRING steht — auch auf Verpackung,
     Etikett, Preisschild oder Hintergrundschild — bedeutet: **nicht hochladen**,
     neu generieren mit gekürztem LOCKED STRING. **Zusätzlich den Schlüssel dieses
     Bildes (`<market_code>!<Zeilennummer>!ad<N>`) in
     `State/flagged_for_regeneration.json` eintragen** (siehe Schritt 2b) — nicht nur
     im Abschlussbericht vermerken, sonst weiß ein späterer/neuer Lauf nicht, dass
     genau dieses eine Bild noch nachgeholt werden muss.
   - Gilt für jedes Bild einzeln, nicht als Stichprobe. Transkription jedes
     hochgeladenen Bildes in der State-Datei protokollieren. Nach erfolgreichem
     erneuten Upload und bestandener Prüfung den Schlüssel aus
     `flagged_for_regeneration.json` wieder entfernen.
   - Diese Prüfung ist ein Sicherheitsnetz. Wenn sie regelmäßig anschlägt, ist Schritt 5
     Punkt 0 falsch ausgeführt worden — dort liegt der Fehler, nicht hier.

6. Ergebnisse zusätzlich inline im Chat zeigen. Ist kein Higgsfield-MCP verfügbar: nur die
   Prompt-Texte ausgeben, Rendering überspringen (dann gibt es keine Bilddateien zum
   Hochladen).

## Schritt 8 — Ablage & Abschluss

1. Alle Text-/Bild-Outputs liegen bereits als **echte Dateien** im Tages-/Produkt-Ordner
   `Translated-Ads/<market_code>/<Lauf-Datum> - <product_name>/` (Schritte 5/7): die
   `<product_name>_<market_code>_ad<N>.jpg`, das `_produktbild.jpg` und die `_ad_copy.md`.
   Es darf **kein** Markdown-Links-Ersatz statt echter Bilddateien stehen bleiben.
2. **Sheet-Rückschreiben — verpflichtend, nicht optional.** Vollständige Anleitung:
   **[`docs/sheet-writeback-SOP.md`](sheet-writeback-SOP.md)**. Pro verarbeiteter Zeile
   vier Zellen im "Funnel Sheet" (`sheet.id`) setzen, damit das Team das Ergebnis im Sheet
   selbst findet und nicht im Chat suchen muss:
   - Spalte `sheet.columns.date_completed_column` (**L**) = Datum dieses Laufs, als
     **echtes Datum** (Format `d-m-yyyy`, z. B. `4-8-2026`). Nach dem Schreiben prüfen,
     dass der Rohwert eine **Zahl** ist — sonst wurde es als Text gespeichert.
   - Spalte `sheet.columns.person_column` (**N**) = `claude` (Dropdown-Wert, exakt
     kleingeschrieben), damit erkennbar ist, wer die Zeile produziert hat.
   - Spalte `sheet.columns.result_folder_link_column` (**O**) = Link auf den
     Tages-/Produkt-Ordner aus Schritt 7, als Formel im vorhandenen Format:
     `=HYPERLINK("<Drive-Ordner-URL>";"<product_name aus Spalte G>")`.
     **Achtung Semikolon** als Argumenttrenner (Locale des Sheets), nicht Komma.
   - Spalte `sheet.columns.status_column` (**P**) = `in progress` (klein).
     **Niemals `Ready`** — ein Lauf liefert praktisch nie alle Ads einer Zeile; `Ready`
     setzt der Mensch, der die fehlenden Ads ergänzt hat.

   Technisch: der Drive-MCP kann keine Zellen schreiben — dafür die **Sheets API mit
   demselben Service-Account** nutzen wie beim Bild-Upload (`GOOGLE_SERVICE_ACCOUNT_JSON`),
   Scope zusätzlich `https://www.googleapis.com/auth/spreadsheets`:
   `POST https://sheets.googleapis.com/v4/spreadsheets/{sheet.id}/values:batchUpdate`
   mit `valueInputOption: "USER_ENTERED"`. Danach die geschriebenen Zellen zurücklesen
   und im Bericht bestätigen.

   Nur für Zeilen schreiben, die in **diesem** Lauf tatsächlich Bilder produziert haben.
   Blockierte Zeilen (keine ladbaren Ad-Bilder) bleiben unangetastet — ein Link auf einen
   nicht existierenden Ordner ist schlimmer als eine leere Zelle. Ebenso Zeilen, in denen
   bereits eine andere Person in Spalte N steht, nicht überschreiben.
3. `State/processed_comments.json` mit den neuen Fingerprints aus Schritt 2 aktualisieren
   (kleine Textdatei → direkt per `Google_Drive.create_file`/`files.update`). Die
   geschriebene Sheet-Zelle dort als `sheet_link_written` vermerken.
4. Kurze Zusammenfassung an den Nutzer: welche Zeilen/Produkte verarbeitet wurden, wie
   viele Ads pro Zeile, Drive-Links zu den neuen Dateien, ob gerendert wurde oder nur
   Prompt-Texte erzeugt wurden, und welche Sheet-Zellen (N/O) gesetzt wurden. Bei
   "nichts Neues" keine Nachricht (siehe Schritt 2.2).
