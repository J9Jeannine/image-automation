#!/usr/bin/env python3
"""
Laedt eine Datei (von einer HTTPS-URL, z.B. der Higgsfield-CDN, ODER von einem
lokalen Pfad) direkt in einen Google-Drive-Ordner hoch -- ALS DU, per
User-OAuth-Refresh-Token. Serverseitig, byte-genau, ohne Groessenlimit, ohne
Umweg ueber Base64 im Chat-Kontext. Ersetzt das unzuverlaessige Durchreichen.

Voraussetzung: diese Env-Secrets sind gesetzt (siehe get_drive_refresh_token.py):
  GOOGLE_OAUTH_CLIENT_ID
  GOOGLE_OAUTH_CLIENT_SECRET
  GOOGLE_OAUTH_REFRESH_TOKEN

Benutzung:
  python3 scripts/upload_cdn_to_drive.py <quelle> <drive_folder_id> [dateiname]

  <quelle>          https://... URL  ODER  lokaler Dateipfad
  <drive_folder_id> Ziel-Ordner-ID in Drive (der Ordner muss DIR gehoeren)
  [dateiname]       optionaler Zielname; sonst aus der Quelle abgeleitet

Gibt bei Erfolg die neue Datei-ID, den Namen und die verifizierte Byte-Groesse aus.
"""
import os, sys, json, uuid, mimetypes, urllib.parse, urllib.request

TOKEN = "https://oauth2.googleapis.com/token"

def access_token():
    cid = os.environ["GOOGLE_OAUTH_CLIENT_ID"]
    sec = os.environ["GOOGLE_OAUTH_CLIENT_SECRET"]
    rt = os.environ["GOOGLE_OAUTH_REFRESH_TOKEN"]
    data = urllib.parse.urlencode({
        "client_id": cid, "client_secret": sec,
        "refresh_token": rt, "grant_type": "refresh_token",
    }).encode()
    return json.loads(urllib.request.urlopen(urllib.request.Request(TOKEN, data=data)).read())["access_token"]

def fetch(src):
    if src.startswith("http://") or src.startswith("https://"):
        req = urllib.request.Request(src, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as r:
            return r.read(), src.split("/")[-1].split("?")[0]
    with open(src, "rb") as f:
        return f.read(), os.path.basename(src)

def upload(token, content, name, folder_id, mime):
    boundary = "====" + uuid.uuid4().hex
    meta = {"name": name, "parents": [folder_id]}
    body = b""
    body += ("--" + boundary + "\r\n").encode()
    body += b"Content-Type: application/json; charset=UTF-8\r\n\r\n"
    body += json.dumps(meta).encode() + b"\r\n"
    body += ("--" + boundary + "\r\n").encode()
    body += ("Content-Type: " + mime + "\r\n\r\n").encode()
    body += content + b"\r\n"
    body += ("--" + boundary + "--").encode()
    req = urllib.request.Request(
        "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id,name,size",
        data=body, method="POST",
        headers={"Authorization": "Bearer " + token,
                 "Content-Type": "multipart/related; boundary=" + boundary})
    return json.loads(urllib.request.urlopen(req).read())

def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    src = sys.argv[1]
    folder_id = sys.argv[2]
    content, default_name = fetch(src)
    name = sys.argv[3] if len(sys.argv) > 3 else default_name
    mime = mimetypes.guess_type(name)[0] or "application/octet-stream"
    tok = access_token()
    r = upload(tok, content, name, folder_id, mime)
    ok = int(r.get("size", -1)) == len(content)
    print(json.dumps({"id": r.get("id"), "name": r.get("name"),
                      "uploaded_bytes": r.get("size"), "source_bytes": len(content),
                      "verified_exact": ok}, ensure_ascii=False))
    if not ok:
        sys.exit("WARNUNG: hochgeladene Groesse != Quellgroesse")

if __name__ == "__main__":
    main()
