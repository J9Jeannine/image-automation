# Status & offene Punkte (Stand: 2026-08-03)

Diese Datei fasst zusammen, was funktioniert, was blockiert ist, und was der Nutzer
konkret tun muss, damit die Pipeline vollständig automatisch läuft. Ziel: alles an
einem Ort nachlesbar, statt über den Chat-Verlauf verstreut.

## 0. Lauf vom 2026-08-03 — zwei harte Blocker (beide verifiziert)

### 0.1 Higgsfield hat 0 Credits — kein einziges Bild rendert

`Higgsfield.balance` → `{"credits": 0, "subscription_plan_type": "starter"}`.
`list_workspaces` zeigt genau **einen** Workspace (`a071cd78-3771-457f-b554-2d6f503190c0`,
starter, 0 Credits) — kein Ausweich-Workspace. `models_explore` → `unlim.available: false`,
`trial_status.eligible: false`. Jede Generierung endet mit
`Error starting generation: Out of credits in the selected workspace.`

Kosten-Preflight (`get_cost: true`, `nano_banana_pro`, 1:1, 1k): **2 Credits pro Render**.
Ein voller Smokola-Lauf (1 Produkt-Asset + 16 Ads) braucht **~34 Credits**.

Folge: 0 von 17 Generierungen im 2026-08-03-Lauf. Kein Prompt-, Format- oder
Content-Filter-Problem — alles Upstream ist fertig und auf Higgsfield gecacht
(9 Assets hochgeladen, `status: uploaded`, Produkt-Ref `media_id`
`86fa5829-70b8-4eb3-8f8b-44ad0fd4348d`). Nach Credit-Top-up ist der Re-Run reine
Wiederholung ohne Neuanalyse.

### 0.2 Bild-Upload nach Drive: der Weg von 2026-07-26 ist zu, MCP-Weg nur für Winzdateien

Drei Wege getestet, Ergebnis eindeutig:

| Weg | Ergebnis |
| --- | --- |
| Service Account (`GOOGLE_SERVICE_ACCOUNT_JSON`) | **Strukturell unmöglich.** `403 storageQuotaExceeded`. SA hat `canAddChildren: true` auf den Zielordnern, aber Google gibt Service Accounts null Speicherkontingent, und die Ordner liegen in My Drive: `drives().list()` → `{"drives": []}`, kein Shared Drive. Nicht durch Retry/Flags umgehbar. |
| OAuth-User-Token (`GOOGLE_OAUTH_REFRESH_TOKEN`) | **Aktuell ungültig.** `{"error": "invalid_grant"}` an `oauth2.googleapis.com/token` *und* `accounts.google.com/o/oauth2/token`, auch mit `.strip()`-bereinigten Werten. Token-Format korrekt (`1//04…`, 103 Zeichen). Muss einmal neu autorisiert werden. **Das war der Weg, mit dem der 2026-07-26-Lauf die 18 Bilder byte-genau ablegte** — erkennbar daran, dass die Dateien `jeannine.thiry1@gmail.com` gehören und nicht dem SA. Die Notiz im FRCA-State-File, das sei der Service Account gewesen, ist falsch. |
| Drive-MCP `create_file` + `base64Content` | **Funktioniert, aber nur bis ~5 KB Base64.** Verifiziert an einer 1.521-Byte-PNG: lokal und remote md5 `fb8a37bba25da5cf50f195ca90c13fc1`, `mimeType: image/png` (mit `disableConversionToGoogleType: true`), byte-identisch. |

**Wichtigster neuer Befund — die Fehlerart bei zu großem Base64:**
Ein 26.985-Byte-PNG (35.980 Zeichen Base64) kam als **3.631 Byte** an, md5 abweichend,
Datei unlesbar (`OSError: unrecognized data stream contents`). Die Ursache ist **nicht**
Bit-Flipping, sondern **stille Kürzung**: die Mitte des Base64-Strings wird ausgelassen,
Kopf und ein syntaktisch gültiger PNG-Schwanz bleiben stehen. Das Ergebnis sieht wie ein
wohlgeformter Base64-String aus und wirft keinen Fehler — der Schaden fällt erst beim
Checksummen-Vergleich auf.

Gemessene Grenzen (Heredoc → `base64 -d` → md5, ohne Drive):
2.028 Zeichen ✅ · 5.048 Zeichen ✅ · 35.980 Zeichen ❌ (gekürzt).
**Regel: jeder Base64-Upload MUSS danach per `md5Checksum` gegen die lokale Datei geprüft
werden.** Fehler sind sonst unsichtbar.

Für echte Ad-Creatives (1–1,5 MB ⇒ 1,4–2,0 Mio. Zeichen Base64) ist der MCP-Weg damit
**nicht** nutzbar; der Server bietet keine Chunk-/Append-/Update-Methode
(nur create/copy/read/download/search/metadata/permissions). Runterskalieren hilft nicht:
unter ~5 KB Base64 bleibt ein 96×96-Thumbnail übrig.

**Die einzigen zwei tragfähigen Lösungen für die 16 Bilder:**
1. OAuth-Refresh-Token neu autorisieren (stellt exakt den 26.07.-Weg wieder her), **oder**
2. Zielordner in ein **Shared Drive** verschieben — dann greift die
   SA-Speicherkontingent-Grenze nicht mehr und `files().create` funktioniert.

Beide übertragen die echten Dateibytes serverseitig, ohne Umweg durch die Modellausgabe.

### 0.3 Aufräumen nötig (kann die Automatisierung nicht selbst)

- **Kaputte Datei in `<base>/FI/Smokola/`:** `Smokola_product_reference.png`
  (id `17yDZYYBprV1zZbxMGaZFILeOtKkjgLQP`, 3.631 Byte) ist der abgebrochene Upload-Versuch
  und unlesbar. Sie belegt zudem den „sauberen" Dateinamen, während die intakte Testdatei
  `Smokola_product_reference_96px_VERIFIED.png` heißt. Der Drive-MCP hat kein Delete-Tool,
  und der Service Account darf sie nicht löschen (`canDelete: false`, `canTrash: false` —
  Datei gehört dem Nutzer). **Muss manuell gelöscht werden.**
- **Doppelte State-Dateien:** im FI-State-Ordner `1RTnBufmjQoZ-6sGC6njAXOUQet5UewNN`
  liegen **drei** Dateien namens `processed_comments.json`
  (`1bo_V9sfD9_59EMZrJBW4MpE98ovCSEvs` = kanonisch, 6.468 B; `1SGv-vwXMzs4Riakak9cTiAhGR-AjMloN`
  = veraltet; `1LssA5s30Egmu-XNw_N3o5iB-eIAy6vmu` = veraltet), im FRCA-Ordner
  `16EZQapSYhZm7DLZERzM2foLPa0HT1TGx` **zwei** (`1hqB-cwX3bs1KZh1A3oQztAURcq9CWAfx` =
  kanonisch, 6.807 B; `19wtmv6eEBKO6txy1imx7s8N_ykq1_Bdx` = veraltet).
  Ursache: `create_file` legt bei gleichem Titel eine **neue** Datei an, es gibt kein
  Update-in-place. Ein künftiger Lauf kann die falsche erwischen. Veraltete löschen.

### 0.4 Korrigiert in diesem Lauf

`drive.base_folder_id` in `config/automation.config.json` war
`176ElFPlxj5hvsVJ8O_AaQSlIoL25IzJD` (kleines `l`) und lieferte
`Requested entity was not found`. Korrekt ist `176EIFPlxj5hvsVJ8O_AaQSlIoL25IzJD`
(großes `I`, Ordner „image creation"). Beide Felder korrigiert.

## 1. Was funktioniert

- Sheet lesen (`Google_Drive.read_file_content`), Kommentar-Threads in Spalte M
  auslesen (Head-Post + Replies).
- Competitor-Foto von der Funnel-Seite (Spalte D) per `curl` laden.
- Higgsfield-Generierung (Produktbild-Umbenennung + Ad-Übersetzung) — Qualität ist
  gut, das ist **nicht** das Problem.
- Ergebnis-Dokumentation als Google Doc (Markdown mit CDN-Links + übersetzter
  Ad-Copy) in Drive ablegen.

## 2. Bekanntes Problem: Bild-Dateien lassen sich nicht zuverlässig in Drive ablegen

Das Google-Drive-Tool (`create_file`) kann Dateien nur hochladen, indem der komplette
Dateiinhalt Base64-codiert als Text-Parameter in den Werkzeugaufruf geschrieben wird.
Es gibt **keine** Funktion "lade dieses Bild von dieser URL herunter und speichere es
in Drive" — der Bildinhalt muss durch das Modell selbst hindurch.

Getestet und bestätigt:
- Ab ca. 5–20 KB Bildgröße treten beim Durchreichen vereinzelt Bit-/Byte-Fehler auf
  (meist am Dateiende, meist ohne sichtbare Auswirkung auf die Darstellung, aber nicht
  garantiert byte-genau).
- Ab ca. 20–25 KB Base64-Text bricht das Lese-Werkzeug selbst mit einer harten
  Token-Grenze ab (Datei kann nicht mehr vollständig eingelesen werden) — das betrifft
  reguläre Higgsfield-Ergebnisbilder (~1 MB, 1024×1024) vollständig.
- Reduziert man Auflösung/Qualität stark genug, um unter dieses Limit zu kommen,
  leidet die sichtbare Bildqualität deutlich (Kompressionsartefakte).

**Fazit:** Mit dem aktuell verfügbaren Werkzeug ist "automatisch UND verlustfrei"
nicht gleichzeitig möglich. Es gibt zwei einzeln funktionierende Wege:
1. Nutzer lädt die Original-Higgsfield-CDN-Links manuell in Drive hoch (verlustfrei,
   ca. 10 Sekunden pro Bild, kein Automatisierungsaufwand nötig).
2. Automatischer Upload mit reduzierter Qualität (funktioniert, aber sichtbar
   schlechter als das Original).

## 3. Echte Lösung: direkter Google-Drive-API-Zugang (Service Account)

Damit Punkt 2 in voller Qualität UND automatisch funktioniert, braucht es einen
direkten API-Zugang, der die Bilddaten nicht durch den Chat-Kontext schleusen muss,
sondern serverseitig von der Higgsfield-CDN-URL direkt zu Google Drive überträgt.

### Was der Nutzer einmalig einrichten muss

1. **Google-Cloud-Projekt + Drive API aktivieren**
   - [console.cloud.google.com](https://console.cloud.google.com) → Projekt anlegen/wählen
   - "APIs & Services" → "Library" → "Google Drive API" → **Enable**

2. **Service Account anlegen**
   - "APIs & Services" → "Credentials" → "Create Credentials" → **"Service Account"**
   - Name frei wählbar, z. B. `image-automation-uploader`
   - Im Service Account → Tab **"Keys"** → "Add Key" → "Create new key" → **JSON** →
     herunterladen. Diese Datei ist ein Geheimnis (privater Schlüssel).
   - Die E-Mail-Adresse des Service Accounts notieren, z. B.
     `image-automation-uploader@<projekt-id>.iam.gserviceaccount.com`

3. **Ziel-Ordner in Drive mit dem Service Account teilen**
   - In Google Drive: Rechtsklick auf den Basis-Ordner
     (`https://drive.google.com/drive/folders/1RH4nagTulPEPXPp5fSwTeccvL-GlMI5-`,
     siehe `config/automation.config.json` → `drive.base_folder_id`) → "Freigeben"
   - Service-Account-E-Mail aus Schritt 2 eintragen, Rolle **"Bearbeiter"**
   - Ohne diesen Schritt sieht der Service Account nichts in Drive.

4. **JSON-Schlüssel sicher bereitstellen — NICHT im Chat einfügen**
   - Der Schlüsselinhalt enthält ein privates Geheimnis.
   - Als Environment-Variable/Secret der Session/des Environments hinterlegen, z. B.
     unter dem Namen `GOOGLE_SERVICE_ACCOUNT_JSON` (Wert = kompletter Inhalt der
     JSON-Datei). Das geschieht in den Umgebungs-/Session-Einstellungen von Claude
     Code on the web, nicht im Chatfenster.

### Was danach automatisch passiert

Sobald die Variable gesetzt ist, kann ein Skript (Python, `google-auth` +
`google-api-python-client` oder reine REST-Calls):
1. sich mit dem Service-Account-Schlüssel authentifizieren,
2. das Originalbild direkt von der Higgsfield-CDN-URL herunterladen,
3. es per Drive-API (`files.create`, multipart) direkt in den Zielordner hochladen —
   ohne Umweg über den Chat-Kontext, ohne Größenlimit, byte-genau.

## 4. Letzter automatischer Trigger-Lauf (2026-07-10) — Ergebnis

- **FRCA, Zeile 33 (Produkt "vanix", Competitor "variclex")**: 3 Ad-Permalinks im
  M-Kommentar, für FI (Zeile 52) bereits übersetzt, für FRCA (Quebec-Französisch)
  noch offen. Nicht abgeschlossen — siehe unten.
- **FRCA, Zeile 34 (Erelso)**: keine neuen Kommentare, bereits vollständig
  verarbeitet.
- **FI-Tab**: konnte in diesem Lauf nicht gelesen werden. `read_file_content` liefert
  bei diesem Sheet aus unbekanntem Grund konsistent nur den FRCA-Tab zurück, auch bei
  wiederholten Aufrufen. Für FI-Zellwerte funktioniert ersatzweise ein XLSX-Export +
  `openpyxl`, aber **Kommentare** (Spalte M) sind darüber nicht erreichbar — es gibt
  aktuell keinen bekannten Workaround für FI-Kommentare.
- **Nicht abgeschlossen:** Sowohl Higgsfield- als auch Google-Drive-Schreibaufrufe
  (`create_file`) sind in diesem Lauf durchgehend mit "Tool permission request
  failed" fehlgeschlagen, obwohl Lesezugriffe im selben Lauf funktionierten. Gleiches
  Muster wie beim vorherigen Trigger-Lauf. Betrifft offenbar spezifisch
  automatische/getriggerte Sessions — im interaktiven Chat liefen dieselben Tools
  zuvor einwandfrei.
- **Korrektur nötig, aber nicht durchführbar:** In
  `<FRCA-Projektordner>/State/processed_comments.json` stand ein nicht durch echte
  Sheet-Daten belegter Eintrag (7 zusätzliche "pending" Permalinks für vanix). Beim
  frischen Sheet-Read ließ sich das nicht bestätigen — vermutlich ein Fehler aus einer
  früheren, durch Verbindungsabbrüche gestörten Session. Die Korrektur (nur die 3
  echten Permalinks eintragen) konnte in diesem Lauf nicht gespeichert werden, siehe
  Punkt oben.

## 5. Offene Punkte für den Nutzer

1. Service-Account-Setup (Abschnitt 3) einrichten, falls automatischer Bild-Upload in
   voller Qualität gewünscht ist.
2. FRCA-Zeile 33 (vanix) manuell anstoßen oder auf den nächsten Lauf warten.
3. Die MCP-Verbindungsinstabilität bei automatischen Trigger-Läufen (Higgsfield +
   Drive-Schreibzugriffe) ist ein wiederkehrendes Muster über mindestens zwei Läufe —
   wert, als eigenständiges Infrastruktur-Problem zu melden/zu untersuchen.
