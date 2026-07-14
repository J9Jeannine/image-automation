# Status & offene Punkte (Stand: 2026-07-13)

**Update 2026-07-13:** `scripts/upload_to_drive.py` ist jetzt gebaut (siehe Abschnitt 3a)
— löst Problem 2 unten. Bild-Upload läuft direkt Server-zu-Server (Higgsfield-CDN →
Google Drive), ohne Bilddaten durch den Chat-Kontext zu schleusen. Einzige verbleibende
Voraussetzung: der Ziel-Ordner muss noch mit dem Service Account geteilt werden (siehe
Abschnitt 3a, Punkt "Noch zu tun"). Nebenbei wurde ein Config-Fehler behoben:
`config/automation.config.json` → `drive.base_folder_id` zeigte auf eine nicht
existente ID (vermutlich ein Tippfehler aus einem früheren automatisierten Lauf am
2026-07-11) und wurde auf die verifizierte ID des `Translated-Ads`-Ordners korrigiert.

Diese Datei fasst zusammen, was funktioniert, was blockiert ist, und was der Nutzer
konkret tun muss, damit die Pipeline vollständig automatisch läuft. Ziel: alles an
einem Ort nachlesbar, statt über den Chat-Verlauf verstreut.

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

## 3a. Umgesetzt (2026-07-13): `scripts/upload_to_drive.py`

Das Skript authentifiziert sich per Service-Account-JWT (`GOOGLE_SERVICE_ACCOUNT_JSON`),
streamt jedes Bild von seiner Higgsfield-CDN-URL auf Platte und lädt es per Drive-API-
Multipart-Upload in `<drive.base_folder_id>/<market>/<product>/<subfolder>/` hoch —
byte-genau, ohne Auflösungsverlust, ohne dass die Bilddaten durch den Modell-Kontext
laufen. Danach genau **ein** Discord-Post (`DISCORD_WEBHOOK_URL_IMAGES`) mit dem Link
zum Ziel-Ordner, keine Einzelbilder im Chat.

```
python3 scripts/upload_to_drive.py --market FRCA --product vanix --subfolder renders \
    --file "https://.../hf_....png=vanix_ad_721441221.png"
```

**Getestet am 2026-07-13:** Token-Erwerb (JWT-Bearer-Flow gegen
`oauth2.googleapis.com/token`) funktioniert mit den hinterlegten Credentials
(`image-automation-uploader@image-automation-502115.iam.gserviceaccount.com`).
Zugriff auf den Ziel-Ordner (`drive.base_folder_id` = `Translated-Ads`-Ordner,
`1JWHztpl2Z6mE9WtcRTObRgwBRp1OsHCb`) schlägt aktuell noch mit 404 fehl — der Ordner ist
noch nicht mit dem Service Account geteilt.

**Update 2026-07-13, nach Freigabe des Ordners:** Ordner-Zugriff funktioniert jetzt
(404 weg, Unterordner FRCA/vanix/renders werden korrekt gefunden/angelegt). Der
eigentliche Datei-Upload schlägt aber mit **403 `storageQuotaExceeded`** fehl:
`"Service Accounts do not have storage quota. Leverage shared drives ..., or use
OAuth delegation ... instead."` — das ist eine harte Google-Drive-Plattform-Grenze, kein
Freigabe-/Config-Problem: Service Accounts besitzen selbst keinen Speicherplatz, neue
Dateien brauchen einen Besitzer mit Kontingent. Zwei offizielle Lösungswege laut
Google, beide für **normale (Nicht-Workspace-)Gmail-Konten wie
`jeannine.thiry1@gmail.com` nicht nutzbar**:
1. Shared Drives (Team Drives) — erfordert Google Workspace, nicht verfügbar für
   Consumer-Gmail.
2. Domain-Wide Delegation ("OAuth delegation") — erfordert eine
   Google-Workspace-Admin-Konsole, ebenfalls nicht verfügbar für Consumer-Gmail.

**Tatsächlich funktionierender Weg für Consumer-Gmail:** Klassischer 3-legged-OAuth als
das echte Google-Konto (nicht als Service Account) — einmalig im Browser einloggen und
Zugriff bestätigen (OAuth-Client vom Typ "Desktop App" im selben Cloud-Projekt), danach
einen langlebigen Refresh-Token als Secret hinterlegen (z. B.
`GOOGLE_OAUTH_CLIENT_ID`/`_SECRET`/`_REFRESH_TOKEN`). Uploads laufen dann unter dem
echten Speicherkontingent von `jeannine.thiry1@gmail.com`. Noch nicht umgesetzt —
erfordert einmaligen manuellen Autorisierungsschritt des Nutzers, siehe Rückfrage im
Chat vom 2026-07-13.

### Was der Nutzer einmalig einrichten musste (jetzt erledigt, Referenz)

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

1. **OAuth-Setup für das echte Google-Konto** (Desktop-App-Client, siehe Chat vom
   2026-07-13/14): `Translated-Ads`-Ordner ist inzwischen mit dem Service Account
   geteilt, aber der eigentliche Datei-Upload scheitert weiterhin mit 403
   `storageQuotaExceeded` (Service Accounts haben kein eigenes Speicherkontingent,
   siehe Abschnitt 3a-Update). Einziger funktionierender Weg für ein normales
   Gmail-Konto: 3-legged OAuth als `jeannine.thiry1@gmail.com` selbst. Wartet auf
   `GOOGLE_OAUTH_CLIENT_ID`/`GOOGLE_OAUTH_CLIENT_SECRET` (Anleitung zum Anlegen des
   OAuth-Clients wurde im Chat gegeben). Sobald vorhanden, deckt derselbe Zugang auch
   Punkt 1a ab:
   1a. **Sheet-Kommentare schreiben:** Für die neue Regel in `docs/workflow.md`
       Schritt 5 ("jedes Bild bekommt einen dauerhaften Link im M-Kommentar-Thread")
       gibt es aktuell kein Tool — das Google-Drive-MCP kann nur lesen, keine
       Kommentare/Antworten erstellen, und der Service Account hat keinen Zugriff auf
       die Funnel-Sheet-Datei selbst. Braucht denselben OAuth-Zugang wie oben
       (Drive-API `comments.create`/`replies.create`).
2. FRCA-Zeile 33 (vanix): weiterhin nur `facebook.com/ads/library/?id=...`-Permalinks
   im M-Kommentar, keine fbcdn.net-Reply. Wartet seit 2026-07-10 auf direkte
   Bild-/Video-URLs vom Nutzer (siehe Lauf-Notiz 2026-07-13 unten).
3. FI-Tab weiterhin nicht per `read_file_content` lesbar (siehe Lauf-Notiz
   2026-07-13) — Kommentare in Spalte M für FI (ab Zeile 52) können aktuell nicht
   automatisiert geprüft werden. Kein bekannter Workaround; ggf. als
   Infrastruktur-Problem melden.
4. Die MCP-Verbindungsinstabilität bei automatischen Trigger-Läufen (Higgsfield +
   Drive-Schreibzugriffe, Stand 2026-07-10) noch nicht erneut beobachtet, aber auch
   noch nicht als behoben bestätigt.

## 6. Lauf-Notiz 2026-07-13

- FRCA erfolgreich geprüft: Zeile 33 (vanix) unverändert pending (10 Permalinks, keine
  fbcdn.net-URL), Zeile 34 (Erelso) bereits vollständig verarbeitet — nichts zu tun.
- FI-Tab: `read_file_content` liefert weiterhin konsistent nur den FRCA-Tab zurück
  (2x erneut getestet) — unverändert gegenüber 2026-07-10/11.
- `scripts/upload_to_drive.py` gebaut und Auth erfolgreich getestet; Ordner-Freigabe
  fehlt noch (siehe Punkt 1 oben).
