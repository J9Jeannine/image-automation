#!/usr/bin/env python3
"""Lädt Bilder direkt von einer Higgsfield-CDN-URL zu Google Drive hoch, per
Service-Account-Zugriff (Drive API v3) statt per Base64-durch-den-Chat-Kontext.

Auth: Umgebungsvariable GOOGLE_SERVICE_ACCOUNT_JSON (kompletter Inhalt des
Service-Account-JSON-Schlüssels).
Zielordner: config/automation.config.json -> drive.base_folder_id, darunter
<base>/<market>/<product>/<subfolder>/.
Benachrichtigung: Umgebungsvariable DISCORD_WEBHOOK_URL_IMAGES -- nach Abschluss
genau EIN Discord-Post mit dem Link zum Ziel-Ordner (keine Einzelbilder im Chat).

Beispiel:
  python3 scripts/upload_to_drive.py --market FRCA --product vanix \\
      --subfolder renders \\
      --file "https://d8j0ntlcm91z4.cloudfront.net/.../hf_....png=vanix_ad_721441221.png"

  # oder mit Manifest-Datei (JSON-Liste von {"url": ..., "filename": ...}):
  python3 scripts/upload_to_drive.py --market FRCA --product vanix \\
      --subfolder renders --manifest manifest.json
"""
import argparse
import json
import os
import sys
import tempfile
import time

import jwt
import requests

TOKEN_URL = "https://oauth2.googleapis.com/token"
DRIVE_FILES_URL = "https://www.googleapis.com/drive/v3/files"
DRIVE_UPLOAD_URL = "https://www.googleapis.com/upload/drive/v3/files"
DRIVE_SCOPE = "https://www.googleapis.com/auth/drive"


def get_access_token():
    key_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not key_json:
        sys.exit("GOOGLE_SERVICE_ACCOUNT_JSON ist nicht gesetzt.")
    try:
        key = json.loads(key_json)
    except json.JSONDecodeError as exc:
        sys.exit(f"GOOGLE_SERVICE_ACCOUNT_JSON ist kein gueltiges JSON: {exc}")

    now = int(time.time())
    claims = {
        "iss": key["client_email"],
        "scope": DRIVE_SCOPE,
        "aud": TOKEN_URL,
        "iat": now,
        "exp": now + 3600,
    }
    assertion = jwt.encode(claims, key["private_key"], algorithm="RS256")
    resp = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": assertion,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def _escape_q(value):
    return value.replace("\\", "\\\\").replace("'", "\\'")


def find_or_create_folder(token, name, parent_id):
    headers = {"Authorization": f"Bearer {token}"}
    query = (
        f"name = '{_escape_q(name)}' and '{parent_id}' in parents "
        "and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    )
    resp = requests.get(
        DRIVE_FILES_URL,
        headers=headers,
        params={"q": query, "fields": "files(id,name)"},
        timeout=30,
    )
    resp.raise_for_status()
    files = resp.json().get("files", [])
    if files:
        return files[0]["id"]

    metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id],
    }
    resp = requests.post(
        DRIVE_FILES_URL,
        headers={**headers, "Content-Type": "application/json"},
        json=metadata,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["id"]


def upload_image(token, cdn_url, filename, parent_id):
    """Streamt die Bilddaten von der CDN-URL auf Platte und von dort per Drive-API
    hoch. Die Bytes laufen nur durch dieses Skript, nie durch den Chat-Kontext."""
    with requests.get(cdn_url, stream=True, timeout=60) as r:
        r.raise_for_status()
        content_type = r.headers.get("Content-Type", "application/octet-stream")
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            for chunk in r.iter_content(chunk_size=262144):
                tmp.write(chunk)
            tmp_path = tmp.name

    try:
        metadata = {"name": filename, "parents": [parent_id]}
        with open(tmp_path, "rb") as fh:
            files = {
                "metadata": (None, json.dumps(metadata), "application/json; charset=UTF-8"),
                "file": (filename, fh, content_type),
            }
            resp = requests.post(
                DRIVE_UPLOAD_URL,
                params={"uploadType": "multipart", "fields": "id,name,webViewLink"},
                headers={"Authorization": f"Bearer {token}"},
                files=files,
                timeout=120,
            )
        resp.raise_for_status()
        return resp.json()
    finally:
        os.remove(tmp_path)


def post_discord_summary(market, product, subfolder, count, folder_link):
    webhook = os.environ.get("DISCORD_WEBHOOK_URL_IMAGES")
    if not webhook:
        print("DISCORD_WEBHOOK_URL_IMAGES nicht gesetzt, Discord-Post uebersprungen.", file=sys.stderr)
        return
    content = f"**{market} / {product}** — {count} Bild(er) in `{subfolder}` hochgeladen.\n{folder_link}"
    resp = requests.post(webhook, json={"content": content}, timeout=30)
    resp.raise_for_status()


def parse_items(args):
    items = []
    if args.manifest:
        with open(args.manifest) as fh:
            items.extend(json.load(fh))
    for entry in args.file:
        url, sep, filename = entry.partition("=")
        if not sep or not filename:
            sys.exit(f"--file erwartet 'URL=Dateiname', bekommen: {entry!r}")
        items.append({"url": url, "filename": filename})
    if not items:
        sys.exit("Keine Bilder angegeben (--manifest oder --file).")
    return items


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", default="config/automation.config.json")
    parser.add_argument("--market", required=True, help="z.B. FI oder FRCA")
    parser.add_argument("--product", required=True, help="Produktname exakt wie in Spalte G")
    parser.add_argument("--subfolder", default="renders", help="z.B. renders oder translated-ads")
    parser.add_argument("--manifest", help="JSON-Datei: [{\"url\": ..., \"filename\": ...}, ...]")
    parser.add_argument("--file", action="append", default=[], help="'URL=Dateiname', wiederholbar")
    parser.add_argument("--no-discord", action="store_true", help="Discord-Post ueberspringen")
    args = parser.parse_args()

    items = parse_items(args)

    with open(args.config) as fh:
        config = json.load(fh)
    base_folder_id = config["drive"]["base_folder_id"]

    token = get_access_token()
    market_folder = find_or_create_folder(token, args.market, base_folder_id)
    product_folder = find_or_create_folder(token, args.product, market_folder)
    target_folder = find_or_create_folder(token, args.subfolder, product_folder)

    uploaded = []
    for item in items:
        print(f"Lade hoch: {item['filename']} <- {item['url']}", file=sys.stderr)
        result = upload_image(token, item["url"], item["filename"], target_folder)
        uploaded.append(result)
        print(f"  OK: {result.get('webViewLink', result['id'])}", file=sys.stderr)

    folder_link = f"https://drive.google.com/drive/folders/{target_folder}"
    print(json.dumps({"folder_id": target_folder, "folder_link": folder_link, "uploaded": uploaded}, indent=2))

    if not args.no_discord:
        post_discord_summary(args.market, args.product, args.subfolder, len(uploaded), folder_link)


if __name__ == "__main__":
    main()
