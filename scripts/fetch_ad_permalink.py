#!/usr/bin/env python3
"""Fetch a single, already-known Meta Ad Library ad permalink and capture its creative.

Unlike scrape_ad_library.py (which searches the library by keyword), this script is
used by the main pipeline: the ad IDs come from comments the team already pasted into
column M of the Funnel Sheet (see docs/workflow.md, Schritt 2/4), so we only ever need
to open one known ad detail page at a time.

Usage:
  python3 fetch_ad_permalink.py --url "https://www.facebook.com/ads/library/?id=1692362565352629" --out /tmp/1692362565352629

Writes:
  <out>.json   {"ad_id", "permalink", "media_type", "media_url", "headline",
                "primary_text", "downloaded_media_path" or null,
                "screenshot_path" or null}
  <out>.png    full-ad screenshot (always taken, as a robust fallback per spec:
               "herunterladen ODER Screenshot machen")
  <out>.<ext>  the downloaded media file, if the direct media URL was reachable
"""
import argparse
import json
import os
import re
import sys
import urllib.request

PLAYWRIGHT_EXECUTABLE = "/opt/pw-browsers/chromium"


def extract_ad_id(url):
    match = re.search(r"[?&]id=(\d+)", url or "")
    return match.group(1) if match else None


def download(url, dest_path):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp, open(dest_path, "wb") as f:
            f.write(resp.read())
        return dest_path
    except Exception as e:
        print(f"download failed for {url}: {e}", file=sys.stderr)
        return None


def fetch(url, out_prefix, timeout_ms=30000):
    from playwright.sync_api import sync_playwright

    ad_id = extract_ad_id(url)
    result = {
        "ad_id": ad_id,
        "permalink": url,
        "media_type": None,
        "media_url": None,
        "headline": None,
        "primary_text": None,
        "downloaded_media_path": None,
        "screenshot_path": None,
    }

    with sync_playwright() as p:
        executable_path = PLAYWRIGHT_EXECUTABLE if os.path.exists(PLAYWRIGHT_EXECUTABLE) else None
        browser = p.chromium.launch(headless=True, executable_path=executable_path)
        page = browser.new_page(viewport={"width": 1000, "height": 1200})
        page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")

        try:
            card = page.wait_for_selector("div[role='article']", timeout=timeout_ms)
        except Exception:
            card = None

        if card:
            text_content = card.inner_text()
            lines = [l.strip() for l in text_content.split("\n") if l.strip()]
            result["headline"] = lines[0] if lines else None
            result["primary_text"] = " ".join(lines[1:4]) if len(lines) > 1 else None

            video_el = card.query_selector("video")
            img_el = card.query_selector("img")
            if video_el:
                result["media_type"] = "video"
                result["media_url"] = video_el.get_attribute("src")
            elif img_el:
                result["media_type"] = "image"
                result["media_url"] = img_el.get_attribute("src")

            screenshot_path = out_prefix + ".png"
            card.screenshot(path=screenshot_path)
            result["screenshot_path"] = screenshot_path
        else:
            # Selector didn't match (markup changed or ad unavailable) -- fall back to
            # a full-page screenshot so the run still produces something usable.
            screenshot_path = out_prefix + ".png"
            page.screenshot(path=screenshot_path, full_page=True)
            result["screenshot_path"] = screenshot_path

        browser.close()

    if result["media_url"]:
        ext = "mp4" if result["media_type"] == "video" else "jpg"
        media_path = f"{out_prefix}.{ext}"
        if download(result["media_url"], media_path):
            result["downloaded_media_path"] = media_path

    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True, help="Ad Library permalink, e.g. https://www.facebook.com/ads/library/?id=...")
    parser.add_argument("--out", required=True, help="Output path prefix (no extension)")
    args = parser.parse_args()

    result = fetch(args.url, args.out)
    with open(args.out + ".json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
