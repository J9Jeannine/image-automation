# Automatischer Drive-Upload in voller Qualität (User-OAuth) — Einrichtung

**Ziel:** Ads landen künftig **automatisch und in voller Auflösung** im richtigen
Drive-Ordner — ohne dass du etwas hochladen oder hineinziehen musst.

## Warum das nötig ist

Der Service Account kann in ein privates Gmail-Drive **keine Bilddateien** hochladen
(„Service Accounts do not have storage quota"). Der einzige andere Weg des verbundenen
Tools verlangt, dass das Bild als riesiger Text-Block durch den Chat gereicht wird — das
verfälscht große Bilder und ist unzuverlässig. Die saubere Lösung: die Automatisierung
lädt **als du** hoch, über ein einmalig erzeugtes OAuth-Token. Dann gilt dein
Speicherplatz, es gibt kein Größenlimit, und die Dateien gehören dir (löschbar).

## Einmalige Einrichtung (~5 Minuten)

Alles im **selben Google-Cloud-Projekt**, in dem schon der Service Account liegt
(`image-automation-502115`).

1. **OAuth-Zustimmungsbildschirm** (falls noch nicht vorhanden)
   - console.cloud.google.com → „APIs & Services" → „OAuth consent screen"
   - User Type **External** → deine Daten eintragen → unter **Test users** deine
     Gmail-Adresse (`jeannine.thiry1@gmail.com`) hinzufügen. Speichern.

2. **OAuth-Client erstellen**
   - „APIs & Services" → „Credentials" → „Create Credentials" → **OAuth client ID**
   - Application type: **Desktop app** → Name frei → **Create**
   - Es erscheinen **Client-ID** und **Client-Secret** — beide kopieren.

3. **Refresh-Token erzeugen** (einmal lokal auf deinem Rechner, wo ein Browser ist)
   ```bash
   GOOGLE_OAUTH_CLIENT_ID=<deine-client-id> \
   GOOGLE_OAUTH_CLIENT_SECRET=<dein-client-secret> \
   python3 scripts/get_drive_refresh_token.py
   ```
   Der Browser öffnet sich → Zugriff bestätigen (ggf. „Erweitert → trotzdem fortfahren",
   da die App im Test-Modus ist). Das Skript druckt am Ende deinen **Refresh-Token**.

4. **Drei Secrets in der Session/Umgebung hinterlegen**
   (in den Environment-Einstellungen von Claude Code, **nicht** in den Chat tippen):
   ```
   GOOGLE_OAUTH_CLIENT_ID
   GOOGLE_OAUTH_CLIENT_SECRET
   GOOGLE_OAUTH_REFRESH_TOKEN
   ```

## Danach — vollautomatisch

Ab dann lädt die Pipeline jede fertige Ad direkt hoch, z. B.:

```bash
python3 scripts/upload_cdn_to_drive.py \
  "https://d8j0ntlcm91z4.cloudfront.net/.../hf_...png" \
  1QWpjnBxGIxSbIUlWm31MHi_myUXVN8Og \
  "Erelso FRCA – ad 1.png"
```

Das Skript lädt byte-genau hoch und **verifiziert** die Größe gegen die Quelle
(`verified_exact: true`). Quelle darf eine CDN-URL **oder** ein lokaler Pfad sein.

`scripts/get_drive_refresh_token.py` benutzt den Scope `drive.file` — die App sieht nur
Dateien, die sie selbst anlegt, sonst nichts in deinem Drive. Wer die Ordner-Bereinigung
(Löschen falsch abgelegter Dateien) automatisieren will, braucht stattdessen den weiteren
Scope `drive` (im Skript die Zeile `SCOPE = ...` anpassen und Token neu erzeugen).
