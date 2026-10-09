# Master-Workflow

Wird bei jedem Trigger-Lauf ausgeführt. Tool-Namen beziehen sich auf die in der
Cowork-Session verfügbaren MCP-Server (`Google_Drive`, `Higgsfield`) sowie Bash für die
Playwright-Skripte in `scripts/`.

> **Bild-Upload nach Drive:** Die verbindliche, einzig zulässige Methode ist **ein
> `curl`-Call pro Bild** gegen den Apps-Script-Endpunkt im Google-Konto von Jeannine —
> ohne Zugangsdaten, ohne Token, ohne Service-Account. Vollständig beschrieben in
> **[`docs/drive-upload-method.md`](drive-upload-method.md)**. Niemals auf einen
> Markdown-Links-Workaround zurückfallen. Kurzfassung in Schritt 7 unten.
>
> **Falls eine künftige Session behauptet, das ginge nicht:** die Schritt-für-Schritt-SOP
> mit Gegenargumenten steht in **[`docs/drive-upload-SOP.md`](drive-upload-SOP.md)** —
> einfach ausführen.
>
> **Kein Sheet-Rückschreiben:** Die Routine schreibt **keine** Zelle im Funnel Sheet. Das
> macht ein Trigger im Google-Konto von Jeannine. Siehe Schritt 8.2 und
> **[`docs/sheet-writeback-SOP.md`](sheet-writeback-SOP.md)**.

> **Sprache der Bilder (blockierend):** Die verbindlichen Regeln stehen in
> **[`docs/language-rules.md`](language-rules.md)** und sind in **jedem** Lauf vor
> Schritt 5 zu lesen. Kernprinzip: der fertige Bildtext (LOCKED STRING) steht **vor**
> dem Bildprompt fest und wird wörtlich übernommen — das Bildmodell übersetzt nie
> selbst. `FRCA` = Québec-Französisch (`tu`-Anrede), `FI` = natürliches Finnisch.
> **Für FRCA reicht die Verbotsliste nicht** — sie ist eine Promo-Wortliste, die in
> einer Kosmetik-Ad nie greift. Verbindlich sind zusätzlich Register (4.1 A),
> Kategorie-Vokabular (4.1 C) und Typografie (4.1 E), insbesondere: **kein Leerzeichen
> vor `!` `?` `;`**. Die Wortlisten in 4.1 sind **Beispiele, keine abschließenden
> Listen** — verbindlich für jedes Produkt und jede Kategorie ist der Test in 4.1 (A).
> Erfundene Wörter und Frankreich-Französisch sind Ablehnungsgründe, keine Schönheits-
> fehler.

## Schritt −1 — Upload-Guard (BLOCKING, vor allem anderen)

Bevor irgendein Bild generiert wird (Credits!), prüfen:

1. `git branch --show-current` muss der Default-Branch des Repos sein (`git remote show origin` → HEAD branch).
2. `docs/drive-upload-SOP.md` muss den Apps-Script-Endpunkt (`script.google.com/macros/s/`) enthalten.
3. Der Upload läuft **ausschließlich** über diesen Endpunkt. `GOOGLE_SERVICE_ACCOUNT_JSON`,
   JWT/Token-Minting, Platzhalter-Dateien und `files.update` sind verboten — wer sie versucht,
   läuft in die Sandbox-Sperre „Credential Materialization“ (Ursache der Fehlläufe bis 01.10.2026).

Schlägt 1 oder 2 fehl: **nichts generieren**, Lauf abbrechen und melden
„Upload-Guard: Fix nicht im Default-Branch“.

**Regel für jede Fix-Session:** Änderungen an Workflow/SOP immer in den Default-Branch
(`claude/adoring-fermat-ikg9pb`) mergen. Ein Fix, der nur auf einem Nebenbranch liegt, ist für die
Routine nicht vorhanden.

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

> **ZWEI QUELLEN, VERSCHIEDENE SPALTEN — nicht vermischen.**
> Dieser Schritt 2 beschreibt die **Markt-Tabs `FI` und `FRCA`**: Kommentare auf
> Spalte **M**, Produktname aus **G**, Rückschreiben nach **L/N/O/P**.
> Der Tab **`Winning Products`** hat **andere Spaltenbuchstaben**: Kommentare auf
> Spalte **D**, Produktname aus **C**, Rückschreiben nach **G/H/I**. Für ihn gilt
> **Anhang A** am Ende dieser Datei — nichts aus Schritt 2 bis 8 mit den hier
> genannten Spaltenbuchstaben darf auf ihn angewendet werden.
> **Jeder Lauf prüft beide Quellen.**

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
   - **Liegen MEHRERE Dateien dieses Namens im State-Ordner, erst zusammenführen,
     bevor irgendetwas daraus gelesen wird** (Regel aus Schritt 8.3a). Beobachteter
     Fehler, gefunden am 2026-10-09: im FI-State-Ordner lagen zwei
     `flagged_for_regeneration.json` — die neuere (2026-10-06) enthielt nur
     `_comment`/`_last_clear`, die ältere (2026-09-29) alle sechs offenen Blocker.
     Wer nur die neueste liest, hält die offenen Einträge für erledigt und verliert
     sie still. Dasselbe gilt für `processed_comments.json` und `row_locks.json`.
   - Existiert `<N>_<Productname>_<countrycode>` (bzw. `_produktbild.jpg`)
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
> Finnisch), als LOCKED STRING in `State/<product>_<market>_locked_strings.md` festgehalten und wörtlich in den
> Prompt gesetzt. Das Bildmodell übersetzt nichts, ergänzt nichts, korrigiert nichts.
> Kein Wort aus der Quell-Ad geht in den Prompt.

0. **LOCKED STRING erzeugen** (vor allem anderen): jeden sichtbaren Text der Ziel-Ad
   ausformulieren — Headline, Banner, Badge, Störer, CTA, Preisschild,
   Verpackungsaufdruck. Zielsprache aus dem Tab (`FI` → Finnisch, `FRCA` →
   Québec-Französisch, siehe `sheet.tabs.*.language` und
   `language_rules.<market_code>` in der Config). Max. 6 Wörter pro Textelement.
   Gegen die Verbots-/Pflichtliste in `docs/language-rules.md` Abschnitt 4 prüfen,
   **bevor** gerendert wird. Der LOCKED STRING wandert unverändert in die
   `State/<product>_<market>_locked_strings.md` aus Punkt 5.

0b. **FREIGABE — blockierend, vor dem ersten `generate_image`-Call.**
   Vollständige Regel: `docs/language-rules.md` Abschnitt 4a. Zwei Pflichtschritte:

   ```
   python3 scripts/check_locked_string.py <MARKET_CODE> <pfad_zur_locked_strings.md>
   ```

   **Exit-Code 1 = nicht rendern.** LOCKED STRING korrigieren, erneut prüfen. Erst
   bei Exit 0 weiter. Kein Higgsfield-Call, solange das Skript blockiert — das spart
   auch Credits, weil ein sprachlich falsches Bild gar nicht erst entsteht.

   Zusätzlich in die `State/<product>_<market>_locked_strings.md`, eine Zeile **pro Textelement**:
   `FREIGABE 4.1(A): "<Text>" — eigenständig im Québec-Französisch? JA, weil <Grund>`
   Fehlt der Block, ist die Ad nicht freigegeben. „Alles geprüft" zählt nicht.

   Grund für diesen Schritt: die Sprach-QA in Schritt 8.5 läuft **nach** dem Rendern
   und vergleicht Bild gegen LOCKED STRING. Sie findet nie, dass der LOCKED STRING
   selbst schon Frankreich-Französisch war. Genau dort ist FRCA monatelang
   durchgerutscht.

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
5. **Keine Textdatei in den Lieferordner.** Der Tages-/Produkt-/Set-Ordner enthält
   ausschließlich Bilddateien. Vorgabe von Jeannine am 2026-09-04: die frühere
   `ad_copy.md` wird dort nicht gebraucht und ist inhaltlich nicht die richtige Ad-Copy.
   Der LOCKED-STRING- und FREIGABE-Nachweis bleibt trotzdem verpflichtend (CLAUDE.md
   Regel 1.5) — er wird als `<product>_<market>_locked_strings.md` nach
   `<Projektordner>/<market_code>/State/` geschrieben, nicht in den Lieferordner
   (`Google_Drive.create_file`, `contentMimeType: text/markdown`,
   `disableConversionToGoogleType: true`, `textContent`).

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

1a. **Mindestgröße 600 × 600 px — blockierend, gilt für JEDE Bilddatei im Lieferordner.**
   Vorgabe von Jeannine am 2026-10-07. Seitenverhältnis und Mindestgröße gelten
   **zusammen**, nicht alternativ:
   - **Jede Seite** (Breite UND Höhe) des fertigen Bildes muss **mindestens 600 px**
     betragen. `300 × 400`, `480 × 600`, `335 × 600` sind damit **ungültig** — auch dann,
     wenn das Seitenverhältnis stimmt und auch dann, wenn die Quell-Anzeige selbst so
     klein war.
   - Das Seitenverhältnis bleibt trotzdem exakt das der Quell-Anzeige. Die Mindestgröße
     wird **nie** durch Beschneiden, Strecken oder ein anderes Format erreicht, sondern
     ausschließlich dadurch, dass größer gerendert/hochskaliert wird.
   - **Richtwert beim Rendern:** lange Seite ~2048 px. Daraus ergeben sich die üblichen
     Zielmaße, alle deutlich über der Grenze:

     | Quell-Format | Zielmaße Render | kurze Seite |
     |---|---|---|
     | `1:1`  | 2048 × 2048 | 2048 ✓ |
     | `4:5`  | 1856 × 2304 | 1856 ✓ |
     | `3:4`  | 1792 × 2400 | 1792 ✓ |
     | `9:16` | 1536 × 2752 | 1536 ✓ |

   - **Nachweis vor dem Upload, pro Datei:** die tatsächlichen Pixelmaße messen, nicht
     schätzen und nicht aus dem `aspect_ratio`-Parameter ableiten:

     ```
     python3 scripts/check_image_size.py <datei> [<datei> ...]
     ```

     **Exit-Code 1 = nicht hochladen.** Das Skript prüft jede Datei einzeln und nennt die
     gemessenen Maße. Erst bei Exit 0 weiter zu Punkt 3 (Upload).
   - **Ist ein Render zu klein:** mit größerem Zielmaß im selben Seitenverhältnis neu
     rendern. Hilfsweise `Higgsfield.upscale_image` — das ändert das Motiv nicht.
   - **Pass-through-Dateien (textlose Ads, Anhang A.5 / Schritt 5.1):** das Motiv bleibt
     unverändert, das ist die stärkere Regel — ein Neurender ist hier weiterhin verboten.
     Liegt eine solche Quelldatei unter 600 px auf einer Seite, wird sie per
     `Higgsfield.upscale_image` auf die Mindestgröße gebracht (kein Neurender, Motiv
     identisch) und das im Abschlussbericht als „hochskaliert, Motiv unverändert"
     ausgewiesen.
   - Die gemessenen Maße jeder hochgeladenen Datei kommen in die State-Datei (wie die
     QA-Transkription in Punkt 5) und in den Abschlussbericht.

2. **Tages-/Produkt-Ordner anlegen:** Pro Lauf einen Ordner
   `<Lauf-Datum YYYY-MM-DD> - <product_name>` (z. B. `2026-07-25 - itzora`) unter
   `Translated-Ads/<market_code>/` erstellen (`Google_Drive.create_file`,
   `mimeType: application/vnd.google-apps.folder`, `parentId` = `drive.translated_ads_subfolders.<market_code>`
   aus der Config). Der Produktname MUSS im Ordnernamen stehen (nicht nur das Datum), damit
   mehrere Produkte am selben Tag unterscheidbar sind.

3. **Bild-Upload — ZWINGEND diese Methode, kein Markdown-Links-Workaround.**
   Der Upload ist **ein einziger `curl`-Call pro Bild** gegen den Apps-Script-Endpunkt im
   Google-Konto von Jeannine. **Keine Zugangsdaten, kein Token, kein Service-Account, kein
   Platzhalter.** Das Script holt die Bild-URL serverseitig selbst — das Bild muss für den
   Upload **nicht** auf die lokale Disk geladen werden (für die Sprach-QA in Punkt 5 schon,
   das ist ein anderer Zweck). Endpunkt und Details:
   `config/automation.config.json` → `upload_method`, Langfassung
   [`docs/drive-upload-method.md`](drive-upload-method.md).

   ```bash
   ENDPOINT="https://script.google.com/macros/s/AKfycbx3em9-sB7jMOXRg58JO94A1muKq1fy-fKT1Vb85Go71RX6K_t5E5kk5EHXRr_pqrXdOQ/exec"

   curl -sS -L "$ENDPOINT" \
     -H "Content-Type: application/json" \
     -d "{\"folderId\":\"${FOLDER_ID}\",\"name\":\"${N}_${PRODUCT}_${MARKET}\",\"url\":\"${CDN_URL}\"}"
   ```

   - `folderId` = Tages-/Produkt-Ordner aus Punkt 2 (bei `Winning Products`: der Set-Ordner).
   - `name` = Dateiname nach dem Schema unten.
   - `url` = CDN-URL des gerenderten Higgsfield-Bildes (muss ohne Login erreichbar sein).
   - **Niemals `-X POST`** — `-d` macht daraus schon einen POST; `-X POST` würde beim
     302-Redirect nach `googleusercontent.com` erneut POSTen und den Call brechen. `-L` ist
     Pflicht.
   - Der frühere Zwei-Schritt-Weg (Platzhalter per Drive-MCP + Service-Account
     `files.update` mit JWT) ist **ersatzlos gestrichen** und darf nicht wieder eingebaut
     werden.

   **Dateibenennung — verbindlich seit 2026-09-04, von Jeannine vorgegeben (unverändert):**

       <laufende Nummer>_<Productname>_<countrycode>

   Beispiel: `1_Pawox_FI`, `2_Pawox_FI`, … bzw. `1_Lumifirm_FI` … `7_Lumifirm_FI`.
   - Laufende Nummer **ohne** führende Null, beginnend bei 1.
   - Produktname mit **großem** Anfangsbuchstaben, auch wenn Spalte C ihn klein schreibt.
   - Ländercode wie im Sheet: `FI`, `FRCA`, `NLBE`, `SE`, `UK`.
   - **Keine Dateiendung im Namen** — Drive leitet sie aus dem MIME-Type ab. Die
     bestehenden Dateien `1_Lumifirm_FRCA` … `10_Lumifirm_FRCA` heißen genau so.
   - Das alte Schema `<product>_<market>_ad<N>.jpg` ist **ungültig** und darf nicht
     mehr verwendet werden.
   - Ausnahme Produktbild: bleibt `<product_name>_<market_code>_produktbild.jpg`.

4. **Verifizieren:** Der Endpunkt antwortet **auch im Fehlerfall mit HTTP 200** — ein Fehler
   kommt als HTML-Seite mit `Exception: …` zurück (z. B. `Invalid file or folder ID: …`).
   Deshalb nach jedem Call: (a) Antworttext auf `Exception` prüfen — trifft das zu, gilt der
   Upload als fehlgeschlagen und der genaue Fehlertext gehört in den Bericht; (b) die Datei
   im Zielordner nachsehen (`Google_Drive.search_files` / `get_file_metadata`), sie muss
   existieren und eine plausible Größe (> 10 KB) haben. Bei Fehlschlag den Call für diese
   Datei wiederholen — niemals eine fehlende Datei oder nur einen Link als Ergebnis stehen
   lassen.

5. **Sprach-QA — verpflichtend, vor jedem Upload, für JEDES einzelne Bild.**
   Vollständige Regeln: `docs/language-rules.md` Abschnitt 5. Kurzfassung:
   - Ergebnisbild mit dem `Read`-Tool ansehen (nicht auf OCR-Snippets der Drive-Suche
     verlassen), jedes sichtbare Wort abtippen und Zeichen für Zeichen gegen den
     LOCKED STRING aus Schritt 5 Punkt 0 diffen — inklusive Akzente, `ä`/`ö` und
     Zahlenformat.
   - Zusätzlich gegen die Landesvariante prüfen. **FRCA — diese fünf Punkte einzeln
     abhaken und einzeln protokollieren; "keine Auffälligkeiten" ohne die Einzelliste
     ist kein gültiger Log-Eintrag:**
     1. `vous / votre / vos` oder eine `-ez`-Verbform als Leseransprache
     2. **Leerzeichen vor `!` `?` `;`** (Frankreich-Satz — häufigster Fehler)
     3. ein Ausdruck, der den Test aus `docs/language-rules.md` 4.1 (A) nicht besteht
        — gilt für **jedes Produkt und jede Kategorie**, nicht nur für die Wörter in
        den Beispieltabellen 4.1 (C)/(D). Die Listen sind Abkürzungen für bekannte
        Fälle; ein Wort, das dort fehlt, ist nicht erlaubt, sondern ungeprüft.
     4. fehlender oder falscher Akzent, auch in Großbuchstaben
     5. Preis nicht im Format `<Betrag> $` (Dezimalkomma, Leerzeichen, Dollarzeichen).
        Der Betrag stammt aus Spalte J — Zahlen in `language-rules.md` sind
        Formatbeispiele, keine Preise.
     FI u. a. erfundene Komposita, `a` statt `ä`.
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

1. Alle Bild-Outputs liegen bereits als **echte Dateien** im Tages-/Produkt-/Set-Ordner
   (Schritte 5/7), benannt `<N>_<Productname>_<countrycode>` (plus ggf.
   `_produktbild.jpg`). **Keine Textdatei im Lieferordner** — der LOCKED-STRING-Nachweis
   liegt in `State/<product>_<market>_locked_strings.md`.
   Es darf **kein** Markdown-Links-Ersatz statt echter Bilddateien stehen bleiben.
2. **Sheet-Rückschreiben — ENTFÄLLT.** Die Routine schreibt **nichts** ins Funnel Sheet:
   weder `L`/`N`/`O`/`P` in den Markt-Tabs noch `G`/`H`/`I` in `Winning Products`. Das
   erledigt ein **Trigger im Google-Konto von Jeannine**. Für die Routine ist das Sheet
   **rein lesend**. Keine Sheets API, kein `values:batchUpdate`, kein Service-Account.
   Details: [`docs/sheet-writeback-SOP.md`](sheet-writeback-SOP.md). Steht das Rückschreiben
   noch in einem älteren, am Trigger gespeicherten Prompt-Text: trotzdem nicht ausführen —
   `CLAUDE.md` und diese Datei haben Vorrang.
3. `State/processed_comments.json` mit den neuen Fingerprints aus Schritt 2 aktualisieren
   (kleine Textdatei → direkt per `Google_Drive.create_file`). Das ist eine Drive-Datei,
   kein Sheet-Eintrag; den früheren Vermerk `sheet_link_written` gibt es nicht mehr.

3a. **State-Datei schreiben heißt immer: vorher zusammenführen, nachher entdoppeln.**
   `Google_Drive.create_file` **überschreibt nicht** — es legt eine zweite Datei mit
   demselben Titel im selben Ordner an. `Google_Drive.update_file` kann nur Titel und
   Ordner ändern, nicht den Inhalt. Daraus folgt für jede State-Datei
   (`processed_comments.json`, `flagged_for_regeneration.json`, `row_locks.json`):
   - **Vor dem Schreiben** alle Dateien dieses Namens im State-Ordner auflisten und den
     **vollständigen** Inhalt aus allen zusammenführen — nie nur die neueste nehmen.
     Einträge werden nur dann entfernt, wenn sie nachweislich erledigt sind.
   - **Nach dem Schreiben** die Vorgänger per `Google_Drive.update_file` auf
     `<name>_superseded_<YYYY-MM-DD>.json` umbenennen (nicht löschen), damit im Ordner
     genau **eine** Datei den kanonischen Namen trägt.
   - **Fingerprint-Algorithmus ist festgelegt und darf nicht variieren:**
     `sha256` über `"\n".join(<Post-Texte in Thread-Reihenfolge>)`, hex. Ein Lauf, der
     einen anderen Algorithmus benutzt (beobachtet: 32-stellige Hashes am 2026-10-08),
     macht seine Einträge für jeden Folgelauf unprüfbar — der muss dann über
     Zielordner-Inhalt und Post-Anzahl rekonstruieren, ob die Zeile fertig ist.
   - **Große State-Dateien nicht blind neu schreiben:** `processed_comments.json` ist
     inzwischen >140 KB. Steht nichts Neues drin, wird sie **nicht** angefasst — ein
     abgeschnittener Schreibvorgang würde den gesamten Zustand zerstören.
4. Kurze Zusammenfassung an den Nutzer: welche Zeilen/Produkte verarbeitet wurden, wie
   viele Ads pro Zeile, Drive-Links zu den neuen Dateien und ob gerendert wurde oder nur
   Prompt-Texte erzeugt wurden. Keine Sheet-Zellen mehr melden — es werden keine gesetzt.
   Bei "nichts Neues" keine Nachricht (siehe Schritt 2.2).

---

# Anhang A — Tab `Winning Products` (eigener Ablauf, eigene Spalten)

**Warum ein eigener Anhang:** Dieser Tab liegt im selben Funnel Sheet, hat aber eine
völlig andere Spaltenbelegung als `FI` und `FRCA`. Wer die Buchstaben aus Schritt 2–8
hier anwendet, liest die Ad-Links aus der falschen Zelle und schreibt das Ergebnis in
die falsche Spalte. Config: `sheet.winning_products_tab`.

## A.0 Spaltenvergleich — auswendig falsch, deshalb hier zum Nachschlagen

| Bedeutung | Tabs `FI` / `FRCA` | Tab `Winning Products` |
|---|---|---|
| Markt | = Tab-Name | **Spalte A** (pro Zeile: FI, NLBE, FRCA, SE, UK …) |
| Produktname für Dateinamen | Spalte **G** (`new PR NAME`) | Spalte **C** (`Product`) |
| Kommentar-Thread mit den Ad-Bild-Links | Spalte **M** | Spalte **D** |
| Preis | Spalte **J** | **gibt es nicht** — im Markt-Tab nachschlagen (A.3) |
| Bearbeiter (nur lesen) | Spalte **N** | Spalte **G** |
| Lauf-Datum (nur lesen) | Spalte **L** | Spalte **I** |
| Link auf den Ergebnis-Ordner (nur lesen) | Spalte **O** | Spalte **H** |
| Status (nur lesen) | Spalte **P** | **gibt es nicht** |

> Die vier unteren Zeilen stehen nur zur Orientierung hier. **Die Routine schreibt in
> keine dieser Spalten** — und auch in keine andere. Siehe Schritt 8.2.

Erste Datenzeile: **3**. Kopfzeile ist Zeile 1.

## A.1 Neue Zeilen finden

1. `Google_Drive.read_file_content(fileId=<Funnel Sheet>, includeComments=true)`. Die
   Kommentar-Anker sind opake `workbook-range`-IDs; die Zuordnung
   `Kommentar-ID -> Winning Products!D<Zeile>` steht in der Mapping-Liste am **Ende**
   des zurückgegebenen `fileContent`.
2. Für jeden Thread auf einer `D`-Zelle: Head-Post **und alle Replies** sammeln. Das
   sind die direkten Bild-/Video-URLs (`scontent…fbcdn.net`). Der **Zellwert** von `D`
   ist nur ein Textlabel und wird ignoriert.
3. Fingerprint des ganzen Threads gegen
   `Translated-Ads/<market_code>/State/processed_comments.json` prüfen — Schlüssel
   **`WP-<Zeile>`** (z. B. `WP-87`). Nur neue/geänderte Threads verarbeiten.
4. Zeilen-Sperre wie Schritt 2a, aber Schlüssel **`WP-<market_code>!<Zeile>`**
   (z. B. `WP-FI!87`), TTL 30 Minuten, nach der Zeile wieder freigeben.

> **Warum die Präfixe `WP-` Pflicht sind:** Die Zeilennummern dieses Tabs überschneiden
> sich mit denen von `FI`/`FRCA`. `Winning Products!87` (lumifirm) und `FI!87` (Cervi)
> sind verschiedene Zeilen. Ohne Präfix überschreibt der eine State-Eintrag den anderen.

## A.2 Markt und Sprache

Der Markt steht in **Spalte A** der Zeile, nicht im Tab-Namen. Er bestimmt Zielsprache,
Sprachregeln, Drive-Zielbaum und den Ländercode im Dateinamen.

**Blockierend:** Hat dieser Markt in `docs/language-rules.md` keinen eigenen
Abschnitt 4.x, wird für die Zeile **nicht generiert** (Regel aus Abschnitt 6 dort).
Aktuell existieren nur **4.1 FRCA** und **4.2 FI**. Zeilen mit `NLBE`, `SE` oder `UK` in
Spalte A werden deshalb übersprungen und im Abschlussbericht mit dem Grund „Markt-
Abschnitt in language-rules.md fehlt" ausgewiesen.

## A.3 Preis nachschlagen

Dieser Tab hat keine Preisspalte. Im Markt-Tab aus Spalte A die Zeile suchen, deren
Spalte **G** (`new PR NAME`) dem Produktnamen aus **C** entspricht — alternativ über den
Code in **B** — und deren Spalte **J** nehmen. Niemals einen Preis aus der Quell-Ad oder
aus der Config übernehmen. Preisformat nach `docs/language-rules.md`.

## A.4 Produktbild

Wie Schritt 3, mit einer Ergänzung: Existiert im Drive-Baum des Marktes bereits ein
`<product>_<market>_produktbild.jpg` aus einem früheren Lauf, wird es **wiederverwendet
und nicht neu erzeugt** (Resume-Regel, Schritt 2b). Vor der Wiederverwendung das Bild mit
dem `Read`-Tool ansehen und prüfen, dass der Verpackungstext in der Zielsprache steht —
ein Produktbild mit englischem oder fremdsprachigem Etikett ist nach CLAUDE.md Regel 1
ein Regenerierungsfall und darf nicht in neue Ads übernommen werden.

Zeigt **keine** Quell-Ad der Zeile ein Produkt, wird gar kein Produktbild gebraucht.

## A.5 Ads erzeugen

Wie Schritt 5, unverändert: LOCKED STRING vor dem Prompt, `check_locked_string.py` mit
Exit 0, `FREIGABE`-Zeile pro Textelement, ein eigener Prompt pro Ad, Modell
`nano_banana_pro`, Seitenverhältnis exakt wie die Quell-Ad **und Mindestgröße 600 × 600 px
pro Datei** (Schritt 7.1a, `scripts/check_image_size.py` mit Exit 0 vor dem Upload).

**Textlose Ads:** Zeigt eine Quell-Ad weder Text noch Produkt (reine Illustration, Foto,
MRT-Aufnahme, Selfie), gibt es nichts zu übersetzen. Die Datei wird **unverändert
übernommen und nicht neu gerendert** — ein Neurender erzeugt ein anderes Motiv und wäre
eine Variante statt einer Übersetzung. Im Bericht als „unverändert übernommen" ausweisen.
Liegt eine solche Datei unter der Mindestgröße aus Schritt 7.1a (eine Seite < 600 px),
wird sie per `Higgsfield.upscale_image` hochskaliert — Motiv und Seitenverhältnis bleiben
identisch — und im Bericht als „hochskaliert, Motiv unverändert" ausgewiesen.

## A.6 Ablage in Drive

- Ziel: `Translated-Ads/<market_code>/<YYYY-MM-DD> - <product_name>/<Productname> Set <N>/`
  Der Set-Ordner liegt **im bestehenden Tages-/Produktordner**. Gibt es den noch nicht,
  zuerst nach `drive.day_folder_name_pattern` anlegen.
- **Set-Nummer `N`:** höchste für dieses Produkt bereits in Spalte **H** vergebene
  Set-Nummer + 1. Steht dort noch nichts, ist es **Set 2** (Set 1 = die ursprüngliche
  Übersetzung aus dem Markt-Tab).
- **Dateinamen:** `<N>_<Productname>_<countrycode>` (Schritt 7.3), also `1_Lumifirm_FI`,
  `2_Lumifirm_FI` … Ländercode = Spalte A.
- **Nur Bilddateien im Ordner.** Keine `ad_copy.md`, keine Textdatei (Schritt 5.5). Der
  LOCKED-STRING-Nachweis geht nach
  `Translated-Ads/<market_code>/State/<product>_<market>_locked_strings.md`.
- Upload-Methode wie in Schritt 7.3: ein `curl`-Call pro Bild gegen den
  Apps-Script-Endpunkt, `folderId` = **Set-Ordner**, ohne Zugangsdaten
  (`docs/drive-upload-method.md`).

## A.7 Rückschreiben ins Sheet — ENTFÄLLT

Die Routine schreibt in diesem Tab **keine einzige Zelle** — weder `G` (Bearbeiter) noch
`H` (Set-Ordner-Link) oder `I` (Lauf-Datum), und erst recht nicht `J`. Das übernimmt ein
Trigger im Google-Konto von Jeannine. Der Tab wird nur gelesen (Kommentare auf **D**,
Produktname aus **C**, Markt aus **A**, Set-Nummern aus **H**). Details:
[`docs/sheet-writeback-SOP.md`](sheet-writeback-SOP.md).

## A.8 Bericht

Pro verarbeiteter Zeile: Zeilennummer, Markt aus Spalte A, Produktname aus Spalte C,
Anzahl Ads (gerendert vs. unverändert übernommen), Link auf den Set-Ordner, Ergebnis der
Sprach-QA je Bild. Keine Sheet-Zellen melden — es werden keine gesetzt. Übersprungene Zeilen mit Grund (gesperrt, fehlender Markt-Abschnitt,
Quell-URL nicht ladbar). Ist in **beiden** Quellen nichts Neues, endet der Lauf ohne
Chat-Nachricht.
