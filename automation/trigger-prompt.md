Führe den image-automation Workflow aus dem Repo `j9jeannine/image-automation`, Branch
`claude/adoring-fermat-ikg9pb`, aus.

1. Lies `docs/workflow.md` und `config/automation.config.json` aus diesem Repo.
2. Folge Schritt 0 (Config-Guard): die Kernübersetzung braucht keine TODO-Felder mehr
   (Sheet/Spalten/Tabs/Zielsprachen sind fest konfiguriert). Nur die optionale
   Foundation-Phase (Schritt 6) überspringen, falls `foundation_phase.mode` das
   verlangt, aber die zugehörigen Foundation-Dokumente fehlen.
3. Führe Schritte 1-8 aus `docs/workflow.md` der Reihe nach aus: Sheet-Tabs `FI`
   (ab Zeile 52) und `FRCA` (ab Zeile 33) auf neue/geänderte Kommentar-Threads in
   Spalte M prüfen (siehe `docs/workflow.md` Schritt 2 für den Abgleich gegen
   `State/processed_comments.json`), unter Verwendung der Regeln in
   `docs/skills/image-ad-prompt-generator.md` und (falls `foundation_phase.mode !=
   translation_only`) `docs/skills/foundation-to-higgsfield.md`.
4. Gibt es in keinem Tab neue/geänderte Kommentar-Threads: Lauf ohne Chat-Nachricht
   beenden (kein Spam).
5. Wurde mindestens eine Zeile verarbeitet: melde kurz welche Zeilen/Produkte (Tab +
   Produktname aus Spalte G), wie viele Ads pro Zeile, Drive-Links zu den neu erzeugten
   Dateien, und ob gerendert wurde oder nur Prompt-Texte erzeugt wurden.
