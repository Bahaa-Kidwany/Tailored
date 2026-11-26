"""Chapter 05 - Graphic language (stitch, notch, armhole curve, patterns, icons)"""
import ds
from ds import *

S = "05 Graphic language"


def tile(inner, bg=PAPER, fg=INK, label="", h=300, extra="", arm=True):
    return (f'<div class="f1 col" style="background:{bg};color:{fg};height:{h}px;position:relative;overflow:hidden;'
            f'{"border-radius:0 26px 0 0;" if arm else ""}{extra}">{inner}'
            f'<div class="abs lab" style="left:20px;bottom:14px;opacity:.7">{label}</div></div>')


def pages():
    P = []

    # 01 intro ---------------------------------------------------------------
    body = f'''
      <div class="eyebrow">Graphic language &middot; Overview</div>
      <div class="h1" style="margin-bottom:34px">Stitch, notch, <em>curve.</em></div>
      <div class="row g24" style="height:470px">
        <div class="f1 card col jb"><div>{mk(INK, 120, 'thread')}</div>
          <div><div class="h3">The stitch</div><div class="sm" style="margin-top:8px">A dashed run of thread. It joins things, underlines things and marks the seam. Always THREAD on light and dark grounds.</div></div></div>
        <div class="f1 card col jb"><div style="padding-top:20px"><svg width="120" height="100" viewBox="0 0 120 100"><path d="M10,10H110L60,90Z" fill="{THREAD}"/></svg></div>
          <div><div class="h3">The notch</div><div class="sm" style="margin-top:8px">The small V cut a tailor makes to line two pieces up. Our bullet, our marker, our brand signature.</div></div></div>
        <div class="f1 card col jb"><div>{fcurve(250, INK, THREAD)}</div>
          <div><div class="h3">The curve</div><div class="sm" style="margin-top:8px">The French curve and the armhole. The one soft, moving gesture in a system of straight cuts. New in version 1.2.</div></div></div>
      </div>
      <div class="abs sm" style="left:96px;right:96px;bottom:46px;opacity:.75">Everything is cut straight except the one place the body moves. That is the whole shape rule.</div>'''
    P.append(page(S, "", body, "light"))

    # 02 armhole rule --------------------------------------------------------
    def obj(radius, label, ok=True, bg=PAPER, w=300, h=190):
        col = GREEN if ok else ALARM
        mark = "&#10003;" if ok else "&#10005;"
        return (f'<div class="col g12"><div style="width:{w}px;height:{h}px;background:{bg};border:2px solid {INK};border-radius:{radius};'
                f'display:flex;align-items:flex-end;padding:18px"><span class="lab">{label}</span></div>'
                f'<div class="lab" style="color:{col}">{mark} {"Do" if ok else "Do not"}</div></div>')
    body = f'''
      <div class="eyebrow">Graphic language &middot; Shape rule</div>
      <div class="row jb" style="gap:60px">
        <div style="width:420px"><div class="h1">One curve <em>per object.</em></div>
          <div class="lead" style="margin-top:22px">Cards, panels, buttons and images are square. Exactly one corner carries a soft armhole curve. It gives the page a lean, a direction, a little life.</div>
          <ul class="b body" style="margin-top:26px"><li>Radius 26px for panels, 12px for buttons, 44px for hero images</li><li>Top-right in English, top-left in Arabic</li><li>Never two curves on the same side</li></ul></div>
        <div class="col g32 f1">
          <div class="row g24">{obj('0 26px 0 0', 'Panel', True)}{obj('0 12px 0 12px', 'Button, diagonal', True, THREAD, 300, 190)}{obj('0 0 0 0', 'Hard rule exception', True, INK)}</div>
          <div class="row g24">{obj('24px', 'All corners round', False)}{obj('99px', 'Pill', False)}{obj('26px 26px 0 0', 'Two curves', False)}</div>
        </div></div>'''
    P.append(page(S, "", body, "paper"))

    # 03 french curve + sweep ------------------------------------------------
    body = f'''
      <div class="abs" style="left:0;top:-170px;opacity:.9">{sweep(1600, 520, THREAD, 5, 4, 18)}</div>
      <div class="eyebrow" style="position:relative;color:var(--chalk)">Graphic language &middot; Curve motif</div>
      <div class="h1" style="position:relative;color:var(--chalk)">The French curve.</div>
      <div class="abs" style="right:110px;top:190px;transform:rotate(-6deg)">{fcurve(620, CHALK, THREAD, sw=3)}</div>
      <div class="abs" style="left:96px;bottom:110px;width:560px;color:var(--chalk)">
        <div class="lead">The template tailors use to draw necklines and armholes becomes our motion line: covers, section openers, empty states and loading arcs.</div>
        <div class="sm" style="margin-top:14px;opacity:.7">Use one or two sweeps per layout. Three to four parallel strokes only on covers. Always THREAD on INK, INK on CHALK.</div></div>'''
    P.append(page(S, "", body, "dark"))

    # 04 patterns ------------------------------------------------------------
    pats = [('seam', 'Seam grid', CHALK, INK, .5), ('notch', 'Notch field', INK, CHALK, .22), ('tape', 'Tape', PAPER, INK, .45),
            ('selvedge', 'Selvedge', KRAFT, INK, 1), ('cross', 'Cross stitch', DYE, CHALK, .35), ('seam', 'Seam on thread', THREAD, INK, .5)]
    cells = ''.join(f'<div style="width:458px;height:236px;position:relative;border-radius:0 26px 0 0;overflow:hidden;background:{bg}">{swatch_pat(k, 458, 236, fg, bg, op)}<div class="abs lab" style="left:18px;bottom:14px;background:{bg};padding:4px 8px;color:{fg}">{lab}</div></div>' for k, lab, bg, fg, op in pats)
    body = f'''
      <div class="eyebrow">Graphic language &middot; Patterns</div>
      <div class="h1" style="margin-bottom:26px">Six cloths, <em>one weave.</em></div>
      <div class="row wrap" style="gap:16px">{cells}</div></div>'''
    P.append(page(S, "", body, "light"))

    # 05 pattern pieces / lay plan ------------------------------------------
    lp = layplan(1408, 560, seed=21, stroke=INK, accent=THREAD, fills=['none', 'none', KRAFT, MIST], scale_range=(.8, 1.6), margin=12, labels=False)
    body = f'''
      <div class="eyebrow">Graphic language &middot; Pattern pieces</div>
      <div class="row jb ac" style="margin-bottom:26px"><div class="h1">Cut from one <em>cloth.</em></div>
      <div class="sm" style="width:420px">Eight pattern pieces, auto-packed into a lay plan. Used for covers, empty states, walls and wrapping. Fills only from KRAFT, MIST or none.</div></div>
      <div style="background:{PAPER};border-radius:0 40px 0 0;padding:0;overflow:hidden">{lp}</div>'''
    P.append(page(S, "", body, "light"))

    # 06 icons ---------------------------------------------------------------
    names = list(ds.ICONS.keys())
    ic = ''.join(f'<div class="col ac g12" style="width:150px;height:150px;background:{PAPER};border-radius:0 18px 0 0;justify-content:center">{icon(n, 56)}<div class="lab">{n}</div></div>' for n in names)
    body = f'''
      <div class="eyebrow">Graphic language &middot; Icons</div>
      <div class="row jb" style="gap:50px"><div style="width:360px"><div class="h1">Icons with <em>a notch.</em></div>
        <div class="body" style="margin-top:22px">48px grid, 3.4px square-cap stroke, miter joins. One THREAD notch triangle marks the active point of each icon.</div></div>
        <div class="row wrap g16 f1" style="gap:16px">{ic}</div></div>'''
    P.append(page(S, "", body, "mist"))

    # 07 tape + chalk --------------------------------------------------------
    body = f'''
      <div class="eyebrow">Graphic language &middot; Tape &amp; chalk</div>
      <div class="h1" style="margin-bottom:34px">Numbers are <em>measurements.</em></div>
      <div class="row g24">
        <div class="f1 card" style="height:420px">{ruler(560, 70, INK, 0, 10, 10, 10)}
          <div style="margin-top:40px" class="row g32 ac">{fit_dial(87, 220)}{fit_dial(64, 220, INK, AMBER)}</div>
          <div class="sm" style="margin-top:20px">Scores, prices and progress are drawn as tape ticks, never as soft rings or gradients.</div></div>
        <div class="f1 col jc ac" style="height:420px;background:{DYE};border-radius:0 40px 0 0;position:relative;overflow:hidden">
          <svg width="520" height="320" viewBox="0 0 520 320">{chalk([(30,260),(160,90),(260,200),(360,60),(490,250)], CHALK, 4)}{chalk([(40,290),(480,290)], THREAD, 3, 1.4, 5)}</svg>
          <div class="abs lab" style="left:24px;bottom:16px;color:var(--chalk)">Chalk marks, on dye</div></div>
      </div>'''
    P.append(page(S, "", body, "light"))
    return P



