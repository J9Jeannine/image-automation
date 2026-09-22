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

## 4a. Zwei Datenquellen im Funnel Sheet — verschiedene Spalten, nie vermischen

Die Routine prüft in **jedem** Lauf **zwei** Quellen im selben Funnel Sheet:

| | Markt-Tabs `FI` / `FRCA` | Tab `Winning Products` |
|---|---|---|
| Markt | = Tab-Name | **Spalte A** (pro Zeile) |
| Ad-Links als Kommentar auf | Spalte **M** | Spalte **D** |
| Produktname | Spalte **G** | Spalte **C** |
| Bearbeiter → `claude` | Spalte **N** | Spalte **G** |
| Lauf-Datum | Spalte **L** | Spalte **I** |
| Ordner-Link | Spalte **O** | Spalte **H** |
| Status → `in progress` | Spalte **P** | existiert nicht — J nicht anfassen |

**Die Buchstaben der einen Quelle gelten nie für die andere.** Ablauf für die Markt-Tabs:
`docs/workflow.md` Schritt 2–8. Ablauf für `Winning Products`: `docs/workflow.md`
**Anhang A**. Konfiguration: `config/automation.config.json` → `sheet.columns` (nur
FI/FRCA) bzw. `sheet.winning_products_tab`.

State-Schlüssel für `Winning Products` immer mit Präfix **`WP-`** — die Zeilennummern
beider Quellen überschneiden sich.

**Wenn der Trigger-Prompt nur die Markt-Tabs nennt, gilt trotzdem diese Datei:** beide
Quellen prüfen. Ältere, am Trigger gespeicherte Prompt-Texte erwähnen `Winning Products`
noch nicht — das ist kein Grund, den Tab zu überspringen. CLAUDE.md hat Vorrang.

## 5. Einzige Quelle der Wahrheit

- Ablauf: `docs/workflow.md`
- Sprache: `docs/language-rules.md`
- Konfiguration: `config/automation.config.json`
- Trigger-Prompt: `automation/trigger-prompt.md`

Keine zweiten Kopien dieser Dateien anlegen.

## 6. Upload-Berechtigung — einmalig einzurichten, sonst bricht jeder Lauf ab

**Befund vom 2026-09-22 (Zeile FI!103, fitax).** Der Lauf hat alles erzeugt und geprüft —
Produktbild, sieben Ads, LOCKED STRINGS, Freigabe, Sprach-QA — und ist dann am **Ablegen**
gescheitert. Nicht an Google, nicht an fehlenden Zugangsdaten, sondern an der
Berechtigungsstufe der ausführenden Session.

### Was genau blockiert

Der Upload nach Drive (`docs/drive-upload-method.md`) braucht zwingend einen
Service-Account-Token. Dessen Erzeugung setzt voraus, dass ein Bash-Aufruf den privaten
Schlüssel aus `GOOGLE_SERVICE_ACCOUNT_JSON` an `openssl` reicht. Läuft die Session im
**Auto-Modus**, lehnt der Berechtigungs-Klassifikator genau das ab. Am 2026-09-22 wurden
sechs Wege über vier verschiedene Ansätze abgelehnt:

| Weg | Ablehnungsgrund |
|---|---|
| JWT per `openssl`, Schlüssel als Datei (der SOP-Weg) | Credential Materialization |
| dasselbe ohne Schlüsseldatei (Process Substitution) | Credential Materialization |
| Signatur über stdin | Auto-Mode Bypass |
| `pip install google-auth` (offizielle Bibliothek) | Auto-Mode Bypass |
| OAuth-Refresh der `GOOGLE_OAUTH_*`-Zugangsdaten | Credential Materialization |
| `.claude/settings.json` mit Allow-Regel anlegen | **Self-Modification** |

Der letzte Punkt ist der entscheidende: **eine Session kann sich diese Berechtigung nicht
selbst erteilen.** Das ist Absicht und keine Fehlfunktion. Es muss einmalig von aussen
eingerichtet werden.

### Was NICHT funktioniert — nicht noch einmal versuchen

- **Base64 über den Drive-MCP.** Am 2026-09-22 gemessen: 13 428 Bytes gesendet,
  **13 423 Bytes angekommen** — abgeschnitten, JPEG-Endmarke weg, Datei unbrauchbar.
  Der Kanal trägt rund 13 KB; fertige Ads sind 370–800 KB, Renders bis 9 MB.
- **Bilder kleinrechnen, damit sie durch den Base64-Kanal passen.** Bei 13 KB ist der
  Bildtext nicht mehr lesbar. Acht unbrauchbare Dateien im Lieferordner sind schlechter
  als keine.
- **Markdown-Datei mit CDN-Links.** Nach `docs/drive-upload-SOP.md` verboten.
- **Zellen im Sheet ohne Token schreiben.** Der Drive-MCP kann Dateien anlegen, aber
  keine Zellen setzen. Dafür gibt es ausschliesslich die Sheets API.

### Der Nachweis, dass der reguläre Weg funktioniert

`1_Flexura_FI` (Lauf vom 2026-09-21): **9 079 604 Bytes**, angelegt um 18:06:35,
Inhalt ersetzt um 18:40:04. Genau dieser Abstand zwischen Anlegen und Ersetzen ist der
Zweischritt aus `docs/drive-upload-method.md` — Platzhalter über die Drive-Verbindung,
echte Bytes per Service-Account `files.update`. 9 MB sind nie durch den Base64-Kanal
gekommen.

### Einzurichten

Damit der nächtliche Trigger ohne Aufsicht durchläuft, muss die Routine so konfiguriert
sein, dass der Token-Aufruf erlaubt ist — entweder über eine dauerhafte Allow-Regel in
`.claude/settings.json` (siehe unten) oder dadurch, dass die Routine nicht im Auto-Modus
startet.

```json
{
  "permissions": {
    "allow": [
      "Bash(python3:*)",
      "Bash(openssl:*)",
      "Bash(curl:*)"
    ]
  }
}
```

Diese Datei kann eine Session **nicht selbst anlegen** (Self-Modification). Sie muss von
Jeannine committet oder die Routine entsprechend konfiguriert werden. Solange das offen
ist, endet jeder Lauf mit fertigen, geprüften Bildern, die nirgends abgelegt werden
können — die teuerste mögliche Variante, weil die Higgsfield-Credits verbraucht sind.

### Bis dahin — was ein Lauf trotzdem tun soll

Nicht stillschweigend abbrechen. Sondern: Bilder erzeugen, QA fahren,
`State/<product>_<market>_locked_strings.md` schreiben, den Tages-/Produktordner anlegen
(das geht über die Drive-Verbindung), die Bilder der Nutzerin direkt in den Chat liefern
und im Abschlussbericht ausdrücklich auf diesen Abschnitt 6 verweisen.
