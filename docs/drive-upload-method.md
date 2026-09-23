# Drive Upload Method — full-quality images (CANONICAL, always use this)

This is the **only** approved way to upload real image files (translated ads, product
images) into Google Drive in this project. It is used by every run, scheduled or manual.

> **Never** fall back to a "markdown file with CDN links" workaround. That was an old
> stopgap. Real image binaries must always land in Drive as actual image files, using the
> single call below. If an upload can't be verified, retry it — do not substitute a links
> document.

---

## TL;DR

One `curl` call per image against the Apps Script endpoint in the user's own Google
account. No credentials, no token, no service account, no placeholder file, no local
download:

```bash
curl -sS -L "https://script.google.com/macros/s/AKfycbx3em9-sB7jMOXRg58JO94A1muKq1fy-fKT1Vb85Go71RX6K_t5E5kk5EHXRr_pqrXdOQ/exec" \
  -H "Content-Type: application/json" \
  -d '{"folderId":"<Ordner-ID>","name":"<Dateiname>","url":"<Bild-URL>"}'
```

The script runs **inside the user's Google account**, fetches `url` server-side and writes
the file into `folderId`. Everything else is unchanged: same folders, same naming scheme,
same workflow.

---

## Rules for the call

- **Never use `-X POST`.** `curl -d` already makes it a POST. `script.google.com` always
  answers with a 302 to `googleusercontent.com`; with `-X POST` curl would re-POST to the
  redirect target and the call breaks. `-L` is mandatory, `-X POST` is forbidden.
- **One call per image.** No batching.
- `folderId` — Drive id of the target folder (day/product folder, or the set folder for
  `Winning Products`). Unchanged from before.
- `name` — the file name from the naming convention below. Unchanged from before.
- `url` — a directly fetchable image URL, normally the Higgsfield CDN URL of the rendered
  image. It must be reachable without a login, because the Apps Script fetches it, not this
  session.
- **No authentication of any kind.** The endpoint URL itself is the secret — don't paste it
  outside this repo/account.

## Checking the result — HTTP 200 is not enough

The web app answers **HTTP 200 even on failure**. An error comes back as an HTML page
containing `Exception: …`, e.g.:

```
Exception: Invalid file or folder ID: THIS_ID_DOES_NOT_EXIST (line 7, file "Code")
```

So:

1. If the response body contains `Exception`, the upload **failed** — report that exact
   message, don't ignore it and don't carry on as if the file existed.
2. Then verify in Drive: the file must be in the target folder
   (`Google_Drive.search_files` / `get_file_metadata`) with a plausible size (> 10 KB for a
   real ad image). On failure repeat the call for that file.

Never leave a missing file or a links-only result as the deliverable.

---

## What is gone (do not reintroduce)

The old two-step method is **removed completely**:

- no `GOOGLE_SERVICE_ACCOUNT_JSON`, no service-account e-mail, no JWT, no `openssl`
  signing, no token minting, no `401 ACCESS_TOKEN_EXPIRED` handling;
- no 1×1 placeholder JPEG created via `Google_Drive.create_file`;
- no `PATCH …/upload/drive/v3/files/{id}?uploadType=media` (`files.update`);
- no `owner = user` / `lastModifyingUser = service account` fingerprint to check.

It existed only because a service account has no storage quota and the MCP `create_file`
base64 channel truncates large values. The Apps Script endpoint sidesteps both: it runs as
the user (so the storage is the user's) and it streams the bytes server-side (so nothing
goes through the model context). Anyone re-adding the service-account path is breaking the
workflow.

The image no longer has to be downloaded to disk **for the upload**. It is still downloaded
with `curl` for the mandatory language QA (`docs/workflow.md` step 7.5), which looks at the
rendered image with the `Read` tool. Those are two separate things.

---

## Folder & file naming convention (unchanged)

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

Keep the returned folder id — it is the `folderId` of every upload call for this run.

### Step 1 — Upload each image (one call per file)

```bash
ENDPOINT="https://script.google.com/macros/s/AKfycbx3em9-sB7jMOXRg58JO94A1muKq1fy-fKT1Vb85Go71RX6K_t5E5kk5EHXRr_pqrXdOQ/exec"

curl -sS -L "$ENDPOINT" \
  -H "Content-Type: application/json" \
  -d "{\"folderId\":\"${FOLDER_ID}\",\"name\":\"${N}_${PRODUCT}_${MARKET}\",\"url\":\"${IMAGE_URL}\"}"
```

`${IMAGE_URL}` is the Higgsfield CDN URL of that rendered ad. For the product image the
name is `<product>_<market>_produktbild.jpg`.

### Step 2 — Verify (mandatory)

For every uploaded file:

- The response must **not** contain `Exception` (see "Checking the result" above).
- The file must show up in the target folder with a plausible size:

```bash
# via the Drive connection
Google_Drive.search_files  -> q: "'<FOLDER_ID>' in parents"
Google_Drive.get_file_metadata -> fields incl. size
```

If a file is missing or suspiciously small, repeat the call for that file.

### Step 3 — Small text files

`State/processed_comments.json` and `State/<product>_<market>_locked_strings.md` are small
enough to write directly with `Google_Drive.create_file` (`textContent`,
`disableConversionToGoogleType: true`). They belong in the `State/` folder; the delivery
folder holds image files only.

---

## The sheet is read-only for this routine

The routine **never writes into the Funnel Sheet** any more — no date, no `claude` in the
person column, no folder link, no status. A trigger in the user's own Google account does
that. Uploading the files is the last write this routine performs. See
`docs/sheet-writeback-SOP.md`.

---

## Quick reference

| Thing | Value |
|---|---|
| Endpoint | `https://script.google.com/macros/s/AKfycbx3em9-sB7jMOXRg58JO94A1muKq1fy-fKT1Vb85Go71RX6K_t5E5kk5EHXRr_pqrXdOQ/exec` |
| Credentials | none — no token, no service account, no OAuth |
| Call | `curl -sS -L "<endpoint>" -H "Content-Type: application/json" -d '{"folderId":…,"name":…,"url":…}'` |
| Forbidden | `-X POST` (breaks on the 302 redirect) |
| Failure signal | response body contains `Exception: …` (still HTTP 200) |
| Verification | file present in the target folder, plausible size |
| Base folder | `image creation` = `176EIFPlxj5hvsVJ8O_AaQSlIoL25IzJD` (6th char is capital **I**, not lowercase l) |
| Day folder name | `<YYYY-MM-DD> - <product_name>` (e.g. `2026-07-25 - itzora`) |
| File name | `<N>_<Productname>_<countrycode>` (product image: `<product>_<market>_produktbild.jpg`) |
