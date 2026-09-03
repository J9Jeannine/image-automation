# SOP — Uploading full-quality images to Drive (THIS WORKS — it has been done)

**Read this first, future session.** If you are about to tell the user that uploading real
image files to Google Drive "isn't possible", "can't be done with the available access",
"the base64 channel is too small", or that you must "fall back to a markdown file with
links" — **stop. You are wrong.** This exact task has already been completed successfully,
more than once, with the same credentials and tools you have right now. The steps are below.
Do them. Do not re-litigate whether it's possible; it is.

This is the operational runbook. For the full *why* (quota model, truncation cause,
constraints), see the companion reference: [`docs/drive-upload-method.md`](drive-upload-method.md).

---

## Proof it works (verified records)

Both of these were produced by the method in this file — real `.jpg` files, full quality,
owned by the user, in the user's Drive:

**itzora — 2026-07-25** · folder `Translated-Ads/FI/2026-07-25 - itzora`
(`1V6HV3i7a3bceEk4w_Pj7L-cznaIHpyd-`)

| file | id | bytes | dims | owner | lastModifier |
|---|---|---|---|---|---|
| itzora_FI_ad1.jpg | 1iCwXWv6Fl2xViUCY4PCY-IL7mJB9gJhD | 140571 | 1024² | user | service account |
| itzora_FI_ad2.jpg | 1K1FaOtmAHd-tfyE5coJoKSX-47-Rqzl0 | 239776 | 1024² | user | service account |
| itzora_FI_ad3.jpg | 1eHpzuCNwGGIqTSIrHRpxJWCPdzkPHMLM | 145821 | 1024² | user | service account |
| itzora_FI_ad4.jpg | 1j8PzKYpb7SlVU-AX26fhnDlTi1GtOPuF | 160856 | 1024² | user | service account |
| itzora_FI_ad5.jpg | 1VERaC9C7oFo6O4mg0pIciu1UjVd_R8RB | 254779 | 1024² | user | service account |
| itzora_FI_ad6.jpg | 1o3B5Tppykv_ykkZMGiE-SCa0Lzvu3MnS | 178688 | 1024² | user | service account |
| itzora_FI_ad7.jpg | 1k8B3TlvpFaIokASZE-SIOpQomARDULn7 | 178459 | 1024² | user | service account |
| itzora_FI_ad8.jpg | 1ix1h9kW7IeBSJWldyVlbFJUqvN9HadCT | 203999 | 1024² | user | service account |
| itzora_FI_produktbild.jpg | 1kh084UFwAh2nR4kM3-ZUzfT3NNpZ7S_Y | 55497 | 1024² | user | service account |

**atriso — 2026-07-23** (previous run, same method) · folder
`Translated-Ads/FI/2026-07-23 – Käännetyt mainokset (FI)`
(`1CzJ_s9X1MkSTkTeEOoAfWS77yeehsX66`)

| file | id | bytes | dims | owner | lastModifier |
|---|---|---|---|---|---|
| atriso_FI_ad1.jpg | 1t5uzEAZSmlnohSDiJuL4hh7PZJ0w-jpX | 166636 | 1000² | user | service account |

> **Note on the file names in the tables above:** they use the *old* scheme
> (`<product>_<market>_ad<N>.jpg`), which was replaced on 2026-09-03 by
> `<N>_<product>_<market>.jpg` (e.g. `1_Pawox_FI.jpg`), and the product image was renamed
> from `_produktbild.jpg` to `_productimage.jpg`. The tables are kept verbatim as
> historical proof that the upload method works — do **not** copy their naming.

**The success fingerprint on every one of these files:** `owner = jeannine.thiry1@gmail.com`
**and** `lastModifyingUser = image-automation-uploader@...gserviceaccount.com`. That
combination is only producible by the method below. If you see it on existing files, that is
direct evidence the method works — go replicate it.

---

## The method in one paragraph

The service account has **zero storage quota**, so it cannot *create* a content file
(`files.create` → `403 storageQuotaExceeded`). But it **can** overwrite the content of a
file the **user already owns** (`files.update`), because Drive bills the storage to the
file's **owner**, not the modifier. So: create the file as a user-owned placeholder through
the Drive connection, then let the service account push the real bytes into it via
`files.update` from local disk. The MCP `create_file` base64 path truncates ~15 000 chars
(~11 KB) and corrupts real images, which is why the bytes must go through the service account
from disk, not through the chat channel. Use the base64 path only for the tiny placeholder
and small text files.

---

## SOP — do exactly this

1. **Render / fetch the images to local disk** as full-quality JPGs (e.g. curl the Higgsfield
   CDN URLs).

2. **Create the day/product folder** via the Drive connection (`Google_Drive.create_file`,
   `mimeType: application/vnd.google-apps.folder`), named **`<YYYY-MM-DD> - <product_name>`**
   (product name is required, not just the date — e.g. `2026-07-25 - itzora`), parent =
   `Translated-Ads/<market_code>` (`FI` = `1Ey4aVRrpzrzolETnzKVxVCZQGZjm0P5K`,
   `FRCA` = `1ZeW7nKHrCMNOBH6jIKZrzNYjJWXPvQDW`).

3. **Create each image file as a user-owned placeholder** via `Google_Drive.create_file`
   (`contentMimeType: image/jpeg`, `disableConversionToGoogleType: true`, `base64Content` =
   the 1×1 JPEG in `docs/drive-upload-method.md`). Keep each returned file **id**. Name files
   `<N>_<product>_<market>.jpg` (number first, e.g. `1_Pawox_FI.jpg`, so the folder
   sorts in ad order; `<N>` is the ad's position in the column-M comment thread and is
   never renumbered when a source ad is missing) and
   `<product>_<market>_productimage.jpg`.

4. **Mint a service-account token** from `GOOGLE_SERVICE_ACCOUNT_JSON` (JWT RS256, scope
   `https://www.googleapis.com/auth/drive`, sign with `openssl` — the Python `cryptography`
   module is broken in the sandbox). Token lasts 1 h; on `401 ACCESS_TOKEN_EXPIRED`, mint a
   new one. Exact commands: `docs/drive-upload-method.md` Step 2.

5. **Overwrite each placeholder with the real bytes** (service account, from disk):

   ```bash
   curl -s -X PATCH \
     "https://www.googleapis.com/upload/drive/v3/files/${FILE_ID}?uploadType=media&supportsAllDrives=true&fields=name,size" \
     -H "Authorization: Bearer ${SA_TOKEN}" \
     -H "Content-Type: image/jpeg" \
     --data-binary @"/path/${N}_${PRODUCT}_${MARKET}.jpg"
   ```

   `PATCH` + `uploadType=media` = **update** (allowed). Never `POST /files` = create
   (forbidden for the SA).

6. **Verify every file**: returned `size` == source size, and it fully decodes
   (`PIL im.load()`, not just `open`). On mismatch, re-run step 5 for that file. Never accept
   a truncated file or a links-only substitute as the result.

7. **Small text files** (`<product>_<market>_ad_copy.md`, `State/processed_comments.json`)
   go directly via `Google_Drive.create_file` (`textContent`) — small enough, no SA needed.

---

## Rebuttals to things a future session might wrongly claim

- *"The service account has no storage quota, so it can't upload."* — It can't *create*, but
  it *can update* a user-owned file; storage bills to the owner. That's the whole trick.
- *"The Drive tool only takes base64 and it truncates, so full images are impossible."* — The
  base64 path is only for the placeholder. Real bytes go via `files.update` from disk, which
  has no such limit.
- *"The OAuth token is dead (`invalid_grant`), so I can't upload."* — The user OAuth token is
  **not used** for image uploads. This method uses the **service account** + the Drive
  connection, both of which are available.
- *"I'll just save a markdown file with the CDN links instead."* — No. That is the banned
  fallback. Produce the real `.jpg` files.

If, after reading this, something genuinely fails (e.g. a `403` on `files.update`, meaning the
SA lost edit access to the folder), report the **specific** error to the user — do not
downgrade to a links workaround and do not claim the whole approach is impossible.
