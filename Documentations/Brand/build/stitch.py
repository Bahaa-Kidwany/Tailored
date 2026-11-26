"""Tailored Stitch engine: builds true vector outlines (shapely) with a knocked-out topstitch."""
import math, itertools
from functools import lru_cache
from shapely.geometry import LineString, Polygon, box, MultiPolygon
from shapely.ops import unary_union, substring
from shapely import affinity
from svgpathtools import parse_path
from stitch_defs import G, W

STITCH_INSET = 3.4
STITCH_W = 2.0
DASH = 4.6
GAP = 4.0


def sample_subpaths(d):
    out = []
    for sp in parse_path(d).continuous_subpaths():
        pts = []
        for seg in sp:
            n = max(2, int(seg.length() / 1.2))
            for k in range(n):
                z = seg.point(k / n)
                pts.append((z.real, z.imag))
        z = sp[-1].point(1)
        pts.append((z.real, z.imag))
        out.append(pts)
    return out


def stroke_poly(d, w=W):
    polys = []
    for pts in sample_subpaths(d):
        if len(pts) < 2:
            continue
        ls = LineString(pts)
        polys.append(ls.buffer(w / 2, cap_style=2, join_style=2, mitre_limit=2.5, resolution=24))
    return unary_union(polys)


def dashes_along(line, dash=DASH, gap=GAP, w=STITCH_W):
    L = line.length
    if L < dash:
        return None
    n = max(1, round((L + gap) / (dash + gap)))
    d = (L + gap) / n - gap  # fit evenly on closed loops
    parts = []
    s = 0.0
    for i in range(n):
        seg = substring(line, s + 0.0, min(L, s + d))
        if seg.length > 0.01:
            parts.append(seg.buffer(w / 2, cap_style=2, join_style=2, resolution=8))
        s += d + gap
    return unary_union(parts) if parts else None


def boundaries(poly):
    geoms = poly.geoms if isinstance(poly, MultiPolygon) else [poly]
    for g in geoms:
        yield LineString(g.exterior.coords)
        for r in g.interiors:
            yield LineString(r.coords)


def stitched(poly, inset=STITCH_INSET, dash=DASH, gap=GAP, w=STITCH_W):
    inner = poly.buffer(-inset, join_style=2, mitre_limit=2.0)
    if inner.is_empty:
        return poly
    cuts = []
    for ls in boundaries(inner):
        dd = dashes_along(ls, dash, gap, w)
        if dd is not None:
            cuts.append(dd)
    if not cuts:
        return poly
    return poly.difference(unary_union(cuts))





def topstitch_dashes(poly, inset=STITCH_INSET, dash=DASH, gap=GAP, w=STITCH_W):
    inner = poly.buffer(-inset, join_style=2, mitre_limit=2.0)
    cuts = []
    if not inner.is_empty:
        for ls in boundaries(inner):
            dd = dashes_along(ls, dash, gap, w)
            if dd is not None:
                cuts.append(dd)
    return unary_union(cuts) if cuts else Polygon()


@lru_cache(maxsize=None)
def glyph_geom(ch):
    """-> (poly, dashes) centre-line running stitch."""
    g = G[ch]
    parts, dparts = [], []
    for d in g['p']:
        parts.append(stroke_poly(d))
        for pts in sample_subpaths(d):
            if len(pts) < 2:
                continue
            ls = LineString(pts)
            closed = math.dist(pts[0], pts[-1]) < 0.5
            if not closed and not g.get('clip'):
                if ls.length < 14:
                    continue
                ls = substring(ls, 6.5, ls.length - 6.5)
            dd = dashes_along(ls, 4.6, 4.0, 2.2)
            if dd is not None:
                dparts.append(dd)
    for tri in g.get('tri', []):
        parts.append(Polygon(tri))
    if not parts:
        return Polygon(), Polygon()
    p = unary_union(parts)
    ds = unary_union(dparts) if dparts else Polygon()
    if g.get('clip'):
        y0, y1 = g['clip']
        bx = box(-60, y0, g['w'] + 60, y1)
        p = p.intersection(bx)
        ds = ds.intersection(p.buffer(-4.2, join_style=2))
    if g.get('rot'):
        p = affinity.rotate(p, 180, origin=(30, 50))
        ds = affinity.rotate(ds, 180, origin=(30, 50))
    return p, ds


def poly_d(poly, nd=2):
    geoms = poly.geoms if isinstance(poly, MultiPolygon) else [poly]
    out = []
    for g in geoms:
        if g.is_empty:
            continue
        for ring in [g.exterior, *g.interiors]:
            c = list(ring.coords)
            out.append('M' + ' L'.join(f'{x:.{nd}f},{y:.{nd}f}' for x, y in c[:-1]) + 'Z')
    return ''.join(out)


def word_geom(text, track=14):
    x = 0
    bodies, dashes = [], []
    ymax = 100
    for ch in text:
        if ch not in G:
            ch = ' '
        p, ds = glyph_geom(ch)
        if not p.is_empty:
            bodies.append(affinity.translate(p, x, 0))
            if not ds.is_empty:
                dashes.append(affinity.translate(ds, x, 0))
        if ch in 'gjpqy,':
            ymax = 140
        x += G[ch]['w'] + track
    return unary_union(bodies), (unary_union(dashes) if dashes else Polygon()), x - track, ymax


_c = {}


def _svg(body, dash, vb, size_style, color, mode, thread):
    x, y, w, h = vb
    if mode == 'solid':
        inner = f'<path d="{poly_d(body)}" fill="{color}" fill-rule="evenodd"/>'
    elif mode == 'thread':
        inner = (f'<path d="{poly_d(body)}" fill="{color}" fill-rule="evenodd"/>'
                 f'<path d="{poly_d(dash)}" fill="{thread}"/>')
    else:  # knock
        inner = f'<path d="{poly_d(body.difference(dash))}" fill="{color}" fill-rule="evenodd"/>'
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x} {y} {w} {h}" style="{size_style}">{inner}</svg>'


def wordmark_svg(text="tailored", color="#1A1412", height=100, track=14, mode='knock', thread="#E9453F", style="", full=False):
    """mode: knock (transparent stitch) | thread (coloured stitch) | solid (no stitch).
    height = px height of viewbox (ascender->baseline unless descenders present)."""
    k = (text, track)
    if k not in _c:
        _c[k] = word_geom(text, track)
    body, dash, w, ymax = _c[k]
    pad = 6
    vb = (-pad - 3, -pad, w + 2 * pad + 6, ymax + 2 * pad)
    ww = height * vb[2] / vb[3]
    return _svg(body, dash, vb, f"width:{ww:.1f}px;height:{height}px;{style}", color, mode, thread)


# ---------------------------------------------------------------- symbol: the Notched T
MARK_PTS = [(6, 10), (44, 10), (50, 18), (56, 10), (94, 10), (94, 38), (62, 38), (62, 94), (38, 94), (38, 38), (6, 38)]
_mk = {}


def mark_geom():
    if 'm' not in _mk:
        p = Polygon(MARK_PTS)
        _mk['m'] = (p, topstitch_dashes(p, 5.0, 6.0, 4.6, 2.6))
    return _mk['m']


def mark_svg(color="#1A1412", size=100, mode='knock', thread="#E9453F", style="", pad=0):
    body, dash = mark_geom()
    vb = (-pad, -pad, 100 + 2 * pad, 100 + 2 * pad)
    return _svg(body, dash, vb, f"width:{size}px;height:{size}px;{style}", color, mode, thread)


if __name__ == "__main__":
    html = "<body style='margin:0;background:#E5E0DA;padding:40px'>"
    html += wordmark_svg("tailored", height=220, mode='thread') + "<br>"
    html += wordmark_svg("tailored", height=120) + "<br>"
    html += wordmark_svg("abcdefghijklm", height=150) + "<br>"
    html += wordmark_svg("nopqrstuvwxyz", height=150) + "<br>"
    html += wordmark_svg("0123456789.,:!-+/", height=150) + "<br>"
    html += mark_svg(size=220, mode='thread') + mark_svg(size=110) + mark_svg(size=48, mode='solid')
    open("_proof.html", "w", encoding="utf8").write(html)




