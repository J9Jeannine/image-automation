# image-ad-prompt-generator — Translation Mode

**Hinweis:** Dies ist nur eine Referenz-Zusammenfassung. Die eigentliche Ausführung soll
den echten, im Account aktivierten Skill `image-ad-prompt-generator` per `Skill`-Tool
aufrufen (siehe `docs/workflow.md` Schritt 5) — diese Datei dient nur als Fallback, falls
der Skill in der ausführenden Session einmal nicht verfügbar ist, und wird nur für
Übersetzungen genutzt, nie für Varianten/Iterationen/New Concepts.

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

1. **Overlay-Text übersetzen**: sämtlicher Text, der auf dem Bild liegt, wird idiomatisch
   in die Zielsprache übersetzt — keine wörtliche Übersetzung. Muss klingen, als wäre er
   original in der Zielsprache getextet.
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

Keep the exact layout, faces, scene, and color palette of the source ad. Do not
redesign the composition.

Replace all on-image overlay text with an idiomatic (not literal) {target_language}
translation. It must read as if a native {target_market} copywriter wrote it from
scratch.

Replace every occurrence of the competitor product name with "{exact_product_name}"
(preserve ®/™ exactly as given).

If the source ad shows a product, replace it with the reference product image, matching
scale, camera angle, and lighting of the original scene. If the source ad shows no
product, do not add one.

Output: a photorealistic ad image ready for {target_market}.
```

Platzhalter werden pro Zeile aus `config/automation.config.json` (Zielsprache je Tab),
Spalte G (Produktname) und den in `docs/workflow.md` Schritt 3/4 gesammelten
Ad-Referenzen und Produktbild-Screenshot befüllt.
