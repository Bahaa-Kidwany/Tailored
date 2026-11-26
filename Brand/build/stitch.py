"""Tailored Stitch vector engine.
Converts stitch_defs glyph paths into Shapely outlines.
Produces SVG strings for wordmarks, marks, and decorative elements.
"""
import itertools
from shapely.geometry import Polygon, MultiPolygon, LineString, Point, box
from shapely.ops import unary_union
from shapely import affinity
import stitch_defs as D

# ── stitch parameters ───────────────────────────────────────────────────────
STROKE_W     = 11.0   # half-width of each glyph stroke (outline buffer)
DASH         = 4.6    # topstitch dash length
GAP          = 4.0    # topstitch gap length
STITCH_W     = 2.0    # topstitch stroke width
STITCH_INSET = 4.2    # inset from stroke edge

_mask_counter = itertools.count(1)


def _mark_shape():
    """T-shaped mark with notch cut from crossbar centre-top."""
    bar = box(0, 0, 112, 28)
    stem = box(44, 0, 68, 100)
    T = bar.union(stem)
    notch = Polygon([(50, 0), (62, 0), (56, 18)])
    return T.difference(notch)


def _stroke_poly(pts, w=STROKE_W):
    """Buffer a polyline into a filled stroke polygon."""
    if len(pts) < 2:
        if len(pts) == 1:
            return Point(pts[0]).buffer(w)
        return Polygon()
    ls = LineString(pts)
    return ls.buffer(w, cap_style=1, join_style=1)


def _ensure_poly(geom):
    if isinstance(geom, MultiPolygon):
        return max(geom.geoms, key=lambda g: g.area)
    return geom


def glyph_geom(ch):
    """Return Shapely geometry for a single character."""
    strokes = D.G.get(ch, [])
    if not strokes:
        return Polygon()
    parts = [_stroke_poly(pts) for pts in strokes if pts]
    geom = unary_union(parts)
    return geom


def _char_width(ch):
    return D.WIDTHS.get(ch, 56)


def word_geom(word, tracking=14):
    """Return (list of (geom, x_offset), total_width)."""
    result = []
    x = 0
    for ch in word.lower():
        g = glyph_geom(ch)
        result.append((g, x))
        x += _char_width(ch) + tracking
    return result, x


def poly_d(geom):
    """Convert a Shapely Polygon/MultiPolygon to SVG path d string."""
    if geom is None or geom.is_empty:
        return ""
    if isinstance(geom, MultiPolygon):
        return " ".join(poly_d(g) for g in geom.geoms)
    if not isinstance(geom, Polygon):
        return ""

    def ring_d(coords):
        pts = list(coords)
        if pts[-1] == pts[0]:
            pts = pts[:-1]
        return "M" + " L".join(f"{x:.2f},{y:.2f}" for x, y in pts) + " Z"

    d = ring_d(geom.exterior.coords)
    for interior in geom.interiors:
        d += " " + ring_d(interior.coords)
    return d


def topstitch_dashes(geom, inset=STITCH_INSET, dash=DASH, gap=GAP):
    """Generate topstitch dash lines inside a stroke polygon."""
    if geom is None or geom.is_empty:
        return []
    shrunk = geom.buffer(-inset, join_style=1)
    if shrunk.is_empty:
        return []
    if isinstance(shrunk, MultiPolygon):
        rings = [g.exterior for g in shrunk.geoms]
    else:
        rings = [shrunk.exterior]

    segs = []
    period = dash + gap
    for ring in rings:
        L = ring.length
        t = 0.0
        while t < L:
            p1 = ring.interpolate(t)
            p2 = ring.interpolate(min(L, t + dash))
            segs.append(((p1.x, p1.y), (p2.x, p2.y)))
            t += period
    return segs


def _svg(geom, fill, stroke_col, mode, thread_col, sw=STITCH_W, inset=STITCH_INSET, dash=DASH, gap=GAP):
    """Render geometry as SVG string with optional topstitch (or knocked-out mask)."""
    d = poly_d(geom)
    if not d:
        return ""
    if mode == 'solid':
        return f'<path d="{d}" fill="{fill}" stroke="none" fill-rule="evenodd"/>'

    segs = topstitch_dashes(geom, inset=inset, dash=dash, gap=gap)
    if not segs:
        return f'<path d="{d}" fill="{fill}" stroke="none" fill-rule="evenodd"/>'

    lines = "".join(
        f'<line x1="{p1[0]:.2f}" y1="{p1[1]:.2f}" x2="{p2[0]:.2f}" y2="{p2[1]:.2f}" '
        f'stroke="{ "black" if mode=="knock" else thread_col }" stroke-width="{sw:.2f}" stroke-linecap="butt"/>'
        for p1, p2 in segs
    )

    if mode == 'knock':
        mid = f"tsm{next(_mask_counter)}"
        return (f'<defs><mask id="{mid}"><rect x="-9999" y="-9999" width="29999" height="29999" fill="white"/>'
                f'{lines}</mask></defs>'
                f'<path d="{d}" fill="{fill}" stroke="none" fill-rule="evenodd" mask="url(#{mid})"/>')
    else:  # 'thread'
        return f'<path d="{d}" fill="{fill}" stroke="none" fill-rule="evenodd"/>{lines}'


def wordmark_svg(word, color, height, tracking=14, mode='knock', thread='#FF4A1C', style=""):
    """Full wordmark SVG string with tight bounding box."""
    chars, total_w = word_geom(word, tracking)
    scale = height / 100.0

    scaled_geoms = []
    for geom, xoff in chars:
        if geom.is_empty:
            continue
        g = affinity.translate(geom, xoff, 0)
        g = affinity.scale(g, scale, scale, origin=(0, 0))
        scaled_geoms.append(g)

    if not scaled_geoms:
        return f'<svg width="10" height="{height:.1f}"></svg>'

    all_bounds = [g.bounds for g in scaled_geoms]
    minx = min(b[0] for b in all_bounds) - 2
    miny = min(b[1] for b in all_bounds) - 2
    maxx = max(b[2] for b in all_bounds) + 2
    maxy = max(b[3] for b in all_bounds) + 2
    sw = maxx - minx
    sh = maxy - miny

    parts = [
        _svg(g, color, color, mode, thread,
             sw=max(1.2, STITCH_W * scale),
             inset=max(1.8, STITCH_INSET * scale),
             dash=max(2.4, DASH * scale),
             gap=max(2.0, GAP * scale))
        for g in scaled_geoms
    ]
    return (f'<svg width="{sw:.1f}" height="{sh:.1f}" '
            f'viewBox="{minx:.1f} {miny:.1f} {sw:.1f} {sh:.1f}" style="{style}">'
            + "".join(parts) + '</svg>')


def mark_svg(color, size=100, mode='knock', thread='#FF4A1C', style=""):
    """The notched-T logo mark."""
    geom = _mark_shape()
    scale = size / 112.0
    geom = affinity.scale(geom, scale, scale, origin=(0, 0))
    sw = size
    sh = 100 * scale

    svg_body = _svg(geom, color, color, mode, thread,
                    sw=max(1.2, STITCH_W * scale),
                    inset=max(1.8, STITCH_INSET * scale),
                    dash=max(2.4, DASH * scale),
                    gap=max(2.0, GAP * scale))
    return (f'<svg width="{sw:.1f}" height="{sh:.1f}" '
            f'viewBox="0 0 {sw:.1f} {sh:.1f}" style="{style}">'
            + svg_body + '</svg>')
