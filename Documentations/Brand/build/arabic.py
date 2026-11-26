import os
"""Arabic wordmark: Reem Kufi (pinned Bold) outlines, dots re-cut as notches, topstitched."""
import functools
import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools.pens.recordingPen import DecomposingRecordingPen
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union
from shapely import affinity
from svgpathtools import Path, Line, CubicBezier, QuadraticBezier
import stitch as S

AR_NAME = "\u062a\u0641\u0635\u064a\u0644"
FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fonts", "ReemKufi.ttf")
PINNED = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ReemKufi-pinned.ttf")


def pinned(wght):
    p = PINNED.replace('.ttf', f'-{wght}.ttf')
    import os
    if not os.path.exists(p):
        f = TTFont(FONT)
        f = instancer.instantiateVariableFont(f, {"wght": wght})
        f.save(p)
    return p


def contour_points(rec):
    """RecordingPen value -> list of contours (list of (x,y))"""
    contours, cur, pos = [], [], None
    for op, args in rec:
        if op == 'moveTo':
            cur = [args[0]]
            pos = args[0]
        elif op == 'lineTo':
            cur.append(args[0]); pos = args[0]
        elif op == 'qCurveTo':
            pts = list(args)
            # TrueType implied on-curve points
            offs = pts[:-1]
            end = pts[-1]
            if end is None:
                continue
            seq = []
            for i, o in enumerate(offs):
                if i < len(offs) - 1:
                    nxt = offs[i + 1]
                    on = ((o[0] + nxt[0]) / 2, (o[1] + nxt[1]) / 2)
                    seq.append((o, on))
                else:
                    seq.append((o, end))
            p0 = pos
            for o, e in seq:
                for k in range(1, 9):
                    t = k / 8
                    x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * o[0] + t * t * e[0]
                    y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * o[1] + t * t * e[1]
                    cur.append((x, y))
                p0 = e
            pos = end
        elif op == 'curveTo':
            p0 = pos
            c1, c2, e = args
            for k in range(1, 11):
                t = k / 10
                x = (1 - t) ** 3 * p0[0] + 3 * (1 - t) ** 2 * t * c1[0] + 3 * (1 - t) * t * t * c2[0] + t ** 3 * e[0]
                y = (1 - t) ** 3 * p0[1] + 3 * (1 - t) ** 2 * t * c1[1] + 3 * (1 - t) * t * t * c2[1] + t ** 3 * e[1]
                cur.append((x, y))
            pos = e
        elif op in ('closePath', 'endPath'):
            if len(cur) > 2:
                contours.append(cur)
            cur = []
    return contours


@functools.lru_cache(maxsize=None)
def shaped_contours(text, wght=700):
    path = pinned(wght)
    blob = hb.Blob.from_file_path(path)
    face = hb.Face(blob)
    font = hb.Font(face)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    buf.direction = 'rtl'
    hb.shape(font, buf, {"kern": True, "liga": True})
    tt = TTFont(path)
    gs = tt.getGlyphSet()
    order = tt.getGlyphOrder()
    x = 0
    allc = []
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        name = order[info.codepoint]
        pen = DecomposingRecordingPen(gs)
        gs[name].draw(pen)
        allc.append([[(px + x + pos.x_offset, py + pos.y_offset) for px, py in c] for c in contour_points(pen.value)])
        x += pos.x_advance
    return allc


def arabic_geom(text=AR_NAME, wght=700, notch_dots=True, height=120, norm=True):
    glyphs = shaped_contours(text, wght)
    bodies, notches = [], []
    allb = []
    for cs in glyphs:
        polys = [Polygon(c).buffer(0) for c in cs]
        if not polys:
            continue
        allb += [p.bounds for p in polys]
    ymin = min(b[1] for b in allb); ymax = max(b[3] for b in allb)
    H = 1000.0
    for cs in glyphs:
        polys = [Polygon(c).buffer(0) for c in cs]
        if not polys:
            continue
        inside = [any(j != i and polys[j].area > p.area * 3 and polys[j].contains(p.representative_point()) for j in range(len(polys))) for i, p in enumerate(polys)]
        outers, holes, dots = [], [], []
        for c, p, ins in zip(cs, polys, inside):
            b = p.bounds
            area2 = sum(c[i][0] * c[(i + 1) % len(c)][1] - c[(i + 1) % len(c)][0] * c[i][1] for i in range(len(c)))
            isdot = (not ins) and max(b[2] - b[0], b[3] - b[1]) < 0.13 * H and p.area < 0.02 * H * H
            if isdot:
                dots.append(p)
            elif area2 < 0:
                outers.append(p)
            else:
                holes.append(p)
        geom = unary_union(outers) if outers else None
        if geom is not None and holes:
            geom = geom.difference(unary_union(holes))
        if geom is not None:
            bodies.append(geom)
        gb = geom.bounds if geom is not None else (0, ymin, 0, ymax)
        mid = gb[1] + (gb[3] - gb[1]) * 0.5
        for p in dots:
            if not notch_dots:
                bodies.append(p); continue
            b = p.bounds
            cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
            w = (b[2] - b[0]) * 1.3
            hh = w * 0.9
            if cy > mid:  # above the letter (font y-up) -> triangle pointing down
                tri = Polygon([(cx - w / 2, cy + hh / 2), (cx + w / 2, cy + hh / 2), (cx, cy - hh / 2)])
            else:
                tri = Polygon([(cx - w / 2, cy - hh / 2), (cx + w / 2, cy - hh / 2), (cx, cy + hh / 2)])
            notches.append(tri)
    g = unary_union(bodies + notches)
    g = affinity.scale(g, 1, -1, origin=(0, 0))
    if not norm:
        g = affinity.scale(g, .12, .12, origin=(0, 0))
        b = g.bounds
        return affinity.translate(g, -b[0], 0)
    b = g.bounds
    s = height / (b[3] - b[1])
    g = affinity.translate(g, -b[0], -b[1])
    g = affinity.scale(g, s, s, origin=(0, 0))
    return g

@functools.lru_cache(maxsize=None)
def arabic_parts(text=AR_NAME, wght=700, height=120, inset=3.6, norm=True):
    g = arabic_geom(text, wght, True, height, norm)
    # stitch only the heavy letter bodies (skip tiny notches)
    big = [p for p in (g.geoms if hasattr(g, 'geoms') else [g]) if p.area > 120]
    small = [p for p in (g.geoms if hasattr(g, 'geoms') else [g]) if p.area <= 120]
    bigu = unary_union(big)
    dash = S.topstitch_dashes(bigu, inset, 5.0, 4.2, 2.0)
    return g, dash


def arabic_svg(text=AR_NAME, color="#1A1412", height=100, mode='knock', thread="#E9453F", wght=700, style="", em=None):
    g, dash = arabic_parts(text, wght, 120, 3.6, em is None)
    b = g.bounds
    pad = 6
    if em:
        height = (b[3] - b[1] + 2 * pad) * em / 120
    vb = (b[0] - pad, b[1] - pad, b[2] - b[0] + 2 * pad, b[3] - b[1] + 2 * pad)
    ww = height * vb[2] / vb[3]
    return S._svg(g, dash, vb, f"width:{ww:.1f}px;height:{height}px;{style}", color, mode, thread)


if __name__ == "__main__":
    html = "<body style='margin:0;background:#E5E0DA;padding:40px'>"
    html += arabic_svg(height=260, mode='thread') + "<br>" + arabic_svg(height=130) + arabic_svg(AR_NAME, height=130, mode='solid')
    html += "<br>" + S.wordmark_svg("tailored", height=150, mode='thread') + S.mark_svg(size=150, mode='thread')
    open("_proof2.html", "w", encoding="utf8").write(html)






