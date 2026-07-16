#!/usr/bin/env python3
"""OAuth-Flow (3-legged) fuer das ECHTE Google-Konto, damit Datei-Uploads gegen
das eigene Speicherkontingent des Nutzers laufen statt gegen den Service Account
(der hat keins -> 403 storageQuotaExceeded, siehe STATUS.md Abschnitt 3a).

Zwei Schritte:
  1) python3 scripts/drive_oauth.py auth-url
     -> gibt den Google-Anmelde-Link aus. Nutzer oeffnet ihn im Browser, meldet
        sich als jeannine.thiry1@gmail.com an, bestaetigt den Zugriff. Die Seite
        danach (http://localhost/...) laedt NICHT -- das ist normal. In der
        Adresszeile des Browsers steht dann ?code=XXXX -> diesen Code kopieren.
  2) python3 scripts/drive_oauth.py exchange "<code>"
     -> tauscht den Code gegen einen langlebigen Refresh-Token. Dieser Token wird
        ausgegeben und muss als Umgebungsvariable GOOGLE_OAUTH_REFRESH_TOKEN
        hinterlegt werden (einmalig, danach nie wieder noetig).

Voraussetzung: Umgebungsvariablen GOOGLE_OAUTH_CLIENT_ID und
GOOGLE_OAUTH_CLIENT_SECRET (aus dem OAuth-Client "Desktop App" im Google-Cloud-
Projekt image-automation-502115).
"""
import os
import sys
import urllib.parse

import requests

AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
# Loopback-Redirect: von Desktop-App-Clients erlaubt. Die Seite laedt nicht,
# aber der ?code=... steht danach in der Adresszeile des Browsers.
REDIRECT_URI = "http://localhost"
# Voller Drive-Scope: deckt sowohl Datei-Upload als auch Kommentare/Antworten auf
# fremde Dateien (z.B. das Funnel Sheet) ab.
SCOPE = "https://www.googleapis.com/auth/drive"


def _need(var):
    val = os.environ.get(var)
    if not val:
        sys.exit(f"{var} ist nicht gesetzt. Bitte zuerst als Umgebungsvariable hinterlegen.")
    return val


def auth_url():
    client_id = _need("GOOGLE_OAUTH_CLIENT_ID")
    params = {
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPE,
        "access_type": "offline",
        "prompt": "consent",
    }
    url = AUTH_ENDPOINT + "?" + urllib.parse.urlencode(params)
    print(url)


def exchange(code):
    client_id = _need("GOOGLE_OAUTH_CLIENT_ID")
    client_secret = _need("GOOGLE_OAUTH_CLIENT_SECRET")
    resp = requests.post(
        TOKEN_ENDPOINT,
        data={
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code",
        },
        timeout=30,
    )
    if resp.status_code != 200:
        sys.exit(f"Token-Tausch fehlgeschlagen ({resp.status_code}): {resp.text}")
    data = resp.json()
    refresh = data.get("refresh_token")
    if not refresh:
        sys.exit(
            "Kein refresh_token in der Antwort. Meist heisst das, die App wurde "
            "schon einmal autorisiert. Widerrufe den Zugriff unter "
            "https://myaccount.google.com/permissions und wiederhole auth-url.\n"
            f"Antwort war: {data}"
        )
    print("=== ERFOLG ===")
    print("Setze diese Umgebungsvariable (Wert geheim halten):")
    print()
    print(f"GOOGLE_OAUTH_REFRESH_TOKEN={refresh}")


def get_access_token():
    """Wird von upload_to_drive.py genutzt: frischer Access-Token aus dem
    gespeicherten Refresh-Token."""
    client_id = _need("GOOGLE_OAUTH_CLIENT_ID")
    client_secret = _need("GOOGLE_OAUTH_CLIENT_SECRET")
    refresh = _need("GOOGLE_OAUTH_REFRESH_TOKEN")
    resp = requests.post(
        TOKEN_ENDPOINT,
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh,
            "grant_type": "refresh_token",
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("auth-url", "exchange"):
        sys.exit("Nutzung:\n  drive_oauth.py auth-url\n  drive_oauth.py exchange \"<code>\"")
    if sys.argv[1] == "auth-url":
        auth_url()
    else:
        if len(sys.argv) < 3:
            sys.exit("Bitte den Code angeben: drive_oauth.py exchange \"<code>\"")
        exchange(sys.argv[2])


if __name__ == "__main__":
    main()
