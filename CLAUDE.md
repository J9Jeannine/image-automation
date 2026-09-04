# CLAUDE.md — verbindliche Regeln für dieses Repo

Diese Datei wird von jeder Claude-Code-Session in diesem Repo automatisch gelesen.
Sie hat Vorrang vor allem anderen im Repo. Wenn eine andere Datei ihr widerspricht,
gilt diese Datei.

---

## 1. Sprache der Bilder — HARTE REGEL, blockierend

Vollständige Spezifikation: **`docs/language-rules.md`** — vor Schritt 5 lesen, jeden Lauf.

Die drei Kernsätze:

1. **Der finale On-Image-Text steht VOR dem Bildprompt fest.** Er wird als
   LOCKED STRING in der Zielsprache geschrieben, in `State/<product>_<market>_locked_strings.md`
   festgehalten und wörtlich in den Higgsfield-Prompt eingesetzt. Das Bildmodell
   übersetzt **nie** selbst.
2. **Kein Wort aus der Quell-Anzeige wandert in den Prompt.** Die Quell-Ad ist
   ausschließlich Layout-/Bildreferenz. Jeder Prompt enthält explizit:
   *"Ignore all text visible in the reference image."*
3. **Kein Wort im gerenderten Bild darf fehlen im LOCKED STRING.** Erscheint im Render
   irgendein Wort, das nicht im LOCKED STRING steht — auch auf Verpackung, Etikett,
   Preisschild, Hintergrundschild — ist das Bild abgelehnt und wird neu generiert.
4. **Jedes Wort im LOCKED STRING selbst muss ein echtes, existierendes Wort der
   Zielsprache sein — für JEDE Sprache, nicht nur FRCA/FI.** Keine erfundenen oder nur
   plausibel klingenden Wörter, keine mechanisch zusammengebauten Komposita, keine
   falschen Endungen — besonders kritisch auf Verpackungen, Etiketten und Preisschildern.
   Vollständige Regel: `docs/language-rules.md` Abschnitt 1a. Gilt automatisch für jeden
   künftigen Markt.

Zielvarianten:

- **FRCA** = Québec-Französisch (wie in Québec geschrieben/gesprochen), **nicht**
  Frankreich-Französisch. Anrede immer **tu**, nie *vous*.
- **FI** = natürliches Finnisch eines Muttersprachlers. Keine maschinell
  zusammengesetzten Komposita, keine erfundenen Wörter.

5. **FREIGABE VOR DEM RENDERN — blockierend.** Vor dem ersten `generate_image`-Call
   jeder Ad muss `python3 scripts/check_locked_string.py <MARKET_CODE> <locked_strings.md>`
   mit Exit-Code 0 durchlaufen sein, und in der `locked_strings.md` muss pro Textelement eine
   `FREIGABE 4.1(A):`-Zeile stehen. Exit 1 oder fehlender Block = **nicht rendern**.
   Vollständige Regel: `docs/language-rules.md` Abschnitt 4a.
   Der Grund: die QA in Abschnitt 5 vergleicht das Bild mit dem LOCKED STRING und kann
   deshalb nie finden, dass der LOCKED STRING selbst schon Frankreich-Französisch war.
   Genau dort ist FRCA monatelang durchgerutscht — bei FI kann das nicht passieren,
   weil falsches Finnisch als Nicht-Finnisch auffällt, falsches Québécois aber immer
   noch gültiges Französisch ist.

**Ein Prompt-Hinweis allein ist kein Nachweis.** Erst der geprüfte Render zählt
(`docs/language-rules.md`, Abschnitt 5).

## 2. Modelle — ZWEI verschiedene, beide fest verankert

Nicht verwechseln, beide sind Pflicht:

- **Claude-Modell dieser Routine: Opus.** Wird am Trigger gesetzt (`update_trigger`,
  Feld `model`), **nicht** über Prompt-Text — eine Anweisung wie "nutze Opus" im Prompt
  hat keinerlei Wirkung. Wird ein Lauf auf einem schwächeren Modell gestartet, im
  Abschlussbericht ausdrücklich vermerken.
- **Higgsfield-Bildmodell: `nano_banana_pro`.** Wird bei **jedem** `generate_image`-Call
  (Produktbild in Schritt 3 UND jede einzelne Ad in Schritt 5) direkt als Parameter
  `model: nano_banana_pro` übergeben. **Kein Ausprobieren mit einem Standard-/anderen
  Modell zuerst und Wechsel erst bei Fehlschlag** — das hat in der Vergangenheit Credits
  für verworfene Zwischenversuche verbrannt. Siehe `config/automation.config.json` →
  `image_model`.

## 3. Nebenläufigkeit

Zwei gleichzeitig laufende Sessions dürfen nie dieselbe Sheet-Zeile bearbeiten — das hat
bereits einmal einen kompletten doppelten Bildersatz erzeugt und Credits verschwendet.
Jede Session sperrt eine Zeile vor der Generierung über
`State/row_locks.json` (30-Minuten-TTL) und gibt sie danach wieder frei. Siehe
`docs/workflow.md` Schritt 2a. Verpflichtend, kein Sonderfall.

## 3a. Resume — nach Abbruch nur Fehlendes nachholen

Bricht ein Lauf mitten in einer Zeile ab (Credits alle, Absturz, Fehler), generiert der
nächste Lauf **nicht** die ganze Zeile neu, sondern nur die Ad-Bilder, die im
Zielordner noch fehlen oder in `State/flagged_for_regeneration.json` als falsch markiert
sind. Bereits vorhandene, nicht markierte Bilder bleiben unangetastet. Siehe
`docs/workflow.md` Schritt 2b. Verpflichtend, kein Sonderfall.

## 4. Branch

Die Routine liest **`claude/adoring-fermat-ikg9pb`** (Default-Branch), siehe
`automation/trigger-prompt.md`. Korrekturen an Workflow/Regeln gehören auf **diesen**
Branch. Ein Fix auf einem anderen `claude/...`-Branch wird von der Routine nie gelesen
und ist wirkungslos.

## 5. Einzige Quelle der Wahrheit

- Ablauf: `docs/workflow.md`
- Sprache: `docs/language-rules.md`
- Konfiguration: `config/automation.config.json`
- Trigger-Prompt: `automation/trigger-prompt.md`

Keine zweiten Kopien dieser Dateien anlegen.
