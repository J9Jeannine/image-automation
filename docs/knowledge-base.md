# Knowledge Base — gesicherte Erkenntnisse (Stand: 2026-07-24)

Diese Datei hält fest, was in echten Läufen gelernt wurde, damit spätere Läufe es
**nicht wieder vergessen**. Ergänzt `docs/workflow.md` (Ablauf) und `STATUS.md`
(offene Infrastruktur-Punkte). Bei Konflikt gilt die jeweils spezifischere Angabe hier.

---

## 1. Bildquellen für die Ads — was funktioniert und was nicht

Reihenfolge, in der eine Ad-Quelle zu beschaffen ist:

1. **Zuerst: Higgsfield-Verlauf („Claudes Gedächtnis").** Viele Ads wurden in früheren
   Läufen bereits erzeugt oder als Quell-Bild hochgeladen. **Immer zuerst dort suchen**,
   bevor irgendein externer Link probiert wird:
   - `Higgsfield.show_generations` → alle gerenderten Ergebnis-Bilder inkl. Prompt,
     Zielsprache, `input_images` (Quell-Media) und Ergebnis-CDN-URL
     (`d8j0ntlcm91z4.cloudfront.net`, langlebig).
   - `Higgsfield.show_medias` → alle hochgeladenen Quell-Bilder
     (`d2ol7oe51mr4n9.cloudfront.net`, langlebig).
   - Beide CDN-Domains sind **dauerhaft** per curl erreichbar (nicht signiert/ablaufend).
   - So lassen sich fertige Ads und Quell-Bilder ohne die Meta-Links wiederherstellen.
2. **Direkte `fbcdn.net`-Bildlinks** aus dem M-Kommentar-Thread: funktionieren per curl,
   **aber die signierten Tokens laufen nach wenigen Tagen ab** (`oe=…`-Parameter). Ältere
   als ~3–5 Tage liefern HTTP 403 „URL signature expired". Nur frisch gepostete Links
   ziehen.
3. **`facebook.com/ads/library/?id=…`-Permalink:** In dieser Sandbox **hart blockiert**
   (HTTP 403 vom Proxy, mehrfach bestätigt — auch am 2026-07-24). Die Seite lässt sich
   NICHT laden, also kann die dahinterliegende fbcdn-URL darüber **nicht** aufgelöst
   werden. Der Wunsch „zieh es doch vom normalen Ad-Link, der bleibt länger gültig"
   ist technisch nachvollziehbar, scheitert hier aber an der Netzwerk-Policy.
4. **Wenn 1–3 alle scheitern:** den Nutzer um frische `fbcdn.net`-Direktlinks bitten
   (Browser: Rechtsklick auf die Anzeige → „Bildadresse kopieren"), am besten direkt als
   Reply im M-Kommentar. Nicht stumm überspringen.

## 2. Auch Ads OHNE Text/Produkt einmal durch Higgsfield laufen lassen

**Korrektur zur früheren Annahme** (Nutzerin, 2026-07-24): Ads, die kein Produkt und
keinen Overlay-Text zeigen (z. B. reine Lifestyle-/Foto-Ads), werden **trotzdem einmal
durch Higgsfield laufen gelassen** (1:1-Reproduktion der Quell-Ad, gleiches
Seitenverhältnis) und als Datei im Ordner gespeichert — sie werden **nicht** nur als
Pass-Through/Copy-only behandelt. Ziel: jede der N Ads einer Zeile liegt am Ende als
eigenes Bild im Render-Ordner, egal ob Text drauf ist oder nicht. Für solche Bilder
gilt weiterhin: nichts Visuelles verändern, kein Produkt einfügen, nur ggf. vorhandenen
Text übersetzen.

## 3. Sprache: natürliches Muttersprachler-Niveau

Finnisch (FI) und Quebec-Französisch (FRCA) müssen **idiomatisch und natürlich** klingen,
wie von einer/einem Muttersprachler:in geschrieben — **nicht** wörtlich/gestelzt und
**nicht** Frankreich-Französisch für FRCA. Beispiel Quebec statt Frankreich:
„Les résultats, ça parle tout seul." / „Plus de 9 000 gars l'ont essayé." /
„Vérifie si c'est disponible" (umgangssprachlicher Quebec-Register).

## 4. Bild-Dateien in Google Drive ablegen — harte Grenzen

- **Service Account kann KEINE Datei-Bytes hochladen.** Google: „Service Accounts do not
  have storage quota." Er kann nur Ordner anlegen (kostet keinen Speicher) und ins Sheet
  schreiben (das Sheet gehört der Nutzerin). Ein SA-Upload scheitert mit HTTP 403
  `storageQuotaExceeded`.
- **Kein Shared Drive möglich:** ein privates Gmail-Konto (jeannine.thiry1@gmail.com)
  kann keine Shared Drives anlegen — dort dürfte der SA sonst hochladen.
- **MCP `Google_Drive.create_file`** lädt als die Nutzerin (mit Speicher) hoch, braucht
  den Inhalt aber als **Base64 durch den Modell-Kontext**. Schon ~46 KB Base64 reißen
  beim Einlesen ab/verfälschen → für ~1-MB-Bilder unbrauchbar. Deshalb sind die bereits
  in Drive liegenden Ad-Bilder (z. B. `atriso_FI_ad1.jpg`) auch **owner =
  jeannine.thiry1** — sie kamen über ihren Login rein, nicht über die Automatik.
- **Konsequenz / aktueller Workaround:** gerenderte Bilder per `SendUserFile` direkt an
  die Nutzerin schicken (volle Qualität), sie zieht sie in den passenden Render-Ordner.
- **Echte Automatik-Lösung (offen):** ein **User-OAuth-Refresh-Token** von
  jeannine.thiry1 (Scope `drive.file`/`drive`) als Env-Secret hinterlegen; dann lädt ein
  Skript als die Nutzerin hoch (mit Quota), ohne Kontext-Umweg. Siehe `STATUS.md`.

## 5. Rückschreiben in Spalte O — funktioniert (Service Account)

- Der SA schreibt **direkt in Sheet-Zellen** (Google Sheets API v4,
  `spreadsheets.values.update`, `valueInputOption=USER_ENTERED`). Das Sheet ist mit der
  SA-E-Mail als Bearbeiter geteilt, Sheets API im Cloud-Projekt aktiviert.
- **Zell-Format wie die bestehenden Zeilen:**
  `=HYPERLINK("<Produkt-Ordner-URL>";"<Produktname aus Spalte G>")` → Produktname als
  klickbarer Text.
- **EU-Locale:** Formel-Argumente mit **Semikolon** (`;`) trennen, nicht Komma — sonst
  `#ERROR!`.
- Spalte O = „[merged] Link to Videos /Images". Ziel ist der **Produkt-Ordner**
  (`<market>/<product>/`), nicht der datierte Unterordner.
- Service-Account-E-Mail:
  `image-automation-uploader@image-automation-502115.iam.gserviceaccount.com`
  (Credentials in Env-Var `GOOGLE_SERVICE_ACCOUNT_JSON`).

## 6. Drive-Ordnerstruktur (in der Praxis bestätigt)

```
<Basis-Ordner>/
  FI/            (id 1XFYmVz3Rh8_KrXa7y891l1Hq3k-E2i07)
    atriso/      (id 1Hn8rnMd6pzoy5IsRxMGPGOvI88Wbxs2b)   <- O54 verlinkt hierauf
      2026-07-23 – Käännetyt mainokset (FI)/  <- nur die Ad-Bilder
    Erelso/      (id 1SwJ0_PA2J6WP5t2Pnc9xo3xLc7L-m0zB)   <- O53 verlinkt hierauf
      2026-07-24 – Käännetyt mainokset (FI)/
    State/processed_comments.json
  FRCA/          (id 125edRJ4kkWee_uv8z8YB1n8qsPTnrwN3)
    Erelso/      (id 1N_sgJ2C9yQwd92OVl7T01ItHYAVcUZ1k)   <- O34 verlinkt hierauf
      2026-07-24 – Publicités traduites (FRCA)/
    vanix/       (id 1rfJsYTGffcJv1PJ13araq4CgNYACJPZ6)
    State/processed_comments.json
```
- **Keine** extra Markdown-/Status-Dokumente in die Render-Ordner (Wunsch Nutzerin
  2026-07-24, alte `*-status.md` wurden gelöscht). Nur die Bild-Dateien.

## 7. Asset-Inventar Higgsfield (Erelso) — Job-IDs / CDN-URLs

Produktbild (Tube „Erelso", einmalig, für FI+FRCA):
`hf_20260710_073329_2abfbb44-…png` (Job 2abfbb44). Neuere Variante 2026-07-17:
`hf_20260717_050542_c82f53ea-…png`.

**Ads 1–3 fertig gerendert (mit Produkt/Text), beide Sprachen:**

| Ad | Motiv | FI (Job) | FRCA/Quebec (Job) |
|----|-------|----------|-------------------|
| 1 | Messband „+10cm" | 089129b6 (`hf_20260710_090620`) | a67ac26c (`hf_20260710_090710`) |
| 2 | Schlafzimmer Tube+Box | 18538532 (`hf_20260710_090639`) | 4ebca2b2 (`hf_20260710_090723`) |
| 3 | Dunkle Studio-Tube | d6369ce8 (`hf_20260710_090652`) | 4200bdf4 (`hf_20260710_090731`) |

Alle unter `https://d8j0ntlcm91z4.cloudfront.net/user_3BikzXfO56jaRWNREGlTan8aoyf/<name>.png`.

**Ads 4–7 (Fingerspitze orange, Fingerspitze schwarz, Paar im Bett, Banane):** zeigen
kein Produkt/Text. **Nicht** in Higgsfield (weder Render noch Quell-Media). Quell-IDs im
M53-Thread: 712684109, 711474750, 701496000, 699738349 — fbcdn-Links **abgelaufen (403)**.
→ Müssen laut Abschnitt 2 einmal durch Higgsfield laufen und gespeichert werden, **sobald
frische fbcdn-Quelllinks vorliegen** (Nutzerin posten lassen; FB-Permalink ist blockiert).

Übersetzte FB-Copy (Primary Text) für Ads 4–7 liegt in den früheren Drive-Docs
(`2026-07-11-erelso-fi`) und ist bei Bedarf ins Quebec-Französische zu übertragen.

## 8. Bearbeitungsstand pro Zeile (2026-07-24)

- **FI Zeile 54 „atriso":** 5 Ads gerendert (2026-07-22), O54 verlinkt. Bilder liegen in Drive.
- **FI Zeile 53 „Erelso":** Ads 1–3 gerendert (FI), an Nutzerin geschickt; O53 verlinkt.
  Ads 4–7 offen (Quellen abgelaufen).
- **FI Zeile 52 „vanix":** Ads gerendert (2026-07-09/11); Rest blockiert (Permalinks).
- **FRCA Zeile 34 „Erelso":** Ads 1–3 gerendert (Quebec), an Nutzerin geschickt; O34
  verlinkt. Ads 4–7 offen (Quellen abgelaufen).
- **FRCA Zeile 33 „vanix":** blockiert (nur facebook.com-Permalinks im Thread).
