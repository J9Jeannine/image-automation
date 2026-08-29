# CLAUDE.md — verbindliche Regeln für dieses Repo

Diese Datei wird von jeder Claude-Code-Session in diesem Repo automatisch gelesen.
Sie hat Vorrang vor allem anderen im Repo. Wenn eine andere Datei ihr widerspricht,
gilt diese Datei.

---

## 1. Sprache der Bilder — HARTE REGEL, blockierend

Vollständige Spezifikation: **`docs/language-rules.md`** — vor Schritt 5 lesen, jeden Lauf.

Die drei Kernsätze:

1. **Der finale On-Image-Text steht VOR dem Bildprompt fest.** Er wird als
   LOCKED STRING in der Zielsprache geschrieben, in `<product>_<market>_ad_copy.md`
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

**Ein Prompt-Hinweis allein ist kein Nachweis.** Erst der geprüfte Render zählt
(`docs/language-rules.md`, Abschnitt 5).

## 2. Modell

Diese Automatisierung läuft auf **Opus**. Das Modell wird am Trigger gesetzt
(`update_trigger`, Feld `model`), **nicht** über Prompt-Text — eine Anweisung wie
"nutze Opus" im Prompt hat keinerlei Wirkung. Wird ein Lauf auf einem schwächeren
Modell gestartet, im Abschlussbericht ausdrücklich vermerken.

## 3. Branch

Die Routine liest **`claude/adoring-fermat-ikg9pb`** (Default-Branch), siehe
`automation/trigger-prompt.md`. Korrekturen an Workflow/Regeln gehören auf **diesen**
Branch. Ein Fix auf einem anderen `claude/...`-Branch wird von der Routine nie gelesen
und ist wirkungslos.

## 4. Einzige Quelle der Wahrheit

- Ablauf: `docs/workflow.md`
- Sprache: `docs/language-rules.md`
- Konfiguration: `config/automation.config.json`
- Trigger-Prompt: `automation/trigger-prompt.md`

Keine zweiten Kopien dieser Dateien anlegen.
