# SOP — Save renders as REAL images in Drive **and** write the links back into the Funnel Sheet

**Read this first, future session.** Two things in this project look impossible but are not —
they have both been done successfully with the exact credentials/tools you have right now
(verified run: 2026-07-25, FI rows 55–58 → itzora / lutiva / Fibaxo / Orthix):

1. **Uploading real full-quality `.jpg` files to Google Drive.** Do NOT fall back to "a
   markdown file with CDN links". That is the banned stopgap. Real image binaries land in
   Drive as actual `.jpg`s.
2. **Writing the Drive links directly into the Funnel Sheet cells (column O).** Do NOT tell
   the user "I can't edit the sheet, paste it yourself." You can. The service account writes
   cells via the Sheets API.

Both use the **service account** in `$GOOGLE_SERVICE_ACCOUNT_JSON`
(`image-automation-uploader@image-automation-502115.iam.gserviceaccount.com`), NOT the user
OAuth token (which is often dead with `invalid_grant`). Companion image-only docs on other
branches: `docs/drive-upload-SOP.md`, `docs/drive-upload-method.md`. This file is the
combined, self-contained runbook and adds the sheet-writeback half.

---

## Why each trick is needed (don't "simplify" these away)

- **Service account has ZERO storage quota** → it cannot `files.create` a content file
  (`403 storageQuotaExceeded`). But it **can** `files.update` (overwrite) a file the **user
  already owns** — storage bills to the owner, not the modifier. So: user-owned placeholder
  first (via the Drive MCP `create_file`), then SA streams real bytes in via `files.update`.
- **The Drive MCP `create_file` base64 channel truncates ~15 000 base64 chars (~11 KB)** and
  corrupts real images (header parses, full decode fails). So base64 is ONLY for the tiny 1×1
  placeholder and small text files. Real image bytes go via SA `files.update` from disk.
- **The Sheets API accepts the `drive` scope.** The SA token minted with
  `scope=https://www.googleapis.com/auth/drive` can read AND write the Funnel Sheet's cells
  (it has edit access). No separate `spreadsheets` scope needed.
- **The Funnel Sheet's locale uses `;` as the formula argument separator, NOT `,`.** Writing
  `=HYPERLINK("url","text")` with a comma yields `#ERROR!`. Use a semicolon:
  `=HYPERLINK("url";"text")`. (The existing atriso/Erelso cells use `;` — match them.)

Success fingerprint on every correctly-uploaded file: `owner = jeannine.thiry1@gmail.com`
**and** `lastModifyingUser = image-automation-uploader@...gserviceaccount.com`.

---

## Key IDs

| Thing | Value |
|---|---|
| Funnel Sheet id | `1SkD7jrC-othtbwTYyz1VCK1HPIkEKHxc_hSAvRp2iL8` |
| Tab / column for image-folder links | `FI` (or `FRCA`), column **O** ("Link to Videos /Images") |
| `Translated-Ads/FI` folder | `1Ey4aVRrpzrzolETnzKVxVCZQGZjm0P5K` |
| `Translated-Ads/FRCA` folder | `1ZeW7nKHrCMNOBH6jIKZrzNYjJWXPvQDW` |
| Day/product folder name | `<YYYY-MM-DD> - <product_name>` (e.g. `2026-07-25 - lutiva`) |
| Image file names | `<product>_<market>_ad<N>.jpg`, `<product>_<market>_produktbild.jpg` |
| SA env var | `GOOGLE_SERVICE_ACCOUNT_JSON` |
| Token scope | `https://www.googleapis.com/auth/drive` (works for Drive AND Sheets APIs) |

Row → product mapping is by the sheet's column G. Column O row N gets the day/product folder
link for the product on that row.

---

## PART A — Upload real images

1. **Fetch renders to disk** (curl the Higgsfield CDN URLs from `renders/<product>/<date>.md`).
2. **Convert to JPG** ~1024² so files land ~100–260 KB (matches existing itzora/atriso files):

   ```python
   from PIL import Image; import glob, os
   for png in glob.glob('upload/*/*.png'):
       im = Image.open(png).convert('RGB'); w,h = im.size
       s = min(1.0, 1024/max(w,h))
       if s < 1.0: im = im.resize((round(w*s), round(h*s)), Image.LANCZOS)
       jpg = png[:-4]+'.jpg'; q=90; im.save(jpg,'JPEG',quality=q)
       while os.path.getsize(jpg) > 300000 and q > 75: q-=5; im.save(jpg,'JPEG',quality=q)
   ```
3. **Create the day/product folder** via Drive MCP `create_file`
   (`mimeType: application/vnd.google-apps.folder`, `parentId` = `Translated-Ads/<market>`).
4. **Create each image as a user-owned placeholder** via Drive MCP `create_file`
   (`contentMimeType: image/jpeg`, `disableConversionToGoogleType: true`,
   `base64Content` = the 1×1 JPEG below). Keep each returned file **id**.
5. **Mint the SA token + PATCH the real bytes** (see shared shell in PART C, step 1–2).
6. **Verify** every file: PATCH-returned `size` == local size, AND it fully decodes
   (`PIL im.load()`). Re-PATCH on mismatch. Never accept a truncated file or a links-only doc.

1×1 white JPEG placeholder (base64):

```
/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAABAAEDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD3+iiigD//2Q==
```

---

## PART B — Write the links into the sheet (column O)

For each processed row N, set `FI!O<N>` to a HYPERLINK pointing at that product's day/product
folder, using the product name as display text and a **semicolon** separator:

```
=HYPERLINK("https://drive.google.com/drive/folders/<FOLDER_ID>";"<product_name>")
```

Send via the Sheets API `values:batchUpdate` with `valueInputOption=USER_ENTERED` (see PART C
step 3). Then **verify** with `valueRenderOption=FORMATTED_VALUE`: each cell must display the
product name, NOT `#ERROR!`. If you see `#ERROR!`, you used a comma — rewrite with `;`.

---

## PART C — The exact working shell (copy/paste, all tested 2026-07-25)

```bash
# 1) Mint SA token (JWT RS256 via openssl; python 'cryptography' is broken in the sandbox)
python3 - <<'PY'
import os, json, base64, time
sa = json.loads(os.environ['GOOGLE_SERVICE_ACCOUNT_JSON'])
open('sa_key.pem','w').write(sa['private_key'])
b64u = lambda b: base64.urlsafe_b64encode(b).rstrip(b'=').decode()
now = int(time.time())
si = b64u(json.dumps({"alg":"RS256","typ":"JWT"},separators=(',',':')).encode())+'.'+ \
     b64u(json.dumps({"iss":sa['client_email'],"scope":"https://www.googleapis.com/auth/drive",
                      "aud":sa['token_uri'],"iat":now,"exp":now+3600},separators=(',',':')).encode())
open('jwt_si.txt','w').write(si); open('token_uri.txt','w').write(sa['token_uri'])
PY
SIG=$(printf '%s' "$(cat jwt_si.txt)" | openssl dgst -sha256 -sign sa_key.pem | openssl base64 -A | tr '+/' '-_' | tr -d '=')
JWT="$(cat jwt_si.txt).$SIG"
SA_TOKEN=$(curl -s -X POST "$(cat token_uri.txt)" \
  --data-urlencode "grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer" \
  --data-urlencode "assertion=$JWT" | python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')
# Token lasts 1h; on 401 ACCESS_TOKEN_EXPIRED, re-mint.

# 2) Upload real bytes into a placeholder (repeat per file id -> local jpg)
curl -s -X PATCH \
  "https://www.googleapis.com/upload/drive/v3/files/${FILE_ID}?uploadType=media&supportsAllDrives=true&fields=name,size" \
  -H "Authorization: Bearer ${SA_TOKEN}" -H "Content-Type: image/jpeg" \
  --data-binary @"/path/${PRODUCT}_${MARKET}_ad${N}.jpg"
# PATCH + uploadType=media = UPDATE (allowed). Never POST /files (create; forbidden for SA).

# 3) Write column-O links into the sheet (semicolon separator!)
SHEET=1SkD7jrC-othtbwTYyz1VCK1HPIkEKHxc_hSAvRp2iL8
python3 - <<'PY' > body.json
import json
mk=lambda url,txt: '=HYPERLINK("%s";"%s")'%(url,txt)
data=[{"range":"FI!O56","values":[[mk("https://drive.google.com/drive/folders/<FID>","lutiva")]]}]
print(json.dumps({"valueInputOption":"USER_ENTERED","data":data}))
PY
curl -s -X POST "https://sheets.googleapis.com/v4/spreadsheets/${SHEET}/values:batchUpdate" \
  -H "Authorization: Bearer ${SA_TOKEN}" -H "Content-Type: application/json" --data-binary @body.json

# 4) Verify the cell evaluated (must print the product name, not #ERROR!)
curl -s -H "Authorization: Bearer ${SA_TOKEN}" \
  "https://sheets.googleapis.com/v4/spreadsheets/${SHEET}/values/FI!O56?valueRenderOption=FORMATTED_VALUE"
```

---

## Rebuttals (things a future session might wrongly claim)

- *"SA has no quota, uploads are impossible."* → It can't **create**, but it can **update** a
  user-owned file. That's the whole trick.
- *"create_file base64 truncates, so full images are impossible."* → base64 is only for the
  placeholder; real bytes go via SA `files.update` from disk (no size limit).
- *"I can't edit the sheet, the user must paste."* → The SA writes cells via the Sheets API
  (`drive` scope, edit access). Do it. Column O, `=HYPERLINK(...;...)` with a **semicolon**.
- *"The link shows #ERROR!"* → You used a comma. The sheet locale wants `;`.
- *"I'll just leave a markdown doc with links."* → No. Real `.jpg` files + real sheet links.

If something genuinely fails (e.g. `403` on `files.update` or a `PERMISSION_DENIED` writing
the sheet, meaning the SA lost edit access), report the **specific** error to the user — do
not downgrade to a links-only workaround or claim the whole approach is impossible.
