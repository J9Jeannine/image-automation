# SOP — Uploading full-quality images to Drive (THIS WORKS — it has been done)

**Read this first, future session.** If you are about to tell the user that uploading real
image files to Google Drive "isn't possible", "can't be done with the available access",
"the base64 channel is too small", or that you must "fall back to a markdown file with
links" — **stop. You are wrong.** Uploading is now a single `curl` call with no credentials
at all. The steps are below. Do them. Do not re-litigate whether it's possible; it is.

This is the operational runbook. For the full reference (call format, failure mode, naming
convention), see the companion file:
[`docs/drive-upload-method.md`](drive-upload-method.md).

---

## The method in one paragraph

An Apps Script web app in **the user's own Google account** takes a JSON body with
`folderId`, `name` and `url`, fetches the image URL **server-side** and writes the file into
that Drive folder. One call per image. No token, no OAuth, no service account, no
placeholder file, no local copy of the image needed for the upload. Because the script runs
as the user, the file is owned by the user and the storage is theirs — the two problems the
old method worked around (service account has no storage quota; the MCP base64 channel
truncates) simply don't exist here.

---

## SOP — do exactly this

1. **Render the images** (Higgsfield, `nano_banana_pro`) and keep each result's **CDN URL**.
   For the mandatory language QA you still `curl` the image to local disk and look at it
   with the `Read` tool (`docs/workflow.md` step 7.5) — that is QA, not the upload.

2. **Create the day/product folder** via the Drive connection (`Google_Drive.create_file`,
   `mimeType: application/vnd.google-apps.folder`), named **`<YYYY-MM-DD> - <product_name>`**
   (product name is required, not just the date — e.g. `2026-07-25 - itzora`), parent =
   `Translated-Ads/<market_code>` (`FI` = `1Ey4aVRrpzrzolETnzKVxVCZQGZjm0P5K`,
   `FRCA` = `1ZeW7nKHrCMNOBH6jIKZrzNYjJWXPvQDW`). Keep its id.

3. **Upload each image — one call per file:**

   ```bash
   ENDPOINT="https://script.google.com/macros/s/AKfycbx3em9-sB7jMOXRg58JO94A1muKq1fy-fKT1Vb85Go71RX6K_t5E5kk5EHXRr_pqrXdOQ/exec"

   curl -sS -L "$ENDPOINT" \
     -H "Content-Type: application/json" \
     -d "{\"folderId\":\"${FOLDER_ID}\",\"name\":\"${N}_${PRODUCT}_${MARKET}\",\"url\":\"${CDN_URL}\"}"
   ```

   **Never `-X POST`** — `-d` already makes it a POST, and `-X POST` would re-POST on the
   302 redirect to `googleusercontent.com` and break the call. `-L` is required.

   Name ad files `<running number>_<Productname>_<countrycode>` (e.g. `1_Pawox_FI`) — no
   file extension in the name — and the product image
   `<product>_<market>_produktbild.jpg`.

4. **Check the answer.** The web app returns **HTTP 200 even when it fails**; a failure is
   an HTML page containing `Exception: …` (e.g. `Invalid file or folder ID: …`). If the body
   contains `Exception`, the upload did **not** happen — report that exact message.

   **Fallback for `Exception: Request failed for <url> returned code 403`** (proven
   2026-10-02, Aurevia FI!110): some source hosts (e.g. `peach.pics`) block Google's
   server-side fetcher, although the sandbox can download the same URL. Then: download the
   file locally, upload it via Higgsfield `media_upload` → PUT bytes → `media_confirm`
   (upload only, **no generation, no credits**), and send the returned Higgsfield/CloudFront
   URL to the endpoint instead. Do this automatically, once per failed file — do not stop
   and ask, and never fall back to the service account.

5. **Verify every file** in Drive: it must exist in the target folder
   (`Google_Drive.search_files` / `get_file_metadata`) with a plausible size (> 10 KB).
   On failure, repeat step 3 for that file. Never accept a missing file or a links-only
   substitute as the result.

6. **Small text files** (`State/processed_comments.json`,
   `State/<product>_<market>_locked_strings.md`) go directly via
   `Google_Drive.create_file` (`textContent`, `disableConversionToGoogleType: true`) —
   small enough, no endpoint needed. **They never go into the delivery folder**, which
   holds image files only.

7. **Do not write anything into the Funnel Sheet.** The routine is read-only on the sheet;
   a trigger in the user's Google account fills the date / person / folder-link / status
   cells. See [`docs/sheet-writeback-SOP.md`](sheet-writeback-SOP.md).

---

## Rebuttals to things a future session might wrongly claim

- *"I need a service account / a token / OAuth to upload."* — No. The endpoint takes no
  credentials at all. `GOOGLE_SERVICE_ACCOUNT_JSON` is **not used any more** and must not be
  reintroduced.
- *"The Drive tool only takes base64 and it truncates, so full images are impossible."* —
  Irrelevant now: the bytes never pass through this session. The Apps Script fetches the URL
  itself.
- *"I have to download the image and create a placeholder first."* — No. Placeholder,
  `files.update` and the local copy for uploading are all gone. The only local download left
  is for the language QA.
- *"It returned HTTP 200, so it worked."* — Not necessarily. Check the body for
  `Exception:` and verify the file in Drive.
- *"I'll just save a markdown file with the CDN links instead."* — No. That is the banned
  fallback. Produce the real image files.
- *"I should also tick the sheet cells."* — No. All sheet writes were removed from the
  routine.

If, after reading this, something genuinely fails (e.g. the endpoint answers with an
`Exception` that names the folder id, meaning the folder is wrong or the deployment was
replaced), report the **specific** error to the user — do not downgrade to a links
workaround and do not claim the whole approach is impossible.
