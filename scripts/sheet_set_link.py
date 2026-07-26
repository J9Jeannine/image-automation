#!/usr/bin/env python3
"""Write a clickable Drive-folder link into a Funnel Sheet cell.

    python3 scripts/sheet_set_link.py <tab> <cell> <folder_url_or_id> <label>

Example — link the FRCA Itzora folder into column O of row 35:

    python3 scripts/sheet_set_link.py FRCA O35 1jWvVRShelG7vkQSKuFh2VUxDY_mkkzK4 Itzora

Column O ("[merged] Link to Videos /Images") is where the team expects the folder link,
matching how the FI rows are filled in.

## The locale trap — this is why a formula can look right and still show #ERROR!

The Funnel Sheet's locale is **nl_NL**, which uses a SEMICOLON as the formula argument
separator, not a comma. Writing

    =HYPERLINK("https://...","Itzora")      -> #ERROR!
    =HYPERLINK("https://...";"Itzora")      -> works

The Sheets API does not translate separators for you: `USER_ENTERED` parses the string in
the spreadsheet's own locale. This script reads the locale from the file and picks the
separator automatically, so it stays correct if the locale is ever changed.

Requires GOOGLE_SERVICE_ACCOUNT_JSON; the service account must have edit access to the
sheet (it does — it is shared as an editor).
"""

import json
import re
import sys

import requests

from google_auth import CA, headers

SHEET_ID = "1SkD7jrC-othtbwTYyz1VCK1HPIkEKHxc_hSAvRp2iL8"
# Locales that use ';' as the formula argument separator (decimal comma locales).
SEMICOLON_LOCALES = ("nl_", "de_", "fr_", "es_", "it_", "pt_", "da_", "fi_", "sv_", "nb_", "pl_", "tr_")


def folder_url(ref: str) -> str:
    if ref.startswith("http"):
        return ref
    return f"https://drive.google.com/drive/folders/{ref}"


def separator(hdrs) -> str:
    props = requests.get(
        f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}",
        params={"fields": "properties(locale)"},
        headers=hdrs, verify=CA, timeout=60,
    ).json()
    locale = props.get("properties", {}).get("locale", "")
    return ";" if locale.startswith(SEMICOLON_LOCALES) else ","


def main(tab, cell, ref, label):
    if not re.fullmatch(r"[A-Z]+\d+", cell):
        print(f"cell must look like O35, got {cell!r}")
        return 2
    hdrs = {**headers(), "Content-Type": "application/json"}
    sep = separator(hdrs)
    formula = f'=HYPERLINK("{folder_url(ref)}"{sep}"{label}")'
    rng = f"{tab}!{cell}"

    prev = requests.get(
        f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/{rng}",
        params={"valueRenderOption": "FORMULA"},
        headers=hdrs, verify=CA, timeout=60,
    ).json().get("values")
    if prev:
        print(f"  note: {rng} was not empty, overwriting -> {prev}")

    resp = requests.put(
        f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/{rng}",
        params={"valueInputOption": "USER_ENTERED"},
        headers=hdrs,
        data=json.dumps({"range": rng, "majorDimension": "ROWS", "values": [[formula]]}),
        verify=CA, timeout=60,
    )
    if resp.status_code != 200:
        print(f"  FAIL {rng}: {resp.status_code} {resp.text[:200]}")
        return 1

    shown = requests.get(
        f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/{rng}",
        headers=hdrs, verify=CA, timeout=60,
    ).json().get("values", [[""]])[0][0]
    if shown.startswith("#"):
        print(f"  FAIL {rng} renders as {shown} — wrong separator? used {sep!r}")
        return 1
    print(f"  OK   {rng} -> {shown}   ({formula})")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(*sys.argv[1:5]))
