# Status & offene Punkte (Stand: 2026-07-10)

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

## 6. Neue Anforderung: Ergebnis-Ordner-Link in Spalte O eintragen (aktuell nicht möglich)

Wunsch (2026-07-24): Der Drive-Link zum Renders-Ordner einer verarbeiteten Zeile soll
nicht nur in der Chat-Zusammenfassung genannt werden, sondern zusätzlich direkt in
Spalte O ("[merged] Link to Videos /Images") der passenden Sheet-Zeile eingetragen
werden (dokumentiert in `docs/workflow.md` Schritt 8.3).

**Blocker:** Die aktuell verbundenen Werkzeuge (`Google_Drive.*`) sind
Datei-Operationen (lesen, anlegen, kopieren, Metadaten, Berechtigungen,
Kommentare lesen) — keines davon kann eine einzelne Zellen in einem bestehenden
Google Sheet schreiben, und Kommentare können ebenfalls nicht per Werkzeug gepostet
werden (nur lesen). Im MCP-Connector-Verzeichnis des Accounts existiert aktuell auch
kein Google-Sheets-Connector, der das könnte — nur "Google Drive" (verbunden) und
"Google Calendar" (nicht aktiviert).

**Lösungswege (einer reicht):**
1. Den in Abschnitt 3 beschriebenen Service Account zusätzlich für die **Google
   Sheets API** freischalten (in derselben Google-Cloud-Projekt-Konsole: "APIs &
   Services" → "Library" → "Google Sheets API" → Enable) und das Funnel Sheet
   (`config/automation.config.json` → `sheet.id`) mit der Service-Account-E-Mail
   teilen (Rolle "Bearbeiter"). Ein Skript kann dann per `spreadsheets.values.update`
   gezielt Spalte O der jeweiligen Zeile schreiben, ohne den Rest des Sheets
   anzufassen.
2. Alternativ einen Sheets-fähigen MCP-Connector in den claude.ai-Connector-
   Einstellungen verbinden, falls/sobald einer mit Schreibzugriff verfügbar ist.

Bis einer der beiden Wege eingerichtet ist, überspringt Schritt 8.3 das Zurückschreiben
und vermerkt das explizit im Abschlussbericht statt es stillschweigend wegzulassen.
