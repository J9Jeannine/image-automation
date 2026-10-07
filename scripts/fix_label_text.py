#!/usr/bin/env python3
"""Setzt eine einzelne verstuemmelte Etikettzeile zeichengenau neu.

Das Bildmodell rendert die kleinsten Zeilen des TanLux-Etiketts (Zaehl-Badge
und Zutatenzeile) bei kleinem Dosendurchmesser unzuverlaessig. Diese Zeilen
stehen woertlich im LOCKED STRING, also wird genau ihr Rechteck neu gesetzt --
Hintergrundfarbe aus dem Bild selbst gemittelt, sonst bleibt das Bild unberuehrt.

  fix_label_text.py <bild> <out> badge   <x0> <y0> <x1> <y1>
  fix_label_text.py <bild> <out> line    <x0> <y0> <x1> <y1> <text> <dark|light>
"""
import sys
from PIL import Image, ImageDraw, ImageFont

BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
REG = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"


def bg_colour(im, box, light_text, pad=6):
    """Flaechenfarbe aus einem schmalen Ring AUSSERHALB des Rechtecks.

    Innerhalb des Rechtecks sitzt der (falsch gerenderte) Text und wuerde den
    Mittelwert verfaelschen -- der Ring zeigt die reine Etikettfarbe.
    """
    x0, y0, x1, y1 = box
    ring = []
    for xa, ya, xb, yb in ((x0 - pad, y0, x0, y1), (x1, y0, x1 + pad, y1),
                           (x0, y0 - pad, x1, y0), (x0, y1, x1, y1 + pad)):
        xa, ya = max(xa, 0), max(ya, 0)
        xb, yb = min(xb, im.width), min(yb, im.height)
        if xb > xa and yb > ya:
            ring += list(im.crop((xa, ya, xb, yb)).resize((6, 6)).getdata())
    if not ring:
        ring = list(im.crop(box).resize((6, 6)).getdata())
    ring.sort(key=sum)
    return ring[len(ring) // 2]


def fit(draw, text, box, font_path, max_h):
    x0, y0, x1, y1 = box
    size = max_h
    while size > 4:
        f = ImageFont.truetype(font_path, size)
        l, t, r, b = draw.textbbox((0, 0), text, font=f)
        if r - l <= (x1 - x0) * 0.94 and b - t <= max_h:
            return f, r - l, b - t, l, t
        size -= 1
    f = ImageFont.truetype(font_path, 5)
    l, t, r, b = draw.textbbox((0, 0), text, font=f)
    return f, r - l, b - t, l, t


def main():
    src, out, mode = sys.argv[1], sys.argv[2], sys.argv[3]
    x0, y0, x1, y1 = map(int, sys.argv[4:8])
    im = Image.open(src).convert("RGB")
    draw = ImageDraw.Draw(im)
    w, h = x1 - x0, y1 - y0

    if mode == "badge":
        # Das Badge ist selbst ein dunkles Rechteck -- seine Flaechenfarbe
        # steht im Rechteck, nicht daneben. Weisse Textpixel ausklammern.
        inner = sorted(im.crop((x0, y0, x1, y1)).resize((10, 10)).getdata(), key=sum)
        bg = inner[len(inner) // 5]
        draw.rectangle((x0, y0, x1, y1), fill=bg)
        for text, path, frac, cy in (("60", BOLD, 0.46, 0.38),
                                     ("Päiväannosta", REG, 0.20, 0.78)):
            f, tw, th, l, t = fit(draw, text, (x0, y0, x1, y1), path, int(h * frac))
            draw.text((x0 + (w - tw) / 2 - l, y0 + h * cy - th / 2 - t),
                      text, font=f, fill=(255, 255, 255))
    else:
        text, tone = sys.argv[8], sys.argv[9]
        light = tone == "light"
        bg = bg_colour(im, (x0, y0, x1, y1), light_text=light)
        draw.rectangle((x0, y0, x1, y1), fill=bg)
        f, tw, th, l, t = fit(draw, text, (x0, y0, x1, y1), REG, int(h * 0.92))
        draw.text((x0 + (w - tw) / 2 - l, y0 + (h - th) / 2 - t), text, font=f,
                  fill=(255, 255, 255) if light else (62, 30, 18))

    im.save(out)
    print(f"{mode} neu gesetzt: {(x0, y0, x1, y1)} Hintergrund {bg} -> {out}")


if __name__ == "__main__":
    main()
