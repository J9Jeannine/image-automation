#!/usr/bin/env python3
"""Mindestgroessen-Guard fuer die fertigen Ad-Bilder.

Verbindliche Regel: docs/workflow.md Schritt 7.1a, CLAUDE.md Regel 2a.
Jede Bilddatei, die in den Lieferordner hochgeladen wird, muss auf BEIDEN Seiten
mindestens MIN_EDGE_PX gross sein. Das Seitenverhaeltnis der Quell-Anzeige bleibt
davon unberuehrt -- es wird nie beschnitten oder gestreckt, sondern groesser
gerendert bzw. hochskaliert.

Aufruf (vor dem Upload, Schritt 7.3):

    python3 scripts/check_image_size.py <datei> [<datei> ...]

Exit 0 = alle Dateien gross genug, Upload erlaubt.
Exit 1 = mindestens eine Datei zu klein oder nicht lesbar -> NICHT hochladen,
         groesser neu rendern (bzw. per Higgsfield.upscale_image hochskalieren).

Optional kann mit --expect-ratio B:H zusaetzlich geprueft werden, dass das
Seitenverhaeltnis der Quell-Anzeige eingehalten wurde (Toleranz 2 %).
"""

import argparse
import sys

MIN_EDGE_PX = 600
RATIO_TOLERANCE = 0.02


def _size_from_header(data):
    """(breite, hoehe) nur aus dem Dateikopf -- reine Standardbibliothek.

    Bewusst ohne Pillow: das Skript laeuft als Guard vor jedem Upload und darf
    nicht daran scheitern, dass in der jeweiligen Session kein Pillow installiert
    ist (das python3 der Sandbox hat es z. B. nicht).
    """
    # PNG
    if data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR":
        return (int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big"))
    # GIF
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return (int.from_bytes(data[6:8], "little"), int.from_bytes(data[8:10], "little"))
    # WEBP
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        chunk = data[12:16]
        if chunk == b"VP8X":
            w = int.from_bytes(data[24:27], "little") + 1
            h = int.from_bytes(data[27:30], "little") + 1
            return (w, h)
        if chunk == b"VP8 ":
            w = int.from_bytes(data[26:28], "little") & 0x3FFF
            h = int.from_bytes(data[28:30], "little") & 0x3FFF
            return (w, h)
        if chunk == b"VP8L":
            bits = int.from_bytes(data[21:25], "little")
            return ((bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1)
    # JPEG -- Marker durchlaufen bis zum Start-of-Frame
    if data[:2] == b"\xff\xd8":
        i = 2
        n = len(data)
        while i + 9 < n:
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
                i += 2
                continue
            seglen = int.from_bytes(data[i + 2:i + 4], "big")
            if seglen < 2:
                break
            # SOF0..SOF15, ohne DHT (C4), JPG (C8) und DAC (CC)
            if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
                h = int.from_bytes(data[i + 5:i + 7], "big")
                w = int.from_bytes(data[i + 7:i + 9], "big")
                return (w, h)
            i += 2 + seglen
    return None


def read_size(path):
    """(breite, hoehe) der Bilddatei, oder None wenn nicht lesbar."""
    try:
        with open(path, "rb") as fh:
            data = fh.read()
    except OSError as exc:
        print(f"NICHT LESBAR  {path}  ({exc})")
        return None

    size = _size_from_header(data)
    if size and size[0] > 0 and size[1] > 0:
        return size

    # Exotisches Format: falls Pillow da ist, damit nachfassen.
    try:
        from PIL import Image
        import io
        with Image.open(io.BytesIO(data)) as im:
            return im.size
    except Exception:  # noqa: BLE001 - jeder Lesefehler ist ein Blocker
        pass

    print(f"NICHT LESBAR  {path}  (Maße nicht aus der Datei bestimmbar)")
    return None


def parse_ratio(text):
    try:
        w, h = text.replace("x", ":").split(":")
        return float(w) / float(h)
    except Exception:
        raise SystemExit(f"FEHLER: --expect-ratio '{text}' nicht als B:H lesbar")


def main():
    ap = argparse.ArgumentParser(description="Mindestgroesse der Ad-Bilder pruefen")
    ap.add_argument("files", nargs="+", help="zu pruefende Bilddateien")
    ap.add_argument("--min-edge", type=int, default=MIN_EDGE_PX,
                    help=f"Mindestlaenge beider Seiten in px (Default {MIN_EDGE_PX})")
    ap.add_argument("--expect-ratio", default=None,
                    help="erwartetes Seitenverhaeltnis der Quell-Anzeige, z. B. 4:5")
    args = ap.parse_args()

    expected = parse_ratio(args.expect_ratio) if args.expect_ratio else None
    failures = 0

    for path in args.files:
        size = read_size(path)
        if size is None:
            failures += 1
            continue
        w, h = size
        problems = []
        if w < args.min_edge or h < args.min_edge:
            problems.append(f"zu klein (Minimum {args.min_edge} x {args.min_edge})")
        if expected is not None:
            actual = w / h
            if abs(actual - expected) / expected > RATIO_TOLERANCE:
                problems.append(
                    f"Seitenverhaeltnis {actual:.3f} weicht von erwartet {expected:.3f} ab"
                )
        if problems:
            failures += 1
            print(f"ABGELEHNT     {path}  {w} x {h} px  -- " + "; ".join(problems))
        else:
            print(f"OK            {path}  {w} x {h} px")

    if failures:
        print(
            f"\n{failures} Datei(en) abgelehnt. NICHT hochladen: im selben "
            f"Seitenverhaeltnis groesser neu rendern oder per "
            f"Higgsfield.upscale_image hochskalieren (docs/workflow.md 7.1a)."
        )
        return 1

    print(f"\nAlle {len(args.files)} Datei(en) bestanden (>= {args.min_edge} px pro Seite).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
