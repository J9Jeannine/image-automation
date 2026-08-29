# image-ad-prompt-generator — Translation Mode

**Hinweis:** Dies ist nur eine Referenz-Zusammenfassung. Die eigentliche Ausführung soll
den echten, im Account aktivierten Skill `image-ad-prompt-generator` per `Skill`-Tool
aufrufen (siehe `docs/workflow.md` Schritt 5) — diese Datei dient nur als Fallback, falls
der Skill in der ausführenden Session einmal nicht verfügbar ist, und wird nur für
Übersetzungen genutzt, nie für Varianten/Iterationen/New Concepts.

> **Auch im Fallback gilt `docs/language-rules.md` uneingeschränkt und zuerst.** Der
> Batch-Prompt weiter unten ist bewusst umgebaut: **das Bildmodell übersetzt hier
> nirgends mehr selbst** — der Text steht vorher fest (LOCKED STRING) und wird nur noch
> abgemalt. `FRCA` = Québec-Französisch mit `tu`-Anrede, nie Frankreich-Französisch,
> nie `SOLDES`. `FI` = natürliches Finnisch, keine erfundenen Komposita.

1:1 übernommene Regeln aus der bestehenden Skill-Logik, angewendet auf Konkurrenz-Anzeigen
aus der Meta Ad Library.

## Grundprinzip

Ein einziger, wiederverwendbarer **Batch-Prompt pro Sprache/Markt** — kein individueller
Prompt pro Einzelanzeige. Der Batch-Prompt wird auf jede gesammelte Quell-Anzeige
angewendet.

## Was beibehalten wird (nicht neu gestalten)

- Layout der Quell-Anzeige
- Gesichter / Personen in der Anzeige
- Szene / Hintergrund / Setting
- Farbpalette

## Was verändert wird

1. **LOCKED STRING zuerst, dann erst der Prompt**: sämtlicher Text, der auf dem Bild
   liegen soll, wird VOR dem Bildprompt vollständig in der Zielsprache ausformuliert
   (natürlich, idiomatisch, wie von einem Muttersprachler getextet — `FRCA` = Québec,
   `FI` = natürliches Finnisch, siehe `docs/language-rules.md` Abschnitt 4) und in
   `<product>_<market>_ad_copy.md` als LOCKED STRING festgehalten. Max. 6 Wörter pro
   Textelement. **Der Bildprompt bekommt diesen fertigen Text nur noch zum Abmalen —
   er übersetzt nichts mehr selbst.**
2. **Produktname ersetzen**: der Produktname in der Quell-Anzeige wird durch den exakten
   Produktnamen aus Spalte G des Funnel Sheets ("new PR NAME") ersetzt — inklusive
   ®/™-Zeichen, exakte Schreibweise wie im Sheet.
3. **Produktbild ersetzen**: das im Quellbild gezeigte Produkt wird durch das
   Produktbild-Referenzfoto ersetzt, das per Screenshot von der Competitor-Funnel-Seite
   (Spalte D, siehe `docs/workflow.md` Schritt 3) entnommen wurde. Visuell bleibt es wie
   beim Competitor — es wird **nicht** neu fotografiert oder aus einer eigenen
   Produktdatenbank ersetzt, nur der Name/Text darauf ändert sich. Maßstab, Blickwinkel
   und Lichtstimmung an die Quell-Szene der Ad anpassen, damit es nicht wie eine Collage
   wirkt. **Ausnahme**: zeigt die Quell-Anzeige gar kein Produkt, wird auch keins
   eingefügt.

## Output pro Batch (pro Sprache/Markt)

- Eine gemeinsame übersetzte **Headline**
- Ein gemeinsamer übersetzter **Primary Text**
- Der eine **Batch-Prompt**, der auf alle Quell-Anzeigen dieses Laufs angewendet wird

Diese drei Artefakte werden pro Zeile/Produkt in
`<Projektordner>/<market_code>/translated-ads/<product_name>/<Lauf-Datum>.md` in Drive
abgelegt, plus die Liste der verarbeiteten Quell-Anzeigen-Permalinks, gegen die der
Batch-Prompt läuft.

## Batch-Prompt-Vorlage

```
SOURCE AD REFERENCE: {source_ad_image_or_video_url}
PRODUCT REFERENCE IMAGE: {product_image_reference}
LOCKED TEXT (already final, target-market language, written before this prompt): {locked_string}

Keep the exact layout, faces, scene, and color palette of the source ad. Do not
redesign the composition.

Render the LOCKED TEXT above EXACTLY as written, character for character, including
every accent and special character. Do NOT translate it. Do NOT rephrase it. Do NOT
correct it. Do NOT add any other words, labels, packaging text, price tags, or
background signage. The image must contain no text other than the LOCKED TEXT above.
Ignore all text visible in the source ad reference — it is a layout/visual reference
only, never a text source.

Replace every occurrence of the competitor product name with "{exact_product_name}"
(preserve ®/™ exactly as given) — this exact string is also part of the LOCKED TEXT
above, never left to the model to translate or restyle.

If the source ad shows a product, replace it with the reference product image, matching
scale, camera angle, and lighting of the original scene. If the source ad shows no
product, do not add one.

Output: a photorealistic ad image ready for {target_market}.
```

Vor dem Upload: jedes Ergebnisbild einzeln mit dem `Read`-Tool ansehen, jedes sichtbare
Wort abtippen und gegen `{locked_string}` diffen (Details: `docs/language-rules.md`
Abschnitt 5). Abweichung = nicht hochladen, mit gekürztem LOCKED TEXT neu generieren.

Platzhalter werden pro Zeile aus `config/automation.config.json` (Zielsprache je Tab,
inkl. `language_rules.<market_code>`), Spalte G (Produktname), dem LOCKED STRING aus
Schritt 1 oben, und den in `docs/workflow.md` Schritt 3/4 gesammelten Ad-Referenzen und
Produktbild-Screenshot befüllt.
