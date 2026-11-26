"""Tailored brand book - design system helpers (colours, CSS, graphic elements)."""
import math, random
from shapely.geometry import Polygon, Point, box, LineString, MultiPolygon
from shapely.ops import unary_union, substring
from shapely import affinity
import stitch as S
import arabic as A

INK = "#1A1412"; CHALK = "#E5E0DA"; THREAD = "#E9453F"; KRAFT = "#CDAE88"; DYE = "#23325E"; MIST = "#C7D2DF"
GREEN = "#1E8A5A"; AMBER = "#E39A1B"; ALARM = "#8F1D2C"; PAPER = "#F5F3EF"
N900 = INK; N700 = "#3A322D"; N500 = "#7A7068"; N300 = "#CBC3BA"; N100 = "#D9D3CB"

AR = A.AR_NAME  # the Arabic name

CSS = """
@font-face{font-family:'Fraunces';src:url('../fonts/Fraunces.ttf');font-weight:100 900;font-style:normal}
@font-face{font-family:'Fraunces';src:url('../fonts/Fraunces-Italic.ttf');font-weight:100 900;font-style:italic}
@font-face{font-family:'Plex';src:url('../fonts/PlexSans.ttf');font-weight:100 700;font-style:normal}
@font-face{font-family:'Plex';src:url('../fonts/PlexSans-Italic.ttf');font-weight:100 700;font-style:italic}
@font-face{font-family:'PlexAr';src:url('../fonts/PlexSansArabic-Regular.ttf');font-weight:400}
@font-face{font-family:'PlexAr';src:url('../fonts/PlexSansArabic-Medium.ttf');font-weight:500}
@font-face{font-family:'PlexAr';src:url('../fonts/PlexSansArabic-SemiBold.ttf');font-weight:600}
@font-face{font-family:'PlexAr';src:url('../fonts/PlexSansArabic-Bold.ttf');font-weight:700}
@font-face{font-family:'Mono';src:url('../fonts/PlexMono-Regular.ttf');font-weight:400}
@font-face{font-family:'Mono';src:url('../fonts/PlexMono-Medium.ttf');font-weight:500}
@font-face{font-family:'Kufi';src:url('../fonts/ReemKufi.ttf');font-weight:400 700}
@font-face{font-family:'Amiri';src:url('../fonts/Amiri-Regular.ttf');font-weight:400}
@font-face{font-family:'Amiri';src:url('../fonts/Amiri-Bold.ttf');font-weight:700}
:root{--arc:26px;--ink:#1A1412;--chalk:#E5E0DA;--thread:#E9453F;--kraft:#CDAE88;--dye:#23325E;--mist:#C7D2DF;--green:#1E8A5A;--amber:#E39A1B;--alarm:#8F1D2C;--paper:#F5F3EF;--n700:#3A322D;--n500:#7A7068;--n300:#CBC3BA;--n100:#D9D3CB}
@page{size:1600px 900px;margin:0}
*{box-sizing:border-box;margin:0;padding:0}
html,body{background:#888}
body{font-family:'Plex',sans-serif;color:var(--ink);-webkit-print-color-adjust:exact;print-color-adjust:exact}
.pg{width:1600px;height:900px;position:relative;overflow:hidden;page-break-after:always;break-after:page;padding:84px 96px 92px;background:var(--chalk);color:var(--ink)}
.pg.dark{background:var(--ink);color:var(--chalk)}
.pg.thread{background:var(--thread);color:var(--ink)}
.pg.kraft{background:var(--kraft);color:var(--ink)}
.pg.paper{background:var(--paper)}
.pg.dye{background:var(--dye);color:var(--chalk)}
.pg.mist{background:var(--mist)}
.pg.bleed{padding:0}
.abs{position:absolute}
.hdr{position:absolute;left:96px;right:96px;top:34px;display:flex;justify-content:space-between;font:500 13px 'Mono';letter-spacing:.14em;text-transform:uppercase;opacity:.75}
.ftr{position:absolute;left:0;right:0;bottom:0;height:40px}
.pgn{position:absolute;right:96px;bottom:50px;font:500 13px 'Mono';letter-spacing:.1em;opacity:.7}
.eyebrow{font:500 14px 'Mono';letter-spacing:.16em;text-transform:uppercase;display:flex;align-items:center;gap:10px;margin-bottom:18px}
.eyebrow:before{content:'';width:13px;height:10px;background:var(--thread);clip-path:polygon(0 0,100% 0,50% 100%)}
.thread .eyebrow:before{background:var(--ink)}
.display{word-spacing:.07em;font-family:'Fraunces';font-weight:560;font-size:112px;line-height:.92;letter-spacing:-.025em;font-variation-settings:'SOFT' 100,'WONK' 0,'opsz' 144}
.h1{word-spacing:.06em;font-family:'Fraunces';font-weight:540;font-size:68px;line-height:1;letter-spacing:-.02em;font-variation-settings:'SOFT' 100,'WONK' 0,'opsz' 144}
.h2{word-spacing:.05em;font-family:'Fraunces';font-weight:540;font-size:44px;line-height:1.05;letter-spacing:-.015em;font-variation-settings:'SOFT' 100,'WONK' 0,'opsz' 96}
.h3{font-family:'Fraunces';font-weight:560;font-size:28px;line-height:1.1;letter-spacing:-.01em;font-variation-settings:'SOFT' 100,'opsz' 48}
em,.it{font-family:'Fraunces';font-style:italic;font-weight:480;font-variation-settings:'SOFT' 100,'WONK' 1,'opsz' 144}
.body{font-size:21px;line-height:1.5;font-weight:400}
.lead{font-size:26px;line-height:1.4;font-weight:400}
.sm{font-size:16px;line-height:1.5}
.xs{font-size:13px;line-height:1.45}
.mono{font-family:'Mono';letter-spacing:.04em}
.lab{font:500 12px 'Mono';letter-spacing:.14em;text-transform:uppercase}
.ar{font-family:'PlexAr',sans-serif;direction:rtl}
.kufi{font-family:'Kufi';direction:rtl;font-weight:600}
.amiri{font-family:'Amiri',serif;direction:rtl}
.row{display:flex}.col{display:flex;flex-direction:column}
.g8{gap:8px}.g12{gap:12px}.g16{gap:16px}.g24{gap:24px}.g32{gap:32px}.g48{gap:48px}
.jb{justify-content:space-between}.ac{align-items:center}.as{align-items:flex-start}.ae{align-items:flex-end}.jc{justify-content:center}
.f1{flex:1}.wrap{flex-wrap:wrap}
.card{background:var(--paper);border-radius:0 var(--arc) 0 0;padding:28px;position:relative}
.ar .card,[dir=rtl] .card{border-radius:var(--arc) 0 0 0}
.dark .card{background:#241C19}
.chip{display:inline-flex;align-items:center;gap:8px;padding:6px 14px;border:1.5px solid currentColor;border-radius:99px;font:500 12px 'Mono';letter-spacing:.1em;text-transform:uppercase}
.rule{height:2px;background:currentColor;opacity:.9}
.stitch{height:3px;background:repeating-linear-gradient(90deg,currentColor 0 9px,transparent 9px 17px)}
.stitch.v{width:3px;height:auto;background:repeating-linear-gradient(180deg,currentColor 0 9px,transparent 9px 17px)}
.notch{display:inline-block;width:16px;height:12px;background:var(--thread);clip-path:polygon(0 0,100% 0,50% 100%)}
.thin{opacity:.7}
.tag{display:inline-block;font:500 11px 'Mono';letter-spacing:.14em;text-transform:uppercase;padding:4px 9px;background:var(--ink);color:var(--chalk)}
.dark .tag{background:var(--chalk);color:var(--ink)}
table{border-collapse:collapse;width:100%}
td,th{padding:10px 12px;text-align:left;border-bottom:1.5px solid rgba(26,20,18,.2);font-size:16px;vertical-align:top}
.dark td,.dark th{border-color:rgba(229,224,218,.25)}
th{font:500 12px 'Mono';letter-spacing:.14em;text-transform:uppercase;opacity:.7}
ul.b{list-style:none}ul.b li{padding-left:26px;position:relative;margin-bottom:10px}
ul.b li:before{content:'';position:absolute;left:0;top:.55em;width:11px;height:8px;background:var(--thread);clip-path:polygon(0 0,100% 0,50% 100%)}
svg{display:block}
.arm{border-radius:0 var(--arc) 0 0}.arm-l{border-radius:var(--arc) 0 0 0}.arm-b{border-radius:0 0 var(--arc) 0}.arm-d{border-radius:0 var(--arc) 0 var(--arc)}
.tilt{transform:rotate(-3deg)}.btn{border-radius:0 12px 0 12px}
.shadow{box-shadow:0 18px 40px -12px rgba(26,20,18,.35)}
.cut{clip-path:polygon(0 0,calc(50% - 14px) 0,50% 14px,calc(50% + 14px) 0,100% 0,100% 100%,0 100%)}
.cutc{clip-path:polygon(0 0,calc(100% - 28px) 0,100% 28px,100% 100%,0 100%)}
"""


# ------------------------------------------------------------ components
def ruler(w, h=34, color=INK, start=0, step=10, label_every=10, unit_px=10, opacity=.8, labels=True, flip=False):
    """Measuring-tape ruler: tick every unit_px; taller every 5; longest + label every label_every."""
    n = int(w / unit_px)
    d = []
    txt = []
    for i in range(n + 1):
        x = i * unit_px
        if i % label_every == 0:
            ln = h * .85
        elif i % 5 == 0:
            ln = h * .55
        else:
            ln = h * .32
        y0, y1 = (0, ln) if not flip else (h, h - ln)
        d.append(f"M{x},{y0}V{y1}")
        if labels and i % label_every == 0 and i > 0:
            ty = ln + 11 if not flip else h - ln - 4
            txt.append(f'<text x="{x+3}" y="{ty:.0f}" font-family="Mono" font-size="9.5" fill="{color}">{start + i // label_every * step}</text>')
    return (f'<svg width="{w}" height="{h+14}" viewBox="0 0 {w} {h+14}" style="opacity:{opacity}"><path d="{"".join(d)}" stroke="{color}" stroke-width="1.5" fill="none"/>{"".join(txt)}</svg>')


def footer(color=INK):
    return f'<div class="ftr">{ruler(1600, 20, color, labels=False, unit_px=8, opacity=.55, flip=False)}</div>'


_counter = {"n": 0}


def page(section, title, body, theme="light", bleed=False, num=True, hdr=True, extra=""):
    _counter["n"] += 1
    n = _counter["n"]
    col = {"light": INK, "paper": INK, "kraft": INK, "mist": INK, "thread": INK, "dark": CHALK, "dye": CHALK}.get(theme, INK)
    h = f'<div class="hdr"><span>Tailored &mdash; Brand Book 1.2</span><span>{section}</span></div>' if hdr else ''
    f = footer(col) if num else ''
    pn = f'<div class="pgn">{n:02d}</div>' if num else ''
    return f'<section class="pg {theme} {"bleed" if bleed else ""}">{h}{body}{f}{pn}{extra}</section>'


def lum(hexc):
    h = hexc.lstrip('#')
    r, g, b = [int(h[i:i+2], 16) / 255 for i in (0, 2, 4)]
    f = lambda c: c / 12.92 if c <= .03928 else ((c + .055) / 1.055) ** 2.4
    return .2126 * f(r) + .7152 * f(g) + .0722 * f(b)


def contrast(a, b):
    la, lb = lum(a), lum(b)
    if la < lb:
        la, lb = lb, la
    return (la + .05) / (lb + .05)


# ------------------------------------------------------------ logo lockups
def mk(color=INK, size=100, mode='knock', thread=THREAD, style=""):
    return S.mark_svg(color, size, mode, thread, style)


def wm(color=INK, height=60, mode='knock', thread=THREAD, style=""):
    return S.wordmark_svg("tailored", color, height, 14, mode, thread, style)


def arwm(color=INK, height=60, mode='knock', thread=THREAD, style=""):
    return A.arabic_svg(AR, color, height, mode, thread, 700, style)


def lockup_h(color=INK, h=64, mode='knock', thread=THREAD, gap=None):
    """symbol + wordmark; wordmark cap-height ~ symbol * .72"""
    gap = gap if gap is not None else h * .28
    return f'<div style="display:flex;align-items:center;gap:{gap}px">{mk(color,h,mode,thread)}{wm(color,h*.78,mode,thread)}</div>'


def lockup_stack(color=INK, h=100, mode='knock', thread=THREAD):
    return f'<div style="display:flex;flex-direction:column;align-items:center;gap:{h*.2}px">{mk(color,h,mode,thread)}{wm(color,h*.5,mode,thread)}</div>'


def lockup_ar_h(color=INK, h=64, mode='knock', thread=THREAD):
    # RTL: wordmark on the right? Mark leads on the right in Arabic reading order
    return f'<div style="display:flex;align-items:center;gap:{h*.28}px;direction:rtl">{mk(color,h,mode,thread)}{arwm(color,h*.78,mode,thread)}</div>'


def lockup_ar_stack(color=INK, h=100, mode='knock', thread=THREAD):
    return f'<div style="display:flex;flex-direction:column;align-items:center;gap:{h*.2}px">{mk(color,h,mode,thread)}{arwm(color,h*.62,mode,thread)}</div>'


def lockup_bi(color=INK, h=64, mode='knock', thread=THREAD):
    """bilingual: mark | english over arabic"""
    return (f'<div style="display:flex;align-items:center;gap:{h*.3}px">{mk(color,h*1.25,mode,thread)}'
            f'<div style="width:3px;height:{h*1.1}px;background:{color};opacity:.9"></div>'
            f'<div style="display:flex;flex-direction:column;gap:{h*.2}px">{wm(color,h*.62,mode,thread)}{arwm(color,h*.5,mode,thread)}</div></div>')


# ------------------------------------------------------------ pattern pieces
def _smooth(p, r=4):
    return p.buffer(-r, join_style=1).buffer(r * 2, join_style=1).buffer(-r, join_style=1)


def shape(name):
    s = _shape(name)
    if isinstance(s, MultiPolygon):
        s = max(s.geoms, key=lambda g: g.area)
    return s


def _shape(name):
    if name == 'front':
        s = box(0, 0, 150, 230).difference(Point(150, 8).buffer(78)).difference(Point(0, -6).buffer(58))
        s = s.union(box(0, 200, 150, 232))
        return _smooth(s, 5)
    if name == 'back':
        s = box(0, 0, 150, 230).difference(Point(150, 18).buffer(66)).difference(Point(0, -14).buffer(40))
        return _smooth(s, 5)
    if name == 'sleeve':
        s = unary_union([box(0, 70, 130, 230), affinity.scale(Point(65, 70).buffer(1), 65, 70)])
        s = s.difference(Polygon([(0, 230), (0, 190), (30, 230)]))
        return _smooth(s, 5)
    if name == 'collar':
        s = Point(110, 110).buffer(110).difference(Point(110, 40).buffer(92)).intersection(box(0, 0, 220, 110))
        return _smooth(s, 4)
    if name == 'pocket':
        return _smooth(Polygon([(0, 0), (130, 0), (130, 110), (65, 160), (0, 110)]), 4)
    if name == 'yoke':
        s = box(0, 0, 260, 90).difference(affinity.scale(Point(130, 100).buffer(1), 100, 52))
        return _smooth(s, 4)
    if name == 'cuff':
        return _smooth(Polygon([(0, 0), (200, 0), (200, 40), (170, 60), (0, 60)]), 3)
    if name == 'placket':
        return _smooth(Polygon([(0, 0), (46, 0), (46, 230), (0, 214)]), 3)
    raise KeyError(name)


def notches_on(poly, ts, size=9):
    ring = LineString(poly.exterior.coords)
    L = ring.length
    out = []
    for t in ts:
        pt = ring.interpolate(t * L)
        a = ring.interpolate(min(L, t * L + 1.0))
        b = ring.interpolate(max(0, t * L - 1.0))
        dx, dy = a.x - b.x, a.y - b.y
        n = math.hypot(dx, dy) or 1
        nx, ny = dy / n, -dx / n  # normal
        # ensure outward
        probe = Point(pt.x + nx * 2, pt.y + ny * 2)
        if poly.contains(probe):
            nx, ny = -nx, -ny
        tx, ty = dx / n, dy / n
        p1 = (pt.x - tx * size * .6, pt.y - ty * size * .6)
        p2 = (pt.x + tx * size * .6, pt.y + ty * size * .6)
        p3 = (pt.x + nx * size, pt.y + ny * size)
        out.append(Polygon([p1, p2, p3]))
    return out


def piece_svg(name, fill="none", stroke=INK, seam=True, label=None, scale=1.0, rot=0, notch_ts=(.12, .46, .8), sw=2.2, accent=THREAD, grain=True, txt=INK, solid_notch=True):
    s = shape(name)
    b = s.bounds
    w, h = b[2] - b[0], b[3] - b[1]
    pad = 18
    out = []
    out.append(f'<path d="{S.poly_d(s)}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round" fill-rule="evenodd"/>')
    if seam:
        inner = s.buffer(-9, join_style=1)
        if not inner.is_empty:
            geoms = inner.geoms if isinstance(inner, MultiPolygon) else [inner]
            for g in geoms:
                out.append(f'<path d="{S.poly_d(Polygon(g.exterior))}" fill="none" stroke="{accent}" stroke-width="2.2" stroke-dasharray="7 6" stroke-linejoin="round"/>')
    for n in notches_on(s, notch_ts):
        out.append(f'<path d="{S.poly_d(n)}" fill="{stroke if solid_notch else accent}"/>')
    cx, cy = s.centroid.x, s.centroid.y
    if grain:
        gh = h * .5
        y0, y1 = cy - gh / 2, cy + gh / 2
        out.append(f'<path d="M{cx},{y0}V{y1}M{cx-6},{y0+12}L{cx},{y0}L{cx+6},{y0+12}M{cx-6},{y1-12}L{cx},{y1}L{cx+6},{y1-12}" stroke="{stroke}" stroke-width="1.6" fill="none"/>')
    if label:
        out.append(f'<text x="{cx+12}" y="{cy+4}" font-family="Mono" font-size="10.5" letter-spacing="1.2" fill="{txt}" transform="rotate(-90 {cx+12} {cy+4})" text-anchor="middle">{label}</text>')
    W_, H_ = (w + 2 * pad) * scale, (h + 2 * pad) * scale
    return (f'<svg viewBox="{b[0]-pad} {b[1]-pad} {w+2*pad} {h+2*pad}" width="{W_:.0f}" height="{H_:.0f}" style="transform:rotate({rot}deg)">{"".join(out)}</svg>')


def layplan(w, h, seed=3, fills=None, stroke=INK, tries=900, names=None, scale_range=(.8, 1.5), labels=True, accent=THREAD, seam=True, txt=None, margin=10, maxn=60):
    """Auto-packed cutting lay-plan of pattern pieces -> svg of size w x h"""
    rnd = random.Random(seed)
    names = names or ['front', 'back', 'sleeve', 'collar', 'pocket', 'yoke', 'cuff', 'placket']
    fills = fills or ['none']
    placed = []
    out = []
    cnt = 0
    for _ in range(tries):
        if cnt >= maxn:
            break
        nm = rnd.choice(names)
        sc = rnd.uniform(*scale_range)
        rot = rnd.choice([0, 0, 90, 180, 270, rnd.uniform(-25, 25), rnd.uniform(155, 205)])
        s = shape(nm)
        s = affinity.scale(s, sc, sc, origin=(0, 0))
        s = affinity.rotate(s, rot, origin=s.centroid)
        b = s.bounds
        x = rnd.uniform(-b[0], w - b[2]); y = rnd.uniform(-b[1], h - b[3])
        if w < b[2] - b[0] or h < b[3] - b[1]:
            continue
        s = affinity.translate(s, x, y)
        if any(s.buffer(margin).intersects(p) for p in placed):
            continue
        placed.append(s)
        cnt += 1
        fill = rnd.choice(fills)
        out.append(f'<path d="{S.poly_d(s)}" fill="{fill}" stroke="{stroke}" stroke-width="2" stroke-linejoin="round" fill-rule="evenodd"/>')
        if seam:
            inner = s.buffer(-8 * sc, join_style=1)
            if not inner.is_empty and isinstance(inner, Polygon):
                out.append(f'<path d="{S.poly_d(Polygon(inner.exterior))}" fill="none" stroke="{accent}" stroke-width="2" stroke-dasharray="6 5" stroke-linejoin="round"/>')
        for n in notches_on(s, (.15, .5, .83), 8 * sc):
            out.append(f'<path d="{S.poly_d(n)}" fill="{stroke}"/>')
        c = s.centroid
        bb = s.bounds
        gh = (bb[3] - bb[1]) * .32
        out.append(f'<path d="M{c.x},{c.y-gh}V{c.y+gh}M{c.x-5},{c.y-gh+10}L{c.x},{c.y-gh}L{c.x+5},{c.y-gh+10}M{c.x-5},{c.y+gh-10}L{c.x},{c.y+gh}L{c.x+5},{c.y+gh-10}" stroke="{stroke}" stroke-width="1.5" fill="none"/>' if abs(rot) % 90 < 1 else '')
    return f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}">{"".join(out)}</svg>'


# ------------------------------------------------------------ chalk marks
def chalk(points, color=CHALK, w=3.2, jitter=1.1, seed=1, op=.85):
    rnd = random.Random(seed)
    pts = []
    for i in range(len(points) - 1):
        (x1, y1), (x2, y2) = points[i], points[i + 1]
        n = max(2, int(math.hypot(x2 - x1, y2 - y1) / 18))
        for k in range(n):
            t = k / n
            pts.append((x1 + (x2 - x1) * t + rnd.uniform(-jitter, jitter), y1 + (y2 - y1) * t + rnd.uniform(-jitter, jitter)))
    pts.append(points[-1])
    d = 'M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in pts)
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round" opacity="{op}"/>'


def fit_dial(score=87, size=120, color=INK, accent=THREAD, bg=None, num=True):
    """Half-moon fit gauge built from tape ticks; needle is the notch."""
    cx, cy, r = 60, 64, 48
    ticks = []
    for i in range(0, 41):
        a = math.pi * (1 - i / 40)
        r1 = r - (14 if i % 5 == 0 else 8)
        x1, y1 = cx + r * math.cos(a), cy - r * math.sin(a)
        x2, y2 = cx + r1 * math.cos(a), cy - r1 * math.sin(a)
        on = i <= score * 40 / 100
        ticks.append(f'<path d="M{x1:.1f},{y1:.1f}L{x2:.1f},{y2:.1f}" stroke="{accent if on else color}" stroke-width="{2.6 if i%5==0 else 1.8}" opacity="{1 if on else .35}"/>')
    t = f'<text x="60" y="62" text-anchor="middle" font-family="Fraunces" font-weight="600" font-size="30" fill="{color}" style="font-variation-settings:\'SOFT\' 100,\'opsz\' 72">{score}</text>' if num else ''
    t2 = f'<text x="60" y="80" text-anchor="middle" font-family="Mono" font-size="8" letter-spacing="1.5" fill="{color}" opacity=".7">FIT</text>' if num else ''
    return f'<svg viewBox="0 0 120 90" width="{size}" height="{size*.75:.0f}">{"".join(ticks)}{t}{t2}</svg>'


# ------------------------------------------------------------ icons (48 grid)
ICONS = {
    'radar': ('<circle cx="21" cy="21" r="13"/><path d="M31,31 L43,43"/>', 'M14,21h14'),
    'cv': ('<path d="M10,6H30L38,14V42H10Z"/><path d="M16,24H32M16,32H32"/>', 'M30,6V14H38'),
    'job': ('<rect x="6" y="16" width="36" height="24"/><path d="M17,16V9H31V16M6,28H42"/>', ''),
    'fit': ('<path d="M6,36A18,18 0 0 1 42,36"/><path d="M24,36L33,22"/>', ''),
    'send': ('<path d="M5,24L43,7L31,41L23,29Z"/><path d="M23,29L43,7"/>', ''),
    'measure': ('<circle cx="24" cy="15" r="8"/><path d="M8,43A16,14 0 0 1 40,43"/>', ''),
    'needle': ('<path d="M42,6L12,40"/><path d="M12,40L8,44"/><ellipse cx="38" cy="10" rx="2" ry="5" transform="rotate(40 38 10)"/>', ''),
    'scissors': ('<circle cx="12" cy="36" r="6"/><circle cx="36" cy="36" r="6"/><path d="M16,31L38,6M32,31L10,6"/>', ''),
    'tape': ('<rect x="3" y="17" width="42" height="14"/><path d="M10,17V24M18,17V22M26,17V24M34,17V22M42,17V24"/>', ''),
    'diff': ('<path d="M8,14H26M8,24H40M8,34H30"/><path d="M36,10V20M31,15H41"/>', ''),
    'globe': ('<circle cx="24" cy="24" r="17"/><ellipse cx="24" cy="24" rx="7" ry="17"/><path d="M7,24H41"/>', ''),
    'credit': ('<circle cx="24" cy="24" r="17"/><circle cx="24" cy="24" r="9" stroke-dasharray="4 3.5"/>', ''),
    'check': ('<path d="M8,26L19,37L40,12"/>', ''),
    'save': ('<path d="M12,6H36V42L24,32L12,42Z"/>', ''),
    'chat': ('<path d="M6,8H42V32H22L12,41V32H6Z"/>', ''),
    'filter': ('<path d="M6,10H42L28,26V40L20,36V26Z"/>', ''),
}


def icon(name, size=40, color=INK, accent=THREAD, sw=3.4):
    body, acc = ICONS[name]
    accent_el = ''
    pos = {'radar': (14, 14), 'cv': (34, 24), 'job': (24, 22), 'fit': (24, 36), 'send': (32, 22), 'measure': (24, 24), 'needle': (22, 26),
           'scissors': (24, 22), 'tape': (24, 24), 'diff': (36, 15), 'globe': (24, 24), 'credit': (24, 24), 'check': (24, 36), 'save': (24, 22), 'chat': (24, 20), 'filter': (24, 18)}[name]
    tri = f'<path d="M{pos[0]-5},{pos[1]-4}H{pos[0]+5}L{pos[0]},{pos[1]+5}Z" fill="{accent}" stroke="none"/>'
    return (f'<svg viewBox="0 0 48 48" width="{size}" height="{size}"><g fill="none" stroke="{color}" stroke-width="{sw}" stroke-linejoin="miter" stroke-linecap="butt">{body}</g>{tri}</svg>')


def swatch_pat(kind, w, h, fg=INK, bg="transparent", op=1):
    """Background patterns as inline svg."""
    if kind == 'seam':  # dashed seam grid
        s = 48
        d = ''.join(f'M0,{y}H{w}' for y in range(0, h + 1, s)) + ''.join(f'M{x},0V{h}' for x in range(0, w + 1, s))
        return f'<svg width="{w}" height="{h}"><rect width="{w}" height="{h}" fill="{bg}"/><path d="{d}" stroke="{fg}" stroke-width="1.4" stroke-dasharray="7 6" fill="none" opacity="{op}"/></svg>'
    if kind == 'notch':
        s = 40
        els = []
        for r, y in enumerate(range(0, h + s, s)):
            off = (s // 2) if r % 2 else 0
            for x in range(-s, w + s, s):
                els.append(f'M{x+off+6},{y+8}h14l-7,10z')
        return f'<svg width="{w}" height="{h}"><rect width="{w}" height="{h}" fill="{bg}"/><path d="{"".join(els)}" fill="{fg}" opacity="{op}"/></svg>'
    if kind == 'tape':
        d = ''
        for y in range(0, h + 1, 36):
            for i in range(0, int(w / 8) + 1):
                x = i * 8
                L = 18 if i % 10 == 0 else (12 if i % 5 == 0 else 7)
                d += f'M{x},{y}v{L}'
        return f'<svg width="{w}" height="{h}"><rect width="{w}" height="{h}" fill="{bg}"/><path d="{d}" stroke="{fg}" stroke-width="1.4" opacity="{op}"/></svg>'
    if kind == 'selvedge':
        els = []
        for x in range(0, w, 56):
            els.append(f'<rect x="{x}" y="0" width="18" height="{h}" fill="{fg}" opacity="{op*.18}"/>')
            els.append(f'<path d="M{x+27},0V{h}" stroke="{THREAD}" stroke-width="2.5" stroke-dasharray="9 8"/>')
        return f'<svg width="{w}" height="{h}"><rect width="{w}" height="{h}" fill="{bg}"/>{"".join(els)}</svg>'
    if kind == 'cross':  # stitch crosses
        els = []
        for y in range(20, h, 44):
            for x in range(20, w, 44):
                els.append(f'M{x-5},{y-5}L{x+5},{y+5}M{x+5},{y-5}L{x-5},{y+5}')
        return f'<svg width="{w}" height="{h}"><rect width="{w}" height="{h}" fill="{bg}"/><path d="{"".join(els)}" stroke="{fg}" stroke-width="2" opacity="{op}"/></svg>'
    raise KeyError(kind)





# ------------------------------------------------------------ French curve (dynamic motif)
def fcurve(w=520, color=INK, accent=THREAD, fill="none", sw=2.6, holes=True, rot=0, seam=True):
    """A tailor's French-curve template: sweeping organic outline, dashed seam, three eyelets, notch ticks."""
    h = w * .46
    d = "M14,122 C40,122 70,52 150,40 C240,26 300,96 392,56 C430,40 470,34 506,30 C470,120 380,196 250,196 C150,196 60,190 28,168 C14,158 8,140 14,122Z"
    sc = f"scale({w/520:.4f})"
    seam_el = f'<path d="{d}" transform="translate(260 113) scale(.9) translate(-260 -113)" fill="none" stroke="{accent}" stroke-width="{sw*.8}" stroke-dasharray="9 7" stroke-linejoin="round"/>' if seam else ''
    hole_el = ''
    if holes:
        hole_el = (f'<ellipse cx="170" cy="128" rx="34" ry="15" transform="rotate(-14 170 128)" fill="none" stroke="{color}" stroke-width="{sw}"/>'
                   f'<ellipse cx="300" cy="128" rx="26" ry="11" transform="rotate(-6 300 128)" fill="none" stroke="{color}" stroke-width="{sw}"/>'
                   f'<circle cx="402" cy="112" r="9" fill="none" stroke="{color}" stroke-width="{sw}"/>')
    ticks = ''.join(f'<path d="M{x},{y}l{dx},{dy}" stroke="{color}" stroke-width="{sw*.7}"/>' for x, y, dx, dy in
                    [(90, 70, -3, 12), (120, 52, -2, 12), (200, 36, 0, 12), (250, 38, 1, 12), (320, 84, 3, 11), (360, 76, 3, 11), (440, 40, 3, 12)])
    return (f'<svg width="{w}" height="{h:.0f}" viewBox="0 0 520 240" style="transform:rotate({rot}deg);overflow:visible">'
            f'<path d="{d}" fill="{fill}" stroke="{color}" stroke-width="{sw}" stroke-linejoin="round"/>{seam_el}{hole_el}{ticks}</svg>')


def sweep(w=900, h=300, color=THREAD, sw=5, n=1, gap=14, dash=False):
    """Long sweeping armhole curve lines (n parallel strokes) for backgrounds / covers."""
    out = []
    for i in range(n):
        o = i * gap
        out.append(f'<path d="M-20,{h*.92+o} C{w*.28},{h*.95+o} {w*.46},{h*.1+o} {w+20},{h*.12+o}" fill="none" stroke="{color}" stroke-width="{sw}" stroke-linecap="round"' + (' stroke-dasharray="14 11"' if dash else '') + '/>')
    return f'<svg width="{w}" height="{h+n*gap}" viewBox="0 0 {w} {h+n*gap}" style="overflow:visible">{"".join(out)}</svg>'

