#!/usr/bin/env python3
"""Scrape the public Meta (Facebook) Ad Library for a given advertiser/search term.

No login required — this only reads the public "All ads" search results page. The page
is a JS-rendered SPA, so a plain HTTP fetch will not return ad data; this script drives
a real (headless) Chromium via Playwright, waits for ad cards to render, and extracts
image/video URL, headline, primary text, and the ad's permalink for each card.

Usage:
  python3 scrape_ad_library.py --search-term "Acme Widgets" --country DE --max-ads 15
  python3 scrape_ad_library.py --page-id 123456789012345 --country DE --max-ads 15

Output: JSON array on stdout, one object per ad:
  {"ad_id": "...", "permalink": "...", "media_type": "image"|"video",
   "media_url": "...", "headline": "...", "primary_text": "..."}

Be a good citizen: this only reads public data at a low, config-driven cadence
(see config/automation.config.json -> advertiser.max_ads_per_run and cadence). Do not
raise max_ads or run frequency beyond what's needed for competitive monitoring.
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.parse

PLAYWRIGHT_EXECUTABLE = "/opt/pw-browsers/chromium"
AD_LIBRARY_BASE = "https://www.facebook.com/ads/library/"


def build_search_url(search_term, page_id, country):
    params = {
        "active_status": "active",
        "ad_type": "all",
        "country": country,
        "is_targeted_country": "false",
        "media_type": "all",
    }
    if page_id:
        params["view_all_page_id"] = page_id
    else:
        params["q"] = search_term
        params["search_type"] = "keyword_unordered"
    return AD_LIBRARY_BASE + "?" + urllib.parse.urlencode(params)


def extract_ad_id(permalink):
    match = re.search(r"[?&]id=(\d+)", permalink or "")
    return match.group(1) if match else None


def scrape(search_term, page_id, country, max_ads, timeout_ms=45000):
    from playwright.sync_api import sync_playwright

    url = build_search_url(search_term, page_id, country)
    results = []

    with sync_playwright() as p:
        executable_path = PLAYWRIGHT_EXECUTABLE if os.path.exists(PLAYWRIGHT_EXECUTABLE) else None
        browser = p.chromium.launch(headless=True, executable_path=executable_path)
        page = browser.new_page(viewport={"width": 1400, "height": 1000})
        page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")

        try:
            page.wait_for_selector("[data-testid='ad-library-card'], div[role='article']", timeout=timeout_ms)
        except Exception:
            browser.close()
            print(json.dumps({"error": "no ad cards rendered — selector may be stale, "
                                        "check Meta Ad Library markup"}), file=sys.stderr)
            return []

        # Ad Library infinite-scrolls; scroll until we have enough cards or stop growing.
        seen_heights = set()
        for _ in range(20):
            cards = page.query_selector_all("div[role='article']")
            if len(cards) >= max_ads:
                break
            height = page.evaluate("document.body.scrollHeight")
            if height in seen_heights:
                break
            seen_heights.add(height)
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(1500)

        cards = page.query_selector_all("div[role='article']")[:max_ads]
        for card in cards:
            text_content = card.inner_text()
            lines = [l.strip() for l in text_content.split("\n") if l.strip()]

            link_el = card.query_selector("a[href*='/ads/library/?id=']")
            permalink = link_el.get_attribute("href") if link_el else None

            img_el = card.query_selector("img")
            video_el = card.query_selector("video")
            media_type = "video" if video_el else "image"
            media_url = None
            if video_el:
                media_url = video_el.get_attribute("src")
            elif img_el:
                media_url = img_el.get_attribute("src")

            headline = lines[0] if lines else None
            primary_text = " ".join(lines[1:4]) if len(lines) > 1 else None

            results.append({
                "ad_id": extract_ad_id(permalink),
                "permalink": permalink,
                "media_type": media_type,
                "media_url": media_url,
                "headline": headline,
                "primary_text": primary_text,
            })

        browser.close()

    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--search-term", default=None, help="Advertiser/brand/keyword to search for")
    parser.add_argument("--page-id", default=None, help="Facebook Page ID to view all ads for (alternative to --search-term)")
    parser.add_argument("--country", required=True, help="Country code for the Ad Library search, e.g. DE, FR, BE")
    parser.add_argument("--max-ads", type=int, default=15)
    args = parser.parse_args()

    if not args.search_term and not args.page_id:
        parser.error("either --search-term or --page-id is required")

    results = scrape(args.search_term, args.page_id, args.country, args.max_ads)
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
