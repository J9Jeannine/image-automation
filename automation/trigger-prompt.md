Führe den image-automation Workflow aus dem Repo `j9jeannine/image-automation`, Branch
`claude/adoring-fermat-ikg9pb`, aus.

1. Lies `docs/workflow.md` und `config/automation.config.json` aus diesem Repo.
2. Folge exakt Schritt 0 (Config-Guard) zuerst. Enthält die Config noch TODO-Platzhalter
   in einem Pflichtfeld: brich sofort ab und poste nur eine kurze Erinnerung, dass das
   Setup noch nicht abgeschlossen ist ("config/automation.config.json ausfüllen"). Führe
   in diesem Fall keinen Drive-Zugriff, kein Scraping und keinen Higgsfield-Aufruf aus.
3. Ist die Config vollständig: führe Schritte 1-8 aus `docs/workflow.md` der Reihe nach
   aus, unter Verwendung der Regeln in `docs/skills/image-ad-prompt-generator.md` und
   (falls `foundation_phase.mode != translation_only`) `docs/skills/foundation-to-higgsfield.md`.
4. Melde am Ende kurz: Anzahl verarbeiteter Ads, betroffene Zielmärkte, Drive-Links zu
   den neu erzeugten Dateien, und ob gerendert wurde oder nur Prompt-Texte erzeugt
   wurden.
