"""Renders the three animated SVGs for the GitHub profile README.

    python build_profile_art.py ascii   <portrait-cutout image>   # once, locally
    python build_profile_art.py card                              # once, locally
    python build_profile_art.py heatmap <github-username>         # daily, in GitHub Actions

Method from avivashishta.com's "animated GitHub profile README" guide: GitHub
strips scripts and inline styles from READMEs, so every animation lives inside
the SVG itself as CSS keyframes. Nolven palette: void black, cream, crimson.
"""

import html
import re
import sys
import urllib.request
from pathlib import Path

OUT = Path(__file__).parent / "assets"
OUT.mkdir(exist_ok=True)

BG = "#06060A"
PANEL = "#0D0D14"
INK = "#EEEAE0"
MUTED = "#8A8798"
CRIMSON = "#C8102E"
VERTICAL_COLOURS = ["#C8102E", "#EEEAE0", "#D4AF6A", "#2449B8", "#3DFF8F"]
MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"


def write(name: str, svg: str) -> None:
    (OUT / name).write_text(svg, encoding="utf-8")
    print("wrote", OUT / name)


# ── ASCII portrait ──────────────────────────────────────────────────────────

def ascii_portrait(src: str, cols: int = 100) -> None:
    from PIL import Image, ImageOps

    ramp = " .:-=+*#%@"
    img = Image.open(src).convert("RGBA")
    # Head and shoulders read better in characters than a full figure.
    img = img.crop((0, 0, img.width, int(img.height * 0.56)))
    alpha = img.getchannel("A")
    grey = ImageOps.autocontrast(img.convert("L"), cutoff=1)
    char_w, line_h = 6.0, 10.4
    rows = int(cols * img.height / img.width * (char_w / line_h))
    grey = grey.resize((cols, rows), Image.LANCZOS)
    alpha = alpha.resize((cols, rows), Image.LANCZOS)

    lines = []
    for y in range(rows):
        row = []
        for x in range(cols):
            if alpha.getpixel((x, y)) < 90:
                row.append(" ")
                continue
            v = grey.getpixel((x, y)) / 255
            row.append(ramp[min(len(ramp) - 1, 1 + int(v * (len(ramp) - 1)))])
        lines.append("".join(row).rstrip())

    pad = 22
    w = int(cols * char_w + pad * 2)
    h = int(rows * line_h + pad * 2)
    texts = []
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        texts.append(
            f'<text x="{pad}" y="{pad + (i + 1) * line_h:.1f}" style="animation-delay:{i * 0.03:.3f}s">{html.escape(line)}</text>'
        )
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
<style>
  text {{ font: 10px {MONO}; fill: {INK}; white-space: pre; opacity: 0; animation: row .5s ease-out forwards; }}
  @keyframes row {{ from {{ opacity: 0; transform: translateY(4px); }} to {{ opacity: .92; transform: none; }} }}
  @media (prefers-reduced-motion: reduce) {{ text {{ animation: none; opacity: .92; }} }}
</style>
<rect width="100%" height="100%" rx="18" fill="{BG}"/>
<g xml:space="preserve">{''.join(texts)}</g>
</svg>"""
    write("ascii-portrait.svg", svg)


# ── neofetch-style info card ────────────────────────────────────────────────

CARD = [
    ("Role", "Data Analyst · Amulyamica"),
    ("Location", "Gandhidham, India"),
    ("Verticals", "Financial Analyst · Project Manager · Full-Stack"),
    ("Builds", "with AI as pair programmer, learning to code by hand"),
    ("Built", "Mica Match · PRISM · Mica Studio · Meeting Island"),
    ("", "Jarvis · TRUCKOS · Nolven tools"),
    ("Tools", "Tally ERP · Excel · n8n · Claude Code"),
    ("Certs", "18 earned · 7 in progress"),
    ("Alias", "nolven"),
    ("Portfolio", "khushal.nolven.co.in"),
]


def info_card() -> None:
    pad, line_h, w = 30, 26, 620
    h = pad * 2 + 52 + line_h * (len(CARD) + 1) + 40
    rows = []
    y = pad + 30
    rows.append(f'<text class="r" x="{pad}" y="{y}" style="animation-delay:.1s"><tspan fill="{CRIMSON}">khushal</tspan><tspan fill="{MUTED}">@</tspan><tspan fill="{INK}">nolven</tspan></text>')
    y += 16
    rows.append(f'<line x1="{pad}" x2="{w - pad}" y1="{y}" y2="{y}" stroke="{MUTED}" stroke-opacity=".35" class="rule"/>')
    y += 30
    for i, (k, v) in enumerate(CARD):
        delay = 0.35 + i * 0.12
        rows.append(
            f'<text class="r" x="{pad}" y="{y}" style="animation-delay:{delay:.2f}s">'
            f'<tspan fill="{CRIMSON}" font-weight="600">{html.escape(k)}</tspan>'
            f'<tspan x="{pad + 116}" fill="{INK}">{html.escape(v)}</tspan></text>'
        )
        y += line_h
    y += 10
    for i, c in enumerate(VERTICAL_COLOURS):
        rows.append(f'<rect class="r" x="{pad + i * 34}" y="{y}" width="26" height="14" rx="3" fill="{c}" style="animation-delay:{0.4 + len(CARD) * 0.12 + i * 0.06:.2f}s"/>')
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
<style>
  text {{ font: 14px {MONO}; }}
  .r {{ opacity: 0; animation: in .45s ease-out forwards; }}
  .rule {{ stroke-dasharray: {w}; stroke-dashoffset: {w}; animation: draw .8s .2s ease-out forwards; }}
  @keyframes in {{ from {{ opacity: 0; transform: translateX(-6px); }} to {{ opacity: 1; transform: none; }} }}
  @keyframes draw {{ to {{ stroke-dashoffset: 0; }} }}
  @media (prefers-reduced-motion: reduce) {{ .r {{ animation: none; opacity: 1; }} .rule {{ animation: none; stroke-dashoffset: 0; }} }}
</style>
<rect width="100%" height="100%" rx="18" fill="{BG}"/>
<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="17" fill="none" stroke="{INK}" stroke-opacity=".1"/>
{''.join(rows)}
</svg>"""
    write("info-card.svg", svg)


# ── contribution heatmap ────────────────────────────────────────────────────

LEVELS = ["#16161F", "#4A0A16", "#7A0D21", "#A80F28", CRIMSON]


def heatmap(user: str) -> None:
    req = urllib.request.Request(
        f"https://github.com/users/{user}/contributions",
        headers={"User-Agent": "profile-art", "Accept": "text/html"},
    )
    page = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")
    days = []
    for tag in re.findall(r"<td[^>]*ContributionCalendar-day[^>]*>", page):
        d = re.search(r'data-date="(\d{4}-\d{2}-\d{2})"', tag)
        lv = re.search(r'data-level="(\d)"', tag)
        if d and lv:
            days.append((d.group(1), int(lv.group(1))))
    if not days:
        raise SystemExit("No contribution cells found; GitHub markup may have changed.")
    days.sort()

    import datetime as dt

    first = dt.date.fromisoformat(days[0][0])
    offset = (first.weekday() + 1) % 7  # GitHub weeks start on Sunday
    cell, gap, pad = 11, 3, 26
    weeks = (len(days) + offset + 6) // 7
    w = pad * 2 + weeks * (cell + gap)
    h = pad * 2 + 7 * (cell + gap) + 30
    active = sum(1 for _, lv in days if lv > 0)
    rects = []
    for i, (date, lv) in enumerate(days):
        col, row = divmod(i + offset, 7)
        x = pad + col * (cell + gap)
        y = pad + 22 + row * (cell + gap)
        rects.append(
            f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2.5" fill="{LEVELS[lv]}" style="animation-delay:{col * 0.025:.3f}s"><title>{date}</title></rect>'
        )
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
<style>
  text {{ font: 12px {MONO}; fill: {MUTED}; letter-spacing: .12em; }}
  rect[rx="2.5"] {{ opacity: 0; transform-box: fill-box; transform-origin: center; animation: pop .4s ease-out forwards; }}
  @keyframes pop {{ from {{ opacity: 0; transform: scale(.4); }} to {{ opacity: 1; transform: none; }} }}
  @media (prefers-reduced-motion: reduce) {{ rect[rx="2.5"] {{ animation: none; opacity: 1; }} }}
</style>
<rect width="100%" height="100%" rx="18" fill="{BG}"/>
<text x="{pad}" y="{pad + 6}">ACTIVE DAYS IN THE LAST YEAR: {active}</text>
{''.join(rects)}
</svg>"""
    write("contrib-heatmap.svg", svg)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    mode = sys.argv[1]
    if mode == "ascii":
        ascii_portrait(sys.argv[2])
    elif mode == "card":
        info_card()
    elif mode == "heatmap":
        heatmap(sys.argv[2])
    else:
        raise SystemExit(__doc__)
