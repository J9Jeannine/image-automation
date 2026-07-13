#!/usr/bin/env python3
"""Upload generated ad images straight from their source URL (Higgsfield CDN or
original ad creative) into a Google Drive folder, authenticating as a service
account -- without the image ever passing through the chat/model context.

Why this exists: the Drive MCP connector (`create_file`) can only upload a file by
embedding its full content as base64 text in a tool call. That breaks down well
before a single ~1 MB Higgsfield render fits (see docs/workflow.md, Schritt 7 and
STATUS.md) -- the model would have to emit millions of characters in one turn. This
script instead runs as a plain subprocess: it downloads the image over HTTP and
uploads it to Drive via a server-to-server API call, so size is a non-issue.

Auth: reads the full service-account JSON key from the GOOGLE_SERVICE_ACCOUNT_JSON
environment variable (not a file path -- the whole JSON content). Signs its own
JWT and exchanges it for an access token, using the `openssl` CLI for the RS256
signature (avoids depending on a Python crypto binding, which is not reliably
installed/working in every sandbox).

Folder layout: <base_folder_id>/<market_code>/<product_name>/ -- created on demand
if it doesn't exist yet. Pass --base-folder-id explicitly, or set it via
DRIVE_BASE_FOLDER_ID, or rely on config/automation.config.json's
`drive.base_folder_id`.

Usage (single file):
  python3 upload_to_drive.py --market FI --product Erelso \
      --url "https://d8j0ntlcm91z4.cloudfront.net/.../hf_....png" \
      --filename "Erelso_FI_20260711_ad4.png"

Usage (batch, manifest file or stdin):
  python3 upload_to_drive.py --manifest manifest.json
  # manifest.json:
  # {
  #   "market_code": "FI",
  #   "product_name": "Erelso",
  #   "base_folder_id": "176ElFPlxj5hvsVJ8O_AaQSlIoL25IzJD",   (optional)
  #   "items": [
  #     {"url": "https://.../hf_....png", "filename": "Erelso_FI_20260711_ad4.png"},
  #     {"url": "https://.../hf_....png", "filename": "Erelso_FI_20260711_ad5.png"}
  #   ]
  # }

Prints one JSON object to stdout:
  {"folder_id": "...", "folder_url": "https://drive.google.com/drive/folders/...",
   "uploaded": [{"filename": ..., "file_id": ..., "web_view_link": ...}, ...],
   "failed": [{"filename": ..., "error": ...}, ...]}
"""
import argparse
import base64
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request

DRIVE_API = "https://www.googleapis.com/drive/v3"
DRIVE_UPLOAD_API = "https://www.googleapis.com/upload/drive/v3/files"
TOKEN_URI_DEFAULT = "https://oauth2.googleapis.com/token"
SCOPE = "https://www.googleapis.com/auth/drive"


def b64url(raw_bytes):
    return base64.urlsafe_b64encode(raw_bytes).rstrip(b"=")


def load_service_account():
    raw = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not raw:
        sys.exit("GOOGLE_SERVICE_ACCOUNT_JSON is not set in the environment.")
    try:
        info = json.loads(raw)
    except json.JSONDecodeError as e:
        sys.exit(f"GOOGLE_SERVICE_ACCOUNT_JSON is not valid JSON: {e}")
    for field in ("client_email", "private_key"):
        if field not in info:
            sys.exit(f"GOOGLE_SERVICE_ACCOUNT_JSON is missing required field: {field}")
    return info


def sign_rs256(signing_input, private_key_pem):
    """Sign with the service account's RSA key via the `openssl` CLI.

    Avoids depending on a Python crypto binding (cryptography/PyJWT), which isn't
    reliably installed in every sandbox -- openssl is a much safer bet.
    """
    with tempfile.NamedTemporaryFile("w", suffix=".pem", delete=False) as key_file:
        key_file.write(private_key_pem)
        key_path = key_file.name
    try:
        os.chmod(key_path, 0o600)
        proc = subprocess.run(
            ["openssl", "dgst", "-sha256", "-sign", key_path],
            input=signing_input,
            capture_output=True,
            check=True,
        )
        return proc.stdout
    finally:
        os.remove(key_path)


def get_access_token(sa_info, scope=SCOPE):
    token_uri = sa_info.get("token_uri", TOKEN_URI_DEFAULT)
    now = int(time.time())
    header = {"alg": "RS256", "typ": "JWT"}
    claims = {
        "iss": sa_info["client_email"],
        "scope": scope,
        "aud": token_uri,
        "iat": now,
        "exp": now + 3600,
    }
    signing_input = b".".join([
        b64url(json.dumps(header, separators=(",", ":")).encode()),
        b64url(json.dumps(claims, separators=(",", ":")).encode()),
    ])
    signature = sign_rs256(signing_input, sa_info["private_key"])
    jwt = signing_input + b"." + b64url(signature)

    body = urllib.parse.urlencode({
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": jwt.decode(),
    }).encode()
    req = urllib.request.Request(token_uri, data=body, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            token_data = json.load(resp)
    except urllib.error.HTTPError as e:
        sys.exit(f"Token exchange failed ({e.code}): {e.read().decode(errors='replace')}")
    return token_data["access_token"]


def drive_request(access_token, method, url, data=None, json_body=None, extra_headers=None):
    headers = {"Authorization": f"Bearer {access_token}"}
    if extra_headers:
        headers.update(extra_headers)
    if json_body is not None:
        data = json.dumps(json_body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.load(resp) if resp.length != 0 else {}
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Drive API {method} {url} failed ({e.code}): {e.read().decode(errors='replace')}")


def find_or_create_folder(access_token, name, parent_id):
    escaped_name = name.replace("'", "\\'")
    query = (
        f"name = '{escaped_name}' and '{parent_id}' in parents "
        "and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    )
    url = f"{DRIVE_API}/files?q={urllib.parse.quote(query)}&fields=files(id,name)"
    result = drive_request(access_token, "GET", url)
    files = result.get("files", [])
    if files:
        return files[0]["id"]

    metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id],
    }
    created = drive_request(access_token, "POST", f"{DRIVE_API}/files?fields=id", json_body=metadata)
    return created["id"]


def resolve_project_folder(access_token, base_folder_id, market_code, product_name):
    market_folder_id = find_or_create_folder(access_token, market_code, base_folder_id)
    product_folder_id = find_or_create_folder(access_token, product_name, market_folder_id)
    return product_folder_id


def guess_mime_type(filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "webp": "image/webp",
        "gif": "image/gif",
        "mp4": "video/mp4",
    }.get(ext, "application/octet-stream")


def download_to_temp(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        fd, path = tempfile.mkstemp()
        with os.fdopen(fd, "wb") as f:
            f.write(resp.read())
    return path


def upload_file(access_token, local_path, filename, parent_id):
    mime_type = guess_mime_type(filename)
    metadata = {"name": filename, "parents": [parent_id]}
    boundary = "drive-upload-boundary-9f3c2a"
    with open(local_path, "rb") as f:
        media_bytes = f.read()

    body = (
        f"--{boundary}\r\n"
        "Content-Type: application/json; charset=UTF-8\r\n\r\n"
        f"{json.dumps(metadata)}\r\n"
        f"--{boundary}\r\n"
        f"Content-Type: {mime_type}\r\n\r\n"
    ).encode() + media_bytes + f"\r\n--{boundary}--".encode()

    url = f"{DRIVE_UPLOAD_API}?uploadType=multipart&fields=id,webViewLink"
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Authorization", f"Bearer {access_token}")
    req.add_header("Content-Type", f"multipart/related; boundary={boundary}")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Upload failed ({e.code}): {e.read().decode(errors='replace')}")


def run(market_code, product_name, base_folder_id, items):
    sa_info = load_service_account()
    access_token = get_access_token(sa_info)
    folder_id = resolve_project_folder(access_token, base_folder_id, market_code, product_name)
    folder_url = f"https://drive.google.com/drive/folders/{folder_id}"

    uploaded, failed = [], []
    for item in items:
        try:
            local_path = download_to_temp(item["url"])
            try:
                result = upload_file(access_token, local_path, item["filename"], folder_id)
            finally:
                os.remove(local_path)
            uploaded.append({
                "filename": item["filename"],
                "file_id": result["id"],
                "web_view_link": result.get("webViewLink"),
            })
        except Exception as e:
            failed.append({"filename": item.get("filename"), "error": str(e)})

    return {
        "folder_id": folder_id,
        "folder_url": folder_url,
        "uploaded": uploaded,
        "failed": failed,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--market", help="Market code, e.g. FI or FRCA (single-file mode)")
    parser.add_argument("--product", help="Product name, e.g. Erelso (single-file mode)")
    parser.add_argument("--url", help="Source image URL to download (single-file mode)")
    parser.add_argument("--filename", help="Target filename in Drive (single-file mode)")
    parser.add_argument("--base-folder-id", default=os.environ.get("DRIVE_BASE_FOLDER_ID"),
                         help="Drive folder ID to nest <market>/<product> under")
    parser.add_argument("--manifest", help="Path to a JSON manifest file, or '-' for stdin (batch mode)")
    args = parser.parse_args()

    if args.manifest:
        raw = sys.stdin.read() if args.manifest == "-" else open(args.manifest, encoding="utf-8").read()
        manifest = json.loads(raw)
        market_code = manifest["market_code"]
        product_name = manifest["product_name"]
        base_folder_id = manifest.get("base_folder_id") or args.base_folder_id
        items = manifest["items"]
    else:
        if not all([args.market, args.product, args.url, args.filename]):
            parser.error("single-file mode requires --market, --product, --url, --filename (or use --manifest)")
        market_code = args.market
        product_name = args.product
        base_folder_id = args.base_folder_id
        items = [{"url": args.url, "filename": args.filename}]

    if not base_folder_id:
        sys.exit("No base folder id given (--base-folder-id, DRIVE_BASE_FOLDER_ID, or manifest.base_folder_id).")

    result = run(market_code, product_name, base_folder_id, items)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["failed"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
