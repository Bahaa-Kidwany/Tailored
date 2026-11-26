"""Chapter 03 — Colour System  (p_system.py)"""
import ds

S = "03 — Colour System"

def _cc(cr):
    if cr >= 7: return "#1E8A5A"
    if cr >= 4.5: return "#E39A1B"
    return "#8F1D2C"

def pages():
    out = []

    # â”€â”€ 03.01  Colour Overview â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    swatches = [
        (ds.INK,    "INK",    "#1A1412", "Primary"),
        (ds.CHALK,  "CHALK",  "#E5E0DA", "Primary"),
        (ds.THREAD, "THREAD", "#E9453F", "Primary"),
        (ds.KRAFT,  "KRAFT",  "#CDAE88", "Extended"),
        (ds.DYE,    "DYE",    "#23325E", "Extended"),
        (ds.MIST,   "MIST",   "#C7D2DF", "Extended"),
        (ds.GREEN,  "GREEN",  "#1E8A5A", "Semantic"),
        (ds.AMBER,  "AMBER",  "#E39A1B", "Semantic"),
        (ds.ALARM,  "ALARM",  "#8F1D2C", "Semantic"),
        (ds.PAPER,  "PAPER",  "#F5F3EF", "Semantic"),
    ]
    items = ""
    for bg, name, hex_, role in swatches:
        fg = ds.CHALK if ds.lum(bg) < 0.18 else ds.INK
        items += (f'<div style="flex:1;min-width:120px;background:{bg};padding:22px 18px 16px;display:flex;flex-direction:column;justify-content:flex-end;min-height:200px">'
                  f'<div style="font:500 11px Mono;letter-spacing:.14em;text-transform:uppercase;color:{fg};opacity:.7;margin-bottom:4px">{role}</div>'
                  f'<div style="font:700 20px Plex;color:{fg};margin-bottom:2px">{name}</div>'
                  f'<div style="font:400 13px Mono;color:{fg};opacity:.8">{hex_}</div>'
                  f'</div>')
    body = (f'<div class="eyebrow">Colour System</div>'
            f'<div class="h1" style="margin-bottom:36px">Ten colours.<br>One palette.</div>'
            f'<div style="display:flex;gap:6px;margin-top:8px">{items}</div>')
    out.append(ds.page(S, "Overview", body, "dark"))

    # â”€â”€ 03.02  Primary Triad â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def big_swatch(bg, name, hex_, role_txt, fg, pct, notes):
        return (f'<div style="background:{bg};flex:{pct};padding:52px 44px;display:flex;flex-direction:column;justify-content:space-between;min-height:620px">'
                f'<div>'
                f'<div style="font:500 12px Mono;letter-spacing:.14em;text-transform:uppercase;color:{fg};opacity:.7;margin-bottom:12px">{role_txt}</div>'
                f'<div style="font:700 72px Plex;line-height:.9;color:{fg}">{name}</div>'
                f'<div style="font:400 20px Mono;color:{fg};opacity:.7;margin-top:10px">{hex_}</div>'
                f'</div>'
                f'<div style="font:400 16px Plex;line-height:1.5;color:{fg};opacity:.85;max-width:260px">{notes}</div>'
                f'</div>')
    row = (big_swatch(ds.INK, "INK", "#1A1412", "60% — Dominant", ds.CHALK, 3,
                      "The ground. Warm espresso-black, like ink on a tailor&rsquo;s bench. Used on all body text, borders, icons, and the logo mark.") +
           big_swatch(ds.CHALK, "CHALK", "#E5E0DA", "20% — Field", ds.INK, 2,
                      "The tailor&rsquo;s chalk. A warm greige that holds the page. The default slide and UI background.") +
           big_swatch(ds.THREAD, "THREAD", "#E9453F", "10% — Accent", ds.INK, 1,
                      "The red thread. A confident signal red that punctuates. Used for the logo notch, CTAs, and wayfinding only."))
    body = (f'<div class="eyebrow">Primary Triad</div>'
            f'<div style="display:flex;height:680px;gap:0;margin:-84px -96px -92px;overflow:hidden">{row}</div>')
    out.append(ds.page(S, "Primary Triad", body, "light"))

    # â”€â”€ 03.03  Extended Palette â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€─
    ext = [
        (ds.KRAFT, "KRAFT", "#CDAE88", ds.INK,
         "Camel cloth. A warm tan used for feature surfaces, pattern-piece illustrations and calm emphasis."),
        (ds.DYE, "DYE", "#23325E", ds.CHALK,
         "Indigo dye vat. Deep navy used sparingly for data callouts, the pipeline view, and bilingual header bands."),
        (ds.MIST, "MIST", "#C7D2DF", ds.INK,
         "Pre-dawn light. Pale blue for secondary chips, hover states on DYE surfaces, and form input backgrounds."),
    ]
    cards = ""
    for bg, name, hex_, fg, desc in ext:
        cards += (f'<div style="background:{bg};flex:1;padding:44px 40px;display:flex;flex-direction:column;justify-content:space-between">'
                  f'<div>'
                  f'<div style="font:700 48px Plex;color:{fg};line-height:.9">{name}</div>'
                  f'<div style="font:400 16px Mono;color:{fg};opacity:.7;margin-top:8px">{hex_}</div>'
                  f'</div>'
                  f'<div style="font:400 17px Plex;line-height:1.5;color:{fg};opacity:.85">{desc}</div>'
                  f'</div>')
    body = (f'<div class="eyebrow">Extended Palette</div>'
            f'<div class="h2" style="margin-bottom:40px">Drawn from the atelier floor.</div>'
            f'<div style="display:flex;gap:12px;height:460px">{cards}</div>'
            f'<div class="body thin" style="margin-top:28px">Extended colours complement but never compete with the primary triad. Use KRAFT and MIST as background variations; DYE for high-information-density views only.</div>')
    out.append(ds.page(S, "Extended Palette", body, "light"))

    # â”€â”€ 03.04  Semantic Colours â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€─
    sem = [
        (ds.GREEN, "STRONG FIT", "Strong match — fit score ≥ 75", "✓", "1E8A5A"),
        (ds.AMBER, "PARTIAL FIT", "Partial match — fit score 50–74", "~", "E39A1B"),
        (ds.ALARM, "LOW FIT",    "Low match — fit score < 50",      "!", "8F1D2C"),
        (ds.PAPER, "SURFACE",    "Page default — large reading areas", "◻", "F5F3EF"),
    ]
    cards2 = ""
    for bg, name, desc, sym, _h in sem:
        fg = ds.CHALK if ds.lum(bg) < 0.2 else ds.INK
        cards2 += (f'<div style="background:{bg};flex:1;padding:36px 32px;border-radius:0;display:flex;flex-direction:column;gap:20px">'
                   f'<div style="font:700 52px Mono;color:{fg};opacity:.35">{sym}</div>'
                   f'<div style="font:700 22px Plex;color:{fg}">{name}</div>'
                   f'<div style="font:400 15px Plex;line-height:1.5;color:{fg};opacity:.8">{desc}</div>'
                   f'<div style="font:400 13px Mono;color:{fg};opacity:.6">#{_h}</div>'
                   f'</div>')
    body = (f'<div class="eyebrow">Semantic Colours</div>'
            f'<div class="h2" style="margin-bottom:36px">Colour as signal, not decoration.</div>'
            f'<div style="display:flex;gap:12px;height:400px">{cards2}</div>'
            f'<div class="body thin" style="margin-top:32px">Semantic colours are reserved exclusively for their assigned meaning. Never repurpose GREEN for a CTA or ALARM for brand moments.</div>')
    out.append(ds.page(S, "Semantic Colours", body, "kraft"))

    # â”€â”€ 03.05  Colour Ratios â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    bars = [
        ("INK",    ds.INK,    60, ds.CHALK),
        ("CHALK",  ds.CHALK,  20, ds.INK),
        ("THREAD", ds.THREAD, 10, ds.INK),
        ("KRAFT",  ds.KRAFT,   4, ds.INK),
        ("DYE",    ds.DYE,     3, ds.CHALK),
        ("MIST",   ds.MIST,    2, ds.INK),
        ("SEM.",   ds.GREEN,   1, ds.CHALK),
    ]
    bar_rows = ""
    for name, col, pct, fg in bars:
        bar_rows += (f'<div style="display:flex;align-items:center;gap:20px;margin-bottom:14px">'
                     f'<div style="font:500 12px Mono;letter-spacing:.12em;width:72px;text-align:right;text-transform:uppercase">{name}</div>'
                     f'<div style="background:{col};width:{pct * 12}px;height:38px;display:flex;align-items:center;padding-left:14px">'
                     f'<span style="font:700 15px Mono;color:{fg}">{pct}%</span></div>'
                     f'</div>')
    body = (f'<div class="eyebrow">Colour Ratios</div>'
            f'<div class="row jb" style="gap:80px">'
            f'<div class="col" style="flex:1">'
            f'<div class="h2" style="margin-bottom:12px">Use in proportion.</div>'
            f'<div class="lead thin" style="margin-bottom:36px">The 60-20-10 rule governs every surface, from slide decks to product screens to print materials.</div>'
            f'{bar_rows}</div>'
            f'<div class="col" style="width:460px;gap:16px">'
            f'<div class="card" style="flex:1">'
            f'<div class="lab" style="margin-bottom:12px">INK — 60%</div>'
            f'<div class="body">Backgrounds, body text, icons, borders. The dominant voice of every surface.</div>'
            f'</div>'
            f'<div class="card" style="flex:1">'
            f'<div class="lab" style="margin-bottom:12px">CHALK — 20%</div>'
            f'<div class="body">Page fields, card fills, negative space. The breath.</div>'
            f'</div>'
            f'<div class="card" style="flex:1;border-left:3px solid {ds.THREAD}">'
            f'<div class="lab" style="margin-bottom:12px">THREAD — 10%</div>'
            f'<div class="body">Accent moments only. CTAs, the logo notch, active states.</div>'
            f'</div>'
            f'</div>'
            f'</div>')
    out.append(ds.page(S, "Colour Ratios", body, "paper"))

    # â”€â”€ 03.06  Accessibility â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    pairs = [
        (ds.INK,    ds.CHALK,   "INK / CHALK"),
        (ds.INK,    ds.PAPER,   "INK / PAPER"),
        (ds.INK,    ds.KRAFT,   "INK / KRAFT"),
        (ds.INK,    ds.MIST,    "INK / MIST"),
        (ds.CHALK,  ds.INK,     "CHALK / INK"),
        (ds.CHALK,  ds.DYE,     "CHALK / DYE"),
        (ds.CHALK,  ds.THREAD,  "CHALK / THREAD"),
        (ds.THREAD, ds.INK,     "THREAD / INK"),
        (ds.THREAD, ds.CHALK,   "THREAD / CHALK"),
        (ds.GREEN,  ds.CHALK,   "GREEN / CHALK"),
        (ds.AMBER,  ds.INK,     "AMBER / INK"),
        (ds.ALARM,  ds.CHALK,   "ALARM / CHALK"),
    ]
    rows = ""
    for a, b, lbl in pairs:
        cr = ds.contrast(a, b)
        badge_col = _cc(cr)
        badge = "AAA" if cr >= 7 else ("AA" if cr >= 4.5 else "FAIL")
        rows += (f'<tr>'
                 f'<td style="font:500 14px Mono">{lbl}</td>'
                 f'<td><div style="display:flex;gap:8px;align-items:center">'
                 f'<div style="width:28px;height:28px;background:{a};border:1.5px solid rgba(26,20,18,.2)"></div>'
                 f'<div style="width:28px;height:28px;background:{b};border:1.5px solid rgba(26,20,18,.2)"></div>'
                 f'<div style="font:400 14px {a};padding:3px 10px;background:{a};color:{b};font-family:Plex">Aa</div>'
                 f'</div></td>'
                 f'<td style="font:600 15px Mono">{cr:.1f}:1</td>'
                 f'<td><span style="background:{badge_col};color:#F5F3EF;font:600 11px Mono;letter-spacing:.1em;padding:3px 9px">{badge}</span></td>'
                 f'</tr>')
    body = (f'<div class="eyebrow">Accessibility</div>'
            f'<div class="row jb ac" style="margin-bottom:28px">'
            f'<div class="h2">Every combination<br>earns its place.</div>'
            f'<div class="body thin" style="max-width:420px">All text-on-background combinations must meet WCAG 2.1 AA (4.5:1 for normal text, 3:1 for large text). Preferred: AAA.</div>'
            f'</div>'
            f'<table><thead><tr><th>Pair</th><th>Sample</th><th>Ratio</th><th>WCAG</th></tr></thead>'
            f'<tbody>{rows}</tbody></table>')
    out.append(ds.page(S, "Accessibility", body, "light"))

    # â”€â”€ 03.07  Neutral Scale â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    neutrals = [
        (ds.N900, "N900 / INK",   "#1A1412", ds.CHALK, "Body text, logo, icons"),
        (ds.N700, "N700",         "#3A322D", ds.CHALK, "Secondary text, borders"),
        (ds.N500, "N500",         "#7A7068", ds.CHALK, "Placeholder, disabled"),
        (ds.N300, "N300",         "#CBC3BA", ds.INK,   "Dividers, track fills"),
        (ds.N100, "N100",         "#D9D3CB", ds.INK,   "Hover tints, nested bg"),
        (ds.CHALK,"CHALK",        "#E5E0DA", ds.INK,   "Card fills, page bg"),
        (ds.PAPER,"PAPER",        "#F5F3EF", ds.INK,   "Reading surface"),
    ]
    swrows = ""
    for bg, name, hex_, fg, usage in neutrals:
        swrows += (f'<div style="display:flex;align-items:stretch;height:68px">'
                   f'<div style="background:{bg};width:200px;flex-shrink:0;display:flex;align-items:center;padding:0 20px">'
                   f'<span style="font:700 15px Plex;color:{fg}">{name}</span></div>'
                   f'<div style="background:{bg};width:120px;display:flex;align-items:center;padding:0 20px;border-left:1.5px solid rgba(26,20,18,.12)">'
                   f'<span style="font:400 13px Mono;color:{fg};opacity:.7">{hex_}</span></div>'
                   f'<div style="background:{bg};flex:1;display:flex;align-items:center;padding:0 20px;border-left:1.5px solid rgba(26,20,18,.12)">'
                   f'<span style="font:400 15px Plex;color:{fg};opacity:.85">{usage}</span></div>'
                   f'</div>')
    body = (f'<div class="eyebrow">Neutral Scale</div>'
            f'<div class="row jb" style="gap:80px">'
            f'<div class="col" style="flex:1">'
            f'<div class="h2" style="margin-bottom:8px">Seven steps from<br>black to white.</div>'
            f'<div class="lead thin" style="margin-bottom:32px">The neutral scale is derived from INK by reducing opacity on PAPER. Use these tokens — never raw hex — in product code.</div>'
            f'<div class="stitch" style="margin-bottom:32px"></div>'
            f'{swrows}</div>'
            f'<div class="col" style="width:380px;justify-content:flex-end;gap:12px">'
            + "".join(
                f'<div style="display:flex;align-items:center;gap:14px">'
                f'<div style="width:40px;height:40px;background:{bg};border:1.5px solid rgba(26,20,18,.18)"></div>'
                f'<div class="lab" style="opacity:.7">var(--{name.lower().split("/")[0].strip().replace(" ","").replace("900","ink").replace("700","n700").replace("500","n500").replace("300","n300").replace("100","n100").replace("chalk","chalk").replace("paper","paper")})</div>'
                f'</div>'
                for bg, name, _, _, _ in neutrals
            )
            + f'</div></div>')
    out.append(ds.page(S, "Neutral Scale", body, "paper"))

    # â”€â”€ 03.08  On-Colour: logo + type examples â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    combos = [
        ("light",  ds.INK,   ds.CHALK,  "CHALK bg",  "knock"),
        ("dark",   ds.CHALK, ds.INK,    "INK bg",    "knock"),
        ("thread", ds.INK,   ds.THREAD, "THREAD bg", "solid"),
        ("kraft",  ds.INK,   ds.KRAFT,  "KRAFT bg",  "knock"),
        ("dye",    ds.CHALK, ds.DYE,    "DYE bg",    "knock"),
        ("mist",   ds.INK,   ds.MIST,   "MIST bg",   "knock"),
    ]
    cells = ""
    for theme, col, bg, lbl, mode in combos:
        inner_bg = "transparent" if theme == "light" else bg
        cells += (f'<div style="background:{bg};flex:1;min-width:0;overflow:hidden;padding:28px 20px;display:flex;flex-direction:column;justify-content:space-between;min-height:260px">'
                  f'<div style="font:500 11px Mono;letter-spacing:.14em;text-transform:uppercase;color:{col};opacity:.6;margin-bottom:16px">{lbl}</div>'
                  f'{ds.lockup_h(col, 30, mode)}'
                  f'<div style="font:400 14px Plex;color:{col};opacity:.85;margin-top:16px;line-height:1.4">"your fit score<br>is 87 — strong."</div>'
                  f'</div>')
    body = (f'<div class="eyebrow">On-Colour</div>'
            f'<div class="h2" style="margin-bottom:32px">The logo on every ground.</div>'
            f'<div style="display:flex;gap:8px;height:420px">{cells}</div>'
            f'<div class="body thin" style="margin-top:24px">Only approved background colours are permitted. Never place the logo on a photographic or patterned field without a solid container.</div>')
    out.append(ds.page(S, "On-Colour", body, "light"))

    # â”€â”€ 03.09  Colour Don'ts â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    donts = [
        ("Never use off-palette colours", "No spontaneous brand colours — not coral, not sage, not dusty rose. The palette is complete."),
        ("Never use gradients", "Gradients are indecisive. The brand uses flat fields only."),
        ("Never overlay logo on pattern without container", "The logo requires a solid single-colour field. Pattern backgrounds need a solid block behind the mark."),
        ("Never use THREAD as a text colour on CHALK at small sizes", "THREAD on CHALK passes AA at large sizes only (≥18pt). Use INK for body text, always."),
        ("Never mix semantic and brand roles", "GREEN means Strong Fit. It is not a CTA button colour. ALARM means error. It is not for urgency headlines."),
        ("Never tint or shade palette colours", "Tints are from the neutral scale only. No arbitrary opacity on brand colours."),
    ]
    dont_items = ""
    for i, (ttl, desc) in enumerate(donts):
        dont_items += (f'<div style="border-left:3px solid {ds.THREAD};padding-left:20px;margin-bottom:22px">'
                       f'<div style="font:600 16px Plex;margin-bottom:4px">{ttl}</div>'
                       f'<div style="font:400 14px Plex;line-height:1.5;opacity:.8">{desc}</div>'
                       f'</div>')
    body = (f'<div class="eyebrow">Colour Don\'ts</div>'
            f'<div class="row jb" style="gap:80px">'
            f'<div class="col" style="flex:1">'
            f'<div class="h2" style="margin-bottom:36px">What to never do.</div>'
            f'{dont_items}</div>'
            f'<div class="col" style="width:460px;justify-content:center;align-items:center;gap:24px">'
            f'<div style="width:380px;height:200px;background:linear-gradient(135deg,{ds.THREAD},{ds.DYE});display:flex;align-items:center;justify-content:center;position:relative">'
            f'{ds.lockup_h(ds.CHALK, 48, "knock")}'
            f'<div style="position:absolute;top:0;left:0;right:0;bottom:0;border:3px solid {ds.ALARM}"></div>'
            f'<div style="position:absolute;bottom:-28px;font:500 12px Mono;letter-spacing:.12em;color:{ds.ALARM};text-transform:uppercase">✕ No gradients</div>'
            f'</div>'
            f'<div style="width:380px;height:200px;background:#89CFF0;display:flex;align-items:center;justify-content:center;position:relative">'
            f'{ds.lockup_h(ds.INK, 48, "knock")}'
            f'<div style="position:absolute;top:0;left:0;right:0;bottom:0;border:3px solid {ds.ALARM}"></div>'
            f'<div style="position:absolute;bottom:-28px;font:500 12px Mono;letter-spacing:.12em;color:{ds.ALARM};text-transform:uppercase">✕ Off-palette background</div>'
            f'</div>'
            f'</div>'
            f'</div>')
    out.append(ds.page(S, "Colour Don'ts", body, "light"))

    # â”€â”€ 03.10  Design Tokens â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    tokens = [
        ("--ink",    ds.INK,    "Primary text, logo"),
        ("--chalk",  ds.CHALK,  "Primary background"),
        ("--thread", ds.THREAD, "Accent, CTA"),
        ("--kraft",  ds.KRAFT,  "Feature surface, camel cloth"),
        ("--dye",    ds.DYE,    "Data-dense accent"),
        ("--mist",   ds.MIST,   "Secondary chip, hover on DYE"),
        ("--green",  ds.GREEN,  "Strong fit semantic"),
        ("--amber",  ds.AMBER,  "Partial fit semantic"),
        ("--alarm",  ds.ALARM,  "Error / low fit semantic"),
        ("--paper",  ds.PAPER,  "Reading surface"),
        ("--n700",   ds.N700,   "Secondary text"),
        ("--n500",   ds.N500,   "Placeholder / disabled"),
        ("--n300",   ds.N300,   "Dividers"),
        ("--n100",   ds.N100,   "Hover tints"),
    ]
    half = len(tokens) // 2
    def tok_col(toks):
        rows = ""
        for tok, col, usage in toks:
            rows += (f'<tr><td style="font:500 13px Mono;color:{ds.THREAD}">{tok}</td>'
                     f'<td><div style="width:22px;height:22px;background:{col};display:inline-block;vertical-align:middle;border:1px solid rgba(26,20,18,.2)"></div></td>'
                     f'<td style="font:400 13px Mono">{col}</td>'
                     f'<td style="font:400 13px Plex;opacity:.7">{usage}</td></tr>')
        return f'<table><thead><tr><th>Token</th><th></th><th>Value</th><th>Usage</th></tr></thead><tbody>{rows}</tbody></table>'
    body = (f'<div class="eyebrow">Design Tokens</div>'
            f'<div class="row jb" style="gap:48px">'
            f'<div class="col" style="flex:1">'
            f'<div class="h2" style="margin-bottom:24px">Tokens over raw hex.</div>'
            f'<div class="lead thin" style="margin-bottom:28px">Reference CSS custom properties in all code. Never hardcode hex values in component styles.</div>'
            f'<div class="mono sm" style="background:{ds.INK};color:{ds.CHALK};padding:20px 24px;line-height:1.9">'
            f':root {{<br>&nbsp;&nbsp;--ink: #1A1412;<br>&nbsp;&nbsp;--chalk: #E5E0DA;<br>&nbsp;&nbsp;--thread: #E9453F;<br>&nbsp;&nbsp;/* … */<br>}}'
            f'</div>'
            f'</div>'
            f'<div class="col f1">{tok_col(tokens[:half])}</div>'
            f'<div class="col f1">{tok_col(tokens[half:])}</div>'
            f'</div>')
    out.append(ds.page(S, "Design Tokens", body, "paper"))

    return out

