"""Arabic SVG engine using HarfBuzz shaping + fonttools outlines.
Dots are detected and replaced with notch triangles.
AR_NAME = تفصيل  (Tafseel — the Arabic name for Tailored)
"""
import math, pathlib
import uharfbuzz as hb
from fonttools.pens.svgPathPen import SVGPathPen
from fonttools.ttLib import TTFont

FONT_PATH = pathlib.Path(__file__).parent.parent / "fonts" / "ReemKufi-pinned-700.ttf"
# Fallback to ReemKufi.ttf if pinned not found
if not FONT_PATH.exists():
    FONT_PATH = pathlib.Path(__file__).parent.parent / "fonts" / "ReemKufi.ttf"

AR_NAME = "تفصيل"   # Tafseel

H = 1000.0  # fixed UPM reference for dot detection


def _load_font():
    with open(FONT_PATH, "rb") as f:
        data = f.read()
    face = hb.Face(data)
    font = hb.Font(face)
    tt = TTFont(str(FONT_PATH))
    return font, tt, data


def shaped_contours(text, font, tt, data, weight=700):
    """Shape Arabic text and return list[glyph][contour][point (x,y)]."""
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    buf.direction = hb.Direction.RTL
    buf.script = hb.Script.ARABIC

    face = hb.Face(data)
    hb_font = hb.Font(face)
    hb.shape(hb_font, buf)

    infos = buf.glyph_infos
    positions = buf.glyph_positions

    glyf = tt["glyf"]
    cmap = tt.getBestCmap()
    glyph_set = tt.getGlyphSet()
    glyph_order = tt.getGlyphOrder()

    result = []  # list[glyph] -> list[contour] -> list[(x,y)]
    x_cursor = 0
    for info, pos in zip(infos, positions):
        gid = info.codepoint
        gname = glyph_order[gid] if gid < len(glyph_order) else ".notdef"

        pen = SVGPathPen(glyph_set)
        try:
            glyph_set[gname].draw(pen)
        except Exception:
            result.append([])
            x_cursor += pos.x_advance
            continue

        d = pen.getCommands()
        # Parse SVG path into contours
        contours = []
        current = []
        import re
        tokens = re.findall(r'[MmLlCcQqZz]|[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?', d)
        i = 0
        cx_off = x_cursor + pos.x_offset
        cy_off = pos.y_offset
        cx_pt, cy_pt = 0.0, 0.0
        while i < len(tokens):
            cmd = tokens[i]; i += 1
            if cmd == 'M':
                if current:
                    contours.append(current)
                    current = []
                cx_pt = float(tokens[i]) + cx_off; cy_pt = float(tokens[i+1]) + cy_off; i += 2
                current.append((cx_pt, cy_pt))
            elif cmd == 'L':
                cx_pt = float(tokens[i]) + cx_off; cy_pt = float(tokens[i+1]) + cy_off; i += 2
                current.append((cx_pt, cy_pt))
            elif cmd in ('C', 'c'):
                # Cubic bezier — just take endpoint
                for _ in range(2): i += 2  # skip control points
                cx_pt = float(tokens[i]) + cx_off; cy_pt = float(tokens[i+1]) + cy_off; i += 2
                current.append((cx_pt, cy_pt))
            elif cmd in ('Q', 'q'):
                i += 2  # skip control point
                cx_pt = float(tokens[i]) + cx_off; cy_pt = float(tokens[i+1]) + cy_off; i += 2
                current.append((cx_pt, cy_pt))
            elif cmd == 'Z':
                if current:
                    contours.append(current)
                    current = []
        if current:
            contours.append(current)

        result.append(contours)
        x_cursor += pos.x_advance

    return result, x_cursor


def _is_dot(contour, total_w):
    """Return True if a contour is a small dot (should become a notch)."""
    if len(contour) < 3:
        return False
    xs = [p[0] for p in contour]
    ys = [p[1] for p in contour]
    w = max(xs) - min(xs)
    h_ = max(ys) - min(ys)
    area = abs(w * h_)
    dim = max(w, h_)
    return dim < 0.13 * H and area < 0.02 * H * H


def _notch_svg(cx, cy, size, color, flip=False):
    """Downward or upward triangle notch."""
    if not flip:
        pts = f"{cx-size/2},{cy} {cx+size/2},{cy} {cx},{cy+size}"
    else:
        pts = f"{cx-size/2},{cy+size} {cx+size/2},{cy+size} {cx},{cy}"
    return f'<polygon points="{pts}" fill="{color}"/>'


def arabic_parts(text, color, height, mode='knock', thread='#FF4A1C', weight=700):
    """Return (outline_svg_parts, notch_svg_parts, total_width, scale)."""
    try:
        font, tt, data = _load_font()
    except Exception as e:
        # font not available yet
        return [], [], 300, 1.0

    contours_per_glyph, raw_w = shaped_contours(text, font, tt, data, weight)

    # Find UPM and scale
    upem = tt["head"].unitsPerEm
    scale = height / upem

    outline_parts = []
    notch_parts = []

    for glyph_contours in contours_per_glyph:
        for contour in glyph_contours:
            if len(contour) < 3:
                continue
            if _is_dot(contour, H):
                # Replace dot with notch
                xs = [p[0] for p in contour]
                ys = [p[1] for p in contour]
                cx = (min(xs) + max(xs)) / 2 * scale
                cy = (min(ys) + max(ys)) / 2 * scale
                notch_parts.append(_notch_svg(cx, cy, 60 * scale, thread))
            else:
                scaled = [(x * scale, y * scale) for x, y in contour]
                d = "M" + " L".join(f"{x:.2f},{y:.2f}" for x, y in scaled) + " Z"
                outline_parts.append(f'<path d="{d}" fill="{color}" fill-rule="evenodd"/>')

    total_w = raw_w * scale
    return outline_parts, notch_parts, total_w, scale


def arabic_svg(text, color, height, mode='knock', thread='#FF4A1C', weight=700, style=""):
    """Full Arabic wordmark SVG."""
    outlines, notches, total_w, scale = arabic_parts(text, color, height, mode, thread, weight)
    if not outlines and not notches:
        # Fallback: render text with Kufi font if outlines unavailable
        return (f'<svg width="{total_w:.0f}" height="{height:.0f}" style="{style}">'
                f'<text y="{height*0.85:.0f}" font-family="Kufi" font-size="{height}px" '
                f'fill="{color}" direction="rtl">{text}</text></svg>')

    h_svg = height * 1.2
    stitch_col = "transparent" if mode == 'knock' else thread
    return (f'<svg width="{total_w:.1f}" height="{h_svg:.1f}" '
            f'viewBox="0 0 {total_w:.1f} {h_svg:.1f}" style="{style}">'
            + "".join(outlines)
            + "".join(notches)
            + '</svg>')
