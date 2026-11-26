from ds import *
import stitch as S
import arabic as A
from shapely.geometry import Polygon
MONO_AR = '\u200d\u062a\u200d'

TAG_EN = "Cut to fit."


def mono_tile(content, bg, fg, w=None, h=300, label=None, extra=""):
    st = f"background:{bg};color:{fg};height:{h}px;" + (f"width:{w}px;" if w else "flex:1;")
    lb = f'<div class="abs lab" style="left:14px;bottom:10px;opacity:.7;color:{fg}">{label}</div>' if label else ''
    return f'<div style="{st}position:relative;display:flex;align-items:center;justify-content:center;{extra}">{content}{lb}</div>'


def pages():
    P = []
    ARM = A.arabic_svg(AR, INK, 300, 'thread')

    # NAME -----------------------------------------------------------------------------
    P.append(page("02 Identity", "", f'''
      <div class="row" style="gap:72px;height:100%">
        <div class="col" style="width:640px"><div class="eyebrow">Identity &middot; The name</div>
          <div class="h1">One name,<br>two <em>languages,</em><br>one meaning.</div>
          <div class="body" style="margin-top:26px"><b>Tailored</b> &mdash; adjective: made to measure. It is also the verb we perform on every CV and cover letter.</div>
          <div class="body" style="margin-top:16px"><b class="ar" style="font-size:26px">&#1578;&#1601;&#1589;&#1610;&#1604;</b> <span class="mono" style="font-size:15px">(tafs&#299;l, say <i>taf-SEEL</i>)</span> &mdash; in Egyptian and Gulf Arabic, <i>tafs&#299;l</i> is exactly what a tailor does: cutting cloth to your measure. It also means <i>detail</i>. A name that says <em>precision</em> and <em>craft</em> in a single word, with no translation loss.</div>
          <div class="stitch" style="margin:26px 0"></div>
          <div class="sm thin">Rule: the Arabic name is not a transliteration of &ldquo;Tailored&rdquo;. It is the same idea, native to the reader. Both are always written in the brand lettering, never typed in a font.</div></div>
        <div class="f1 col jc ac g32" style="background:var(--paper);border-radius:6px;position:relative">
          <div class="abs lab" style="left:20px;top:16px;opacity:.6">English &middot; Latin</div>
          <div style="margin-top:20px">{wm(INK,170,'thread')}</div>
          <div class="stitch" style="width:70%;opacity:.35"></div>
          <div>{arwm(INK,190,'thread')}</div>
          <div class="abs lab" style="left:20px;bottom:16px;opacity:.6">Arabic</div>
        </div></div>
    '''))

    # HERO LOGO ------------------------------------------------------------------------------
    P.append(page("02 Identity", "", f'''
      <div class="abs" style="left:96px;top:90px"><div class="eyebrow">Identity &middot; The logo</div></div>
      <div class="abs" style="left:0;right:0;top:0;bottom:0;display:flex;align-items:center;justify-content:center;padding-bottom:30px">{lockup_h(INK, 320, 'thread')}</div>
      <div class="abs row jb" style="left:96px;right:96px;bottom:90px"><div class="lab">Primary lockup &middot; stitch in thread red</div><div class="lab">The notched T + Tailored Stitch wordmark</div></div>
    ''', "paper"))

    # LOGO EXPLAINED ------------------------------------------------------------------------------
    big = mk(INK, 440, 'thread')
    P.append(page("02 Identity", "", f'''
      <div class="eyebrow">Identity &middot; The logo explained</div>
      <div class="h1" style="max-width:1100px">A pattern piece, a notch, <em>a thread.</em></div>
      <div class="abs" style="left:96px;top:250px">{big}
         <div class="abs lab" style="left:455px;top:36px;white-space:nowrap">A &mdash; The notch</div>
         <div class="abs lab" style="left:455px;top:118px;white-space:nowrap">B &mdash; The T</div>
         <div class="abs lab" style="left:455px;top:348px;white-space:nowrap">C &mdash; The stitch</div>
         <div class="abs" style="left:230px;top:48px;width:220px;border-top:2px solid var(--ink)"></div>
         <div class="abs" style="left:413px;top:130px;width:37px;border-top:2px solid var(--ink)"></div>
         <div class="abs" style="left:273px;top:360px;width:177px;border-top:2px solid var(--ink)"></div>
      </div>
      <div class="abs col g24" style="left:760px;top:230px;width:740px">
        <div class="row g24 as"><div class="mono" style="font-size:22px;color:var(--thread);width:36px">A</div><div><div class="h3">The notch</div><div class="body" style="margin-top:6px">Tailors cut tiny triangles into the edge of every pattern piece so two pieces meet exactly where they should. Our notch is the match: your CV meeting the job. It is also the brand&rsquo;s pointer, bullet, and cursor.</div></div></div>
        <div class="row g24 as"><div class="mono" style="font-size:22px;color:var(--thread);width:36px">B</div><div><div class="h3">The T</div><div class="body" style="margin-top:6px">A cross-bar like the shoulders of a garment on a single measured stem. Heavy, stable, symmetric: it reads as a hanger, a pattern piece, and the initial of the name. Sharp corners, no rounding.</div></div></div>
        <div class="row g24 as"><div class="mono" style="font-size:22px;color:var(--thread);width:36px">C</div><div><div class="h3">The stitch</div><div class="body" style="margin-top:6px">A topstitch runs inside the edge in thread red. It is the &ldquo;we never invent a thread&rdquo; promise: every change is visible and sewn on. At small sizes the stitch drops out and the shape stands alone.</div></div></div>
        <div class="stitch"></div>
        <div class="body"><b>In Arabic,</b> the dots of &#1578;&#1601;&#1589;&#1610;&#1604; are re-cut as notches, so both scripts carry the same signature.</div>
      </div>
    ''', "light"))

    # MARK CONSTRUCTION ----------------------------------------------------------------------------
    sc = 6.2
    grid = ''.join(f'<path d="M{i*10*sc},0V{100*sc}M0,{i*10*sc}H{100*sc}" stroke="{INK}" stroke-width="1" opacity=".13"/>' for i in range(11))
    ps = ' '.join(f'{x*sc},{y*sc}' for x, y in S.MARK_PTS)
    dim = lambda x1, y1, x2, y2: f'<path d="M{x1*sc},{y1*sc}L{x2*sc},{y2*sc}" stroke="{THREAD}" stroke-width="2"/>'
    ann = (f'<polygon points="{ps}" fill="{INK}" opacity=".08"/><polygon points="{ps}" fill="none" stroke="{INK}" stroke-width="2.2"/>'
           f'<path d="M{6*sc},{10*sc}H{94*sc}M{6*sc},{38*sc}H{94*sc}M{38*sc},{10*sc}V{94*sc}M{62*sc},{10*sc}V{94*sc}M{50*sc},{10*sc}V{94*sc}" stroke="{THREAD}" stroke-width="1.5" stroke-dasharray="6 5"/>'
           f'<circle cx="{50*sc}" cy="{18*sc}" r="6" fill="{THREAD}"/><circle cx="{44*sc}" cy="{10*sc}" r="5" fill="{INK}"/><circle cx="{56*sc}" cy="{10*sc}" r="5" fill="{INK}"/>')
    P.append(page("02 Identity", "", f'''
      <div class="row g48">
        <div style="width:560px"><div class="eyebrow">Identity &middot; Construction</div><div class="h1">Built on a<br><em>100-unit</em> grid.</div>
        <table style="margin-top:30px">
          <tr><td class="mono">Bar</td><td>88 &times; 28 units</td></tr>
          <tr><td class="mono">Stem</td><td>24 units wide, to y = 94</td></tr>
          <tr><td class="mono">Notch</td><td>12 wide, 8 deep, centred</td></tr>
          <tr><td class="mono">Stitch</td><td>5 inset &middot; 6 on / 4.6 off &middot; 2.6 weight</td></tr>
          <tr><td class="mono">Corners</td><td>Square by default. One 26px &ldquo;armhole&rdquo; curve per object, top-right (top-left in Arabic).</td></tr>
        </table>
        <div class="sm thin" style="margin-top:24px">Never redraw the mark by hand. Use the supplied vector files; stitch cadence is calculated to close evenly around the outline.</div></div>
        <div class="f1 row jc" style="padding-top:10px"><div style="position:relative;width:{100*sc}px;height:{100*sc}px;background:var(--paper)"><svg width="{100*sc}" height="{100*sc}" viewBox="0 0 {100*sc} {100*sc}" style="position:absolute;inset:0">{grid}{ann}</svg>{mk(INK,100*sc,'thread',THREAD,'position:absolute;inset:0;opacity:.0')}</div></div>
      </div>
    '''))

    # WORDMARK ----------------------------------------------------------------------------------------
    d, w, ymax = S.word_d("tailored", 14, True) if False else (None, None, None)
    body, dash, ww, ym = S.word_geom("tailored", 14)
    sc2 = 1.7
    pad = 6
    guides = [(0, "ascender"), (40, "x-height"), (100, "baseline")]
    gl = ''.join(f'<path d="M-20,{y}H{ww+20}" stroke="{THREAD}" stroke-width=".7" stroke-dasharray="3 2"/><text x="{ww+24}" y="{y+2}" font-family="Mono" font-size="5" fill="{INK}">{n}</text>' for y, n in guides)
    wsvg = (f'<svg width="{(ww+160)*sc2*3.2/3.2:.0f}" height="{(ym+40)*sc2:.0f}" viewBox="-20 -20 {ww+110} {ym+40}" style="overflow:visible">{gl}'
            f'<path d="{S.poly_d(body.difference(dash))}" fill="{INK}" fill-rule="evenodd"/>'
            f'<path d="M0,112H16" stroke="{INK}"/></svg>')
    P.append(page("02 Identity", "", f'''
      <div class="eyebrow">Identity &middot; The wordmark</div>
      <div class="h1">Lower-case, built from <em>straight lines</em><br>and true circles.</div>
      <div class="abs" style="left:96px;top:330px">{wsvg}</div>
      <div class="abs row g48" style="left:96px;right:96px;bottom:90px">
        <div class="f1 body"><b>Custom letterforms.</b> Eight letters drawn from one stroke (16 units) on a 60-unit x-height: bowls are perfect circles of 23-unit radius, stems are verticals. No font was used.</div>
        <div class="f1 body"><b>The i-dot is the notch.</b> The only ornament in the word. It echoes the mark and ties the letters to the pattern-piece system.</div>
        <div class="f1 body"><b>Centre-line stitch.</b> A running stitch (4.6 on, 4.0 off) is knocked out along every stroke&rsquo;s centre-line, or sewn in thread red on the primary version.</div></div>
    '''))

    # ARABIC WORDMARK ---------------------------------------------------------------------------------------
    mono_t = A.arabic_svg(MONO_AR, INK, 280, 'thread')
    P.append(page("02 Identity", "", f'''
      <div class="eyebrow">Identity &middot; The Arabic wordmark</div>
      <div class="row g48"><div style="width:600px"><div class="h1">Kufi, re-cut to<br>share <em>one signature.</em></div>
        <div class="body" style="margin-top:26px">The Arabic name is set in a geometric Kufi (Reem Kufi Bold) and then hand-modified: every dot becomes a triangular notch, pointing down above the letters and up below. The same topstitch runs inside every stroke.</div>
        <ul class="b body" style="margin-top:22px"><li>Reads <i>tafs&#299;l</i> right to left. Never letter-space or break the joins.</li><li>Dots are always notches. Never round dots in the logo.</li><li>Optical weight is matched to the Latin wordmark, not the stroke width.</li></ul></div>
        <div class="f1 col g24"><div class="card col ac jc" style="height:340px">{A.arabic_svg(AR, INK, 280, 'thread')}</div>
          <div class="row g24"><div class="card f1 col ac jc g16" style="height:220px">{mono_t.replace('height:280px','height:130px').replace('width:','width:')}<div class="lab thin">Arabic monogram &middot; &#1578;</div></div>
          <div class="card f1 col ac jc g16" style="height:220px;background:var(--ink)">{A.arabic_svg(AR, CHALK, 100, 'knock')}<div class="lab" style="color:var(--chalk);opacity:.7">Knock-out version</div></div></div></div></div>
    '''))

    # LOCKUPS EN ------------------------------------------------------------------------------------------------
    P.append(page("02 Identity", "", f'''
      <div class="row jb ae"><div><div class="eyebrow">Identity &middot; Lockups &middot; English</div><div class="h1">Six ways to <em>sign.</em></div></div>
      <div class="sm thin" style="max-width:420px;text-align:right">Pick the first lockup that fits. Horizontal is the default; stacked for square spaces; symbol only when the name is already present.</div></div>
      <div class="row g16" style="margin-top:30px">
        {mono_tile(lockup_h(INK,90,'thread'), PAPER, INK, h=300, label="01 Horizontal &middot; primary")}
        {mono_tile(lockup_stack(INK,140,'thread'), PAPER, INK, h=300, label="02 Stacked")}
        {mono_tile(wm(INK,100,'thread'), PAPER, INK, h=300, label="03 Wordmark")}
      </div>
      <div class="row g16" style="margin-top:16px">
        {mono_tile(mk(INK,170,'thread'), PAPER, INK, h=300, label="04 Symbol")}
        {mono_tile(f'<div class="col ac g16">{lockup_h(CHALK,64,"thread")}<div class="lab" style="color:var(--chalk);letter-spacing:.3em">{TAG_EN.upper()}</div></div>', INK, CHALK, h=300, label="05 With tagline")}
        {mono_tile(f'<div class="row ac g24">{mk(INK,90,"solid")}<div style="width:2px;height:70px;background:var(--ink)"></div><div class="h2" style="font-size:36px">Brand book<br><span class="lab">v1.0</span></div></div>', THREAD, INK, h=300, label="06 Endorsement &middot; sub-brand")}
      </div>
    '''))

    # LOCKUPS AR + BI ------------------------------------------------------------------------------------------------
    P.append(page("02 Identity", "", f'''
      <div class="row jb ae"><div><div class="eyebrow">Identity &middot; Lockups &middot; Arabic &amp; bilingual</div><div class="h1">&#1593;&#1585;&#1576;&#1610; <em>first,</em> not mirrored.</div></div>
      <div class="sm thin" style="max-width:480px;text-align:right">In Arabic layouts the symbol sits on the right and leads. The Arabic wordmark is drawn, not typed: use the supplied artwork. Bilingual lockup separates the two names with a stitch-weight vertical.</div></div>
      <div class="row g16" style="margin-top:30px">
        {mono_tile(lockup_ar_h(INK,96,'thread'), PAPER, INK, h=290, label="07 Arabic horizontal")}
        {mono_tile(lockup_ar_stack(INK,130,'thread'), PAPER, INK, h=290, label="08 Arabic stacked")}
        {mono_tile(arwm(INK,130,'thread'), PAPER, INK, h=290, label="09 Arabic wordmark")}
      </div>
      <div class="row g16" style="margin-top:16px">
        {mono_tile(lockup_bi(INK,90,'thread'), PAPER, INK, h=330, label="10 Bilingual horizontal &middot; Gulf and regional use")}
        {mono_tile(f'<div class="col ac g16">{lockup_ar_h(CHALK,60,"thread")}<div class="lab" style="color:var(--chalk);letter-spacing:.2em">&#1593;&#1604;&#1609; &#1605;&#1602;&#1575;&#1587;&#1603;</div></div>', INK, CHALK, h=330, label="11 Arabic + tagline")}
        {mono_tile(f'<div class="col ac g24">{mk(INK,110,"thread")}<div class="col ac g8">{wm(INK,46,"thread")}<div style="width:120px;height:3px;background:var(--ink)"></div>{arwm(INK,44,"thread")}</div></div>', KRAFT, INK, h=330, label="12 Bilingual stacked")}
      </div>
    '''))

    # COLOUR VERSIONS ---------------------------------------------------------------------------------------------------
    def ver(bg, fg, mode, th, label):
        return mono_tile(lockup_h(fg, 66, mode, th), bg, fg, h=250, label=label)
    P.append(page("02 Identity", "", f'''
      <div class="eyebrow">Identity &middot; Colour versions</div>
      <div class="h1">One logo, <em>eight</em> approved dresses.</div>
      <div class="row g12" style="margin-top:32px">{ver(PAPER, INK, 'thread', THREAD, '01 Primary: ink + thread')}{ver(INK, CHALK, 'thread', THREAD, '02 Reversed: chalk + thread')}{ver(THREAD, INK, 'knock', INK, '03 On thread: ink knock-out')}{ver(KRAFT, INK, 'thread', THREAD, '04 On kraft')}</div>
      <div class="row g12" style="margin-top:12px">{ver(CHALK, INK, 'knock', INK, '05 One-colour ink')}{ver(INK, CHALK, 'knock', INK, '06 One-colour chalk')}{ver(DYE, CHALK, 'thread', THREAD, '07 On dye blue')}{ver(MIST, INK, 'thread', THREAD, '08 On mist')}</div>
      <div class="sm thin" style="margin-top:20px">Thread stitch only appears on chalk, paper, kraft, mist, ink and dye. On thread red the stitch is knocked out. Never place the red stitch on any other colour.</div>
    '''))

    # RESPONSIVE LADDER --------------------------------------------------------------------------------------------------
    sizes = [(120, 'thread', "&ge; 96 px"), (64, 'thread', "48 px"), (40, 'knock', "32 px"), (28, 'solid', "24 px"), (20, 'solid', "16 px")]
    P.append(page("02 Identity", "", f'''
      <div class="eyebrow">Identity &middot; Responsive logo</div>
      <div class="h1">The stitch is a <em>luxury</em> of size.</div>
      <div class="body" style="margin-top:20px;max-width:900px">Below 48&nbsp;px the stitch fights the edge. We drop it in three steps so the mark stays crisp from billboard to browser tab.</div>
      <div class="row g16 ae" style="margin-top:50px">
        {''.join(f'<div class="card col g16 ac jc" style="width:300px;height:360px">{mk(INK,s,m,THREAD)}<div class="lab thin">{lbl}</div><div class="sm">{["Full: thread stitch","Full: thread stitch","Knock-out stitch","Solid, no stitch","Solid, no stitch"][i]}</div></div>' for i,(s,m,lbl) in enumerate([(sizes[0][0],sizes[0][1],"96 px +"),(sizes[1][0],sizes[1][1],"64 px"),(sizes[2][0],sizes[2][1],"40 px"),(sizes[3][0],sizes[3][1],"28 px"),(sizes[4][0],sizes[4][1],"16 px favicon")]))}
      </div>
    '''))

    # CLEAR SPACE + MINIMUM ------------------------------------------------------------------------------------------------
    h = 130
    cs = h * .28
    P.append(page("02 Identity", "", f'''
      <div class="row g48">
        <div style="width:500px"><div class="eyebrow">Identity &middot; Clear space &amp; size</div><div class="h1">Give it <em>room</em> to breathe.</div>
          <div class="body" style="margin-top:22px">Clear space <b>C</b> equals the height of the T&rsquo;s cross-bar (28 % of the mark). Keep every edge of the lockup at least <b>C</b> from text, images or the page edge. Use <b>2C</b> on covers.</div>
          <div class="stitch" style="margin:28px 0"></div>
          <table><tr><th>Asset</th><th>Print</th><th>Screen</th></tr>
          <tr><td>Horizontal lockup</td><td>24 mm</td><td>96 px wide</td></tr>
          <tr><td>Stacked lockup</td><td>18 mm</td><td>64 px</td></tr>
          <tr><td>Symbol</td><td>6 mm</td><td>16 px</td></tr>
          <tr><td>Arabic wordmark</td><td>18 mm</td><td>40 px high</td></tr></table></div>
        <div class="f1 col jc ac"><div style="position:relative;padding:{cs}px;border:2px dashed var(--thread);background:var(--paper)">
          <div style="position:absolute;left:0;top:0;width:{cs}px;height:{cs}px;background:rgba(255,74,28,.18)"></div>
          <div style="position:absolute;right:0;bottom:0;width:{cs}px;height:{cs}px;background:rgba(255,74,28,.18)"></div>
          <div style="position:absolute;left:{cs/2-4}px;top:{cs/2-8}px" class="mono"><span style="font-size:13px;color:var(--thread);font-weight:500">C</span></div>
          {lockup_h(INK, h, 'thread')}</div></div></div>
    '''))

    # MISUSE ------------------------------------------------------------------------------------------------------------------
    bad_css = '<style>.outl path{fill:none!important;stroke:#1A1412;stroke-width:1.2}</style><svg width="0" height="0"><defs><linearGradient id="badGrad" x1="0" x2="1"><stop offset="0" stop-color="#7B2FFF"/><stop offset="1" stop-color="#18C5FF"/></linearGradient></defs></svg>'
    tiles = [
        ("Do not stretch or squash", f'<div style="transform:scaleX(1.6) scaleY(.8)">{lockup_h(INK,70,"thread")}</div>'),
        ("Do not rotate", f'<div style="transform:rotate(-14deg)">{lockup_h(INK,70,"thread")}</div>'),
        ("Do not use gradients", lockup_h("url(#badGrad)", 70, 'solid')),
        ("Do not add shadows or glow", f'<div style="filter:drop-shadow(8px 10px 6px rgba(0,0,0,.5))">{lockup_h(INK,70,"thread")}</div>'),
        ("Do not outline", f'<div class="outl">{lockup_h(INK,70,"solid")}</div>'),
        ("Do not recolour off-palette", f'<div>{lockup_h("#2B7BFF",70,"thread","#00D38F")}</div>'),
        ("Do not rearrange", f'<div class="col g8 ac" style="direction:ltr">{wm(INK,50,"thread")}<div style="align-self:flex-end">{mk(INK,60,"thread")}</div></div>'),
        ("Do not place on busy imagery", f'<div style="position:absolute;inset:0;opacity:1">{swatch_pat("selvedge",360,200,INK,CHALK)}</div><div style="position:relative">{lockup_h(INK,70,"thread")}</div>'),
    ]
    tt = ''.join(f'<div class="col g8" style="width:calc(25% - 12px)"><div style="position:relative;height:200px;background:var(--paper);display:flex;align-items:center;justify-content:center;overflow:hidden">{c}<div class="abs" style="right:10px;top:8px;width:30px;height:30px;background:var(--alarm);color:#fff;font:700 20px/30px Plex;text-align:center">&times;</div></div><div class="sm">{t}</div></div>' for t, c in tiles)
    P.append(page("02 Identity", "", f'''{bad_css}
      <div class="eyebrow">Identity &middot; Misuse</div><div class="h1">Eight ways to <em>unpick</em> the work.</div>
      <div class="row g16 wrap" style="margin-top:34px">{tt}</div>
    '''))

    # APP ICON + AVATARS ----------------------------------------------------------------------------------------------------------
    def appicon(bg, fg, size, radius, content=None, th=THREAD):
        c = content if content else mk(fg, size * .62, 'thread' if size > 90 else 'solid', th)
        return f'<div style="width:{size}px;height:{size}px;background:{bg};border-radius:{radius}px;display:flex;align-items:center;justify-content:center;{"box-shadow:0 14px 28px -10px rgba(0,0,0,.4)" if size>90 else ""}">{c}</div>'
    P.append(page("02 Identity", "", f'''
      <div class="eyebrow">Identity &middot; Icons &amp; avatars</div><div class="h1">Small, <em>sharp,</em> recognisable.</div>
      <div class="row g32 ae" style="margin-top:40px">
        <div class="col g12 ac">{appicon(INK, CHALK, 220, 48)}<div class="lab">App icon &middot; ink</div></div>
        <div class="col g12 ac">{appicon(THREAD, INK, 220, 48, mk(INK,136,'knock'))}<div class="lab">App icon &middot; thread</div></div>
        <div class="col g12 ac">{appicon(CHALK, INK, 220, 48, mk(INK,136,'thread'))}<div class="lab">App icon &middot; chalk</div></div>
        <div class="col g12 ac">{appicon(INK, CHALK, 220, 48, A.arabic_svg(MONO_AR, CHALK, 140, 'thread'))}<div class="lab">Arabic app icon &middot; &#1578;</div></div>
        <div class="col g16"><div class="row g16 ae">{appicon(INK, CHALK, 96, 22)}{appicon(INK, CHALK, 64, 15)}{appicon(INK, CHALK, 44, 10)}{appicon(INK, CHALK, 32, 7)}</div><div class="lab">Scaling &middot; stitch drops &lt; 90 px</div></div>
      </div>
      <div class="row g32 ae" style="margin-top:46px">
        <div class="col g12 ac"><div style="width:140px;height:140px;border-radius:50%;background:{INK};display:flex;align-items:center;justify-content:center">{mk(CHALK,80,'thread')}</div><div class="lab">Avatar &middot; round</div></div>
        <div class="col g12 ac"><div style="width:140px;height:140px;background:{THREAD};display:flex;align-items:center;justify-content:center">{mk(INK,80,'knock')}</div><div class="lab">Avatar &middot; square</div></div>
        <div class="col g12 ac"><div style="display:flex;align-items:center;gap:12px;padding:12px 18px;background:#fff;border:1px solid #ccc;border-radius:8px 8px 0 0;width:280px">{mk(INK,18,'solid')}<span style="font:13px Plex">Tailored &middot; Radar</span><span style="margin-left:auto">&times;</span></div><div class="lab">Favicon &middot; 16 px</div></div>
        <div class="col g12 ac"><div class="row g12">{mk(INK,48,'solid')}{mk(THREAD,48,'solid')}{mk(DYE,48,'solid')}</div><div class="lab">Solid symbol for UI</div></div>
      </div>
    '''))

    return P



