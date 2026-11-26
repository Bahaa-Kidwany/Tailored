"""Tailored Stitch - custom display letterforms + logo generators.
Coordinate system: baseline y=100, x-height top y=40, ascender/cap top y=0, descender y=140.
Stroke weight W=14. Every letter carries a knocked-out running stitch on its centreline.
"""
import itertools, math

W = 16
R = 23  # bowl radius (centreline)
_ids = itertools.count(1)


def circ(cx=30, cy=70, r=R):
    return f"M{cx-r},{cy} A{r},{r} 0 1 1 {cx+r},{cy} A{r},{r} 0 1 1 {cx-r},{cy} Z"


def ln(x1, y1, x2, y2, ext=0.0):
    """line, optionally extended both ends by fraction ext (for clipped diagonals)"""
    dx, dy = x2 - x1, y2 - y1
    return f"M{x1-dx*ext:.2f},{y1-dy*ext:.2f} L{x2+dx*ext:.2f},{y2+dy*ext:.2f}"


def v(x, y1, y2):
    return f"M{x},{y1} L{x},{y2}"


# glyph: dict(w=advance, p=[paths], clip=(ymin,ymax)|None, tri=[polygons], rot=bool)
G = {}
G['a'] = dict(w=60, p=["M53,66 A23,23 0 1 0 53,74", v(53, 40, 100)])
G['b'] = dict(w=60, p=[v(7, 0, 100), "M7,66 A23,23 0 1 1 7,74"])
G['c'] = dict(w=54, p=["M47.6,55.2 A23,23 0 1 0 47.6,84.8"])
G['d'] = dict(w=60, p=["M53,66 A23,23 0 1 0 53,74", v(53, 0, 100)])
G['e'] = dict(w=60, p=["M53,70 L7,70 A23,23 0 0 0 47.6,84.8", "M7,70 A23,23 0 0 1 53,70"])
G['f'] = dict(w=52, p=["M22,100 L22,25 A18,18 0 0 1 40,7 L52,7", "M2,47 L44,47"])
G['g'] = dict(w=60, p=["M53,66 A23,23 0 1 0 53,74", "M53,40 L53,110 A23,23 0 0 1 30,133 L12,133"])
G['h'] = dict(w=60, p=[v(7, 0, 100), "M7,70 A23,23 0 0 1 53,70 L53,100"])
G['i'] = dict(w=14, p=[v(7, 40, 100)], tri=[[(-4, 4), (18, 4), (7, 28)]])
G['j'] = dict(w=44, p=["M33,40 L33,110 A23,23 0 0 1 10,133 L-2,133"], tri=[[(22, 4), (44, 4), (33, 28)]])
G['k'] = dict(w=56, p=[v(7, 0, 100), "M54,40 L7,77", "M30,60 L62,110"], clip=(0, 100))
G['l'] = dict(w=14, p=[v(7, 0, 100)])
G['m'] = dict(w=82, p=[v(7, 40, 100), "M7,64 A17,17 0 0 1 41,64 L41,100", "M41,64 A17,17 0 0 1 75,64 L75,100"])
G['n'] = dict(w=60, p=[v(7, 40, 100), "M7,70 A23,23 0 0 1 53,70 L53,100"])
G['o'] = dict(w=60, p=[circ()])
G['p'] = dict(w=60, p=[v(7, 40, 140), "M7,66 A23,23 0 1 1 7,74"])
G['q'] = dict(w=60, p=[v(53, 40, 140), "M53,66 A23,23 0 1 0 53,74"])
G['r'] = dict(w=46, p=[v(7, 40, 100), "M7,70 A23,23 0 0 1 30,47 L46,47"])
G['s'] = dict(w=58, p=["M54,47 H21 A12,12 0 0 0 21,71 H39 A11,11 0 0 1 39,93 H4"])
G['t'] = dict(w=44, p=[v(22, 12, 100), "M0,47 L44,47"])
G['u'] = dict(w=60, p=["M7,40 L7,70 A23,23 0 0 0 53,70", v(53, 40, 100)])
G['v'] = dict(w=60, p=[ln(4, 40, 30, 100, .25), ln(56, 40, 30, 100, .25)], clip=(40, 100))
G['w'] = dict(w=90, p=[ln(3, 40, 24, 100, .25), ln(45, 40, 24, 100, .25), ln(45, 40, 66, 100, .25), ln(87, 40, 66, 100, .25)], clip=(40, 100))
G['x'] = dict(w=60, p=[ln(4, 40, 56, 100, .25), ln(56, 40, 4, 100, .25)], clip=(40, 100))
G['y'] = dict(w=60, p=[ln(4, 40, 30, 100, .25), "M64.5,25 L12.7,140 "], clip=(40, 140))
G['z'] = dict(w=60, p=[v(0, 0, 0) and "M4,47 L56,47", "M4,93 L56,93", ln(54, 47, 6, 93, .25)], clip=(40, 100))
# numerals (cap height 0..100)
G['0'] = dict(w=60, p=["M7,30 A23,23 0 0 1 53,30 L53,70 A23,23 0 0 1 7,70 Z"])
G['1'] = dict(w=50, p=[v(36, 0, 100), ln(6, 30, 36, 8)], clip=(0, 100))
G['2'] = dict(w=60, p=["M7,30 A23,23 0 0 1 53,30 L7,93", "M0,93 L60,93"])
G['3'] = dict(w=62, p=["M7,7 H33 A21,21 0 0 1 33,49 H20", "M33,49 A22,22 0 0 1 33,93 H7"])
G['4'] = dict(w=60, p=[ln(42, 0, 6, 68, .1), "M0,70 L60,70", v(42, 0, 100)], clip=(0, 100))
G['5'] = dict(w=58, p=["M53,7 H11 V50", "M11,50 H33 A21.5,21.5 0 0 1 33,93 H7"])
G['6'] = dict(w=60, p=["M7,66 A23,23 0 1 1 7,74", "M7,70 V30 A23,23 0 0 1 49,19"])
G['9'] = dict(w=60, p=["M7,66 A23,23 0 1 1 7,74", "M7,70 V30 A23,23 0 0 1 49,19"], rot=True)
G['7'] = dict(w=60, p=["M4,7 L56,7", ln(54, 7, 20, 100, .1)], clip=(0, 100))
G['8'] = dict(w=60, p=[circ(30, 26, 19), circ(30, 69, 24)])
G['.'] = dict(w=14, p=[v(7, 86, 100)])
G[','] = dict(w=14, p=[v(7, 86, 100), ln(7, 100, 0, 118)], clip=(0, 120))
G[':'] = dict(w=14, p=[v(7, 40, 54), v(7, 86, 100)])
G['!'] = dict(w=14, p=[v(7, 0, 66), v(7, 86, 100)])
G['-'] = dict(w=40, p=["M0,70 L40,70"])
G['+'] = dict(w=50, p=["M0,70 L50,70", v(25, 45, 95)])
G['/'] = dict(w=44, p=[ln(42, 0, 2, 100, .1)], clip=(0, 100))
G['→'] = dict(w=70, p=["M0,50 L66,50", "M44,26 L68,50 L44,74"])
G[' '] = dict(w=36, p=[])




