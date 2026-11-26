"""Chapter 03 — Colour System  (p_system.py) — ATELIER GRAPHITE v2"""
import ds

S = "03 — Colour System"

def _cc(cr):
    if cr >= 7: return ds.GREEN
    if cr >= 4.5: return ds.AMBER   # COBALT
    return ds.ALARM  # CRIMSON

def pages():
    out = []

    # ── 03.01  Colour Overview ──────────────────────────────────────────────
    swatches = [
        (ds.INK,    "INK",     "#14110F", "Primary"),
        (ds.CHALK,  "ZINC",    "#ECEAE5", "Primary"),
        (ds.THREAD, "THREAD",  "#FF4A1C", "Primary"),
        (ds.KRAFT,  "STEEL",   "#898984", "Extended"),
        (ds.DYE,    "DYE",     "#243268", "Extended"),
        (ds.MIST,   "MIST",    "#BFD0E3", "Extended"),
        (ds.GREEN,  "GREEN",   "#16764B", "Semantic"),
        (ds.AMBER,  "COBALT",  "#005AC2", "Semantic"),
        (ds.ALARM,  "CRIMSON", "#D4003F", "Semantic"),
        (ds.PAPER,  "PAPER",   "#F5F5F3", "Surface"),
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

    # ── 03.02  Primary Triad ────────────────────────────────────────────────
    def big_swatch(bg, name, hex_, role_txt, fg, pct, notes):
        return (f'<div style="background:{bg};flex:{pct};padding:52px 44px;display:flex;flex-direction:column;justify-content:space-between;min-height:620px">'
                f'<div>'
                f'<div style="font:500 12px Mono;letter-spacing:.14em;text-transform:uppercase;color:{fg};opacity:.7;margin-bottom:12px">{role_txt}</div>'
                f'<div style="font:700 72px Plex;line-height:.9;color:{fg}">{name}</div>'
                f'<div style="font:400 20px Mono;color:{fg};opacity:.7;margin-top:10px">{hex_}</div>'
                f'</div>'
                f'<div style="font:400 16px Plex;line-height:1.5;color:{fg};opacity:.85;max-width:260px">{notes}</div>'
                f'</div>')
    row = (big_swatch(ds.INK, "INK", "#14110F", "60% — Dominant", ds.CHALK, 3,
                      "The ground. Warm near-black from artisanal ink. Used for all body text, borders, icons, and the logo mark. Temperature: warm dark — opposite of cool teal.") +
           big_swatch(ds.CHALK, "ZINC", "#ECEAE5", "20% — Field", ds.INK, 2,
                      "The fabric. Cool grey-white that holds the page. The default slide and UI background. Cooler than ivory — industrially neutral.") +
           big_swatch(ds.THREAD, "THREAD", "#FF4A1C", "10% — Accent", ds.INK, 1,
                      "The stitch. Burnt orange-red that punctuates. Used for the logo notch, CTAs, and wayfinding only."))
    body = (f'<div class="eyebrow">Primary Triad</div>'
            f'<div style="display:flex;height:680px;gap:0;margin:-84px -96px -92px;overflow:hidden">{row}</div>')
    out.append(ds.page(S, "Primary Triad", body, "light"))

    # ── 03.03  Extended Palette ─────────────────────────────────────────────
    ext = [
        (ds.KRAFT, "STEEL", "#898984", ds.CHALK,
         "Graphite grey. The presser's iron surface. Used for card surfaces, mid-tone chips, and structural dividers. Replaces sandy kraft — now fully industrial."),
        (ds.DYE, "DYE", "#243268", ds.CHALK,
         "Indigo. Deep navy used for data callouts, the pipeline view, and bilingual header bands. Distinct from teal — it is ink in a vat, not a night sky."),
        (ds.MIST, "MIST", "#BFD0E3", ds.INK,
         "Periwinkle. Pale blue for secondary chips, hover states on DYE surfaces, and form input backgrounds. Cool but not cold."),
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
            f'<div class="h2" style="margin-bottom:40px">Drawn from the pressroom floor.</div>'
            f'<div style="display:flex;gap:12px;height:460px">{cards}</div>'
            f'<div class="body thin" style="margin-top:28px">Extended colours complement but never compete with the primary triad. Use STEEL as a neutral mid-tone; DYE for high-information-density views; MIST for cool-secondary contexts only.</div>')
    out.append(ds.page(S, "Extended Palette", body, "light"))

    # ── 03.04  Semantic Colours ─────────────────────────────────────────────
    sem = [
        (ds.GREEN,  "STRONG FIT",  "Fit score ≥ 75", "✓", "16764B"),
        (ds.AMBER,  "PARTIAL FIT", "Fit score 50–74", "~", "005AC2"),  # COBALT
        (ds.ALARM,  "LOW FIT",     "Fit score < 50",  "!", "D4003F"),  # CRIMSON
        (ds.PAPER,  "SURFACE",     "Reading areas",   "◻", "F5F5F3"),
    ]
    cards2 = ""
    for bg, name, desc, sym, _h in sem:
        fg = ds.CHALK if ds.lum(bg) < 0.2 else ds.INK
        cards2 += (f'<div style="background:{bg};flex:1;padding:36px 32px;display:flex;flex-direction:column;gap:20px">'
                   f'<div style="font:700 52px Mono;color:{fg};opacity:.35">{sym}</div>'
                   f'<div style="font:700 22px Plex;color:{fg}">{name}</div>'
                   f'<div style="font:400 15px Plex;line-height:1.5;color:{fg};opacity:.8">{desc}</div>'
                   f'<div style="font:400 13px Mono;color:{fg};opacity:.6">#{_h}</div>'
                   f'</div>')
    body = (f'<div class="eyebrow">Semantic Colours</div>'
            f'<div class="h2" style="margin-bottom:36px">Colour as signal, not decoration.</div>'
            f'<div style="display:flex;gap:12px;height:400px">{cards2}</div>'
            f'<div class="body thin" style="margin-top:32px">Semantic colours are reserved exclusively for their assigned meaning. COBALT = Partial Fit. GREEN = Strong Fit. CRIMSON = Low Fit / Error. Never swap them for brand decoration.</div>')
    out.append(ds.page(S, "Semantic Colours", body, "kraft"))

    # ── 03.05  Why This Palette Changed ────────────────────────────────────
    # The differentiation story
    comp_rows = ""
    pairs = [
        ("CHALK → ZINC",   "#F2EDE3", "#ECEAE5", "Warm ivory → cool grey-white. Away from Angelsta's identical Paper/Ivory."),
        ("KRAFT → STEEL",  "#D9C29B", "#898984", "Sandy beige → graphite. Completely different family."),
        ("AMBER → COBALT", "#E8A317", "#005AC2", "Warm gold → electric blue. Opposite of Angelsta's Saffron Star."),
        ("ALARM → CRIMSON","#B3261E", "#D4003F", "Red-terracotta → magenta-red. Clear hue shift away from Angelsta Terracotta."),
    ]
    for change, old, new, reason in pairs:
        comp_rows += (f'<tr>'
                      f'<td style="font:600 14px Mono">{change}</td>'
                      f'<td><div style="display:flex;align-items:center;gap:10px">'
                      f'<div style="width:28px;height:28px;background:{old};border:1px solid rgba(20,17,15,.2)"></div>'
                      f'<span style="font:400 12px Mono;opacity:.6">{old}</span>'
                      f'<span style="font:700 14px Mono;color:{ds.THREAD}">→</span>'
                      f'<div style="width:28px;height:28px;background:{new};border:1px solid rgba(20,17,15,.2)"></div>'
                      f'<span style="font:400 12px Mono;opacity:.6">{new}</span>'
                      f'</div></td>'
                      f'<td style="font:400 13px Plex;opacity:.8">{reason}</td>'
                      f'</tr>')
    body = (f'<div class="eyebrow">Palette Evolution</div>'
            f'<div class="row jb" style="gap:60px">'
            f'<div class="col" style="flex:1">'
            f'<div class="h2" style="margin-bottom:12px">Atelier Graphite.<br>Four deliberate changes.</div>'
            f'<div class="lead thin" style="margin-bottom:24px">The original palette was warm-craft. It read too close to another MENA brand\'s warm-teal-gold-ivory palette. The rebrand shifts to precision-industrial: cooler, sharper, distinctly different.</div>'
            f'<table><thead><tr><th>Change</th><th>Before → After</th><th>Rationale</th></tr></thead><tbody>{comp_rows}</tbody></table>'
            f'</div>'
            f'<div class="col" style="width:360px;justify-content:center;gap:12px">'
            f'<div class="lab" style="margin-bottom:4px">Visual Fingerprint</div>'
            f'<div style="padding:20px;background:{ds.INK};color:{ds.CHALK}">'
            f'<div style="font:500 11px Mono;letter-spacing:.14em;text-transform:uppercase;color:{ds.THREAD};margin-bottom:10px">Tailored v2 — Atelier Graphite</div>'
            f'<div style="font:400 13px Mono;line-height:2;color:{ds.CHALK}">'
            f'■ INK &nbsp;&nbsp;#14110F warm charcoal<br>'
            f'□ ZINC &nbsp;#ECEAE5 cool grey-white<br>'
            f'● THREAD #FF4A1C burnt orange<br>'
            f'▪ STEEL #898984 graphite grey<br>'
            f'■ DYE &nbsp;&nbsp;#243268 indigo<br>'
            f'● COBALT #005AC2 electric blue<br>'
            f'▲ CRIMSON #D4003F magenta-red'
            f'</div>'
            f'</div>'
            f'<div class="body thin" style="margin-top:8px">Mood: industrial · precise · cool. Far from warm-celestial.</div>'
            f'</div>'
            f'</div>')
    out.append(ds.page(S, "Palette Evolution", body, "paper"))

    # ── 03.06  Accessibility ─────────────────────────────────────────────────
    pairs_a = [
        (ds.INK,   ds.CHALK,  "INK / ZINC"),
        (ds.INK,   ds.PAPER,  "INK / PAPER"),
        (ds.INK,   ds.KRAFT,  "INK / STEEL"),
        (ds.INK,   ds.MIST,   "INK / MIST"),
        (ds.CHALK, ds.INK,    "ZINC / INK"),
        (ds.CHALK, ds.DYE,    "ZINC / DYE"),
        (ds.CHALK, ds.THREAD, "ZINC / THREAD"),
        (ds.THREAD,ds.INK,    "THREAD / INK"),
        (ds.AMBER, ds.CHALK,  "COBALT / ZINC"),
        (ds.GREEN, ds.CHALK,  "GREEN / ZINC"),
        (ds.ALARM, ds.CHALK,  "CRIMSON / ZINC"),
        (ds.DYE,   ds.CHALK,  "DYE / ZINC"),
    ]
    rows = ""
    for a, b, lbl in pairs_a:
        cr = ds.contrast(a, b)
        badge_col = _cc(cr)
        badge = "AAA" if cr >= 7 else ("AA" if cr >= 4.5 else "FAIL")
        badge_fg = ds.CHALK if ds.lum(badge_col) < 0.2 else ds.INK
        rows += (f'<tr>'
                 f'<td style="font:500 14px Mono">{lbl}</td>'
                 f'<td><div style="display:flex;gap:8px;align-items:center">'
                 f'<div style="width:28px;height:28px;background:{a};border:1.5px solid rgba(20,17,15,.2)"></div>'
                 f'<div style="width:28px;height:28px;background:{b};border:1.5px solid rgba(20,17,15,.2)"></div>'
                 f'<div style="font:400 14px Plex;padding:3px 10px;background:{a};color:{b}">Aa</div>'
                 f'</div></td>'
                 f'<td style="font:600 15px Mono">{cr:.1f}:1</td>'
                 f'<td><span style="background:{badge_col};color:{badge_fg};font:600 11px Mono;letter-spacing:.1em;padding:3px 9px">{badge}</span></td>'
                 f'</tr>')
    body = (f'<div class="eyebrow">Accessibility</div>'
            f'<div class="row jb ac" style="margin-bottom:28px">'
            f'<div class="h2">Every combination<br>earns its place.</div>'
            f'<div class="body thin" style="max-width:420px">All text-on-background combinations must meet WCAG 2.1 AA (4.5:1 for normal text, 3:1 for large). Target AAA wherever possible.</div>'
            f'</div>'
            f'<table><thead><tr><th>Pair</th><th>Sample</th><th>Ratio</th><th>WCAG</th></tr></thead>'
            f'<tbody>{rows}</tbody></table>')
    out.append(ds.page(S, "Accessibility", body, "light"))

    # ── 03.07  Design Tokens ─────────────────────────────────────────────────
    tokens = [
        ("--ink",    ds.INK,    "Primary text, logo"),
        ("--chalk",  ds.CHALK,  "Primary background (ZINC)"),
        ("--thread", ds.THREAD, "Accent, CTA"),
        ("--kraft",  ds.KRAFT,  "STEEL — card surface, structural grey"),
        ("--dye",    ds.DYE,    "Indigo accent, data-dense"),
        ("--mist",   ds.MIST,   "Secondary chip, hover on DYE"),
        ("--green",  ds.GREEN,  "Strong fit semantic"),
        ("--amber",  ds.AMBER,  "COBALT — partial fit semantic"),
        ("--alarm",  ds.ALARM,  "CRIMSON — error / low fit"),
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
                     f'<td><div style="width:22px;height:22px;background:{col};display:inline-block;vertical-align:middle;border:1px solid rgba(20,17,15,.2)"></div></td>'
                     f'<td style="font:400 13px Mono">{col}</td>'
                     f'<td style="font:400 13px Plex;opacity:.7">{usage}</td></tr>')
        return f'<table><thead><tr><th>Token</th><th></th><th>Value</th><th>Usage</th></tr></thead><tbody>{rows}</tbody></table>'
    body = (f'<div class="eyebrow">Design Tokens</div>'
            f'<div class="row jb" style="gap:48px">'
            f'<div class="col" style="flex:1">'
            f'<div class="h2" style="margin-bottom:24px">Tokens over raw hex.</div>'
            f'<div class="lead thin" style="margin-bottom:28px">Reference CSS custom properties in all code. Never hardcode hex values. Token names use the original variable names for backward compatibility.</div>'
            f'<div class="mono sm" style="background:{ds.INK};color:{ds.CHALK};padding:20px 24px;line-height:1.9">'
            f':root {{<br>&nbsp;&nbsp;--ink: #14110F;&nbsp;&nbsp;&nbsp;/* warm charcoal */<br>'
            f'&nbsp;&nbsp;--chalk: #ECEAE5;&nbsp;/* zinc / cool white */<br>'
            f'&nbsp;&nbsp;--thread: #FF4A1C; /* burnt orange */<br>'
            f'&nbsp;&nbsp;--amber: #005AC2;&nbsp;/* cobalt blue */<br>'
            f'&nbsp;&nbsp;--alarm: #D4003F;&nbsp;/* crimson */<br>'
            f'&nbsp;&nbsp;/* … */<br>}}'
            f'</div>'
            f'</div>'
            f'<div class="col f1">{tok_col(tokens[:half])}</div>'
            f'<div class="col f1">{tok_col(tokens[half:])}</div>'
            f'</div>')
    out.append(ds.page(S, "Design Tokens", body, "paper"))

    return out
