from ds import *
import stitch as S
import arabic as A
import stitch_defs as D

LOW1 = "abcdefghijklm"
LOW2 = "nopqrstuvwxyz"
NUMS = "0123456789"


def st(text, cap, color=INK, mode='knock', track=14, thread=THREAD):
    """stitched Latin text; cap = px height of ascender zone"""
    ymax = 140 if any(c in text for c in 'gjpqy,') else 100
    return S.wordmark_svg(text, color, cap * (ymax + 12) / 100, track, mode, thread)


def art(text, em, color=INK, mode='knock', thread=THREAD):
    return A.arabic_svg(text, color, 100, mode, thread, 700, "", em)


def skeleton(ch, sc=3.2):
    p, ds_ = S.glyph_geom(ch)
    g = D.G[ch]
    b = (-12, -12, g['w'] + 24, 164)
    paths = ''.join(f'<path d="{d}" fill="none" stroke="{THREAD}" stroke-width="1.1" stroke-dasharray="2.5 2"/>' for d in g['p'])
    lines = ''.join(f'<path d="M-12,{y}H{g["w"]+12}" stroke="{INK}" stroke-width=".5" stroke-dasharray="1.5 1.5" opacity=".5"/>' for y in (0, 40, 100, 140))
    return (f'<svg width="{b[2]*sc:.0f}" height="{b[3]*sc:.0f}" viewBox="{b[0]} {b[1]} {b[2]} {b[3]}">{lines}'
            f'<path d="{S.poly_d(p)}" fill="{INK}" opacity=".16" fill-rule="evenodd"/>'
            f'<path d="{S.poly_d(p)}" fill="none" stroke="{INK}" stroke-width=".9"/>{paths}</svg>')


def pages():
    P = []

    # 1 OVERVIEW -------------------------------------------------------------------------------
    cols = [
        ("01 &middot; Display", "Tailored Stitch", "Custom lettering. Wordmark, numerals, big statements. Latin + Arabic.", st("cut", 66, INK, 'thread'), "stitch"),
        ("02 &middot; Voice", "Fraunces &middot; Amiri", "Headlines and editorial copy. Warm, soft-serif, a human hand.", '<div class="h1" style="font-size:78px;line-height:1">Fit<em>.</em></div>', "serif"),
        ("03 &middot; Workhorse", "IBM Plex Sans &middot; Plex Sans Arabic", "Interface and body text. Clear in both scripts.", '<div style="font:500 62px/1 Plex;letter-spacing:-.02em">Aa <span class="ar" style="font-size:54px">&#1571;&#1576;</span></div>', "sans"),
        ("04 &middot; Measure", "IBM Plex Mono", "Scores, prices, labels, rulers. Everything that is a number.", '<div class="mono" style="font-size:56px;font-weight:500">87.5</div>', "mono"),
    ]
    cc = ''.join(f'''<div class="card f1 col g16" style="height:560px;{'background:var(--ink);color:var(--chalk)' if i==0 else ''}"><div class="lab" style="opacity:.7">{a}</div>
        <div style="height:150px;display:flex;align-items:center">{d}</div><div class="stitch" style="opacity:.5"></div>
        <div class="h3">{b}</div><div class="body">{c}</div></div>''' for i, (a, b, c, d, _) in enumerate(cols))
    cc = cc.replace('stroke="#1A1412"', 'stroke="#1A1412"')
    P.append(page("04 Typography", "", f'''
      <div class="eyebrow">Typography &middot; The system</div>
      <div class="h1" style="max-width:1200px">One custom voice, three <em>workhorses.</em></div>
      <div class="row g16" style="margin-top:32px">{cc}</div>
    '''))

    # 2 TAILORED STITCH ----------------------------------------------------------------------------
    P.append(page("04 Typography", "", f'''
      <div class="abs lab" style="left:96px;top:70px;color:var(--chalk);opacity:.7">Typography &middot; 01 Tailored Stitch</div>
      <div class="abs" style="left:96px;top:140px">{st(LOW1, 150, CHALK, 'thread')}</div>
      <div class="abs" style="left:96px;top:380px">{st(LOW2, 150, CHALK, 'thread')}</div>
      <div class="abs" style="left:96px;top:620px">{st(NUMS + ".,:!-+/", 100, CHALK, 'thread')}</div>
      <div class="abs lab" style="right:96px;top:70px;color:var(--chalk);opacity:.7">Latin &middot; lower-case &middot; numerals &middot; 8 punctuation</div>
    ''', "dark"))

    # 3 STITCH ANATOMY ------------------------------------------------------------------------------------
    P.append(page("04 Typography", "", f'''
      <div class="eyebrow">Typography &middot; Tailored Stitch &middot; Anatomy</div>
      <div class="row g32">
        <div style="width:480px"><div class="h1">Drawn, not<br><em>chosen.</em></div>
          <div class="body" style="margin-top:22px">Every glyph is one monoline stroke. That makes the stitch mathematically exact: a running stitch is laid along the centre-line of each letter, so it follows curves, joins and ends without ever colliding.</div>
          <table style="margin-top:26px">
            <tr><td class="mono">Stroke</td><td>16 units</td></tr><tr><td class="mono">x-height</td><td>60 units</td></tr><tr><td class="mono">Ascender</td><td>100 units</td></tr>
            <tr><td class="mono">Bowl radius</td><td>23 units, true circle</td></tr><tr><td class="mono">Tracking</td><td>14 units (default)</td></tr>
            <tr><td class="mono">Stitch</td><td>4.6 on / 4.0 off, 2.2 wide</td></tr><tr><td class="mono">Terminals</td><td>Flat, square. No serifs.</td></tr></table></div>
        <div class="f1 row g16 ae jc" style="padding-top:8px">
          <div class="col ac g8">{skeleton('a',1.9)}<div class="lab">a</div></div>
          <div class="col ac g8">{skeleton('e',1.9)}<div class="lab">e</div></div>
          <div class="col ac g8">{skeleton('g',1.9)}<div class="lab">g</div></div>
          <div class="col ac g8">{skeleton('k',1.9)}<div class="lab">k</div></div>
          <div class="col ac g8">{skeleton('8',1.9)}<div class="lab">8</div></div>
        </div></div>
      <div class="abs row g16" style="left:96px;right:96px;bottom:66px">
        <div class="f1 sm"><span class="mono" style="color:var(--thread)">- - -</span> centre-line, where the stitch sits</div>
        <div class="f1 sm"><span class="mono">&mdash;</span> body outline from true geometry</div>
        <div class="f1 sm"><span class="mono" style="opacity:.5">&middot;&middot;&middot;</span> ascender, x-height, baseline, descender</div></div>
    '''))

    # 4 STITCH MODES + USE ------------------------------------------------------------------------------------
    def mtile(mode, bg, fg, label, thread=THREAD):
        return f'<div class="col g12 f1"><div style="background:{bg};height:230px;display:flex;align-items:center;justify-content:center">{st("cut to fit", 66, fg, mode, 14, thread)}</div><div class="lab">{label}</div></div>'
    P.append(page("04 Typography", "", f'''
      <div class="eyebrow">Typography &middot; Tailored Stitch &middot; Modes</div>
      <div class="h1">Three settings: <em>thread,</em> knock-out, solid.</div>
      <div class="row g16" style="margin-top:36px">{mtile('thread', PAPER, INK, "Thread &middot; hero use, &ge; 56 px cap-height")}{mtile('knock', INK, CHALK, "Knock-out &middot; mono, any background, &ge; 40 px", INK)}{mtile('solid', THREAD, INK, "Solid &middot; small sizes, &lt; 40 px")}</div>
      <div class="row g32" style="margin-top:36px">
        <div class="f1 col g12"><div class="lab">Where it appears</div><div class="stitch"></div><ul class="b body"><li>The wordmark and short statements</li><li>Big numbers: fit scores, prices, counts</li><li>Section openers (&le; 4 words, lower-case)</li><li>Social covers and campaign lines</li></ul></div>
        <div class="f1 col g12"><div class="lab">Where it never appears</div><div class="stitch"></div><ul class="b body"><li>Paragraphs, buttons, form labels, nav</li><li>Anything under 28 px cap-height</li><li>Upper-case (the face has no capitals)</li><li>Tight tracking: never below 10 units</li></ul></div>
        <div class="f1 card col g8 jc ac" style="height:230px"><div class="lab thin">Big number</div>{st("87", 110, INK, 'thread')}<div class="mono thin" style="font-size:13px">fit score &middot; display numeral</div></div>
      </div>
    '''))

    # 5 ARABIC DISPLAY -----------------------------------------------------------------------------------------------
    words = ["\u0623\u0628\u062c\u062f \u0647\u0648\u0632", "\u062d\u0637\u064a \u0643\u0644\u0645\u0646", "\u0633\u0639\u0641\u0635 \u0642\u0631\u0634\u062a", "\u062b\u062e\u0630 \u0636\u0638\u063a"]
    P.append(page("04 Typography", "", f'''
      <div class="eyebrow">Typography &middot; Tailored Stitch Arabic</div>
      <div class="row g32"><div style="width:520px"><div class="h1">Kufi, re-cut<br>by the <em>same rules.</em></div>
        <div class="body" style="margin-top:22px">Arabic display text uses Reem Kufi Bold, processed with the same pipeline as the Latin: dots become notches, a topstitch runs inside each stroke. The result is a display face that is <i>native</i> to both scripts, not a Latin face with Arabic bolted on.</div>
        <ul class="b body" style="margin-top:20px"><li>Statements of &le; 5 words only</li><li>Never letter-spaced; never italic</li><li>Body Arabic always in Plex Sans Arabic</li></ul></div>
        <div class="f1 card col g24 ac jc" style="height:640px;padding:40px">
          {art(words[0], 150, INK, 'thread')}{art(words[1], 150, INK, 'thread')}
          <div class="stitch" style="width:100%;opacity:.3"></div>
          {art(words[2], 110, INK, 'knock')}{art(words[3], 110, INK, 'knock')}</div></div>
    '''))

    # 6 ARABIC PHRASES -----------------------------------------------------------------------------------------------------
    ph = ["\u0639\u0644\u0649 \u0645\u0642\u0627\u0633\u0643", "\u062a\u0648\u0627\u0641\u0642 87", "\u0627\u0628\u062f\u0623 \u0645\u062c\u0627\u0646\u0627\u064b"]
    P.append(page("04 Typography", "", f'''
      <div class="abs lab" style="left:96px;top:70px;opacity:.8">Typography &middot; Tailored Stitch &middot; In use</div>
      <div class="abs" style="left:96px;top:150px">{st("cut to fit.", 170, INK, 'knock', 14, INK)}</div>
      <div class="abs" style="right:96px;top:520px">{art(ph[0], 190, INK, 'knock')}</div>
      <div class="abs row g32" style="left:96px;bottom:90px">{''.join(f'<div class="col g8"><div>{st(t, 52, INK, "knock", 14, INK)}</div></div>' for t in ["87 fit", "49 egp", "2 credits"])}</div>
    ''', "thread"))

    # 7 FRAUNCES ---------------------------------------------------------------------------------------------------------------------
    wts = ''.join(f'<div class="row ac g24" style="border-bottom:1.5px solid rgba(26,20,18,.15);padding:6px 0"><div class="mono" style="width:70px;font-size:13px">{w}</div><div style="font-family:Fraunces;font-weight:{w};font-size:40px;font-variation-settings:\'SOFT\' 100,\'opsz\' 96">Measure once, cut right.</div></div>' for w in (300, 400, 500, 600, 700, 800))
    P.append(page("04 Typography", "", f'''
      <div class="eyebrow">Typography &middot; 02 Fraunces &middot; Amiri &mdash; the voice</div>
      <div class="row g48"><div style="width:560px">
        <div class="display" style="font-size:200px;line-height:.9">Aa<em style="font-size:200px">g</em></div>
        <div class="body" style="margin-top:12px">Fraunces is an &ldquo;old-style soft-serif&rdquo; with a variable <b>SOFT</b> and <b>WONK</b> axis. We run it at <span class="mono">SOFT 100</span>, optical size on auto, with WONK on italics only: warm, a little eccentric, and nothing like a typical tech sans.</div>
        <div class="stitch" style="margin:20px 0"></div>
        <div class="row g24 ac"><div class="amiri" style="font-size:64px;font-weight:700;line-height:1">&#1571;&#1576;&#1580;&#1583;</div><div class="sm">Amiri is the Arabic partner for editorial headlines and quotes. Classic Naskh warmth to match Fraunces.</div></div></div>
        <div class="f1 col" style="padding-top:20px">{wts}<div class="row g24 ac" style="padding:12px 0"><div class="mono" style="width:70px;font-size:13px">Italic</div><div class="it" style="font-size:44px">made to <em style="font-size:44px">fit.</em></div></div>
        <div class="sm thin" style="margin-top:12px">Use: H1&ndash;H3, pull-quotes, editorial emphasis. Never for UI controls or data.</div></div></div>
    '''))

    # 8 PLEX SANS + ARABIC ---------------------------------------------------------------------------------------------------------------
    P.append(page("04 Typography", "", f'''
      <div class="eyebrow">Typography &middot; 03 IBM Plex Sans &amp; Plex Sans Arabic &mdash; the workhorse</div>
      <div class="row g48"><div class="f1 col g16">
        <div style="font:500 150px/.95 Plex;letter-spacing:-.04em">Aa</div>
        <div class="row g24" style="font-size:22px"><span style="font-weight:300">Light 300</span><span style="font-weight:400">Regular 400</span><span style="font-weight:500">Medium 500</span><span style="font-weight:600">Semibold 600</span></div>
        <div class="stitch"></div>
        <div class="body">Plex is engineered, rational and slightly mechanical: a good home for UI. Its character set is wide and its Arabic sibling, designed by the same foundry, is metrically harmonised so both scripts sit on one line without hacks.</div>
        <div style="font:400 17px/1.55 Plex;max-width:640px" class="thin">ABCDEFGHIJKLMNOPQRSTUVWXYZ<br>abcdefghijklmnopqrstuvwxyz<br>0123456789 &amp; @ # % + &minus; &times; &rarr; &#10003;</div></div>
        <div class="f1 col g16 ar" style="text-align:right">
        <div style="font:600 150px/1.2 PlexAr">&#1571;&#1576;</div>
        <div class="row g24" style="font-size:24px;direction:rtl"><span style="font-weight:400">&#1593;&#1575;&#1583;&#1610; 400</span><span style="font-weight:500">&#1605;&#1578;&#1608;&#1587;&#1591; 500</span><span style="font-weight:600">&#1593;&#1585;&#1610;&#1590; 600</span><span style="font-weight:700">&#1587;&#1608;&#1583;&#1575;&#1569; 700</span></div>
        <div class="stitch"></div>
        <div style="font:400 22px/1.8 PlexAr">&#1585;&#1587;&#1575;&#1604;&#1577; &#1575;&#1604;&#1578;&#1602;&#1583;&#1610;&#1605; &#1578;&#1608;&#1590;&#1581; &#1604;&#1603; &#1605;&#1575; &#1578;&#1594;&#1610;&#1617;&#1585; &#1601;&#1610; &#1587;&#1610;&#1585;&#1578;&#1603; &#1575;&#1604;&#1584;&#1575;&#1578;&#1610;&#1577; &#1576;&#1575;&#1604;&#1590;&#1576;&#1591;&#1548; &#1608;&#1604;&#1605;&#1575;&#1584;&#1575;. &#1604;&#1575; &#1606;&#1590;&#1610;&#1601; &#1588;&#1610;&#1574;&#1575;&#1611; &#1604;&#1610;&#1587; &#1601;&#1610;&#1603;.</div>
        <div style="font:400 17px/1.8 PlexAr" class="thin">&#1575;&#1576;&#1578;&#1579;&#1580;&#1581;&#1582;&#1583;&#1584;&#1585;&#1586;&#1587;&#1588;&#1589;&#1590;&#1591;&#1592;&#1593;&#1594;&#1601;&#1602;&#1603;&#1604;&#1605;&#1606;&#1607;&#1608;&#1610;<br>0123456789</div></div></div>
    '''))

    # 9 PLEX MONO --------------------------------------------------------------------------------------------------------------------------
    rows = [("Core stack", "30", 92), ("Proof of work", "20", 78), ("Seniority", "10", 85), ("Experience", "10", 70), ("Domain", "10", 64), ("Persona track", "5", 90), ("Education", "5", 100), ("Work mode", "5", 50), ("Language", "5", 95)]
    tbl = ''.join(f'<tr><td class="mono" style="width:240px">{a}</td><td class="mono thin" style="width:70px">w {b}%</td><td style="width:340px"><div style="display:flex;align-items:center;gap:12px"><div style="flex:1;position:relative;height:14px">{ruler(300,10,INK,labels=False,unit_px=6,opacity=.4)}<div class="abs" style="left:0;top:0;height:10px;width:{c*3}px;background:var(--thread);opacity:.9"></div></div></div></td><td class="mono" style="text-align:right;font-weight:500">{c}</td></tr>' for a, b, c in rows)
    P.append(page("04 Typography", "", f'''
      <div class="eyebrow">Typography &middot; 04 IBM Plex Mono &mdash; the measure</div>
      <div class="row g48"><div style="width:620px"><div class="mono" style="font-size:190px;line-height:.9;font-weight:500;letter-spacing:-.04em">87.5</div>
        <div class="body" style="margin-top:20px">Anything measured is set in Mono: fit scores, credits, prices, labels, dates, table headers, rulers. Tabular figures align, and the typewriter rhythm echoes the tick marks of a tape.</div>
        <ul class="b body" style="margin-top:18px"><li>Tracking +4 % at body, +14 % in uppercase labels</li><li>Western digits 0&ndash;9 in both languages</li><li>Never for sentences longer than a line</li></ul></div>
        <div class="f1 card"><div class="lab thin" style="margin-bottom:10px">Nine pillars &middot; example breakdown</div><table>{tbl}</table></div></div>
    '''))

    # 10 TYPE SCALE ---------------------------------------------------------------------------------------------------------------------------
    scale = [("Display", "Fraunces 560 / Stitch", "96 / 92%", "-2.5%", "Hero, campaign", "display", 56),
             ("H1", "Fraunces 540", "64 / 100%", "-2%", "Page title", "h1", 48), ("H2", "Fraunces 540", "40 / 108%", "-1.5%", "Section title", "h2", 36), ("H3", "Fraunces 560", "26 / 115%", "-1%", "Card title", "h3", 26),
             ("Lead", "Plex 400", "22 / 140%", "0", "Intro paragraph", "lead", 22), ("Body", "Plex 400", "17 / 150%", "0", "Paragraph, UI", "body", 19),
             ("Small", "Plex 400", "14 / 150%", "0", "Captions, helper", "sm", 16), ("Label", "Mono 500 caps", "12 / 120%", "+14%", "Eyebrows, tags", "lab", 13)]
    tr = ''.join(f'<tr><td style="width:120px"><span class="lab">{a}</span></td><td style="width:520px"><div class="{c}" style="font-size:{s}px;line-height:1.1;white-space:nowrap;overflow:hidden">{"Cut to fit." if c in ("display","h1","h2","h3") else ("Measure once, cut right." if c not in ("lab",) else "FIT SCORE")}</div></td><td class="mono sm">{b}</td><td class="mono sm">{d}</td><td class="mono sm">{e}</td><td class="sm">{f}</td></tr>' for a, b, d, e, f, c, s in scale)
    P.append(page("04 Typography", "", f'''
      <div class="eyebrow">Typography &middot; Scale &middot; Latin</div><div class="h1" style="font-size:52px">A scale with a <em>1.5 ratio</em> at the top, 1.2 at the bottom.</div>
      <table style="margin-top:20px"><tr><th>Level</th><th>Specimen (px values are web, desktop)</th><th>Face</th><th>Size / LH</th><th>Tracking</th><th>Use</th></tr>{tr}</table>
    '''))

    # 11 ARABIC SCALE ----------------------------------------------------------------------------------------------------------------------------
    sc2 = [("Display", "Kufi stitch", "&times;1.10", "&#1593;&#1604;&#1609; &#1605;&#1602;&#1575;&#1587;&#1603;", 56), ("H1", "Plex Arabic 700", "&times;1.10", "&#1604;&#1603;&#1604; &#1608;&#1592;&#1610;&#1601;&#1577; &#1605;&#1602;&#1575;&#1587;", 44),
           ("H2", "Plex Arabic 600", "&times;1.10", "&#1575;&#1582;&#1578;&#1585; &#1608;&#1592;&#1610;&#1601;&#1578;&#1603; &#1575;&#1604;&#1578;&#1575;&#1604;&#1610;&#1577;", 34), ("Body", "Plex Arabic 400", "LH 170%", "&#1604;&#1605; &#1606;&#1590;&#1610;&#1601; &#1588;&#1610;&#1574;&#1575;&#1611; &#1604;&#1610;&#1587; &#1601;&#1610;&#1603; &#1593;&#1604;&#1609; &#1575;&#1604;&#1573;&#1591;&#1604;&#1575;&#1602;.", 22), ("Label", "Plex Arabic 500", "no caps", "&#1575;&#1604;&#1578;&#1608;&#1575;&#1601;&#1602;", 16)]
    tr2 = ''.join(f'<tr><td style="width:120px"><span class="lab">{a}</span></td><td class="ar f1" style="font-size:{s}px;line-height:1.5;text-align:right;font-weight:{600 if a!="Body" and a!="Label" else 400};{"font-family:Kufi" if a=="Display" else ""}">{t}</td><td class="mono sm" style="width:180px">{b}</td><td class="mono sm" style="width:130px">{c}</td></tr>' for a, b, c, t, s in sc2)
    P.append(page("04 Typography", "", f'''
      <div class="eyebrow">Typography &middot; Scale &middot; Arabic</div><div class="h1" style="font-size:52px">Arabic is set <em>larger,</em> looser and upright.</div>
      <div class="row g32" style="margin-top:20px"><div class="f1"><table dir="rtl"><tr><th class="ar">&#1575;&#1604;&#1605;&#1587;&#1578;&#1608;&#1609;</th><th></th><th></th><th></th></tr>{tr2}</table></div>
        <div style="width:440px" class="col g16"><div class="lab">Rules</div><div class="stitch"></div>
          <ul class="b body" style="font-size:18px"><li>+10 % size, +15&ndash;20 % line-height versus Latin.</li><li>No letter-spacing, no italics, no capitals.</li><li>Emphasis = weight 700 or a thread stitch underline, never slant.</li><li>Western digits by default; Eastern digits only in editorial.</li><li>Kufi stitch display for &le; 5 words; everything else Plex Arabic or Amiri.</li></ul></div></div>
    '''))

    # 12 BILINGUAL ------------------------------------------------------------------------------------------------------------------------------------
    def card_en():
        return f'''<div class="card col g12" style="height:460px;width:640px"><div class="lab thin">Radar</div><div class="h2">Senior Backend Engineer</div><div class="sm thin">Fawry &middot; Cairo &middot; Hybrid</div><div class="row g16 ac" style="margin:10px 0">{fit_dial(87,110)}<div class="body">Strong fit. Missing: <b>Kafka</b>. Add one project bullet.</div></div><div class="stitch"></div><div class="row g12"><span class="chip">Tailor CV</span><span class="chip" style="border-color:transparent;background:var(--ink);color:var(--chalk)">Dispatch</span></div></div>'''

    def card_ar():
        return f'''<div class="card col g12 ar" style="height:460px;width:640px"><div class="lab thin" style="font-family:PlexAr;letter-spacing:0;font-size:14px;text-transform:none">&#1575;&#1604;&#1585;&#1575;&#1583;&#1575;&#1585;</div><div style="font:600 34px/1.35 PlexAr">&#1605;&#1607;&#1606;&#1583;&#1587; &#1576;&#1575;&#1603; &#1573;&#1606;&#1583; &#1571;&#1608;&#1604;</div><div class="sm thin" style="font-family:PlexAr">&#1601;&#1608;&#1585;&#1610; &middot; &#1575;&#1604;&#1602;&#1575;&#1607;&#1585;&#1577; &middot; &#1607;&#1580;&#1610;&#1606;</div><div class="row g16 ac" style="margin:10px 0">{fit_dial(87,110)}<div style="font:400 20px/1.7 PlexAr">&#1578;&#1608;&#1575;&#1601;&#1602; &#1602;&#1608;&#1610;. &#1575;&#1604;&#1606;&#1575;&#1602;&#1589;: <b>Kafka</b>. &#1571;&#1590;&#1601; &#1606;&#1602;&#1591;&#1577; &#1605;&#1588;&#1585;&#1608;&#1593; &#1608;&#1575;&#1581;&#1583;&#1577;.</div></div><div class="stitch"></div><div class="row g12"><span class="chip" style="font-family:PlexAr;letter-spacing:0;text-transform:none;font-size:15px">&#1601;&#1589;&#1617;&#1604; &#1575;&#1604;&#1587;&#1610;&#1585;&#1577;</span><span class="chip" style="border-color:transparent;background:var(--ink);color:var(--chalk);font-family:PlexAr;letter-spacing:0;text-transform:none;font-size:15px">&#1573;&#1585;&#1587;&#1575;&#1604;</span></div></div>'''
    P.append(page("04 Typography", "", f'''
      <div class="eyebrow">Typography &middot; Bilingual setting</div><div class="h1" style="max-width:1200px">Two scripts, <em>one grid,</em> mirrored with care.</div>
      <div class="row g24 jb" style="margin-top:32px">{card_en()}{card_ar()}</div>
      <div class="row g32" style="margin-top:28px"><div class="f1 sm">&bull; Layout mirrors, <b>content does not</b>: numbers, Latin product names (Kafka) and the fit dial keep their direction.</div><div class="f1 sm">&bull; Arabic baseline sits <b>2 px lower</b> than Latin in the same row; Plex pairs align naturally.</div><div class="f1 sm">&bull; Mono labels are Latin only; Arabic labels use Plex Arabic 500 with no tracking.</div></div>
    '''))

    # 13 DEVICES ------------------------------------------------------------------------------------------------------------------------------------------------------
    P.append(page("04 Typography", "", f'''
      <div class="eyebrow">Typography &middot; Typographic devices</div><div class="h1">Small habits that make it <em>ours.</em></div>
      <div class="row g16" style="margin-top:34px">
        <div class="card f1 col g16" style="height:520px"><div class="lab">01 Stitch underline</div><div class="h2" style="margin-top:20px">Every change is <span style="background:linear-gradient(90deg,var(--thread) 0 9px,transparent 9px 15px) 0 100%/15px 4px repeat-x;padding-bottom:8px">visible.</span></div><div class="sm thin" style="margin-top:auto">Emphasis in Latin and Arabic. 4 px dashed thread, 9 on / 6 off, 8 px below baseline.</div></div>
        <div class="card f1 col g16" style="height:520px"><div class="lab">02 Measure ticks</div><div style="margin-top:20px">{ruler(380,28,INK,start=0,step=1,unit_px=9,label_every=10)}</div><div class="mono" style="font-size:30px;margin-top:10px">12.5 cm</div><div class="sm thin" style="margin-top:auto">Captions, dividers and progress sit on a ruler. Labels in Plex Mono, ticks every 8-10 px.</div></div>
        <div class="card f1 col g16" style="height:520px"><div class="lab">03 Notch bullets</div><ul class="b body" style="margin-top:20px"><li>Measure the candidate</li><li>Cut the job pattern</li><li>Stitch the edits</li><li>Send with confidence</li></ul><div class="sm thin" style="margin-top:auto">Lists use a 11&times;8 notch pointing down. In RTL the notch sits on the right.</div></div>
        <div class="card f1 col g16" style="height:520px"><div class="lab">04 Pattern labels</div><div class="mono" style="margin-top:20px;font-size:14px;line-height:2;border:1.5px dashed var(--ink);padding:14px">FRONT &middot; CUT 2X<br>GRAIN &uarr;<br>SIZE: M &middot; 87 FIT</div><div class="sm thin" style="margin-top:auto">Metadata set like pattern markings: Mono, uppercase, +14 % tracking, dashed frame.</div></div>
      </div>
    '''))

    # 14 DON'TS -----------------------------------------------------------------------------------------------------------------------------------------------------------------
    dn = [("Do not set paragraphs in Stitch", f'<div style="opacity:.9">{st("measure once cut right", 30, INK, "solid")}</div>'),
          ("Do not use all-caps Stitch or invent capitals", '<div class="display" style="font-size:44px;font-weight:300;letter-spacing:.2em;font-family:Plex">TAILORED</div>'),
          ("Do not italicise or letter-space Arabic", '<div class="ar" style="font-size:44px;font-style:italic;letter-spacing:.3em;font-family:PlexAr">&#1593;&#1604;&#1609; &#1605;&#1602;&#1575;&#1587;&#1603;</div>'),
          ("Do not fake bold or stretch", '<div class="h2" style="transform:scaleX(1.5);transform-origin:left;-webkit-text-stroke:1.5px var(--ink)">Cut to fit.</div>'),
          ("Do not mix more than 3 families in one block", '<div class="col"><span class="h3">Fraunces</span><span style="font-family:Amiri;font-size:26px">Amiri</span><span class="mono" style="font-size:22px">Mono</span><span style="font-family:Kufi;font-size:22px">Kufi</span><span style="font-family:Georgia;font-size:22px">Georgia</span></div>'),
          ("Do not substitute system fonts", '<div style="font:34px Arial">Tailored. Made to measure.</div>')]
    P.append(page("04 Typography", "", f'''
      <div class="eyebrow">Typography &middot; Misuse</div><div class="h1">Six <em>frayed</em> edges.</div>
      <div class="row g16 wrap" style="margin-top:34px">{''.join(f'<div class="col g8" style="width:calc(33.3% - 11px)"><div style="position:relative;height:200px;background:var(--paper);display:flex;align-items:center;padding:0 30px;overflow:hidden">{c}<div class="abs" style="right:10px;top:8px;width:30px;height:30px;background:var(--alarm);color:#fff;font:700 20px/30px Plex;text-align:center">&times;</div></div><div class="sm">{t}</div></div>' for t, c in dn)}</div>
    '''))

    # 15 IMPLEMENTATION ---------------------------------------------------------------------------------------------------------------------------------------------------------------------
    P.append(page("04 Typography", "", f'''
      <div class="eyebrow">Typography &middot; Implementation</div><div class="h1">Open fonts, <em>cheap</em> to ship.</div>
      <div class="row g32" style="margin-top:28px">
        <div class="f1"><table><tr><th>Family</th><th>Role</th><th>Licence</th></tr>
        <tr><td>Tailored Stitch (custom)</td><td>Display, wordmark</td><td>Proprietary, SVG lettering</td></tr>
        <tr><td>Reem Kufi (modified)</td><td>Arabic display source</td><td>SIL OFL 1.1</td></tr>
        <tr><td>Fraunces</td><td>Headlines</td><td>SIL OFL 1.1</td></tr>
        <tr><td>Amiri</td><td>Arabic editorial</td><td>SIL OFL 1.1</td></tr>
        <tr><td>IBM Plex Sans / Arabic / Mono</td><td>UI, body, data</td><td>SIL OFL 1.1</td></tr></table>
        <div class="card" style="margin-top:22px"><div class="lab thin">Roadmap</div><div class="sm" style="margin-top:6px">Tailored Stitch ships today as vector lettering and a build script. Commissioning a full OpenType font (caps, kerning, Arabic joining) is recommended once the identity is approved.</div></div></div>
        <div class="f1" style="background:var(--ink);color:var(--chalk);padding:26px 30px;border-radius:6px;font:14px/1.7 Mono;white-space:pre">:root {{
  --font-voice: 'Fraunces', 'Amiri', Georgia, serif;
  --font-ui:    'IBM Plex Sans', 'IBM Plex Sans Arabic',
                system-ui, sans-serif;
  --font-mono:  'IBM Plex Mono', ui-monospace, monospace;
  --font-kufi:  'Reem Kufi', 'IBM Plex Sans Arabic', sans-serif;
}}
h1,h2,h3 {{ font-family: var(--font-voice);
  font-variation-settings: 'SOFT' 100, 'WONK' 0; }}
h1 em {{ font-variation-settings: 'SOFT' 100, 'WONK' 1; }}
[dir=rtl] body {{ font-size: 1.1em; line-height: 1.7;
  letter-spacing: 0; }}
.num, .label {{ font-family: var(--font-mono);
  font-feature-settings: 'tnum'; }}</div></div>
    '''))
    return P

