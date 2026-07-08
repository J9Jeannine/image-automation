# foundation-to-higgsfield — Foundation-Dokumente & wöchentliche Ad-Produktion

Optionale Phase 2 dieser Automatisierung (siehe `foundation_phase.mode` in der Config).
Nur relevant, wenn `mode` `combined` oder `foundation_once_then_weekly_json` ist.

## Foundation-Set (pro Produkt, i.d.R. einmalig gepflegt)

- **Research Doc** — Markt-/Zielgruppenrecherche
- **Avatar Sheet** — Zielgruppen-Personas
- **Offer Brief** — Angebot, Preis, Guarantee, USPs
- **Necessary Beliefs** — Überzeugungen, die die Anzeige beim Betrachter erzeugen muss
- **Swipe File** — Sammlung bewährter Referenz-Ads/Hooks

IDs/Links dieser Dokumente liegen in `config/automation.config.json` →
`foundation_documents`. Existiert ein Dokument nicht, wird der entsprechende Kontext beim
Prompt-Bau schlicht weggelassen (kein Blocker).

## Wöchentliche Produktion

Pro Lauf (bei `mode: combined` oder `foundation_once_then_weekly_json`) werden aus dem
Foundation-Set **60 Higgsfield-JSON-Konfigurationen** erzeugt, aufgeteilt:

- **48 (80%) neue Konzepte** — frisch aus Research Doc / Avatar Sheet / Necessary
  Beliefs / Offer Brief abgeleitet, keine Wiederholung bereits produzierter Konzepte
  (Abgleich gegen vorherige Läufe in `<Projektordner>/higgsfield-json/`).
- **12 (20%) Iterationen aus Top-Performern** — Variationen (Hook, Winkel, Farbschema,
  Call-to-Action) der laut Swipe File / bisherigen Performance-Daten stärksten
  bestehenden Ads.

## Output

Eine JSON-Datei pro Lauf in `<Projektordner>/higgsfield-json/<Lauf-Datum>.json` mit dem
Schema:

```json
{
  "run_date": "YYYY-MM-DD",
  "product": "TODO",
  "concepts": [
    {
      "id": "new-01",
      "type": "new_concept",
      "hook": "...",
      "prompt": "...",
      "model": "nano_banana_pro",
      "aspect_ratio": "4:5",
      "reference_images": ["..."]
    },
    {
      "id": "iter-01",
      "type": "top_performer_iteration",
      "based_on": "<Referenz auf Original-Ad>",
      "prompt": "...",
      "model": "nano_banana_pro",
      "aspect_ratio": "4:5",
      "reference_images": ["..."]
    }
  ]
}
```

Rendering erfolgt nur, wenn ein Higgsfield-MCP-Tool in der ausführenden Session
verfügbar ist (siehe `docs/workflow.md`, Schritt 7); sonst bleibt es bei den
JSON-Configs/Prompt-Texten.
