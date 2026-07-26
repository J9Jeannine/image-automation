Führe den image-automation Workflow aus dem Repo `j9jeannine/image-automation`, Branch
`claude/adoring-fermat-ikg9pb`, aus.

1. Lies **`STATUS.md`**, `docs/workflow.md` und `config/automation.config.json` aus
   diesem Repo. `STATUS.md` zuerst: dort steht, wie Bilder in Drive und Links ins Sheet
   kommen (Service Account + `scripts/`). Beides funktioniert — aber nicht über den
   Drive-MCP-Connector allein. Behaupte nie, etwas ginge nicht, ohne vorher `STATUS.md`
   gelesen und `env | grep -i google` geprüft zu haben.
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
6. Gibt es in keinem Tab neue/geänderte Kommentar-Threads: Lauf ohne Chat-Nachricht
   beenden (kein Spam).
6b. Hat eine Zeile keinen eigenen M-Thread, aber der andere Tab hat dieselbe
   Competitor-URL (Spalte C/D)? Dann die dortigen Quell-Ads wiederverwenden und in die
   Zielsprache dieses Tabs übersetzen, statt die Zeile zu überspringen — mit Produktname
   und Preis aus dem **eigenen** Tab. Siehe `docs/workflow.md` Schritt 2.4.
7. **Ergebnisse ablegen — beides gehört zum Lauf, nicht zur Nacharbeit des Nutzers:**
   die Bilddateien selbst in voller Auflösung in den Drive-Produktordner
   (`scripts/drive_upload.py`, zweistufig — siehe `STATUS.md` 2a), und den Ordnerlink in
   Spalte O der Sheet-Zeile (`scripts/sheet_set_link.py`, Label = Produktname aus
   Spalte G).
8. Wurde mindestens eine Zeile verarbeitet: melde kurz welche Zeilen/Produkte (Tab +
   Produktname aus Spalte G), wie viele Ads pro Zeile, Drive-Links zu den neu erzeugten
   Dateien, und ob gerendert wurde oder nur Prompt-Texte erzeugt wurden.
