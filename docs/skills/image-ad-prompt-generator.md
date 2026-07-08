# image-ad-prompt-generator — Translation Mode

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
2. **Produktname ersetzen**: der Produktname in der Quell-Anzeige wird durch den exakten,
   hinterlegten Produktnamen ersetzt — inklusive ®/™-Zeichen, exakte Schreibweise wie in
   `config/automation.config.json` → `product.exact_name`.
3. **Produktbild ersetzen**: das im Quellbild gezeigte Produkt wird durch das hinterlegte
   Produktbild (`product.product_image_drive_file_id`) ersetzt. Maßstab, Blickwinkel und
   Lichtstimmung werden an die Quell-Szene angepasst, damit es nicht wie eine Collage
   wirkt. **Ausnahme**: zeigt die Quell-Anzeige gar kein Produkt, wird auch keins
   eingefügt.

## Output pro Batch (pro Sprache/Markt)

- Eine gemeinsame übersetzte **Headline**
- Ein gemeinsamer übersetzter **Primary Text**
- Der eine **Batch-Prompt**, der auf alle Quell-Anzeigen dieses Laufs angewendet wird

Diese drei Artefakte werden pro Zielmarkt in
`<Projektordner>/translated-ads/<market_code>/<Lauf-Datum>.md` in Drive abgelegt, plus
die Liste der verarbeiteten Quell-Anzeigen-Links, gegen die der Batch-Prompt läuft.

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

Platzhalter werden pro Zielmarkt aus `config/automation.config.json` und den in Schritt 2
gesammelten Ad-Links befüllt (siehe `docs/workflow.md`).
