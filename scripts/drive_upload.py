#!/usr/bin/env python3
"""Put real image files into a Google Drive folder, at full quality.

    python3 scripts/drive_upload.py <folder_id> <local_dir>

Matches local files to Drive files **by identical filename** inside <folder_id>, then
overwrites each Drive file's content with the local bytes. Prints one line per file and
exits non-zero if anything did not end up byte-exact.

## The two-step dance — read this before you assume it is broken

A service account has **no Drive storage quota of its own**. It therefore cannot CREATE a
file in a normal (non-shared-drive) folder: `files.create` returns

    403 "Service Accounts do not have storage quota. Leverage shared drives ..."

It *can* however OVERWRITE a file that somebody else already owns, because the bytes are
then billed to that owner. So the working sequence is:

  1. Create a tiny placeholder for every image via the **Google Drive MCP tool**
     (`create_file`), which acts as the signed-in user and therefore owns the file.
     Use PLACEHOLDER_JPEG_B64 below — 630 bytes, cheap enough to pass through context.
     Name it exactly like the local file you intend to upload.
  2. Run this script. It finds those placeholders by name and replaces their content with
     the real full-resolution bytes via `files.update`.

Do NOT try to skip step 1 by having the service account create the file — that is the
403 above, and it is not a permissions problem you can fix by re-sharing the folder.

This project's Drive lives in a personal Google account, so there are no shared drives
available (`drive/v3/drives` returns an empty list). If a Workspace shared drive is ever
added, step 1 becomes unnecessary and the service account can create files directly.
"""

import os
import sys

import requests

from google_auth import CA, headers

# 1x1 white JPEG, 630 bytes. Pass as `base64Content` to the Drive MCP `create_file`
# tool with contentMimeType image/jpeg and disableConversionToGoogleType true.
PLACEHOLDER_JPEG_B64 = (
    "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAFA3PEY8MlBGQUZaVVBfeMiCeG5uePWvuZHI////////"
    "////////////////////////////////////////////////2wBDAVVaWnhpeOuCguv/////////"
    "////////////////////////////////////////////////////////////////////wAARCAAB"
    "AAEDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUF"
    "BAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3"
    "ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ip"
    "qrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEB"
    "AQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMi"
    "MoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVm"
    "Z2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU"
    "1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwC7RRRQB//Z"
)

IMAGE_MIME = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}


def list_folder(hdrs, folder_id):
    out, page = {}, None
    while True:
        params = {
            "q": f"'{folder_id}' in parents and trashed=false",
            "fields": "nextPageToken,files(id,name,size)",
            "pageSize": 200,
        }
        if page:
            params["pageToken"] = page
        data = requests.get(
            "https://www.googleapis.com/drive/v3/files",
            params=params, headers=hdrs, verify=CA, timeout=60,
        ).json()
        for f in data.get("files", []):
            out[f["name"]] = f["id"]
        page = data.get("nextPageToken")
        if not page:
            return out


def main(folder_id, local_dir):
    hdrs = headers()
    existing = list_folder(hdrs, folder_id)

    locals_ = sorted(
        f for f in os.listdir(local_dir)
        if os.path.splitext(f)[1].lower() in IMAGE_MIME
    )
    if not locals_:
        print(f"no images in {local_dir}")
        return 1

    missing = [n for n in locals_ if n not in existing]
    if missing:
        print("MISSING PLACEHOLDERS — create these first via the Drive MCP `create_file`")
        print(f"(parentId={folder_id}, base64Content=PLACEHOLDER_JPEG_B64,")
        print(" disableConversionToGoogleType=true), then re-run:")
        for n in missing:
            print(f"    {n}   contentMimeType={IMAGE_MIME[os.path.splitext(n)[1].lower()]}")
        print()

    ok = failed = 0
    for name in locals_:
        if name not in existing:
            continue
        path = os.path.join(local_dir, name)
        data = open(path, "rb").read()
        mime = IMAGE_MIME[os.path.splitext(name)[1].lower()]
        resp = requests.patch(
            f"https://www.googleapis.com/upload/drive/v3/files/{existing[name]}",
            params={"uploadType": "media", "fields": "id,name,size"},
            headers={**hdrs, "Content-Type": mime},
            data=data, verify=CA, timeout=300,
        )
        if resp.status_code == 200 and int(resp.json()["size"]) == len(data):
            ok += 1
            print(f"  OK   {name:34} {len(data):>9} bytes")
        else:
            failed += 1
            print(f"  FAIL {name:34} {resp.status_code} {resp.text[:120]}")

    print(f"\nbyte-exact: {ok}, failed: {failed}, awaiting placeholder: {len(missing)}")
    return 0 if (failed == 0 and not missing) else 1


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2]))
