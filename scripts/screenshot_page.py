#!/usr/bin/env python3
"""Screenshot an arbitrary URL (e.g. a competitor funnel/advertorial page) and try to
locate its main product/hero image.

Used by the main pipeline (docs/workflow.md, Schritt 3) to capture the product photo
from a competitor's funnel page (Spalte D of the Funnel Sheet), which then serves as
the product-image reference for the Higgsfield translation prompt.

Usage:
  python3 screenshot_page.py --url "https://example.com/product/adv" --out /tmp/product

Writes:
  <out>.png        full-page screenshot (always taken, robust fallback)
  <out>_hero.png    the single largest above-the-fold <img>, if one is found
  <out>.json        {"url", "screenshot_path", "hero_image_path" or null,
                      "hero_image_src" or null}
"""
import argparse
import json
import os

PLAYWRIGHT_EXECUTABLE = "/opt/pw-browsers/chromium"


def capture(url, out_prefix, timeout_ms=30000):
    from playwright.sync_api import sync_playwright

    result = {
        "url": url,
        "screenshot_path": None,
        "hero_image_path": None,
        "hero_image_src": None,
    }

    with sync_playwright() as p:
        executable_path = PLAYWRIGHT_EXECUTABLE if os.path.exists(PLAYWRIGHT_EXECUTABLE) else None
        browser = p.chromium.launch(headless=True, executable_path=executable_path)
        page = browser.new_page(viewport={"width": 1280, "height": 1600})
        page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
        page.wait_for_timeout(2000)  # let lazy-loaded hero images settle

        screenshot_path = out_prefix + ".png"
        page.screenshot(path=screenshot_path, full_page=True)
        result["screenshot_path"] = screenshot_path

        # Heuristic: largest visible <img> in the first viewport is usually the
        # product/hero shot on these advertorial-style landing pages.
        largest = page.evaluate("""
            () => {
                const imgs = Array.from(document.querySelectorAll('img'));
                let best = null, bestArea = 0;
                for (const img of imgs) {
                    const r = img.getBoundingClientRect();
                    const area = r.width * r.height;
                    if (r.top < window.innerHeight * 2 && area > bestArea && img.src) {
                        best = img.src;
                        bestArea = area;
                    }
                }
                return best;
            }
        """)
        if largest:
            result["hero_image_src"] = largest
            try:
                hero_el = page.query_selector(f"img[src='{largest}']")
                if hero_el:
                    hero_path = out_prefix + "_hero.png"
                    hero_el.screenshot(path=hero_path)
                    result["hero_image_path"] = hero_path
            except Exception:
                pass  # full-page screenshot above is always the fallback

        browser.close()

    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--out", required=True, help="Output path prefix (no extension)")
    args = parser.parse_args()

    result = capture(args.url, args.out)
    with open(args.out + ".json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
