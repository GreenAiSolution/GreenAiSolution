#!/usr/bin/env python3
"""Rebuild the "Build an AI Empire" field-guide poster.

The original render (source/original.webp) had a good background plate but sloppy
UI chrome: every layer card was drawn twice (an empty duplicate box sat above each
one), titles ran past the card borders and the third line of copy fell outside the
box. This script keeps the artwork, throws away the broken chrome, and redraws the
seven layer cards and seven connector panels as real HTML/CSS laid out on a grid.

The connector glyphs are lifted pixel-for-pixel out of the original render so the
logos stay exactly as they were drawn.

Requires: Pillow, a Chromium binary, and (first run only) network access to fetch
the two Google fonts into fonts/.

    python3 build_poster.py [--chromium /path/to/chrome]
"""
from __future__ import annotations

import argparse
import base64
import io
import os
import re
import shutil
import subprocess
import sys
import urllib.request

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "source", "original.webp")
FONT_DIR = os.path.join(HERE, "fonts")
BUILD_DIR = os.path.join(HERE, "build")

W, H = 900, 1125

# Geometry of the original render, measured off source/original.webp.
# Every layer's chrome occupied a band of rows; the new card for a layer has to
# cover that whole band, duplicate box included, or the old outline shows through.
PANEL_TOPS = {"07": 172, "06": 291, "05": 421, "04": 557, "03": 700, "02": 845, "01": 972}
ICON_XS = (703, 766, 828)      # tile centres, identical on every row
ICON_DY = 34                   # icon centre, relative to the old panel top

# New layout. Cards and connector panels share a top/height per row so the two
# columns line up; rows 02 and 01 are taller because the stray duplicate boxes
# there sat ~40px above the real card and have to be covered.
CARD_X, CARD_W = 56, 240
PANEL_X, PANEL_W = 646, 226

ROWS = [
    # top,  h,   accent,    n,    title,            accent line,                               muted line,                    connectors
    (158, 100, "#DFE85E", "07", "COMPOUND", "Observe &rsaquo; test &rsaquo; improve", "Ship from real traces",
     [("PostHog", "posthog"), ("Sentry", "sentry"), ("Langfuse", "langfuse")]),
    (273, 100, "#F6853A", "06", "REVENUE LOOP", "Auth + pay + CRM + email", "Trigger lifecycle journeys",
     [("Clerk", "clerk"), ("Stripe", "stripe"), ("HubSpot", "hubspot")]),
    (407, 100, "#E45AD8", "05", "ACTION LAYER", "Webhook &rsaquo; approval &rsaquo; retry", "Let agents do real work",
     [("n8n", "n8n"), ("Zapier", "zapier"), ("Slack", "slack")]),
    (543, 100, "#9A7CF2", "04", "MEMORY LAYER", "SQL truth + vectors", "Cache hot context only",
     [("Supabase", "supabase"), ("Pinecone", "pinecone"), ("Upstash", "upstash")]),
    (677, 100, "#5FD0E8", "03", "ADD THE BRAIN", "Tools + JSON + evals", "Route models by task",
     [("OpenAI", "openai"), ("Claude", "claude"), ("Gemini", "gemini")]),
    (800, 115, "#BFE96B", "02", "SHIP THE SHELL", "Next.js + TS + Tailwind", "Stream every AI state",
     [("Figma", "figma"), ("Next.js", "nextjs"), ("Vercel", "vercel")]),
    (926, 120, "#F4622F", "01", "FIND THE WEDGE", "1 user &times; 1 painful job", "Promise one measurable win",
     [("Perplexity", "perplexity"), ("Typeform", "typeform"), ("Airtable", "airtable")]),
]

FONTS = {  # family -> Google Fonts css2 query
    "Inter": "Inter:wght@500;600;700;800",
    "Archivo": "Archivo:wght@700;800;900",
}
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")


def fetch_fonts() -> dict[str, str]:
    """Download the latin subset of each family once, return {family: path}."""
    os.makedirs(FONT_DIR, exist_ok=True)
    out = {}
    for family, query in FONTS.items():
        path = os.path.join(FONT_DIR, f"{family}.woff2")
        out[family] = path
        if os.path.exists(path):
            continue
        url = f"https://fonts.googleapis.com/css2?family={query}&display=block"
        css = urllib.request.urlopen(
            urllib.request.Request(url, headers={"User-Agent": UA}), timeout=30
        ).read().decode()
        parts = re.split(r"/\*\s*([a-z0-9\-]+)\s*\*/", css)
        for i in range(1, len(parts), 2):
            if parts[i] != "latin":
                continue
            font_url = re.search(r"url\((https://[^)]+)\)", parts[i + 1]).group(1)
            with urllib.request.urlopen(font_url, timeout=30) as r, open(path, "wb") as f:
                shutil.copyfileobj(r, f)
            break
        else:
            raise SystemExit(f"no latin subset found for {family}")
        print(f"fetched {path}")
    return out


def extract_icons(src: Image.Image) -> dict[str, str]:
    """Cut each connector glyph out of the original render, base64 PNG per slug."""
    px = src.load()
    icons = {}
    for _, _, _, num, _, _, _, conns in ROWS:
        cy = PANEL_TOPS[num] + ICON_DY
        for (_, slug), cx in zip(conns, ICON_XS):
            x0, y0, x1, y1 = cx - 17, cy - 10, cx + 18, cy + 11
            bx0 = by0 = 10 ** 6
            bx1 = by1 = -1
            for y in range(y0, y1):
                for x in range(x0, x1):
                    r, g, b = px[x, y]
                    if r + g + b > 120:          # glyph pixel, tile fill is near black
                        bx0, bx1 = min(bx0, x), max(bx1, x)
                        by0, by1 = min(by0, y), max(by1, y)
            if bx1 < 0:
                raise SystemExit(f"no glyph found for {slug}")
            patch = src.crop((bx0 - 1, by0 - 1, bx1 + 2, by1 + 2))
            buf = io.BytesIO()
            patch.save(buf, "PNG")
            icons[slug] = base64.b64encode(buf.getvalue()).decode()
    return icons


def build_html(src: Image.Image, fonts: dict[str, str], icons: dict[str, str]) -> str:
    buf = io.BytesIO()
    src.save(buf, "PNG")
    bg = base64.b64encode(buf.getvalue()).decode()
    inter = base64.b64encode(open(fonts["Inter"], "rb").read()).decode()
    archivo = base64.b64encode(open(fonts["Archivo"], "rb").read()).decode()

    blocks = []
    for top, h, accent, num, title, line2, line3, conns in ROWS:
        tiles = "".join(
            f'<div class="tile"><img src="data:image/png;base64,{icons[slug]}" alt="">'
            f"<span>{label}</span></div>"
            for label, slug in conns
        )
        blocks.append(f"""
  <div class="card" style="top:{top}px;height:{h}px;--a:{accent}">
    <div class="row1"><span class="badge">{num}</span><span class="title">{title}</span></div>
    <div class="l2">{line2}</div>
    <div class="l3">{line3}</div>
  </div>
  <div class="panel" style="top:{top}px;height:{h}px;--a:{accent}">
    <div class="plabel">CONNECTORS</div>
    <div class="tiles">{tiles}</div>
  </div>""")

    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Build an AI Empire</title>
<style>
@font-face {{ font-family:'Inter'; src:url(data:font/woff2;base64,{inter}) format('woff2');
  font-weight:100 900; font-display:block; }}
@font-face {{ font-family:'Archivo'; src:url(data:font/woff2;base64,{archivo}) format('woff2');
  font-weight:100 900; font-display:block; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
html,body {{ width:{W}px; height:{H}px; overflow:hidden; background:#05050b; }}
#stage {{ position:relative; width:{W}px; height:{H}px;
  background:url(data:image/png;base64,{bg}) 0 0/{W}px {H}px no-repeat; }}

.card, .panel {{ position:absolute; border-radius:14px;
  background:linear-gradient(180deg,#12121f 0%,#0a0a13 100%);
  border:1.5px solid var(--a);
  box-shadow:0 0 0 1px rgba(0,0,0,.55),
             0 0 14px -2px color-mix(in srgb, var(--a) 55%, transparent),
             inset 0 1px 0 rgba(255,255,255,.05);
  display:flex; flex-direction:column; justify-content:center; }}

.card {{ left:{CARD_X}px; width:{CARD_W}px; padding:0 14px; overflow:hidden; }}
.row1 {{ display:flex; align-items:center; gap:8px; }}
.badge {{ flex:0 0 auto; min-width:29px; height:21px; border-radius:6px;
  background:var(--a); color:#0a0a12;
  font-family:'Archivo'; font-weight:800; font-size:12px; letter-spacing:.4px;
  display:flex; align-items:center; justify-content:center; }}
.title {{ font-family:'Archivo'; font-weight:800; font-size:19px; line-height:1; color:#fff;
  letter-spacing:-.3px; word-spacing:1.5px; white-space:nowrap;
  text-shadow:0 1px 3px rgba(0,0,0,.6); }}
.l2 {{ margin-top:8px; font-family:'Inter'; font-weight:700; font-size:12.5px; line-height:1.15;
  color:var(--a); letter-spacing:-.05px; word-spacing:.8px; white-space:nowrap; }}
.l3 {{ margin-top:3px; font-family:'Inter'; font-weight:500; font-size:11.5px; line-height:1.15;
  color:#C6C9D8; letter-spacing:0; word-spacing:.6px; white-space:nowrap; }}

.panel {{ left:{PANEL_X}px; width:{PANEL_W}px; padding:0 12px; }}
.plabel {{ font-family:'Inter'; font-weight:700; font-size:9.5px; letter-spacing:1.35px;
  color:#E8EAF4; }}
.tiles {{ display:flex; gap:7px; margin-top:7px; }}
.tile {{ flex:1 1 0; height:46px; border-radius:9px; background:#0a0913;
  border:1px solid rgba(255,255,255,.16); display:flex; flex-direction:column;
  align-items:center; justify-content:center; gap:3px; overflow:hidden; }}
.tile img {{ display:block; max-width:19px; max-height:19px; mix-blend-mode:screen; }}
.tile span {{ font-family:'Inter'; font-weight:600; font-size:8.6px; line-height:1;
  color:#D8DBE8; letter-spacing:-.05px; white-space:nowrap; }}
</style></head>
<body><div id="stage">{''.join(blocks)}</div></body></html>"""


def find_chromium(explicit: str | None) -> str:
    if explicit:
        return explicit
    for cand in ("/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
                 "chromium", "chromium-browser", "google-chrome"):
        path = cand if os.path.isabs(cand) else shutil.which(cand)
        if path and os.path.exists(path):
            return path
    raise SystemExit("no chromium found; pass --chromium /path/to/chrome")


def render(chrome: str, html_path: str, scale: int, out: str) -> None:
    # headless Chromium reserves some window height for browser UI, so ask for a
    # taller window than the poster and crop the plate back off the top-left.
    shot = os.path.join(BUILD_DIR, f"shot{scale}x.png")
    subprocess.run([
        chrome, "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
        f"--force-device-scale-factor={scale}", f"--window-size={W},{H + 87}",
        "--virtual-time-budget=8000", f"--screenshot={shot}", f"file://{html_path}",
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    Image.open(shot).crop((0, 0, W * scale, H * scale)).save(out)
    print(f"wrote {out}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--chromium")
    args = ap.parse_args()

    os.makedirs(BUILD_DIR, exist_ok=True)
    src = Image.open(SOURCE).convert("RGB")
    if src.size != (W, H):
        raise SystemExit(f"expected a {W}x{H} source, got {src.size}")

    html = build_html(src, fetch_fonts(), extract_icons(src))
    html_path = os.path.join(BUILD_DIR, "poster.html")
    with open(html_path, "w") as f:
        f.write(html)

    chrome = find_chromium(args.chromium)
    render(chrome, html_path, 1, os.path.join(HERE, "build-an-ai-empire.png"))
    render(chrome, html_path, 2, os.path.join(BUILD_DIR, "build-an-ai-empire@2x.png"))
    for scale, name in ((1, "build-an-ai-empire.webp"), (2, "build-an-ai-empire@2x.webp")):
        srcfile = (os.path.join(HERE, "build-an-ai-empire.png") if scale == 1
                   else os.path.join(BUILD_DIR, "build-an-ai-empire@2x.png"))
        Image.open(srcfile).save(os.path.join(HERE, name), "WEBP",
                                 quality=95 if scale == 1 else 92, method=6)
        print(f"wrote {os.path.join(HERE, name)}")


if __name__ == "__main__":
    main()
