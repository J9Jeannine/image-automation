# Status & offene Punkte (Stand: 2026-07-26)

Diese Datei fasst zusammen, was funktioniert, was blockiert ist, und was der Nutzer
konkret tun muss, damit die Pipeline vollständig automatisch läuft. Ziel: alles an
einem Ort nachlesbar, statt über den Chat-Verlauf verstreut.

> **Wenn du ein Agent bist, der diesen Workflow ausführt: lies zuerst Abschnitt 2.**
> Dort steht, wie Bilder in Drive und Links ins Sheet kommen. Beides geht — aber
> **nicht** über den Google-Drive-MCP-Connector allein. Wer nur auf die MCP-Toolliste
> schaut, kommt zum falschen Schluss "geht nicht" und liefert unnötig eine
> Handarbeits-Lösung ab. Genau das ist am 2026-07-26 passiert.

## 1. Was funktioniert

- Sheet lesen (`Google_Drive.read_file_content`), Kommentar-Threads in Spalte M
  auslesen (Head-Post + Replies).
- Competitor-Foto von der Funnel-Seite (Spalte D) per `curl` laden.
- Ad-Bilder von `scontent.*.fbcdn.net` per `curl` laden (signierte Links, siehe README).
- Higgsfield-Generierung (Produktbild-Umbenennung + Ad-Übersetzung).
- **Bilddateien in voller Auflösung in Drive ablegen** — siehe Abschnitt 2.
- **Drive-Links in Sheet-Zellen schreiben** — siehe Abschnitt 2.
- Ergebnis-Dokumentation als Google Doc (Markdown mit CDN-Links + Ad-Copy) in Drive.

## 2. GELÖST: Drive-Upload und Sheet-Schreibzugriff über den Service Account

Der Google-Drive-**MCP-Connector** hat genau acht Tools (`create_file`, `copy_file`,
`download_file_content`, `get_file_metadata`, `get_file_permissions`,
`list_recent_files`, `read_file_content`, `search_files`). Damit gilt:

- Er kann Dateien nur hochladen, indem der komplette Inhalt base64-codiert durch den
  Modell-Kontext läuft. Ab ~20–25 KB Base64 bricht das Lese-Werkzeug mit einer harten
  Token-Grenze ab — ein 1024×1024-Higgsfield-Bild (~150–500 KB) ist damit unmöglich.
- Er kann **überhaupt nicht** in eine Tabellenzelle schreiben. Im Connector-Verzeichnis
  gibt es auch keinen Google-Sheets-Connector, der das nachrüsten würde.

**Beides ist trotzdem lösbar** — über den Service Account, der als
`GOOGLE_SERVICE_ACCOUNT_JSON` in der Umgebung liegt (bereits eingerichtet und
freigegeben):

```
image-automation-uploader@image-automation-502115.iam.gserviceaccount.com
```

Er hat `canEdit` auf dem Funnel Sheet und `canAddChildren` auf den Projektordnern.
Damit läuft der Datentransfer serverseitig, ohne Umweg über den Chat-Kontext, ohne
Größenlimit und byte-genau.

### 2a. Bilder in Drive ablegen — zweistufig

Ein Service Account hat **keine eigene Speicherquota**. Er kann deshalb in einem
normalen (Nicht-Shared-Drive-)Ordner keine Datei *anlegen*:

```
403 "Service Accounts do not have storage quota. Leverage shared drives ..."
```

Er kann aber eine Datei *überschreiben*, die jemand anderes besitzt — dann zählt der
Speicher gegen den Besitzer. Der funktionierende Ablauf ist deshalb:

1. **Platzhalter anlegen** — pro Bild eine 630-Byte-Dummy-Datei über das
   Drive-MCP-Tool `create_file` (das handelt als eingeloggter Nutzer, dem die Datei
   dann gehört). Konstante `PLACEHOLDER_JPEG_B64` in `scripts/drive_upload.py`.
   Dateiname exakt so wie die lokale Datei, `disableConversionToGoogleType: true`.
2. **Inhalt ersetzen** — `python3 scripts/drive_upload.py <folder_id> <local_dir>`.
   Das Skript ordnet lokale Dateien über den Dateinamen den Drive-Dateien zu,
   überschreibt sie per `files.update` und prüft die Bytegröße gegen. Fehlen
   Platzhalter, listet es exakt auf, welche noch per MCP angelegt werden müssen.

Schritt 1 entfällt, sobald ein Workspace-**Shared Drive** existiert — dort hat der
Service Account Quota und kann direkt anlegen. Aktuell gibt es keins
(`drive/v3/drives` liefert eine leere Liste; das Konto ist ein privates Google-Konto).

### 2b. Links ins Sheet schreiben

```
python3 scripts/sheet_set_link.py FRCA O35 <folder_id> Itzora
```

**Locale-Falle:** Das Funnel Sheet hat Locale `nl_NL` und erwartet in Formeln ein
**Semikolon** als Argumenttrenner. `=HYPERLINK("https://…","Itzora")` ergibt `#ERROR!`,
`=HYPERLINK("https://…";"Itzora")` funktioniert. Die Sheets-API übersetzt das nicht —
`USER_ENTERED` parst in der Locale der Datei. Das Skript liest die Locale aus und wählt
den Trenner selbst, und verifiziert danach, dass die Zelle nicht `#ERROR!` anzeigt.

Der Link gehört in **Spalte O** (`[merged] Link to Videos /Images`), Label = Produktname
aus Spalte G — so wie es die FI-Zeilen bereits vormachen.

### 2c. Technische Randnotiz

`google-auth` ist in dieser Sandbox nicht nutzbar (`cryptography` wirft
`ModuleNotFoundError: _cffi_backend`). `scripts/google_auth.py` signiert das JWT deshalb
mit der `openssl`-CLI. Nicht auf `google-auth` umbauen, ohne das vorher zu testen.

## 3. Verifiziert am 2026-07-26 (FRCA-Zeilen 35–37)

17 übersetzte Ads + 1 Produktbild, alle 1024×1024, byte-genau in Drive, plus die drei
Ordnerlinks in `FRCA!O35:O37`:

| Zeile | Produkt | Ads | Drive-Ordner |
| --- | --- | --- | --- |
| 35 | Itzora | 8 | `1jWvVRShelG7vkQSKuFh2VUxDY_mkkzK4` |
| 36 | lutiva | 6 | `1H9Cd93BNTsCzY29ju7R2e3lwWGYAT16P` |
| 37 | Orthix | 3 | `1rQ__4gHgslZd1MVH4OllxwvrSAuKri7G` |

Besonderheit dieses Laufs: FRCA hat für diese Zeilen **keine eigenen M-Kommentare**. Die
Produkte sind aber dieselben wie in FI (Zeilen 55/56/58), also wurden die FI-Quell-Ads
wiederverwendet und nach Quebec-Französisch übersetzt. Wenn FRCA und FI denselben
Competitor in Spalte C/D haben, ist das der richtige Weg — nicht die Zeile überspringen.

## 4. Weiterhin offen

1. **FRCA 33 (vanix) und 34 (Erelso)** sind nicht verarbeitbar: alle fbcdn.net-Links in
   beiden Tabs liefern HTTP 403 "URL signature expired", und für vanix stehen ohnehin nur
   blockierte facebook.com-Permalinks im Thread. Braucht frische Direktlinks im
   M-Kommentar.
2. **FI-Kommentare** sind über `read_file_content` nicht erreichbar — das Tool liefert
   bei diesem Sheet konsistent nur den FRCA-Tab. Für FI-Zellwerte funktioniert der
   XLSX-Export + `openpyxl`; für FI-**Kommentare** gibt es keinen Workaround über MCP.
   *Der Service Account kann das inzwischen lösen* (Drive Comments API bzw. Sheets API),
   das ist aber noch nicht umgesetzt.
3. **`drive.base_folder_id` in `config/automation.config.json` enthält einen Tippfehler**
   (`176ElFPlxj…` mit kleinem L statt `176EIFPlxj…` mit großem i). Die ID löst nicht auf.
   Deshalb landete ein früherer Lauf in einem Streuordner unter *Meine Ablage*.
4. Die früher beobachtete MCP-Instabilität bei Trigger-Läufen ("Tool permission request
   failed" bei Schreibzugriffen) ist mit dem Service-Account-Weg weitgehend entschärft —
   der hängt nicht am MCP-Connector.
