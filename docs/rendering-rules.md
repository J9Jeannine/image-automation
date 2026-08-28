# Rendering-Regeln — verbindlich für jede Ad-Übersetzung

Diese Datei sammelt die Regeln, die sich in echten Läufen als zwingend erwiesen haben.
Sie gilt zusätzlich zu `docs/workflow.md` Schritt 5 und 7. Jede Regel hier steht,
weil ihr Fehlen schon einmal Credits verbrannt oder unbrauchbare Ads erzeugt hat.

---

## 1. Modell: IMMER `nano_banana_pro`, sobald Text im Bild steht

| Modell | Credits | Text im Bild |
|---|---|---|
| `nano_banana` | 1 | **unbrauchbar** — produziert Buchstabensalat |
| `nano_banana_pro` | 2 | sauber |

Belegt am 2026-08-28 (Dermaflex, zweimal unabhängig):

- Französisch auf `nano_banana`: „Ça comimnce à brüler / des que je comanne au suer",
  „avent que lure Haut es sente"
- Finnisch auf `nano_banana`: „Heitä **votre** ekonatsolisi. Tässa **poryoy**",
  Tube „INTER**R**IGO-VOIDE"

Das billigere Modell ist keine Ersparnis — jeder Render damit ist Ausschuss und muss
auf Pro wiederholt werden, kostet also am Ende 3 statt 2 Credits.

`nano_banana` ist nur für **textfreie** Bilder zulässig (reine Produktfreisteller).

**Budget-Faustregel:** Anzahl Ads × 2 Credits, plus ~20 % Puffer für Nachbesserungen.

---

## 2. Das Modell darf NICHT übersetzen — Zieltext wird vorgegeben

Ein Prompt der Form „translate the overlay text into Quebec French" liefert
**immer** neutrales Standard-/Frankreich-Französisch, egal wie viele Stilregeln
danebenstehen. Dasselbe gilt sinngemäß für jede Zielsprache mit eigener Varietät.

**Richtig:** Den Zieltext selbst formulieren und als wörtlich zu setzenden String
übergeben:

```
Set the text to EXACTLY these strings, copied character for character INCLUDING
every accent mark - do not translate, rephrase, shorten, correct or strip accents:
TOP DARK BAR: "Ça se met à chauffer dès que je commence à suer."
BOTTOM RIGHT TEXT: "Fait pour pomper l'humidité avant que ta peau s'en aperçoive."
```

Das Modell hat dann nur noch eine Satz-Aufgabe, keine Übersetzungsaufgabe.

### 2a. Akzente und Umlaute gehören IN den String

„Render all French accents correctly" reicht **nicht**. Wird der String ohne Akzente
übergeben, kommt er ohne Akzente heraus — das Modell setzt exakt, was dasteht:

- falsch übergeben: `"Ca se met a chauffer des que je commence a suer."`
  → im Bild: „Ca se met a chauffer des que je commence a suer."
- richtig übergeben: `"Ça se met à chauffer dès que je commence à suer."`

Gleiches gilt für finnische Umlaute (ä, ö) und für ™/®.

---

## 3. Québécois (FRCA) — was den Ton wirklich ausmacht

Grammatikalisch korrektes Französisch ist noch lange kein Québécois. Prüfliste:

| Nicht verwenden (Frankreich) | Verwenden (Québec) |
|---|---|
| „aussitôt que" | „dès que" |
| „avant que ta peau **ne** la sente" (ne explétif) | „avant que ta peau le sente" |
| „vous" / „Utilisez" | „tu" / „Mets-en" |
| „ce n'est pas" | „c'est pas" |
| „Jetez" | „**Garroche**" |
| „et" (in Ad-Copy) | „**pis**" |
| „Les Trois Choses" | „Les trois **affaires**" |
| „d'autres n'en ont pas" | „**le monde** en a pas" |
| „Ça commence à brûler" | „Ça **se met à** chauffer" |
| „Conçu pour absorber" | „**Fait pour pomper**" |

Grundsatz: So, wie eine Québecerin es einer Freundin erzählen würde — nicht wie ein
Pariser Apothekenprospekt.

---

## 4. Markenname auf der Verpackung

Spalte G enthält oft einen internen Arbeitsnamen (z. B. `dernaflex2`), **nicht** den
Namen, der auf die Tube gehört (z. B. `Dermaflex`).

- Für **Datei- und Ordnernamen sowie den Sheet-Linktext**: den Namen verwenden, den
  der Nutzer als Produktnamen bestätigt hat.
- Für den **Aufdruck im Bild**: denselben Namen, exakt geschrieben, mit ™ falls
  vorgegeben.
- Bei Abweichung zwischen Spalte G und Nutzer-Vorgabe: **vor dem Batch nachfragen**,
  nicht raten. Ein falscher Aufdruck bedeutet, dass jede Ad des Batches neu muss.

---

## 5. Detailregeln für die Tube

Immer explizit in den Prompt schreiben, sonst erfindet das Modell Text:

- Markenname exakt, mit kleinem hochgestelltem ™
- Beschreibungszeile pro Markt:
  - FRCA: `CRÈME APAISANTE CONTRE L'INTERTRIGO`
  - FI: `INTERTRIGO-VOIDE` (Schreibweise ausbuchstabieren — sonst wird „INTERRIGO" daraus)
- Rundes Siegel: `SOIN MÉDICAL` — **niemals erfundene Wörter**. Ohne diese Regel
  entstand wiederholt das Artefakt „SOUCHETTE MÉDICALE".

---

## 6. Split-Screen-Ads

Bei Vorher/Nachher-Ads explizit fordern:
„nothing may sit on or across the vertical dividing line between the two panels".
Sonst klebt das Produktbündel mittig über der Trennlinie und überdeckt beide Panels.

---

## 7. NSFW-Filter

Manche Quell-Ads (Haut/Unterwäsche) werden als Referenz abgelehnt — teils schon beim
`media_import_url`, teils erst beim Generieren (`status: "nsfw"`).

- Ablehnung auf `nano_banana` heißt **nicht**, dass es auf `nano_banana_pro` scheitert:
  erst dort erneut versuchen, bevor die Ad als blockiert gemeldet wird.
- Bleibt sie blockiert: im Bericht und in der `ad_copy.md` vermerken, nicht stumm
  überspringen.

---

## 8. Rate-Limit und parallele Sessions

- Nie mehr als ~6 Requests auf einmal submitten und die Queue zwischendurch leerlaufen
  lassen. Größere Batches liefern `429 rate_limit_reached`.
- **Ein `429` heißt nicht, dass kein Bild entstanden ist.** Läuft eine zweite Session
  am selben Job, sättigt sie das Limit und ihre Jobs laufen trotzdem durch.
- **Vor jeder Behauptung über verlorene Credits** `show_generations` prüfen und mit
  `transactions` abgleichen. Am 2026-08-28 wurden 24 Buchungen fälschlich als
  „abgebucht ohne Ergebnis" gemeldet — die Bilder existierten, sie stammten nur aus
  einer parallelen Session.

---

## 9. QC vor dem Upload — Pflicht

Jede gerenderte Ad **ansehen**, bevor sie nach Drive geht. Geprüft wird:

- [ ] Alle Wörter korrekt und vollständig geschrieben (kein Buchstabensalat)
- [ ] Alle Akzente / Umlaute vorhanden
- [ ] Keine Wörter der falschen Sprache übrig
- [ ] Markenname auf der Tube korrekt
- [ ] Siegeltext korrekt, kein erfundenes Wort
- [ ] Seitenverhältnis wie die Quell-Ad
- [ ] Bei Ads ohne Produkt: kein Produkt eingefügt

Erst danach hochladen. Eine unbrauchbare Ad in Drive ist schlimmer als eine fehlende —
sie wird versehentlich ausgespielt.

---

## 10. Drive: Berechtigungen beim Aufräumen

- Der Service-Account kann **Bytes überschreiben** (`files.update media`), aber
  **keine User-Dateien löschen** → `403 insufficientFilePermissions`.
- Zum Löschen/Verschieben in den Papierkorb die Drive-Verbindung des Nutzers nutzen
  (`Google_Drive.trash_file`).
- Beim Ersetzen fehlerhafter Ads: bestehende Datei-IDs mit den neuen Bytes
  überschreiben statt neue Dateien anzulegen — dann bleiben Links und Sheet-Verweise
  gültig. Nur überzählige Dateien in den Papierkorb.
- Falsche Ads **nicht liegen lassen**: sie werden sonst versehentlich verwendet.
