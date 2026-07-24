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

## 3b. Ad-Lokalisierung = UMBRANDEN + Übersetzen (nicht nur übersetzen)

**Bestätigt 2026-07-24 an Erelso.** Die Quell-Ads stammen vom Competitor (Spalte D),
dessen Marke auf Tube/Box/Badge steht — bei Erelso: **„PrimeErect"**. Die fertigen Ads
müssen **unser** Produkt zeigen: der Markenname wird im Bild auf den Produktnamen aus
**Spalte G** umgeschrieben (**„Erelso"**), das Motiv/Layout bleibt sonst identisch.
Es ist also **nicht** reine Text-Übersetzung, sondern Umbranden PLUS ggf. Übersetzung.

- Beleg: die ältere `erelso ad.png` (FI) zeigt bereits „Erelso" auf der Tube (umgebrandet
  von PrimeErect), mit finnischem Text — d. h. der Umbrand-Schritt gehört fest dazu.
- **Umsetzung, die zuverlässig funktioniert:** Quell-Bild per `media_import_url` in
  Higgsfield importieren, dann `generate_image` mit `model: nano_banana_pro` (läuft als
  `nano_banana_2`), `medias:[{value: <media_id>, role:"image"}]`, exaktes Seitenverhältnis
  (1:1 bzw. 4:5), und einem **chirurgischen Prompt**: „Edit this image, single change:
  replace the brand name 'PrimeErect'/'PRIME' with 'Erelso'/'ERELSO' in the same font/
  colour/position; keep EVERYTHING else pixel-identical; do not change/re-spell/move any
  [Sprache]-text; preserve the N:M framing." → hält Layout und Copy sauber, nur die Marke
  wechselt. Ergebnis-Auflösung 1024 px (bzw. 928×1152 bei 4:5).
- **Ads ohne Marke** (z. B. der Raketen-Cartoon, Ad 5) brauchen keinen Umbrand; ist die
  Copy sprachlich schon korrekt (natürliches Quebec-/Finnisch), das scharfe Quell-Bild
  **behalten** statt neu zu rendern (nano_banana kann sonst Text/Zeichnung verschlechtern).

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
- **MCP-Base64-Upload ist UNZUVERLÄSSIG (empirisch bestätigt 2026-07-24).** Der einzige
  User-Upload-Weg (`create_file` mit `base64Content`) erzwingt, dass das Modell den
  kompletten Base64-String im Tool-Aufruf reproduziert. Getestet:
  - ~400 px / ~25k Base64: ging vereinzelt (byte-genau, fileSize stimmte).
  - ~512 px / ~29k Base64: **abgeschnitten** → korrupte Datei (13k statt 22k).
  - Selbst ~16–19k Base64 schlug mal fehl („not a valid base64 string" bzw. falsche
    fileSize) durch Transkriptionsfehler. **Keine Größe ist verlässlich** — jeder Upload
    ist ein Glücksspiel, und Fehler erzeugen korrupte Dateien.
  - **Löschen unmöglich:** Es gibt kein Drive-Lösch-Tool im MCP, und der Service Account
    darf user-eigene Dateien nicht löschen (403). Korrupte Uploads bleiben also liegen,
    bis die Nutzerin sie manuell entfernt.
  - **Fazit:** Base64-Upload NICHT als Standardweg verwenden. Immer `fileSize` der
    Antwort gegen die Quellgröße prüfen; bei Abweichung ist die Datei kaputt.
- **Zuverlässiger Workaround (aktuell):** gerenderte Bilder per `SendUserFile` in voller
  Qualität an die Nutzerin schicken, sie zieht sie in den Render-Ordner (ein Drag pro
  Ordner). 100 % zuverlässig, verlustfrei.
- **Kein Google-Token in der Umgebung nutzbar (geprüft 2026-07-24):** `CLOUDSDK_AUTH_
  ACCESS_TOKEN` ist ein Proxy-Token und liefert bei der Drive-API `401 Invalid
  Credentials` / `tokeninfo: Invalid Value` — also KEIN Drive-Zugriff. Es gibt in der
  Session keinen fertigen User-Drive-Token; er muss aktiv eingerichtet werden.
- **Echte Automatik-Lösung (SKRIPTE LIEGEN BEREIT, EMPFOHLEN):** ein **User-OAuth-
  Refresh-Token** von jeannine.thiry1 (Scope `drive.file`) als Env-Secret hinterlegen;
  dann lädt ein Python-Skript als die Nutzerin server-seitig von der Higgsfield-CDN-URL
  direkt in den Zielordner hoch (mit Quota, byte-genau, kein Kontext-Umweg, löschbar).
  Einzige saubere Dauerlösung. **Fertig implementiert:**
  - `scripts/get_drive_refresh_token.py` — einmalig lokal ausführen, erzeugt den
    Refresh-Token (Desktop-OAuth-Client aus derselben Cloud-Konsole, Loopback-Flow).
  - `scripts/upload_cdn_to_drive.py` — `<quelle-url-oder-pfad> <folder_id> [name]`,
    lädt hoch und **verifiziert die Byte-Größe** gegen die Quelle.
  - Env-Secrets: `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`,
    `GOOGLE_OAUTH_REFRESH_TOKEN`. Details/Setup: `docs/oauth-drive-upload.md`.
  Solange diese Secrets fehlen, bleibt `SendUserFile` + Drag der Zwischenweg.

## 4b. „Wie kamen die atriso-Bilder automatisch in Drive?" — untersucht 2026-07-24

Die Nutzerin war sicher, dass die atriso-Ads **automatisch** in den Drive-Ordner kamen,
und bat, „diesen Weg" zu dokumentieren. Untersuchung ergab:

- `FI/atriso/2026-07-23 – …/` enthält `atriso_FI_ad1..5.jpg` mit **110–166 KB**
  (volle Qualität), owner `jeannine.thiry1`, erstellt **2026-07-23 21:08**.
- Diese Session lief komplett am **2026-07-24**; der atriso-Upload passierte in einer
  **früheren Session**, deren Transkript hier nicht mehr vorliegt.
- In den vorhandenen Transkripten: **0** `copy_file`-Aufrufe, **kein** `create_file` für
  eine atriso-Datei. Die einzigen `create_file`-Uploads waren erelso, alle klein
  (16–25k Base64) — mehrere davon korrupt.
- 110–166 KB ⇒ ~175k Zeichen Base64 ⇒ über `create_file` **unmöglich** (der Kanal
  verfälscht schon ab ~17k).

**Schlussfolgerung (ehrlich):** Es gibt in der aktuellen Toolbox **keinen** Weg, der
volle-Qualität-Bilder automatisch in ein privates Gmail-Drive lädt. Gäbe es ihn, wäre er
bei erelso benutzt worden statt des Base64-Kampfs. Die vollauflösenden atriso-Dateien
kamen über den **eigenen Drive-Login der Nutzerin (Drag-Drop)** rein — dasselbe, was sie
für erelso ebenfalls selbst getan hat. **Kein wiederholbarer Auto-Weg aus atriso** —
nicht erneut danach suchen.

**Der einzige echte Auto-Weg = OAuth-Uploader** (`scripts/upload_cdn_to_drive.py`,
Abschnitt 4). Sobald die drei `GOOGLE_OAUTH_*`-Secrets gesetzt sind, lädt er jede Ad
direkt von der Higgsfield-CDN in den datierten Zielordner — volle Qualität, byte-genau,
kein Drag. **Das** ist „der Weg", der in Zukunft immer genutzt wird.

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

**FRCA „mit Text"-Set, neu gerendert 2026-07-24** (Quelle: frische fbcdn-Links der
Nutzerin; Marke PrimeErect→Erelso umgebrandet, Quebec-Französisch geprüft, per
`nano_banana_2` editiert). Diese fünf sind der aktuelle FRCA-Erelso-Deliverable:

| Ad | Motiv | AR | Job / Ergebnis-Datei |
|----|-------|----|----------------------|
| 1 | Messband „+10cm", Headline „Les Résultats Parlent D'eux-Mêmes." | 1:1 | 868659ec (`hf_20260724_115332`) |
| 2 | Schlafzimmer, Tube+Box, „…tout a changé." | 1:1 | 30ac5b46 (`hf_20260724_115349`) |
| 3 | Urologe/Klemmbrett, „Recommandé Par Des Urologues." | 1:1 | 95243f1a (`hf_20260724_115354`) |
| 4 | Dunkle Tube, Badge „ERELSO…RESTORATION", „CE TUBE NOIR…" | 4:5 | 806ecdeb (`hf_20260724_115357`) |
| 5 | Raketen-Cartoon „UNE SENSATION DIFFÉRENTE…" (keine Marke) | 1:1 | **kein Render** — scharfes Quell-JPEG behalten (fbcdn) |

Alle Renders unter `https://d8j0ntlcm91z4.cloudfront.net/user_3BikzXfO56jaRWNREGlTan8aoyf/<name>.png`.
An die Nutzerin per `SendUserFile` in voller Auflösung geschickt (Drag in den
FRCA/Erelso-Unterordner `2026-07-24 – Publicités traduites (FRCA)`), da Auto-Upload noch
blockiert ist (siehe Abschnitt 4). Sobald die OAuth-Secrets gesetzt sind, kann
`scripts/upload_cdn_to_drive.py <CDN-URL> 1QWpjnBxGIxSbIUlWm31MHi_myUXVN8Og` sie direkt
ablegen.

## 8. Bearbeitungsstand pro Zeile (2026-07-24)

- **FI Zeile 54 „atriso":** 5 Ads gerendert (2026-07-22), O54 verlinkt. Bilder liegen in Drive.
- **FI Zeile 53 „Erelso":** Ads 1–3 gerendert (FI), an Nutzerin geschickt; O53 verlinkt.
  Ads 4–7 offen (Quellen abgelaufen).
- **FI Zeile 52 „vanix":** Ads gerendert (2026-07-09/11); Rest blockiert (Permalinks).
- **FRCA Zeile 34 „Erelso":** „mit Text"-Set (5 Ads) am 2026-07-24 neu aus frischen
  fbcdn-Links gerendert (PrimeErect→Erelso, Quebec-FR), an Nutzerin geschickt; O34
  verlinkt. Die Foto-Ads (`erelso ad 5/6/7.jpg`) hat die Nutzerin selbst in den
  Unterordner `2026-07-24 – Publicités traduites (FRCA)` gelegt. **Hinweis:** in diesem
  Ordner liegt fälschlich `erelso ad.png` mit **finnischem** Text (FI-Version, gehört
  nach FI) — bei Gelegenheit bereinigen.
- **FRCA Zeile 33 „vanix":** blockiert (nur facebook.com-Permalinks im Thread).
