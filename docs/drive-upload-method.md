# Drive Upload Method — full-quality images (CANONICAL, always use this)

This is the **only** approved way to upload real image files (translated ads, product
images) into Google Drive in this project. It is used by every run, scheduled or manual.

> **Never** fall back to a "markdown file with CDN links" workaround. That was an old
> stopgap. Real image binaries must always land in Drive as actual `.jpg` files, using the
> two-step method below. If an upload can't be verified as full-quality, retry it — do not
> substitute a links document.

---

## TL;DR

1. **Create an empty/placeholder file owned by the user** (`jeannine.thiry1@gmail.com`) via
   the Drive connection (`Google_Drive.create_file`, tiny 1×1 JPEG).
2. **Have the service account overwrite that file's content with the real image bytes via
   `files.update`** (an *update* of the existing file — **not** `files.create`), streaming
   the bytes straight from local disk.
3. Verify the uploaded size matches the source and the image fully decodes.

Result: `owner = user`, `lastModifyingUser = service account`, full quality, no truncation.

---

## Why this specific method is needed (read before changing anything)

Two independent constraints force this exact shape:

1. **A service account has zero storage quota.** When the service account
   (`GOOGLE_SERVICE_ACCOUNT_JSON` → `image-automation-uploader@image-automation-502115.iam.gserviceaccount.com`)
   tries to **create** a file with content (`files.create` with bytes), Google rejects it:

   ```
   403 storageQuotaExceeded
   "Service Accounts do not have storage quota. Leverage shared drives, or use OAuth delegation instead."
   ```

   So the service account can **never** be the *creator* of an image file here (there is no
   Shared Drive, and domain-wide delegation isn't available for a consumer Gmail account).

2. **But updating a file the user already owns bills the storage to the user, not to the
   modifier.** When the service account calls `files.update` (media) on a file whose
   **owner** is the user, the bytes count against the **user's** Drive quota (the user has
   100 GB). The service account only needs *edit* permission on that file/folder — which it
   has on the `Translated-Ads` tree. This succeeds at full quality.

   This is exactly why the existing/working files show `owner = user` **and**
   `lastModifyingUser = service account`. That fingerprint is the tell-tale of this method.

3. **The Drive MCP `create_file` base64 channel truncates large values.** `create_file`
   passes `base64Content` through the model's tool-call context, which caps very long
   parameter values at roughly **15 000 base64 characters (~11 KB decoded)**. Anything
   larger arrives **truncated and corrupt** (the JPEG header parses but full decode fails
   with "broken data stream"). Real ad images are 100–260 KB, so they cannot go through
   this channel intact. Therefore `create_file` is used **only** for the tiny placeholder
   and for small text files (copy `.md`, `State/*.json`); the real image bytes always go via
   the service account's `files.update` from disk (no context channel, no size limit).

Put together: the user's Drive connection is the only thing that can *create* a user-owned
file, and the service account is the only thing that can *stream full bytes from disk* — so
we combine them. Neither alone is sufficient.

---

## Folder & file naming convention

- **Day/product folder:** `Translated-Ads/<market_code>/<YYYY-MM-DD> - <product_name>/`
  - The product name **must** be in the folder name, not just the date — e.g.
    **`2026-07-25 - itzora`**, not `2026-07-25`. This keeps multiple products processed on
    the same day distinguishable.
  - Parent folder ids (from `config/automation.config.json` → `drive`):
    - `Translated-Ads` = `1JWHztpl2Z6mE9WtcRTObRgwBRp1OsHCb`
    - `Translated-Ads/FI` = `1Ey4aVRrpzrzolETnzKVxVCZQGZjm0P5K`
    - `Translated-Ads/FRCA` = `1ZeW7nKHrCMNOBH6jIKZrzNYjJWXPvQDW`
- **File names inside that folder — MANDATORY, set by Jeannine on 2026-09-04:**
  - Ads: `<running number>_<Productname>_<countrycode>` — e.g. `1_Pawox_FI`,
    `2_Pawox_FI`, `1_Lumifirm_FRCA`. No leading zero, product name capitalised,
    country code as in the sheet (FI, FRCA, NLBE, SE, UK), and **no file extension in
    the name** — Drive derives it from the MIME type.
  - The old scheme `<product>_<market>_ad<N>.jpg` is **obsolete** and must not be used.
  - Product image (exception): `<product_name>_<market_code>_produktbild.jpg`
  - **No text file goes into the delivery folder.** The LOCKED STRING / FREIGABE record
    lives in `State/<product>_<market>_locked_strings.md`, not here.

---

## Step-by-step

### Step 0 — Create the day/product folder (once per run)

Via the Drive connection (`Google_Drive.create_file`):

- `mimeType`: `application/vnd.google-apps.folder`
- `title`: `<YYYY-MM-DD> - <product_name>` (e.g. `2026-07-25 - itzora`)
- `parentId`: the market's `Translated-Ads/<market_code>` folder id

Keep the returned folder id.

### Step 1 — Create each file as a user-owned placeholder

For every image you will upload, call `Google_Drive.create_file`:

- `title`: e.g. `itzora_FI_ad1.jpg`
- `parentId`: the day/product folder id from Step 0
- `contentMimeType`: `image/jpeg`
- `disableConversionToGoogleType`: `true`
- `base64Content`: a tiny **1×1 white JPEG** (below), which is well under the truncation cap

Keep each returned file **id**. The file is now owned by the user.

1×1 white JPEG placeholder (base64):

```
/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAABAAEDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD3+iiigD//2Q==
```

### Step 2 — Mint a service-account access token

The token is short-lived (1 hour); on `401 ACCESS_TOKEN_EXPIRED`, mint a fresh one and
retry. Build and sign the JWT with `openssl` — the Python `cryptography` module is broken in
this sandbox, so don't rely on it.

```bash
# Write the private key and build the JWT signing input
python3 - <<'PY'
import os, json, base64, time
sa = json.loads(os.environ['GOOGLE_SERVICE_ACCOUNT_JSON'])
open('sa_key.pem','w').write(sa['private_key'])
b64u = lambda b: base64.urlsafe_b64encode(b).rstrip(b'=').decode()
now = int(time.time())
header = {"alg":"RS256","typ":"JWT"}
claim  = {"iss":sa['client_email'],
          "scope":"https://www.googleapis.com/auth/drive",
          "aud":sa['token_uri'], "iat":now, "exp":now+3600}
si = b64u(json.dumps(header,separators=(',',':')).encode()) + '.' + \
     b64u(json.dumps(claim ,separators=(',',':')).encode())
open('jwt_si.txt','w').write(si)
open('token_uri.txt','w').write(sa['token_uri'])
PY

# Sign with openssl (RS256), base64url-encode the signature, assemble the JWT
SIG=$(printf '%s' "$(cat jwt_si.txt)" | openssl dgst -sha256 -sign sa_key.pem \
      | openssl base64 -A | tr '+/' '-_' | tr -d '=')
JWT="$(cat jwt_si.txt).$SIG"

# Exchange the JWT for an access token
SA_TOKEN=$(curl -s -X POST "$(cat token_uri.txt)" \
  --data-urlencode "grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer" \
  --data-urlencode "assertion=$JWT" | python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')
```

### Step 3 — Overwrite each placeholder with the real bytes (files.update, NOT create)

For each file id from Step 1 and its local full-quality JPG on disk:

```bash
curl -s -X PATCH \
  "https://www.googleapis.com/upload/drive/v3/files/${FILE_ID}?uploadType=media&supportsAllDrives=true&fields=name,size" \
  -H "Authorization: Bearer ${SA_TOKEN}" \
  -H "Content-Type: image/jpeg" \
  --data-binary @"/path/to/${PRODUCT}_${MARKET}_ad${N}.jpg"
```

Note `PATCH` + `/upload/…?uploadType=media` = **update the media of an existing file**. Do
**not** use `POST …/files` (`files.create`) — that path is what the service account is
forbidden from doing.

### Step 4 — Verify (mandatory)

For every uploaded file:

- The `size` returned by the PATCH must equal the local source file's byte size.
- Download the bytes back and confirm the image **fully decodes** (not just opens):

```bash
curl -s -H "Authorization: Bearer ${SA_TOKEN}" \
  "https://www.googleapis.com/drive/v3/files/${FILE_ID}?alt=media&supportsAllDrives=true" -o /tmp/verify.jpg
python3 -c "from PIL import Image; im=Image.open('/tmp/verify.jpg'); im.load(); print('OK', im.size)"
```

If size mismatches or decode fails, re-run Step 3 for that file. Never leave a truncated or
links-only result as the deliverable.

### Step 5 — Small text files

The ad copy (`<product>_<market>_ad_copy.md`) and `State/processed_comments.json` are small
enough to write directly with `Google_Drive.create_file` (`textContent`) — no truncation and
no service account needed for those.

---

## Quick reference

| Thing | Value |
|---|---|
| Service account env var | `GOOGLE_SERVICE_ACCOUNT_JSON` |
| Service account email | `image-automation-uploader@image-automation-502115.iam.gserviceaccount.com` |
| Token scope | `https://www.googleapis.com/auth/drive` |
| Placeholder creator | Drive connection `create_file` (user-owned) |
| Real-byte upload | `PATCH /upload/drive/v3/files/{id}?uploadType=media` (service account) |
| Success fingerprint | `owner = user`, `lastModifyingUser = service account` |
| Base folder | `image creation` = `176EIFPlxj5hvsVJ8O_AaQSlIoL25IzJD` (6th char is capital **I**, not lowercase l) |
| Day folder name | `<YYYY-MM-DD> - <product_name>` (e.g. `2026-07-25 - itzora`) |

The `GOOGLE_OAUTH_*` user credentials are **not** required for image uploads. (They were
failing with `invalid_grant` because the OAuth consent screen is in "Testing", which expires
Gmail refresh tokens after 7 days. Fixing that — publish to production, re-mint — only
matters for other OAuth-based parts, not for this upload path.)
