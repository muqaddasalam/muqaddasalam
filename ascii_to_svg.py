#!/usr/bin/env python3
"""
ascii_to_svg.py  -  builds dark.svg and light.svg for a GitHub profile README.

Usage:
    python3 ascii_to_svg.py --photo portrait.jpg --crop 0,170,1108,1420 --out .
"""
import argparse
import os
from xml.sax.saxutils import escape

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps

TITLE = "muqaddas@github  ~/profile  zsh"
ROWS_RIGHT = [
    ("h", "profile"),
    ("r", "Name", "Muqaddas Alam"),
    ("r", "Role", "Computer Science Student"),
    ("r", "Origin", "Karachi, Pakistan"),
    ("r", "Education", "HSC II (ICS) · Govt. Degree College for Women, Nazimabad"),
    ("r", "Status", "Building · Learning · Sharing"),
    ("r", "Workflow", "VS Code · Git · GitHub"),
    ("r", "Brand", "Muqaddas Digital — Learn, Grow, Share"),
    ("gap",),
    ("h", "stack"),
    ("r", "Core Lang", "C, C++, Python"),
    ("r", "Core Frontend", "HTML, CSS, JavaScript"),
    ("r", "Interests", "Front-end Web · Cybersecurity"),
    ("r", "Internships", "CodeAlpha (C) · Arch Technologies (C++)"),
    ("gap",),
    ("h", "contact"),
    ("r", "Mail", "muqaddasalm999@gmail.com"),
    ("r", "GitHub", "github.com/muqaddasalam"),
    ("r", "LinkedIn", "linkedin.com/in/muqaddas-alam-405194312"),
    ("gap",),
    ("h", "live stats"),
    ("last", "See live GitHub stats badges below in README"),
]
STATUS_TEXT = "online · Karachi, PK"

THEMES = {
    "dark": dict(
        bg="#0d1117", panel="#0a0e14", dim="#30363d", title="#8b949e",
        key="#22d3ee", head="#a78bfa", val="#c9d1d9", ok="#3fb950",
        b1="#7c5cff", b2="#22d3ee", art1="#22d3ee", art2="#8b5cf6",
        scan="#22d3ee", scan_op="0.22", glow_op="0.9",
    ),
    "light": dict(
        bg="#ffffff", panel="#f6f8fa", dim="#d0d7de", title="#57606a",
        key="#0969da", head="#8250df", val="#24292f", ok="#1a7f37",
        b1="#8250df", b2="#0969da", art1="#0550ae", art2="#6639ba",
        scan="#0969da", scan_op="0.16", glow_op="0.55",
    ),
}

W, H = 1000, 496
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"

COLS, ROWS = 64, 39
CHAR_W, LINE_H, ART_FONT = 4.7, 8.7, 7.8
RAMP = " .:-=+*#%@"

LP_X, LP_Y, LP_W, LP_H = 22, 58, 330, 412
RP_X, RP_Y, RP_W, RP_H = 372, 58, 606, 412
TX0, TX1 = 392, 958
FS, CH = 12.5, 7.5
LINE, GAP, FIRST_Y = 19, 9, 92


def placeholder_density():
    w, h = 300, 400
    im = Image.new("L", (w, h), 10)
    d = ImageDraw.Draw(im)
    d.ellipse((70, 40, 230, 250), fill=110)
    d.ellipse((20, 300, 280, 560), fill=150)
    d.ellipse((100, 80, 200, 235), fill=225)
    return im.filter(ImageFilter.GaussianBlur(2.2))


# Backdrop is removed with a colour mask (backdrop = grey-olive, hue ~30 deg,
# low saturation; clothes/skin = redder, hue < 26 deg or more saturated).
# Inside the subject: dark cloth -> dense ink, skin -> light dots.
POINTS = [(0, 1), (25, 1), (60, .8), (90, .55), (130, .38), (170, .26), (255, .22)]
CURVES = {"dark": POINTS, "light": POINTS}


def curve_lut(points):
    lut = []
    for v in range(256):
        for (x0, y0), (x1, y1) in zip(points, points[1:]):
            if x0 <= v <= x1:
                lut.append(int(255 * (y0 + (y1 - y0) * (v - x0) / (x1 - x0))))
                break
    return lut


def photo_density(path, theme, box=None):
    import numpy as np
    src = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    w, h = src.size
    target = COLS * CHAR_W / (ROWS * LINE_H)
    if box:
        src = src.crop(box)
    elif w / h > target:
        nw = int(h * target)
        left = (w - nw) // 2
        src = src.crop((left, 0, left + nw, h))
    else:
        nh = int(w / target)
        src = src.crop((0, 0, w, nh))
    hsv = np.asarray(src.convert("HSV")).astype(float)
    hue = hsv[..., 0] * 360 / 255
    sat = hsv[..., 1] / 255
    val = hsv[..., 2] / 255
    fg = (hue < 26) | (sat > 0.45) | (val > 0.62) | (val < 0.2)
    mask = Image.fromarray((fg * 255).astype("uint8")).filter(ImageFilter.MedianFilter(15))
    mask = mask.filter(ImageFilter.GaussianBlur(2))
    gray = src.convert("L").filter(ImageFilter.GaussianBlur(0.9)).point(curve_lut(CURVES[theme]))
    return ImageChops.multiply(gray, mask.point(lambda v: 255 if v > 128 else 0))


def portrait_rows(photo, theme, box=None):
    im = photo_density(photo, theme, box) if photo else placeholder_density()
    im = im.resize((COLS, ROWS), Image.LANCZOS)
    px = im.load()
    n = len(RAMP)
    return ["".join(RAMP[min(n - 1, px[x, y] * n // 256)] for x in range(COLS))
            for y in range(ROWS)]


def t(sec):
    return f"{sec:.2f}s"


def build(theme, photo, box=None):
    p = THEMES[theme]
    rows = portrait_rows(photo, theme, box)
    defs, body = [], []

    defs.append(
        f'<linearGradient id="bg-grad" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="{W}" y2="{H}">'
        f'<stop offset="0" stop-color="{p["b1"]}">'
        f'<animate attributeName="stop-color" values="{p["b1"]};{p["b2"]};{p["b1"]}" dur="8s" repeatCount="indefinite"/></stop>'
        f'<stop offset="1" stop-color="{p["b2"]}">'
        f'<animate attributeName="stop-color" values="{p["b2"]};{p["b1"]};{p["b2"]}" dur="8s" repeatCount="indefinite"/></stop>'
        f'</linearGradient>'
    )
    defs.append(
        f'<linearGradient id="art-grad" gradientUnits="userSpaceOnUse" x1="0" y1="96" x2="0" y2="440">'
        f'<stop offset="0" stop-color="{p["art1"]}"/><stop offset="1" stop-color="{p["art2"]}"/></linearGradient>'
    )
    defs.append(
        f'<linearGradient id="scan-grad" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{p["scan"]}" stop-opacity="0"/>'
        f'<stop offset="0.5" stop-color="{p["scan"]}" stop-opacity="{p["scan_op"]}"/>'
        f'<stop offset="1" stop-color="{p["scan"]}" stop-opacity="0"/></linearGradient>'
    )
    defs.append(
        '<filter id="glow" x="-5%" y="-5%" width="110%" height="110%">'
        '<feGaussianBlur stdDeviation="3" result="b"/>'
        '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
    )
    defs.append(
        f'<clipPath id="art-clip"><rect x="{LP_X + 1}" y="{LP_Y + 30}" width="{LP_W - 2}" height="{LP_H - 62}"/></clipPath>'
    )

    body.append(f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="14" fill="{p["bg"]}" '
                f'stroke="url(#bg-grad)" stroke-width="1.5"/>')
    perim = 2 * ((W - 2) + (H - 2))
    body.append(
        f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="14" fill="none" stroke="url(#bg-grad)" '
        f'stroke-width="3" stroke-linecap="round" stroke-dasharray="160 {perim}" '
        f'opacity="{p["glow_op"]}" filter="url(#glow)">'
        f'<animate attributeName="stroke-dashoffset" from="0" to="-{perim}" dur="7s" repeatCount="indefinite"/></rect>'
    )

    for cx, col in ((28, "#ff5f56"), (50, "#ffbd2e"), (72, "#27c93f")):
        body.append(f'<circle cx="{cx}" cy="22" r="6" fill="{col}"/>')
    body.append(
        f'<text x="{W // 2}" y="26" text-anchor="middle" font-family="{MONO}" font-size="12" '
        f'fill="{p["title"]}">{escape(TITLE)}</text>'
    )
    body.append(f'<line x1="14" y1="42" x2="{W - 14}" y2="42" stroke="{p["dim"]}" stroke-width="1"/>')

    body.append(f'<rect x="{LP_X}" y="{LP_Y}" width="{LP_W}" height="{LP_H}" rx="8" fill="{p["panel"]}" '
                f'stroke="{p["dim"]}" stroke-width="1"/>')
    body.append(f'<text x="{LP_X + 14}" y="{LP_Y + 20}" font-family="{MONO}" font-size="11" '
                f'fill="{p["title"]}">portrait.asc</text>')

    art_w = COLS * CHAR_W
    art_x = LP_X + (LP_W - art_w) / 2
    art_y = LP_Y + 48
    body.append('<g id="portrait">')
    for i, row in enumerate(rows):
        if not row.strip():
            continue
        y = art_y + i * LINE_H
        body.append(
            f'<text x="{art_x:.1f}" y="{y:.1f}" xml:space="preserve" font-family="{MONO}" '
            f'font-size="{ART_FONT}" fill="url(#art-grad)" opacity="0" '
            f'textLength="{art_w:.1f}" lengthAdjust="spacing">{escape(row)}'
            f'<animate attributeName="opacity" from="0" to="1" begin="{t(0.5 + i * 0.045)}" '
            f'dur="0.25s" fill="freeze"/></text>'
        )
    body.append(
        '<animate attributeName="opacity" values="1;0.8;1;0.92;1" keyTimes="0;0.2;0.4;0.7;1" '
        'dur="5s" begin="3s" repeatCount="indefinite"/></g>'
    )
    body.append(
        f'<g clip-path="url(#art-clip)"><rect x="{LP_X}" y="{LP_Y + 30}" width="{LP_W}" height="26" '
        f'fill="url(#scan-grad)" opacity="0">'
        f'<set attributeName="opacity" to="1" begin="1.8s"/>'
        f'<animateTransform attributeName="transform" type="translate" from="0 -26" to="0 {LP_H - 40}" '
        f'begin="1.8s" dur="3.4s" repeatCount="indefinite"/></rect></g>'
    )
    sy = LP_Y + LP_H - 18
    body.append(
        f'<circle cx="{LP_X + 20}" cy="{sy - 4}" r="4" fill="{p["ok"]}">'
        f'<animate attributeName="r" values="3;5;3" dur="1.8s" repeatCount="indefinite"/>'
        f'<animate attributeName="opacity" values="1;0.45;1" dur="1.8s" repeatCount="indefinite"/></circle>'
        f'<text x="{LP_X + 34}" y="{sy}" font-family="{MONO}" font-size="11" fill="{p["val"]}">'
        f'{escape(STATUS_TEXT)}</text>'
    )

    body.append(f'<rect x="{RP_X}" y="{RP_Y}" width="{RP_W}" height="{RP_H}" rx="8" fill="{p["panel"]}" '
                f'stroke="{p["dim"]}" stroke-width="1"/>')
    body.append(f'<text x="{RP_X + RP_W - 14}" y="{RP_Y + 20}" text-anchor="end" font-family="{MONO}" '
                f'font-size="11" fill="{p["title"]}">profile.yml</text>')

    wipe_w = TX1 - TX0 + 14
    cx0 = TX0 - 6
    y = FIRST_Y
    t0, step, dur = 1.0, 0.30, 0.28
    n = 0
    last_caret = None
    for row in ROWS_RIGHT:
        kind = row[0]
        if kind == "gap":
            y += GAP
            continue
        begin = t0 + n * step
        cid = f"w{n}"
        defs.append(
            f'<clipPath id="{cid}"><rect x="{cx0}" y="{y - 14}" width="0" height="20">'
            f'<animate attributeName="width" from="0" to="{wipe_w}" begin="{t(begin)}" dur="{t(dur)}" '
            f'fill="freeze"/></rect></clipPath>'
        )
        g = [f'<g clip-path="url(#{cid})">']
        if kind == "h":
            label = row[1]
            g.append(f'<text x="{TX0}" y="{y}" font-family="{MONO}" font-size="{FS}" font-weight="bold" '
                     f'fill="{p["head"]}">{escape(label)}</text>')
            lx = TX0 + len(label) * CH + 10
            g.append(f'<line x1="{lx:.0f}" y1="{y - 4}" x2="{TX1}" y2="{y - 4}" stroke="{p["dim"]}" stroke-width="1"/>')
        elif kind == "r":
            key, val = row[1], row[2]
            kx = TX0 + 12
            g.append(f'<text x="{kx}" y="{y}" font-family="{MONO}" font-size="{FS}" fill="{p["key"]}">{escape(key)}</text>')
            g.append(f'<text x="{TX1}" y="{y}" text-anchor="end" font-family="{MONO}" font-size="{FS}" '
                     f'fill="{p["val"]}">{escape(val)}</text>')
            ds = kx + len(key) * CH + 10
            de = TX1 - len(val) * CH - 10
            if de - ds > 12:
                g.append(f'<line x1="{ds:.0f}" y1="{y - 3}" x2="{de:.0f}" y2="{y - 3}" stroke="{p["dim"]}" '
                         f'stroke-width="1" stroke-dasharray="1 4" stroke-linecap="round"/>')
        else:
            txt = row[1]
            g.append(f'<text x="{TX0 + 12}" y="{y}" font-family="{MONO}" font-size="{FS}" '
                     f'fill="{p["val"]}">{escape(txt)}</text>')
            last_caret = (TX0 + 12 + len(txt) * CH + 4, y, begin + dur)
        g.append("</g>")
        body.append("".join(g))
        body.append(
            f'<rect x="{cx0}" y="{y - 12}" width="7" height="15" fill="{p["key"]}" opacity="0">'
            f'<set attributeName="opacity" to="0.9" begin="{t(begin)}"/>'
            f'<animate attributeName="x" from="{cx0}" to="{cx0 + wipe_w}" begin="{t(begin)}" dur="{t(dur)}" fill="freeze"/>'
            f'<set attributeName="opacity" to="0" begin="{t(begin + dur)}"/></rect>'
        )
        y += LINE
        n += 1

    if last_caret:
        cx, cy, cb = last_caret
        body.append(
            f'<rect x="{cx:.0f}" y="{cy - 12}" width="7" height="15" fill="{p["key"]}" opacity="0">'
            f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="1.1s" '
            f'begin="{t(cb)}" repeatCount="indefinite"/></rect>'
        )

    inner = "".join(body)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'role="img" aria-labelledby="t d">\n'
        '<title id="t">Muqaddas - GitHub profile</title>\n'
        '<desc id="d">Animated terminal-style profile card with an ASCII portrait and typed profile details.</desc>\n'
        f'<defs>{"".join(defs)}</defs>\n'
        f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" begin="0s" dur="0.5s" fill="freeze"/>'
        f'{inner}</g>\n</svg>\n'
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--photo")
    ap.add_argument("--crop", help="left,top,right,bottom in photo pixels")
    ap.add_argument("--out", default=".")
    a = ap.parse_args()
    box = tuple(int(v) for v in a.crop.split(",")) if a.crop else None
    os.makedirs(a.out, exist_ok=True)
    for theme in ("dark", "light"):
        path = os.path.join(a.out, f"{theme}.svg")
        with open(path, "w", encoding="utf-8") as f:
            f.write(build(theme, a.photo, box))
        print("wrote", path, os.path.getsize(path), "bytes")


if __name__ == "__main__":
    main()
