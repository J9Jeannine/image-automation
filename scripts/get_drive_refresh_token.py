#!/usr/bin/env python3
"""
Einmalig lokal auf deinem eigenen Rechner ausfuehren, um EINEN dauerhaften
Google-Drive-Refresh-Token fuer dein persoenliches Gmail-Konto zu erzeugen.

Warum ueberhaupt? Ein Service Account kann in ein persoenliches Gmail-Drive
KEINE Dateibytes hochladen ("Service Accounts do not have storage quota").
Mit einem User-OAuth-Refresh-Token laedt die Automatisierung dagegen ALS DU
hoch -- volle Aufloesung, kein Groessenlimit, Dateien gehoeren dir (loeschbar).
Das ersetzt das unzuverlaessige Base64-Durchreichen komplett.

VORAUSSETZUNG (einmalig, ~3 Min in der Google Cloud Console):
  1. console.cloud.google.com -> dasselbe Projekt wie der Service Account.
  2. "APIs & Services" -> "OAuth consent screen": falls noch nicht getan,
     als "External" anlegen, deine Gmail-Adresse unter "Test users" eintragen.
  3. "APIs & Services" -> "Credentials" -> "Create Credentials"
     -> "OAuth client ID" -> Application type: "Desktop app" -> anlegen.
  4. Client-ID und Client-Secret notieren.

DANN dieses Skript starten:
  GOOGLE_OAUTH_CLIENT_ID=xxx GOOGLE_OAUTH_CLIENT_SECRET=yyy \
      python3 scripts/get_drive_refresh_token.py

Es oeffnet den Browser (oder zeigt eine URL), du bestaetigst den Zugriff,
und es druckt am Ende deinen REFRESH TOKEN. Diesen zusammen mit Client-ID und
Client-Secret als Environment-Secrets der Session hinterlegen:
  GOOGLE_OAUTH_CLIENT_ID, GOOGLE_OAUTH_CLIENT_SECRET, GOOGLE_OAUTH_REFRESH_TOKEN
"""
import os, sys, json, urllib.parse, urllib.request, webbrowser, http.server, threading

CLIENT_ID = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
CLIENT_SECRET = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
SCOPE = "https://www.googleapis.com/auth/drive.file"  # nur von dieser App erstellte Dateien
AUTH = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN = "https://oauth2.googleapis.com/token"

if not CLIENT_ID or not CLIENT_SECRET:
    sys.exit("Bitte GOOGLE_OAUTH_CLIENT_ID und GOOGLE_OAUTH_CLIENT_SECRET setzen "
             "(aus dem 'Desktop app' OAuth-Client in der Google Cloud Console).")

code_holder = {}

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        q = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(q)
        code_holder["code"] = params.get("code", [None])[0]
        code_holder["error"] = params.get("error", [None])[0]
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        msg = "Fertig. Du kannst dieses Fenster schliessen und zum Terminal zurueckkehren."
        self.wfile.write(f"<html><body><h2>{msg}</h2></body></html>".encode())
    def log_message(self, *a):  # keine Server-Logs
        pass

# lokalen Loopback-Server auf einem freien Port starten
server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
port = server.server_address[1]
redirect_uri = f"http://127.0.0.1:{port}/"

auth_url = AUTH + "?" + urllib.parse.urlencode({
    "client_id": CLIENT_ID,
    "redirect_uri": redirect_uri,
    "response_type": "code",
    "scope": SCOPE,
    "access_type": "offline",       # <- liefert den Refresh Token
    "prompt": "consent",
})

print("\nOeffne diese URL im Browser und bestaetige den Zugriff:\n")
print(auth_url + "\n")
try:
    webbrowser.open(auth_url)
except Exception:
    pass

threading.Thread(target=server.handle_request).start()
# warten bis der Redirect eintrifft
import time
for _ in range(300):
    if "code" in code_holder or "error" in code_holder:
        break
    time.sleep(1)

if code_holder.get("error") or not code_holder.get("code"):
    sys.exit("Kein Autorisierungscode erhalten: " + str(code_holder.get("error")))

data = urllib.parse.urlencode({
    "code": code_holder["code"],
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "redirect_uri": redirect_uri,
    "grant_type": "authorization_code",
}).encode()
resp = json.loads(urllib.request.urlopen(urllib.request.Request(TOKEN, data=data)).read())

rt = resp.get("refresh_token")
if not rt:
    sys.exit("Kein refresh_token in der Antwort. Antwort war:\n" + json.dumps(resp, indent=2))

print("\n=========================================================")
print("ERFOLG. Hinterlege diese drei Werte als Session-Secrets:")
print("  GOOGLE_OAUTH_CLIENT_ID     =", CLIENT_ID)
print("  GOOGLE_OAUTH_CLIENT_SECRET = (dein Client-Secret)")
print("  GOOGLE_OAUTH_REFRESH_TOKEN =", rt)
print("=========================================================")
