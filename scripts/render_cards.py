"""Draws every animated card on the GitHub profile README, from real data.

    python scripts/render_cards.py            # fetch contributions, redraw all cards (runs daily in GitHub Actions)
    STATIC=1 python scripts/render_cards.py   # same, but every card sits at its final frame (for screenshots)

GitHub strips scripts and styles from a README, so each card is an SVG shown through <img>:
CSS keyframes and SMIL animate inside the image, fonts are embedded as base64, and
prefers-reduced-motion switches the motion off. Method: avivashishta.com, "animated SVG cards".
Nolven palette: void black, cream, one crimson accent; the three tile colours are the three
portfolio verticals (Terminal green, Ledger gold, Blueprint blue).
"""
import base64, datetime as dt, html, json, math, os, re, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CARDS, DATA, FONTS = ROOT / "cards", ROOT / "data", ROOT / "fonts"
for d in (CARDS, DATA): d.mkdir(exist_ok=True)
STATIC = os.environ.get("STATIC") == "1"
WEEKS = 12
USER = os.environ.get("GITHUB_REPOSITORY_OWNER", "Nolven-Khushal")

BG, PANEL, INK, MUTED, CRIMSON = "#06060A", "#0D0D14", "#EEEAE0", "#8A8798", "#C8102E"
GREEN, GOLD, BLUE = "#3DFF8F", "#D4AF6A", "#6B8CFF"
SANS = "-apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace"
FONT_B64 = base64.b64encode((FONTS / "clash-600.woff").read_bytes()).decode()


def css(extra=""):
    freeze = "*{animation:none!important} .in,.row,.sq,.bar,.tile{opacity:1!important;transform:none!important} .rule{stroke-dashoffset:0!important}" if STATIC else ""
    return f"""<style>
@font-face{{font-family:'Clash';src:url(data:font/woff;base64,{FONT_B64}) format('woff');font-weight:600}}
.clash{{font-family:'Clash',{SANS};font-weight:600}}
.sans{{font-family:{SANS}}} .mono{{font-family:{MONO}}}
.in{{opacity:0;animation:in .6s ease-out forwards}}
@keyframes in{{from{{opacity:0;transform:translateY(8px)}}to{{opacity:1;transform:none}}}}
{extra}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}} .in,.row,.sq,.bar,.tile{{opacity:1!important;transform:none!important}}}}
{freeze}
</style>"""


def svg(w, h, body, extra="", label=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{html.escape(label)}">'
            f'{css(extra)}<rect width="{w}" height="{h}" rx="22" fill="{BG}"/>'
            f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="21.5" fill="none" stroke="{INK}" stroke-opacity=".1"/>{body}</svg>')


def write(name, text):
    (CARDS / name).write_text(text, encoding="utf-8"); print("wrote", name)


def esc(s): return html.escape(str(s))


def chip(x, y, text, dot):
    w = int(len(text) * 7.4 + 38)
    return (f'<g class="in" style="animation-delay:.9s"><rect x="{x}" y="{y}" width="{w}" height="30" rx="15" fill="{PANEL}" stroke="{INK}" stroke-opacity=".14"/>'
            f'<circle cx="{x + 16}" cy="{y + 15}" r="4.5" fill="{dot}"/><text x="{x + 29}" y="{y + 20}" class="sans" font-size="13" fill="{INK}" fill-opacity=".9">{esc(text)}</text></g>'), w + 10


# ── data ────────────────────────────────────────────────────────────────────

def fetch_contributions():
    path = DATA / "contributions.json"
    try:
        req = urllib.request.Request(f"https://github.com/users/{USER}/contributions", headers={"User-Agent": "profile-cards", "Accept": "text/html"})
        page = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")
        cells = {}
        for tag in re.findall(r"<td[^>]*ContributionCalendar-day[^>]*>", page):
            i, d, lv = (re.search(p, tag) for p in (r'id="([^"]+)"', r'data-date="(\d{4}-\d{2}-\d{2})"', r'data-level="(\d)"'))
            if i and d and lv: cells[i.group(1)] = [d.group(1), int(lv.group(1)), 0]
        for tid, text in re.findall(r'<tool-tip[^>]*for="([^"]+)"[^>]*>([^<]*)</tool-tip>', page):
            m = re.match(r"(\d+) contribution", text.strip())
            if tid in cells and m: cells[tid][2] = int(m.group(1))
        days = sorted(cells.values())
        if not days: raise ValueError("no contribution cells found")
        path.write_text(json.dumps({"days": days, "fetched": dt.date.today().isoformat()}), encoding="utf-8")
    except Exception as e:                                   # keep yesterday's data rather than break the profile
        print("contributions fetch failed, using saved data:", e)
    return json.loads(path.read_text(encoding="utf-8"))["days"]


def stats(days):
    total = sum(c for _, _, c in days)
    streak, today = 0, len(days) - 1
    for i in range(today, -1, -1):
        if days[i][2] > 0: streak += 1
        elif i == today: continue          # today may simply not have happened yet
        else: break
    best = max(days, key=lambda d: d[2])
    return total, streak, best


# ── cards ───────────────────────────────────────────────────────────────────

def hero():
    port = json.loads((DATA / "portrait.json").read_text(encoding="utf-8"))
    rows = "".join(f'<text class="row mono" x="22" y="{y}" style="animation-delay:{.25 + i * .03:.2f}s">{esc(t)}</text>' for i, (y, t) in enumerate(port["rows"]))
    chips, x = [], 44
    for t, c in (("Financial Analyst", GOLD), ("Project Manager", BLUE), ("Full-Stack, built with AI", GREEN)):
        s, adv = chip(x, 352, t, c); chips.append(s); x += adv
    body = f"""
<defs><linearGradient id="shine" x1="0" x2="1" y1="0" y2="0"><stop offset="0" stop-color="{INK}"/><stop offset=".42" stop-color="{INK}"/><stop offset=".5" stop-color="#FFFFFF"/><stop offset=".58" stop-color="{INK}"/><stop offset="1" stop-color="{INK}"/>
<animateTransform attributeName="gradientTransform" type="translate" from="-1 0" to="1 0" dur="4.5s" begin="1.2s" repeatCount="indefinite"/></linearGradient></defs>
<text class="in mono" x="44" y="62" font-size="12" letter-spacing="2.6" fill="{MUTED}" style="animation-delay:.1s">DATA ANALYST · AMULYAMICA · GANDHIDHAM</text>
<text class="in clash" x="42" y="148" font-size="80" fill="url(#shine)" style="animation-delay:.2s">Khushal</text>
<text class="in clash" x="42" y="226" font-size="80" fill="url(#shine)" style="animation-delay:.32s">Vashistha</text>
<line class="rule" x1="46" x2="170" y1="252" y2="252" stroke="{CRIMSON}" stroke-width="4" stroke-linecap="round"/>
<text class="in sans" x="44" y="294" font-size="21" fill="{INK}" fill-opacity=".9" style="animation-delay:.6s">Accountant by training. Analyst by trade.</text>
<text class="in sans" x="44" y="323" font-size="21" fill="{INK}" fill-opacity=".9" style="animation-delay:.72s">Builder by obsession.</text>
{''.join(chips)}
<g transform="translate(500 18) scale(.585)">{rows}</g>"""
    extra = f".row{{opacity:0;animation:row .5s ease-out forwards;font-size:10px;fill:{INK};white-space:pre}} @keyframes row{{from{{opacity:0;transform:translateY(4px)}}to{{opacity:.92;transform:none}}}}\n.rule{{stroke-dasharray:130;stroke-dashoffset:130;animation:draw .8s .5s ease-out forwards}} @keyframes draw{{to{{stroke-dashoffset:0}}}}"
    write("hero.svg", svg(880, 400, body, extra, "Khushal Vashistha. Data Analyst at Amulyamica. Accountant by training, analyst by trade, builder by obsession."))


def counter(x, y, final, size, delay, fill, suffix=""):
    steps, dur = 18, 1.1
    vals = [max(0, round(final * (1 - (1 - (i + 1) / steps) ** 3))) for i in range(steps)]
    if STATIC: return f'<text class="clash" x="{x}" y="{y}" font-size="{size}" fill="{fill}">{final}{suffix}</text>'
    out = []
    for i, v in enumerate(vals):
        last = i == steps - 1
        begin = delay + i * dur / steps
        if last:   # the final number is visible by default, so a viewer that cannot run SMIL still shows it
            out.append(f'<text class="clash" x="{x}" y="{y}" font-size="{size}" fill="{fill}">{v}{suffix}<set attributeName="visibility" to="hidden" begin="0s" dur="{begin:.3f}s"/></text>')
        else:
            out.append(f'<text class="clash" x="{x}" y="{y}" font-size="{size}" fill="{fill}" visibility="hidden">{v}{suffix}<set attributeName="visibility" to="visible" begin="{begin:.3f}s" dur="{dur / steps:.3f}s"/></text>')
    return "".join(out)


def tile(name, label, colour, final, suffix, caption, items, delay):
    w, h = 286, 236
    its = "".join(f'<text class="sans in" x="26" y="{178 + i * 20}" font-size="13" fill="{INK}" fill-opacity=".62" style="animation-delay:{delay + .9 + i * .1:.2f}s">{esc(t)}</text>' for i, t in enumerate(items))
    body = f"""<defs><clipPath id="c"><rect width="{w}" height="{h}" rx="22"/></clipPath></defs><g class="tile" style="animation-delay:{delay}s"><g clip-path="url(#c)">
<rect x="0" y="0" width="{w}" height="{h}" fill="{PANEL}"/><rect x="0" y="0" width="{w}" height="5" fill="{colour}"/></g>
<text class="mono" x="26" y="44" font-size="12" letter-spacing="3" fill="{colour}">{label}</text>
{counter(24, 122, final, 78, delay + .35, INK, suffix)}
<text class="sans" x="26" y="150" font-size="14" fill="{INK}" fill-opacity=".85">{esc(caption)}</text>{its}
<text class="mono" x="{w - 26}" y="44" font-size="13" fill="{colour}" text-anchor="end">→</text></g>"""
    extra = ".tile{transform-origin:50% 100%;opacity:0;animation:swing 1s cubic-bezier(.2,.9,.3,1.15) forwards;transform-box:fill-box}\n@keyframes swing{0%{opacity:0;transform:translateY(44px) rotate(-5deg)}55%{opacity:1;transform:translateY(-7px) rotate(1.6deg)}100%{opacity:1;transform:none}}"
    write(f"{name}.svg", svg(w, h, body, extra, f"{label}: {final}{suffix} {caption}. {', '.join(items)}."))


def activity(days):
    total, streak, best = stats(days)
    first = dt.date.fromisoformat(days[0][0]); first -= dt.timedelta(days=(first.weekday() + 1) % 7)
    weeks = {}
    for d, _, c in days:
        k = (dt.date.fromisoformat(d) - first).days // 7
        weeks[k] = weeks.get(k, 0) + c
    n = max(weeks) + 1
    last = [weeks.get(i, 0) for i in range(max(0, n - WEEKS), n)]
    start_week = first + dt.timedelta(weeks=max(0, n - WEEKS))
    peak = max(last) or 1
    top = last.index(max(last)) if max(last) else -1
    bw, gap, x0, base_y, maxh = 34, 14, 44, 196, 112
    bars = []
    for i, v in enumerate(last):
        hh = max(3, v / peak * maxh)
        col = CRIMSON if i == top else INK
        op = 1 if i == top else (.38 if v else .14)
        bars.append(f'<rect class="bar" x="{x0 + i * (bw + gap)}" y="{base_y - hh:.1f}" width="{bw}" height="{hh:.1f}" rx="5" fill="{col}" fill-opacity="{op}" style="animation-delay:{.2 + i * .05:.2f}s"><title>{v} contributions</title></rect>')
        wk = start_week + dt.timedelta(weeks=i)
        if i == 0 or wk.month != (start_week + dt.timedelta(weeks=i - 1)).month:
            bars.append(f'<text class="mono" x="{x0 + i * (bw + gap)}" y="{base_y + 24}" font-size="11" fill="{MUTED}" letter-spacing="1.4">{wk.strftime("%b").upper()}</text>')
    bd = dt.date.fromisoformat(best[0])
    stat = lambda y, k, v: (f'<text class="mono" x="694" y="{y}" font-size="11" letter-spacing="2.2" fill="{MUTED}">{k}</text>'
                            f'<text class="clash" x="692" y="{y + 36}" font-size="38" fill="{INK}">{v}</text>')
    body = f"""<text class="mono" x="44" y="46" font-size="12" letter-spacing="3" fill="{MUTED}">ACTIVITY · LAST {WEEKS} WEEKS</text>
{''.join(bars)}
{stat(76, 'THIS YEAR', total)}{stat(136, 'STREAK', f'{streak} d')}{stat(196, f'BUSIEST DAY · {bd.strftime("%b").upper()} {bd.day}', best[2])}"""
    extra = ".bar{opacity:0;transform-box:fill-box;transform-origin:bottom;animation:grow .7s cubic-bezier(.2,.9,.3,1) forwards}\n@keyframes grow{from{opacity:0;transform:scaleY(.05)}to{opacity:1;transform:none}}"
    # the bars already carry their own fill-opacity; the animation only animates the element opacity to 1
    write("activity.svg", svg(880, 250, body, extra, f"Contribution activity over the last {WEEKS} weeks. {total} contributions this year, current streak {streak} days, busiest day {best[2]} contributions."))


def graph(days):
    levels = ["#14141C", "#3E3B34", "#76726A", "#B4AF9F", INK]
    first = dt.date.fromisoformat(days[0][0]); off = (first.weekday() + 1) % 7
    cell, gap, pad = 12, 3, 44
    wk = (len(days) + off + 6) // 7
    w = 880; h = pad + 22 + 7 * (cell + gap) + 46
    step = (w - pad * 2) / wk
    sq = []
    for i, (d, lv, c) in enumerate(days):
        col, row = divmod(i + off, 7)
        sq.append(f'<rect class="sq" x="{pad + col * step:.1f}" y="{pad + 22 + row * (cell + gap)}" width="{cell}" height="{cell}" rx="3" fill="{levels[lv]}" style="animation-delay:{col * .022:.3f}s"><title>{d}: {c}</title></rect>')
    lg = "".join(f'<rect x="{w - pad - 5 * 20 + i * 20}" y="{h - 34}" width="14" height="14" rx="3" fill="{c}"/>' for i, c in enumerate(levels))
    body = f"""<text class="mono" x="{pad}" y="{pad}" font-size="12" letter-spacing="3" fill="{MUTED}">CONTRIBUTIONS · LAST 12 MONTHS</text>{''.join(sq)}
<text class="mono" x="{w - pad - 5 * 20 - 12}" y="{h - 22}" font-size="11" fill="{MUTED}" text-anchor="end">LESS</text>{lg}<text class="mono" x="{w - pad + 6}" y="{h - 22}" font-size="11" fill="{MUTED}">MORE</text>"""
    extra = ".sq{opacity:0;transform-box:fill-box;transform-origin:center;animation:pop .4s ease-out forwards}\n@keyframes pop{from{opacity:0;transform:scale(.35)}to{opacity:1;transform:none}}"
    write("graph.svg", svg(w, h, body, extra, "Contribution graph for the last 12 months."))


def repo(name, title, line, tags, colour, status, delay):
    w, h = 432, 168
    tg, x = [], 28
    for t in tags:
        tw = int(len(t) * 7 + 22)
        tg.append(f'<rect x="{x}" y="116" width="{tw}" height="26" rx="13" fill="{INK}" fill-opacity=".06"/><text class="sans" x="{x + tw / 2}" y="133" font-size="12" fill="{INK}" fill-opacity=".72" text-anchor="middle">{esc(t)}</text>')
        x += tw + 8
    words, lines_, cur = line.split(), [], ""
    for wd in words:
        if len(cur) + len(wd) > 54: lines_.append(cur); cur = wd
        else: cur = f"{cur} {wd}".strip()
    lines_.append(cur)
    ln = "".join(f'<text class="sans" x="28" y="{74 + i * 20}" font-size="14" fill="{INK}" fill-opacity=".8">{esc(t)}</text>' for i, t in enumerate(lines_[:2]))
    body = f"""<defs><clipPath id="c"><rect width="{w}" height="{h}" rx="22"/></clipPath></defs><g class="tile" style="animation-delay:{delay}s"><g clip-path="url(#c)"><rect width="{w}" height="{h}" fill="{PANEL}"/><rect width="5" height="{h}" fill="{colour}"/></g>
<text class="clash" x="28" y="46" font-size="26" fill="{INK}">{esc(title)}</text><text class="mono" x="{w - 28}" y="44" font-size="11" letter-spacing="1.8" fill="{colour}" text-anchor="end">{esc(status)}</text>{ln}{''.join(tg)}</g>"""
    extra = ".tile{transform-origin:50% 100%;opacity:0;animation:swing 1s cubic-bezier(.2,.9,.3,1.15) forwards;transform-box:fill-box}\n@keyframes swing{0%{opacity:0;transform:translateY(36px) rotate(-3deg)}55%{opacity:1;transform:translateY(-5px) rotate(1deg)}100%{opacity:1;transform:none}}"
    write(f"repo-{name}.svg", svg(w, h, body, extra, f"{title}: {line}"))


REPOS = [
    ("conjure", "Conjure", "Control the whole PC with your hands, and pull 26,000-dot holograms apart with your fingers.", ["Computer vision", "Rust", "Three.js"], GREEN, "WINDOWS APP", .2),
    ("jarvis", "Jarvis", "A personal AI that understands loose, typo-filled commands and acts with safety rules held in code.", ["AI agent", "Python", "1,256 tests"], GREEN, "IN PROGRESS", .35),
    ("prism", "PRISM", "Sales and productivity reporting for management across India, in one desktop app.", ["Analytics", "Python", "~54,000 lines"], GOLD, "IN DAILY USE", .5),
    ("mica-match", "Mica Match", "Point a phone at a laminate shade and find it in a 2,300-shade catalogue, offline.", ["Machine learning", "Mobile", "0.5 s a photo"], BLUE, "CLOSED TESTING", .65),
]

if __name__ == "__main__":
    days = fetch_contributions()
    hero()
    tile("build", "BUILD", GREEN, 8, "", "projects built with AI", ["Conjure · Jarvis · PRISM", "Mica Match · Meeting Island"], .35)
    tile("analyse", "ANALYSE", GOLD, 3, "", "years across accounts and data", ["GST · TDS · DCF · WACC", "MIS · EVA · Power BI"], .55)
    tile("learn", "LEARN", BLUE, 18, "", "certificates, MBA underway", ["IESE · Illinois · J.P. Morgan", "Goldman · KPMG · IBM"], .75)
    activity(days); graph(days)
    for r in REPOS: repo(*r)
