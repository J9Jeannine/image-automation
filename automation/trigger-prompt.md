**ZUERST LESEN — nicht überspringen:** `CLAUDE.md` und `docs/language-rules.md` aus
diesem Repo. Die Sprachregeln sind blockierend: der komplette sichtbare Bildtext wird
**vor** dem Bildprompt in der Zielsprache ausformuliert (LOCKED STRING) und wörtlich in
den Higgsfield-Prompt gesetzt — das Bildmodell übersetzt nie selbst. `FRCA` =
Québec-Französisch mit `tu`-Anrede, `FI` = natürliches Finnisch ohne erfundene
Komposita. **Für FRCA reicht die Verbotsliste nicht** — verbindlich sind der Test in
`docs/language-rules.md` 4.1 (A), die Kategorie-Prüfung 4.1 (C) und die Québec-Typografie
4.1 (E), insbesondere: kein Leerzeichen vor `!` `?` `;`. **Und vor jedem Rendern die
blockierende Freigabe nach Abschnitt 4a.** Kein Wort aus der Quell-Ad geht in den
Prompt. Jedes Wort im Render, das nicht im LOCKED STRING steht, bedeutet: nicht
hochladen, neu generieren.

Führe den image-automation Workflow aus dem Repo `j9jeannine/image-automation`, Branch
`claude/adoring-fermat-ikg9pb`, aus.

1. Lies `docs/workflow.md` und `config/automation.config.json` aus diesem Repo.
2. Folge Schritt 0 (Config-Guard): die Kernübersetzung braucht keine TODO-Felder mehr
   (Sheet/Spalten/Tabs/Zielsprachen sind fest konfiguriert). Nur die optionale
   Foundation-Phase (Schritt 6) überspringen, falls `foundation_phase.mode` das
   verlangt, aber die zugehörigen Foundation-Dokumente fehlen.
3. Führe Schritte 1-8 aus `docs/workflow.md` der Reihe nach aus: Sheet-Tabs `FI`
   (ab Zeile 52) und `FRCA` (ab Zeile 33) auf neue/geänderte Kommentar-Threads in
   Spalte M prüfen (siehe Schritt 2 für den Abgleich gegen
   `State/processed_comments.json`). **Vor jeder Generierung pro Zeile zwingend Schritt
   2a beachten (Zeilen-Sperre über `State/row_locks.json`)** — verhindert, dass zwei
   gleichzeitig laufende Sessions (z. B. dieser Trigger und ein manueller Lauf)
   dieselbe Zeile doppelt bearbeiten und Credits verbrennen. **Zusätzlich zwingend
   Schritt 2b beachten (Resume):** vor jeder Generierung (Produktbild UND jede Ad)
   prüfen, ob die Zieldatei im Drive-Ordner schon existiert und nicht in
   `State/flagged_for_regeneration.json` als falsch markiert ist — falls ja, NICHT neu
   generieren, sondern überspringen. Nach einem Abbruch (z. B. Credits alle) generiert
   der nächste Lauf so automatisch nur das Fehlende, nie die ganze Zeile neu.
4. **Pro Zeile genau EIN Produktbild erzeugen** (Schritt 3): Competitor-Foto aus Spalte D
   per curl holen, per Higgsfield einmalig auf den Produktnamen aus Spalte G umbenennen,
   Modell-Parameter dabei immer direkt `nano_banana_pro` (nie erst ein anderes Modell
   versuchen). Dieses eine Bild für ALLE Ads dieser Zeile wiederverwenden — nie pro Ad
   neu erzeugen.
5. Für jede Ad aus dem M-Kommentar-Thread (Schritt 4/5): **zuerst den LOCKED STRING
   nach `docs/language-rules.md` schreiben** (fertiger Zieltext, max. 6 Wörter pro
   Textelement), **dann die Freigabe nach Abschnitt 4a durchlaufen — blockierend:**
   `python3 scripts/check_locked_string.py <MARKET_CODE> <ad_copy.md>` muss Exit 0
   liefern, und in der `ad_copy.md` muss pro Textelement eine `FREIGABE 4.1(A):`-Zeile
   stehen. Exit 1 oder fehlender Block = nicht rendern, LOCKED STRING korrigieren.
   Erst danach rendern. Ad erst versuchen zu öffnen. Ist
   `facebook.com` blockiert (bekannte Einschränkung dieser Sandbox, siehe
   `network_access` in der Config) — **den Nutzer nach den direkten
   Bild-/Video-URLs fragen**, nicht stumm überspringen oder mehrfach versuchen. Dann:
   den `Skill`-Tool mit `skill: "image-ad-prompt-generator"` aufrufen (echter, im Account
   aktivierter Skill — nicht die lokale Doku-Kopie), pro Ad genau ein Ergebnisbild im
   exakten Seitenverhältnis der Quell-Anzeige, Produktbild nur einsetzen wenn die
   Quell-Ad ein Produkt zeigt, korrekten Preis aus Spalte J in der Ad-Copy nutzen, Modell
   immer direkt `nano_banana_pro`. Dieser
   Skill ist ausschließlich für Übersetzungen zu nutzen, niemals für
   Varianten/Iterationen/New Concepts. Nur falls `foundation_phase.mode !=
   translation_only` zusätzlich `docs/skills/foundation-to-higgsfield.md` für die
   separate Foundation-Phase anwenden.
6. **Sprach-QA vor dem Upload (Schritt 7.5):** jedes Bild einzeln mit dem `Read`-Tool
   ansehen, jedes sichtbare Wort abtippen und Zeichen für Zeichen gegen den LOCKED
   STRING diffen (inkl. Akzente, `ä`/`ö`, Zahlenformat `<Betrag> $` / `<Betrag> €` —
   der Betrag kommt aus Spalte J, die Zahlen in den Docs sind Formatbeispiele).
   Zusätzlich die fünf FRCA-Punkte aus `docs/workflow.md` Schritt 8.5 einzeln
   protokollieren.
   Abweichung = nicht hochladen, neu generieren, **und den Schlüssel dieses Bildes in
   `State/flagged_for_regeneration.json` eintragen** (Schritt 2b) — sonst weiß ein
   späterer Lauf nicht, dass genau dieses Bild noch fehlt. Ein Prompt-Hinweis ist kein
   Nachweis.

7. **Bild-Upload nach Drive ist verpflichtend (Schritt 7):** die gerenderten Higgsfield-Bilder
   per curl auf die Disk laden und als **echte JPG-Dateien** in Drive ablegen — Ordner
   `Translated-Ads/<market_code>/<Lauf-Datum YYYY-MM-DD> - <product_name>/` (Produktname MUSS
   im Ordnernamen stehen), Dateien `<N>_<product_name>_<market_code>.jpg` (Zahl zuerst,
   z. B. `1_Pawox_FI.jpg` — siehe `config/automation.config.json` →
   `drive.file_name_pattern`). Upload-Methode
   ZWINGEND wie in `config/automation.config.json` → `upload_method`: Platzhalter per
   Drive-`create_file` anlegen (User-owned), dann per Service-Account (`GOOGLE_SERVICE_ACCOUNT_JSON`)
   `files.update` mit den vollen Bytes überschreiben. Niemals auf den alten
   Markdown-Links-Workaround zurückfallen; jede hochgeladene Datei auf volle Größe/Dekodierung
   verifizieren.
7. **Sheet-Rückschreiben (Schritt 8.2) ist verpflichtend** — volle Anleitung in
   `docs/sheet-writeback-SOP.md`. Für jede Zeile, die in diesem Lauf wirklich Bilder
   produziert hat, im Funnel Sheet vier Zellen setzen: **L** = Lauf-Datum (echtes Datum,
   `d-m-yyyy`), **N** = `claude`, **O** = `=HYPERLINK("<URL>";"<Produktname aus G>")`
   (Semikolon als Trenner!), **P** = `in progress` — niemals `Ready`, das setzt der
   Mensch, der die fehlenden Ads ergänzt. Das geht nicht über den Drive-MCP, sondern über
   die Sheets API mit demselben Service-Account (`GOOGLE_SERVICE_ACCOUNT_JSON`, Scope
   `.../auth/spreadsheets`). Blockierte Zeilen und Zeilen mit einer anderen Person in
   Spalte N nicht anfassen. Danach zurücklesen und im Bericht bestätigen.
8. Gibt es in keinem Tab neue/geänderte Kommentar-Threads: Lauf ohne Chat-Nachricht
   beenden (kein Spam).
9. Wurde mindestens eine Zeile verarbeitet: melde kurz welche Zeilen/Produkte (Tab +
   Produktname aus Spalte G), wie viele Ads pro Zeile, Drive-Links zu den neu erzeugten
   Dateien, welche Sheet-Zellen (N/O) gesetzt wurden, und ob gerendert wurde oder nur
   Prompt-Texte erzeugt wurden.
