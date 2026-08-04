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
   `State/processed_comments.json`).
4. **Pro Zeile genau EIN Produktbild erzeugen** (Schritt 3): Competitor-Foto aus Spalte D
   per curl holen, per Higgsfield einmalig auf den Produktnamen aus Spalte G umbenennen.
   Dieses eine Bild für ALLE Ads dieser Zeile wiederverwenden — nie pro Ad neu erzeugen.
5. Für jede Ad aus dem M-Kommentar-Thread (Schritt 4/5): erst versuchen zu öffnen. Ist
   `facebook.com` blockiert (bekannte Einschränkung dieser Sandbox, siehe
   `network_access` in der Config) — **den Nutzer nach den direkten
   Bild-/Video-URLs fragen**, nicht stumm überspringen oder mehrfach versuchen. Dann:
   den `Skill`-Tool mit `skill: "image-ad-prompt-generator"` aufrufen (echter, im Account
   aktivierter Skill — nicht die lokale Doku-Kopie), pro Ad genau ein Ergebnisbild im
   exakten Seitenverhältnis der Quell-Anzeige, Produktbild nur einsetzen wenn die
   Quell-Ad ein Produkt zeigt, korrekten Preis aus Spalte J in der Ad-Copy nutzen. Dieser
   Skill ist ausschließlich für Übersetzungen zu nutzen, niemals für
   Varianten/Iterationen/New Concepts. Nur falls `foundation_phase.mode !=
   translation_only` zusätzlich `docs/skills/foundation-to-higgsfield.md` für die
   separate Foundation-Phase anwenden.
6. **Bild-Upload nach Drive ist verpflichtend (Schritt 7):** die gerenderten Higgsfield-Bilder
   per curl auf die Disk laden und als **echte JPG-Dateien** in Drive ablegen — Ordner
   `Translated-Ads/<market_code>/<Lauf-Datum YYYY-MM-DD> - <product_name>/` (Produktname MUSS
   im Ordnernamen stehen), Dateien `<product_name>_<market_code>_ad<N>.jpg`. Upload-Methode
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
