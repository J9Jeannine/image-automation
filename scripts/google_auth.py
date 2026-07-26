"""Google service-account auth for the image-automation pipeline.

Why this exists: the Google Drive MCP connector can only upload a file by pushing its
bytes as base64 through the model's context, which breaks on anything bigger than a few
KB, and it cannot write into a spreadsheet cell at all. The service account bypasses both
limits by talking to the Google APIs directly from the shell.

Credential: environment variable GOOGLE_SERVICE_ACCOUNT_JSON (full JSON key as a string).
Account:    image-automation-uploader@image-automation-502115.iam.gserviceaccount.com

The JWT is signed with the `openssl` CLI on purpose — the Python `cryptography` wheel is
broken in this sandbox (missing _cffi_backend), so `google-auth` cannot be used.
"""

import base64
import json
import os
import subprocess
import time

import requests

CA = "/root/.ccr/ca-bundle.crt"
SCOPES = (
    "https://www.googleapis.com/auth/drive "
    "https://www.googleapis.com/auth/spreadsheets"
)


def _b64u(raw: bytes) -> bytes:
    return base64.urlsafe_b64encode(raw).rstrip(b"=")


def token(scopes: str = SCOPES) -> str:
    """Return a fresh OAuth access token for the service account."""
    info = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])
    now = int(time.time())
    header = _b64u(json.dumps({"alg": "RS256", "typ": "JWT"}).encode())
    claims = _b64u(
        json.dumps(
            {
                "iss": info["client_email"],
                "scope": scopes,
                "aud": "https://oauth2.googleapis.com/token",
                "exp": now + 3600,
                "iat": now,
            }
        ).encode()
    )
    signing_input = header + b"." + claims

    key_path = "/tmp/_sa_key.pem"
    old_umask = os.umask(0o077)
    try:
        with open(key_path, "w") as fh:
            fh.write(info["private_key"])
    finally:
        os.umask(old_umask)
    try:
        signature = subprocess.run(
            ["openssl", "dgst", "-sha256", "-sign", key_path],
            input=signing_input,
            capture_output=True,
            check=True,
        ).stdout
    finally:
        os.remove(key_path)

    assertion = (signing_input + b"." + _b64u(signature)).decode()
    resp = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": assertion,
        },
        verify=CA,
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def headers(scopes: str = SCOPES) -> dict:
    return {"Authorization": f"Bearer {token(scopes)}"}
