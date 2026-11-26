"""Chapter 06 — Product UI  (p_ui.py)"""
import ds

S = "06 — Product UI"

def _screen(title, content, bg=None, w=1100, h=640, bar_col=None):
    bg = bg or ds.PAPER
    bar = bar_col or ds.INK
    # browser chrome
    chrome = (f'<div style="background:{ds.N700};height:36px;display:flex;align-items:center;padding:0 14px;gap:8px">'
              f'<div style="width:11px;height:11px;border-radius:50%;background:#8F1D2C"></div>'
              f'<div style="width:11px;height:11px;border-radius:50%;background:#E39A1B"></div>'
              f'<div style="width:11px;height:11px;border-radius:50%;background:#1E8A5A"></div>'
              f'<div style="flex:1;background:{ds.N900};border-radius:0;height:20px;margin:0 20px;display:flex;align-items:center;padding:0 12px">'
              f'<span style="font:400 10px Mono;color:{ds.N300};letter-spacing:.06em">tailored.io/{title.lower().replace(" ","")}</span></div>'
              f'</div>')
    return (f'<div style="width:{w}px;border:1.5px solid {ds.N300};position:relative;box-shadow:0 24px 48px -16px rgba(26,20,18,.35);border-radius:0 34px 0 0;overflow:hidden">'
            f'{chrome}'
            f'<div style="background:{bg};height:{h}px;overflow:hidden">{content}</div>'
            f'</div>')

def _nav(active="Studio", dark=False):
    bg = ds.INK if dark else ds.CHALK
    fg = ds.CHALK if dark else ds.INK
    items = ["Radar", "Studio", "Pipeline", "Profile"]
    links = ""
    for it in items:
        is_a = it == active
        links += (f'<a style="font:{"600" if is_a else "400"} 13px Mono;letter-spacing:.1em;text-transform:uppercase;'
                  f'color:{ds.THREAD if is_a else fg};text-decoration:none;padding:0 16px;opacity:{"1" if is_a else ".7"}">{it}</a>')
    return (f'<div style="height:52px;background:{bg};border-bottom:1.5px solid rgba(26,20,18,.18);'
            f'display:flex;align-items:center;padding:0 28px;gap:0;justify-content:space-between">'
            f'<div style="display:flex;align-items:center;gap:24px">'
            f'{ds.lockup_h(fg, 28, "knock")}'
            f'<div style="width:1.5px;height:22px;background:{fg};opacity:.2"></div>'
            f'<div style="display:flex;gap:0">{links}</div>'
            f'</div>'
            f'<div style="display:flex;align-items:center;gap:12px">'
            f'<div style="width:30px;height:30px;border-radius:50%;background:{ds.THREAD};display:flex;align-items:center;justify-content:center;font:700 12px Plex;color:{ds.INK}">K</div>'
            f'</div>'
            f'</div>')

def pages():
    out = []

    # ── 06.01  UI Principles ────────────────────────────────────────────────
    principles = [
        ("Precision over flair",  "measure", "Every pixel must earn its place. The interface communicates job intelligence — clarity is the highest form of craft."),
        ("Sharp cut, one curve", "needle",  "No pill-shaped blobs. One curved corner per object, like an armhole. The voice is warm and direct, like a skilled tailor advising a client."),
        ("RTL first-class",        "globe",   "Arabic layouts are not mirrored afterthoughts. Every component is designed bidirectionally from the first commit."),
        ("Fit as north star",      "fit",     "The fit score is the product's heartbeat. UI hierarchy always surfaces relevance first, detail second."),
        ("Stitch, not chrome",     "tape",    "The only ornament is the stitch. No drop shadows on interactive elements, no decorative borders, no imagery in UI chrome."),
        ("Zero empty states",      "chat",    "Every empty state is an action prompt. The product is never silent."),
    ]
    cards = ""
    for title, ico, desc in principles:
        cards += (f'<div class="card" style="flex:1;min-width:220px;padding:28px 24px">'
                  f'<div style="margin-bottom:14px">{ds.icon(ico, 36)}</div>'
                  f'<div style="font:600 16px Plex;margin-bottom:8px">{title}</div>'
                  f'<div style="font:400 14px Plex;line-height:1.5;opacity:.8">{desc}</div>'
                  f'</div>')
    body = (f'<div class="eyebrow">Product UI</div>'
            f'<div class="h1" style="margin-bottom:36px">The interface is the brand.</div>'
            f'<div style="display:flex;flex-wrap:wrap;gap:12px">{cards}</div>')
    out.append(ds.page(S, "UI Principles", body, "light"))

    # ── 06.02  Component Foundations ───────────────────────────────────────
    # Buttons, Typography scale, Spacing, Border radius
    btn_row = (
        f'<div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap">'
        f'<button style="background:{ds.THREAD};color:{ds.INK};border:none;padding:12px 32px;font:600 13px Mono;letter-spacing:.12em;text-transform:uppercase;cursor:pointer;border-radius:0 12px 0 12px">Apply Now</button>'
        f'<button style="background:{ds.INK};color:{ds.CHALK};border:none;padding:12px 32px;font:600 13px Mono;letter-spacing:.12em;text-transform:uppercase;cursor:pointer;border-radius:0 12px 0 12px">Save Draft</button>'
        f'<button style="background:transparent;color:{ds.INK};border:1.5px solid {ds.INK};padding:12px 32px;font:600 13px Mono;letter-spacing:.12em;text-transform:uppercase;cursor:pointer;border-radius:0 12px 0 12px">View Job</button>'
        f'<button style="background:transparent;color:{ds.N500};border:1.5px solid {ds.N300};padding:12px 32px;font:500 13px Mono;letter-spacing:.12em;text-transform:uppercase;cursor:pointer;border-radius:0 12px 0 12px;opacity:.6">Disabled</button>'
        f'</div>'
    )
    chip_row = (
        f'<div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:16px">'
        + "".join(
            f'<div style="display:inline-flex;align-items:center;gap:7px;padding:5px 14px;border:1.5px solid {col};font:500 11px Mono;letter-spacing:.1em;text-transform:uppercase;color:{fg};background:{bg}">'
            f'<div style="width:7px;height:6px;background:{dot};clip-path:polygon(0 0,100% 0,50% 100%)"></div>{label}</div>'
            for label, col, fg, bg, dot in [
                ("Python",         ds.INK,   ds.INK,   "transparent",  ds.THREAD),
                ("Full-time",      ds.INK,   ds.INK,   "transparent",  ds.THREAD),
                ("Cairo, Egypt",   ds.N300,  ds.N500,  "transparent",  ds.N300),
                ("Strong Fit",     ds.GREEN, ds.GREEN, "transparent",  ds.GREEN),
                ("Partial Fit",    ds.AMBER, ds.AMBER, "transparent",  ds.AMBER),
                ("Remote",         ds.DYE,   ds.DYE,   "transparent",  ds.DYE),
            ]
        )
        + f'</div>'
    )
    input_row = (
        f'<div style="display:flex;gap:12px;margin-top:20px;align-items:flex-end">'
        f'<div style="flex:1">'
        f'<div style="font:500 11px Mono;letter-spacing:.12em;text-transform:uppercase;margin-bottom:6px;opacity:.7">Job Title</div>'
        f'<div style="border:1.5px solid {ds.INK};padding:11px 16px;font:400 15px Plex;background:{ds.PAPER}">Senior Product Designer</div>'
        f'</div>'
        f'<div style="flex:1">'
        f'<div style="font:500 11px Mono;letter-spacing:.12em;text-transform:uppercase;margin-bottom:6px;opacity:.7">Company</div>'
        f'<div style="border:1.5px solid {ds.N300};padding:11px 16px;font:400 15px Plex;background:{ds.PAPER};color:{ds.N500}">Start typing…</div>'
        f'</div>'
        f'<div style="background:{ds.THREAD};padding:11px 28px;font:600 13px Mono;letter-spacing:.12em;text-transform:uppercase;cursor:pointer;border-radius:0 12px 0 12px;white-space:nowrap">Dispatch</div>'
        f'</div>'
    )
    body = (f'<div class="eyebrow">Component Foundations</div>'
            f'<div class="row jb" style="gap:60px">'
            f'<div class="col" style="flex:1;gap:28px">'
            f'<div>'
            f'<div class="lab" style="margin-bottom:12px">Buttons — square cut, one diagonal curve</div>'
            f'{btn_row}'
            f'</div>'
            f'<div>'
            f'<div class="lab" style="margin-bottom:12px">Chips & Tags</div>'
            f'{chip_row}'
            f'</div>'
            f'<div>'
            f'<div class="lab" style="margin-bottom:12px">Form Inputs</div>'
            f'{input_row}'
            f'</div>'
            f'</div>'
            f'<div class="col" style="width:360px;gap:16px">'
            f'<div class="lab">Spacing Scale</div>'
            + "".join(
                f'<div style="display:flex;align-items:center;gap:14px">'
                f'<div style="width:{px}px;height:16px;background:{ds.THREAD};opacity:.85"></div>'
                f'<div style="font:400 12px Mono;letter-spacing:.08em">{label} — {px}px</div>'
                f'</div>'
                for label, px in [("4xs",4),("3xs",8),("2xs",12),("xs",16),("sm",24),("md",32),("lg",48),("xl",64),("2xl",96)]
            )
            + f'</div></div>')
    out.append(ds.page(S, "Component Foundations", body, "paper"))

    # ── 06.03  Fit Score Dial ──────────────────────────────────────────────
    scores = [(92,"Strong — Architecture match"), (74,"Partial — Mid-seniority gap"), (41,"Low — Domain mismatch")]
    dial_cells = ""
    for score, label in scores:
        col = ds.GREEN if score >= 75 else (ds.AMBER if score >= 50 else ds.ALARM)
        dial_cells += (f'<div style="text-align:center;padding:32px 20px;background:{ds.PAPER};flex:1">'
                       f'{ds.fit_dial(score, 180, ds.INK, col)}'
                       f'<div style="font:600 16px Plex;margin-top:16px">{label}</div>'
                       f'</div>')
    pillar_rows = ""
    pillars = [("Core Stack","30%"),("Projects","20%"),("Seniority","10%"),("Experience","10%"),("Domain","10%"),
               ("Persona","5%"),("Education","5%"),("Work Mode","5%"),("Language","5%")]
    for name, wt in pillars:
        pillar_rows += (f'<div style="display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid {ds.N100};font:400 14px Plex">'
                        f'<span>{name}</span><span style="font-family:Mono;font-weight:500;color:{ds.THREAD}">{wt}</span></div>')
    body = (f'<div class="eyebrow">Fit Score</div>'
            f'<div class="row jb" style="gap:60px">'
            f'<div class="col" style="flex:1">'
            f'<div class="h2" style="margin-bottom:8px">The dial is the product.</div>'
            f'<div class="lead thin" style="margin-bottom:28px">Every job card surfaces a half-moon fit gauge built from measuring-tape ticks. Colour shifts with score tier.</div>'
            f'<div style="display:flex;gap:12px">{dial_cells}</div>'
            f'</div>'
            f'<div class="col" style="width:300px">'
            f'<div class="lab" style="margin-bottom:16px">Nine Pillars & Weights</div>'
            f'{pillar_rows}'
            f'</div>'
            f'</div>')
    out.append(ds.page(S, "Fit Score Dial", body, "light"))

    # ── 06.04  Radar Feed Card ─────────────────────────────────────────────
    def job_card(title, co, loc, score, tags, lang="en", w=440):
        is_ar = lang == "ar"
        col = ds.GREEN if score >= 75 else (ds.AMBER if score >= 50 else ds.ALARM)
        dir_ = "rtl" if is_ar else "ltr"
        chip_els = "".join(
            f'<div style="border:1.5px solid {ds.N300};padding:4px 10px;font:500 10px Mono;letter-spacing:.08em;text-transform:uppercase;color:{ds.N700}">{t}</div>'
            for t in tags
        )
        return (f'<div style="border:1.5px solid {ds.N200 if hasattr(ds,"N200") else ds.N300};padding:24px;background:{ds.PAPER};border-radius:0 26px 0 0;'
                f'width:{w}px;position:relative;direction:{dir_}">'
                f'<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:14px">'
                f'<div>'
                f'<div style="font:600 18px {("PlexAr" if is_ar else "Plex")};margin-bottom:4px">{title}</div>'
                f'<div style="font:400 14px Mono;color:{ds.N500}">{co} · {loc}</div>'
                f'</div>'
                f'{ds.fit_dial(score, 72, ds.INK, col, num=True)}'
                f'</div>'
                f'<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px">{chip_els}</div>'
                f'<div style="display:flex;gap:10px">'
                f'<div style="flex:1;background:{ds.THREAD};padding:9px 0;font:600 11px Mono;letter-spacing:.12em;text-transform:uppercase;text-align:center;color:{ds.INK}">{"تقدم الآن" if is_ar else "Apply Now"}</div>'
                f'<div style="border:1.5px solid {ds.INK};padding:9px 20px;font:500 11px Mono;letter-spacing:.1em;text-transform:uppercase;text-align:center">{"حفظ" if is_ar else "Save"}</div>'
                f'</div>'
                f'</div>')
    en_card = job_card("Senior Product Designer", "Noon", "Cairo, Egypt", 87,
                       ["Full-time","Cairo","UX","Figma","Strong Fit"], "en")
    ar_card = job_card("مصمم منتج أول", "نون", "القاهرة، مصر", 87,
                       ["دوام كامل","القاهرة","تجربة المستخدم","فيغما","توافق قوي"], "ar")
    body = (f'<div class="eyebrow">Radar Feed Card</div>'
            f'<div class="row jb" style="gap:60px">'
            f'<div class="col" style="flex:1">'
            f'<div class="h2" style="margin-bottom:28px">Every job is a card.<br>Every card scores the fit.</div>'
            f'<div style="display:flex;gap:24px;align-items:flex-start">'
            f'<div><div class="lab" style="margin-bottom:12px">English (LTR)</div>{en_card}</div>'
            f'<div><div class="lab" style="margin-bottom:12px">Arabic (RTL)</div>{ar_card}</div>'
            f'</div>'
            f'</div>'
            f'<div class="col" style="width:280px;gap:16px;justify-content:center">'
            f'<div class="lab">Card Anatomy</div>'
            + "".join(
                f'<div style="display:flex;gap:12px;align-items:flex-start">'
                f'<div style="width:20px;height:20px;background:{ds.THREAD};clip-path:polygon(0 0,100% 0,50% 100%);flex-shrink:0;margin-top:3px"></div>'
                f'<div style="font:400 14px Plex;line-height:1.4">{txt}</div>'
                f'</div>'
                for txt in [
                    "Job title + company + location (always above fold)",
                    "Fit dial — size 72px, right-aligned",
                    "Tag chips — skill, type, location, fit tier",
                    "CTA row — primary (THREAD) + secondary (outline)",
                    "Card border 1.5px N300; hover lifts to INK",
                ]
            )
            + f'</div></div>')
    out.append(ds.page(S, "Radar Feed Card", body, "kraft"))

    # ── 06.05  CV Studio ───────────────────────────────────────────────────
    studio_content = (
        _nav("Studio") +
        f'<div style="display:flex;height:572px">'
        # sidebar
        f'<div style="width:200px;background:{ds.INK};padding:16px 0;flex-shrink:0">'
        + "".join(
            f'<div style="padding:9px 20px;font:{"600" if active else "400"} 12px Mono;letter-spacing:.1em;text-transform:uppercase;'
            f'color:{ds.CHALK if not active else ds.THREAD};opacity:{1 if active else .6}">{label}</div>'
            for label, active in [("Contact",False),("Summary",True),("Experience",False),("Projects",False),("Skills",False),("Education",False)]
        )
        + f'</div>'
        # editor area
        f'<div style="flex:1;background:{ds.PAPER};padding:28px 32px;overflow:hidden">'
        f'<div style="font:500 11px Mono;letter-spacing:.12em;text-transform:uppercase;margin-bottom:14px;color:{ds.N500}">Professional Summary</div>'
        f'<div style="border:1.5px solid {ds.THREAD};padding:16px;font:400 15px Plex;line-height:1.6;min-height:120px;background:white;position:relative">'
        f'Product designer with 7+ years building consumer fintech products across the MENA region. Expert in research-led design systems and cross-functional delivery.'
        f'<div style="position:absolute;bottom:8px;right:12px;font:400 11px Mono;color:{ds.N500}">212 / 500 chars</div>'
        f'</div>'
        f'<div style="display:flex;gap:10px;margin-top:12px">'
        f'<div style="background:{ds.THREAD};padding:8px 20px;font:600 11px Mono;letter-spacing:.12em;text-transform:uppercase;cursor:pointer;border-radius:0 12px 0 12px;color:{ds.INK}">Regenerate ✦</div>'
        f'<div style="border:1.5px solid {ds.INK};padding:8px 20px;font:500 11px Mono;letter-spacing:.1em;text-transform:uppercase;cursor:pointer;border-radius:0 12px 0 12px">Keep Draft</div>'
        f'</div>'
        f'<div style="margin-top:24px;padding:16px;background:{ds.CHALK};border-left:3px solid {ds.GREEN}">'
        f'<div style="font:500 11px Mono;letter-spacing:.12em;text-transform:uppercase;color:{ds.GREEN};margin-bottom:6px">Fit Analysis · 87</div>'
        f'<div style="font:400 14px Plex;line-height:1.5">Your summary addresses 6 of 7 key signals for this role. Add a mention of "design systems" to reach top-tier phrasing.</div>'
        f'</div>'
        f'</div>'
        # preview pane
        f'<div style="width:260px;background:{ds.N100};padding:16px;flex-shrink:0;overflow:hidden">'
        f'<div style="font:500 10px Mono;letter-spacing:.12em;text-transform:uppercase;margin-bottom:10px;opacity:.6">Live Preview</div>'
        f'<div style="background:white;padding:14px;font:400 12px Plex;line-height:1.5;transform:scale(.85);transform-origin:top left;width:280px">'
        f'<div style="font:700 16px Fraunces;margin-bottom:4px">Khalid Nasser</div>'
        f'<div style="font:400 10px Mono;color:{ds.N500};margin-bottom:8px">Senior Product Designer · Cairo</div>'
        f'<div style="height:1.5px;background:{ds.THREAD};margin-bottom:8px"></div>'
        f'<div style="font:400 11px Plex;line-height:1.5">Product designer with 7+ years building consumer fintech products…</div>'
        f'</div>'
        f'</div>'
        f'</div>'
    )
    screen = _screen("studio", studio_content, ds.PAPER, 1100, 624)
    body = (f'<div class="eyebrow">CV Studio</div>'
            f'<div class="row jb" style="gap:48px">'
            f'<div class="col" style="width:280px;gap:16px;justify-content:center">'
            f'<div class="h2">Write once.<br>Tailor always.</div>'
            f'<div class="lead thin">The studio is a three-pane editor: sidebar navigation, AI-assisted draft area, and a live CV preview.</div>'
            f'</div>'
            f'<div>{screen}</div>'
            f'</div>')
    out.append(ds.page(S, "CV Studio", body, "light"))

    # ── 06.06  Radar & Pipeline ─────────────────────────────────────────────
    # Radar feed
    radar_row = "".join(
        f'<div style="display:flex;align-items:center;padding:12px 16px;border-bottom:1px solid {ds.N100};gap:16px;background:{ds.PAPER if i%2==0 else "white"}">'
        f'<div style="flex:1">'
        f'<div style="font:600 14px Plex">{title}</div>'
        f'<div style="font:400 12px Mono;color:{ds.N500}">{co} · {loc}</div>'
        f'</div>'
        + "".join(f'<div style="border:1px solid {ds.N300};padding:3px 8px;font:400 10px Mono;text-transform:uppercase;color:{ds.N700}">{t}</div>' for t in tags)
        + f'{ds.fit_dial(score, 44, ds.INK, ds.GREEN if score>=75 else (ds.AMBER if score>=50 else ds.ALARM), num=True)}'
        f'</div>'
        for i, (title, co, loc, score, tags) in enumerate([
            ("Senior Product Designer","Noon","Cairo",87,["UX","Figma"]),
            ("UX Lead","Careem","Dubai",73,["UX","Leadership"]),
            ("Product Designer","Fawry","Cairo",61,["Fintech","UX"]),
            ("Design Manager","Paymob","Cairo",48,["Management","Figma"]),
            ("Senior UX Designer","OLX","Cairo",82,["UX","B2C"]),
        ])
    )
    # Pipeline columns
    pipeline_cols = "".join(
        f'<div style="flex:1;min-width:0">'
        f'<div style="font:500 11px Mono;letter-spacing:.12em;text-transform:uppercase;padding:8px 12px;background:{hdr_bg};color:{hdr_fg};margin-bottom:6px">{stage} <span style="opacity:.5">({count})</span></div>'
        + "".join(
            f'<div style="background:{ds.PAPER};border:1.5px solid {ds.N300};padding:10px 12px;margin-bottom:6px">'
            f'<div style="font:600 12px Plex">{job}</div>'
            f'<div style="font:400 10px Mono;color:{ds.N500}">{company}</div>'
            f'</div>'
            for job, company in jobs
        )
        + f'</div>'
        for stage, count, hdr_bg, hdr_fg, jobs in [
            ("Interested",3,ds.N100,ds.INK,[("Senior UX","Noon"),("UX Lead","Careem"),("Design Mgr","Fawry")]),
            ("Applied",2,ds.DYE,ds.CHALK,[("Product Designer","Paymob"),("Sr Designer","OLX")]),
            ("Interview",1,ds.AMBER,ds.INK,[("Design Lead","Talabat")]),
            ("Offer",0,ds.GREEN,ds.CHALK,[]),
        ]
    )
    body = (f'<div class="eyebrow">Radar & Pipeline</div>'
            f'<div class="row jb" style="gap:0;height:680px">'
            f'<div class="col" style="flex:1;border-right:1.5px solid {ds.N300};padding-right:48px">'
            f'<div class="lab" style="margin-bottom:16px">Radar Feed — job intelligence stream</div>'
            f'<div style="border:1.5px solid {ds.N300}">{radar_row}</div>'
            f'</div>'
            f'<div class="col" style="width:520px;padding-left:48px">'
            f'<div class="lab" style="margin-bottom:16px">Pipeline — kanban track</div>'
            f'<div style="display:flex;gap:8px;height:580px;align-items:flex-start">{pipeline_cols}</div>'
            f'</div>'
            f'</div>')
    out.append(ds.page(S, "Radar & Pipeline", body, "paper"))

    # ── 06.07  Onboarding Wizard ────────────────────────────────────────────
    steps = ["Account","Profile","Upload CV","Preferences","Done"]
    step_els = ""
    for i, s in enumerate(steps):
        done = i < 2
        active = i == 2
        col = ds.THREAD if active else (ds.INK if done else ds.N300)
        step_els += (f'<div style="display:flex;flex-direction:column;align-items:center;gap:6px;flex:1">'
                     f'<div style="width:32px;height:32px;border:2px solid {col};display:flex;align-items:center;justify-content:center;'
                     f'font:{"700" if active else "500"} 13px Mono;color:{col};background:{"transparent"}">'
                     f'{"✓" if done and not active else str(i+1)}</div>'
                     f'<div style="font:{"600" if active else "400"} 11px Mono;letter-spacing:.1em;text-transform:uppercase;color:{col}">{s}</div>'
                     f'</div>'
                     + (f'<div style="height:2px;background:{ds.THREAD if done else ds.N300};flex:0.5;margin-top:14px"></div>' if i < len(steps)-1 else ""))
    upload_zone = (
        f'<div style="border:2px dashed {ds.THREAD};padding:48px 32px;text-align:center;background:{ds.PAPER}">'
        f'<div style="font:400 40px Mono;margin-bottom:12px;opacity:.4">↑</div>'
        f'<div style="font:600 18px Plex;margin-bottom:8px">Drop your CV here</div>'
        f'<div style="font:400 14px Plex;color:{ds.N500};margin-bottom:20px">PDF, DOCX or TXT — max 5 MB</div>'
        f'<div style="background:{ds.THREAD};padding:10px 32px;display:inline-block;font:600 13px Mono;letter-spacing:.12em;text-transform:uppercase;cursor:pointer;border-radius:0 12px 0 12px">Browse Files</div>'
        f'</div>'
    )
    body = (f'<div class="eyebrow">Onboarding</div>'
            f'<div class="row jb" style="gap:60px">'
            f'<div class="col" style="flex:1">'
            f'<div class="h2" style="margin-bottom:28px">Five steps to your<br>first fit score.</div>'
            f'<div style="display:flex;align-items:center;margin-bottom:36px">{step_els}</div>'
            f'{upload_zone}'
            f'<div style="margin-top:16px;font:400 14px Plex;color:{ds.N500}">We read your CV to pre-fill your profile. No data is shared externally.</div>'
            f'</div>'
            f'<div class="col" style="width:380px;gap:16px;justify-content:center">'
            f'<div class="lab">Onboarding Principles</div>'
            + "".join(
                f'<div style="padding:14px 0;border-bottom:1px solid {ds.N100};font:400 15px Plex;line-height:1.5">{txt}</div>'
                for txt in [
                    "No account without immediate value. First fit score appears before onboarding ends.",
                    "CV upload is optional — the form path offers equal depth.",
                    "Progress bar uses THREAD for active, INK for done, N300 for upcoming.",
                    "Arabic onboarding flips the step order visually (right to left) but preserves data flow.",
                ]
            )
            + f'</div></div>')
    out.append(ds.page(S, "Onboarding Wizard", body, "light"))

    # ── 06.08  Trial Gate Modal ─────────────────────────────────────────────
    plans = [
        ("Free",    "0",    "EGP", "2 credits / month", ds.N100, ds.INK, False),
        ("Starter", "49",   "EGP", "5 credits / month",  ds.INK,  ds.CHALK, False),
        ("Hunter",  "179",  "EGP", "25 credits / month", ds.THREAD, ds.INK, True),
        ("Sprint",  "399",  "EGP", "70 credits / month", ds.DYE,  ds.CHALK, False),
    ]
    plan_cards = ""
    for name, price, cur, creds, bg, fg, featured in plans:
        plan_cards += (f'<div style="background:{bg};padding:20px 16px;flex:1;position:relative;border:{"2px solid "+ds.THREAD if featured else "1.5px solid "+ds.N300}">'
                       + (f'<div style="position:absolute;top:-12px;left:50%;transform:translateX(-50%);background:{ds.THREAD};padding:3px 12px;font:600 10px Mono;letter-spacing:.12em;text-transform:uppercase;color:{ds.INK};white-space:nowrap">Popular</div>' if featured else "")
                       + f'<div style="font:600 14px Mono;color:{fg};margin-bottom:8px;text-transform:uppercase;letter-spacing:.1em">{name}</div>'
                       f'<div style="font:700 32px Fraunces;color:{fg};line-height:1">{price} <span style="font-size:14px;font-family:Mono;opacity:.7">{cur}</span></div>'
                       f'<div style="font:400 12px Plex;color:{fg};opacity:.7;margin-top:4px;margin-bottom:14px">{creds}</div>'
                       f'<div style="background:{fg};color:{bg};padding:8px 0;font:600 11px Mono;letter-spacing:.1em;text-transform:uppercase;text-align:center;cursor:pointer;border-radius:0 12px 0 12px">{"Choose" if name!="Free" else "Current"}</div>'
                       f'</div>')
    modal = (f'<div style="background:rgba(26,20,18,.7);display:flex;align-items:center;justify-content:center;width:900px;height:520px">'
             f'<div style="background:{ds.CHALK};width:720px;padding:40px;position:relative;border-radius:0 40px 0 0">'
             f'<div style="position:absolute;top:16px;right:16px;font:400 20px Mono;cursor:pointer;border-radius:0 12px 0 12px;opacity:.4">✕</div>'
             f'<div style="font:500 11px Mono;letter-spacing:.14em;text-transform:uppercase;color:{ds.THREAD};margin-bottom:8px">Credits Exhausted</div>'
             f'<div style="font-family:Fraunces;font-weight:540;font-size:32px;line-height:1.1;margin-bottom:6px">Your 2 free credits<br>are spent.</div>'
             f'<div style="font:400 15px Plex;color:{ds.N500};margin-bottom:28px;line-height:1.5">Upgrade to keep tailoring. Cancel anytime. No auto-renewal on annual.</div>'
             f'<div style="display:flex;gap:12px;margin-bottom:20px">{plan_cards}</div>'
             f'<div style="font:400 12px Plex;color:{ds.N500};text-align:center">All prices in EGP · VAT inclusive · Secure payment via Paymob</div>'
             f'</div>'
             f'</div>')
    body = (f'<div class="eyebrow">Trial Gate Modal</div>'
            f'<div class="row jb" style="gap:48px">'
            f'<div class="col" style="width:300px;gap:16px;justify-content:center">'
            f'<div class="h2">The upgrade moment.</div>'
            f'<div class="lead thin">Triggered when credits reach 0. Non-dismissable until a plan is chosen or the user explicitly clicks ✕.</div>'
            f'<div class="stitch" style="margin:8px 0"></div>'
            f'<div style="font:400 14px Plex;line-height:1.5">Pricing is localised to EGP for Egypt, AED for UAE, SAR for Saudi Arabia. Displayed in local currency throughout the funnel.</div>'
            f'</div>'
            f'<div>{modal}</div>'
            f'</div>')
    out.append(ds.page(S, "Trial Gate Modal", body, "dark"))

    # ── 06.09  Arabic / RTL Screen ─────────────────────────────────────────
    ar_nav = (f'<div style="height:52px;background:{ds.INK};border-bottom:1.5px solid rgba(229,224,218,.18);'
              f'display:flex;align-items:center;padding:0 28px;gap:0;justify-content:space-between;direction:rtl">'
              f'<div style="display:flex;align-items:center;gap:24px">'
              f'{ds.lockup_ar_h(ds.CHALK, 28, "knock")}'
              f'<div style="width:1.5px;height:22px;background:{ds.CHALK};opacity:.2"></div>'
              + "".join(
                  f'<a style="font:{"600" if active else "400"} 13px Mono;letter-spacing:.1em;text-transform:uppercase;'
                  f'color:{ds.THREAD if active else ds.CHALK};text-decoration:none;padding:0 16px;opacity:{"1" if active else ".7"}">{label}</a>'
                  for label, active in [("الرادار",True),("الاستوديو",False),("المسار",False),("الملف",False)]
              )
              + f'</div>'
              f'<div style="width:30px;height:30px;border-radius:50%;background:{ds.THREAD};display:flex;align-items:center;justify-content:center;font:700 12px Plex;color:{ds.INK}">خ</div>'
              f'</div>')
    ar_card_content = (f'<div style="direction:rtl;padding:16px;background:{ds.PAPER};border:1.5px solid {ds.N300};margin-bottom:8px">'
                       f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">'
                       f'<div>'
                       f'<div style="font:600 16px PlexAr">مصمم منتج أول</div>'
                       f'<div style="font:400 12px Mono;color:{ds.N500}">نون · القاهرة، مصر</div>'
                       f'</div>'
                       f'{ds.fit_dial(87, 56, ds.INK, ds.GREEN)}'
                       f'</div>'
                       f'<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px">'
                       + "".join(f'<span style="border:1px solid {ds.N300};padding:3px 8px;font:400 10px Mono;text-transform:uppercase;color:{ds.N700}">{t}</span>'
                                 for t in ["دوام كامل","القاهرة","تجربة مستخدم","توافق قوي"])
                       + f'</div>'
                       f'<div style="display:flex;gap:8px">'
                       f'<div style="flex:1;background:{ds.THREAD};padding:8px 0;font:600 12px PlexAr;text-align:center;color:{ds.INK}">تقدم الآن</div>'
                       f'<div style="border:1.5px solid {ds.CHALK};padding:8px 16px;font:500 12px PlexAr;text-align:center;color:{ds.CHALK}">حفظ</div>'
                       f'</div>'
                       f'</div>')
    ar_screen_content = ar_nav + f'<div style="padding:28px 32px;background:{ds.INK};height:572px">' + ar_card_content * 3 + f'</div>'
    screen = _screen("radar/ar", ar_screen_content, ds.INK, 900, 624)
    body = (f'<div class="eyebrow">Arabic RTL Screen</div>'
            f'<div class="row jb" style="gap:48px">'
            f'<div class="col" style="width:300px;gap:16px;justify-content:center">'
            f'<div class="h2">عربي.<br>أولاً.</div>'
            f'<div class="lead thin">The Arabic interface is not a mirror of English. Layout is natively RTL: navigation starts right, content flows right-to-left, alignment tokens flip.</div>'
            f'<div style="font:400 14px PlexAr;direction:rtl;line-height:1.6;margin-top:12px;color:{ds.N700}">الواجهة بالعربية ليست ترجمة؛ هي تجربة مستقلة مصممة للمستخدم العربي من الأساس.</div>'
            f'</div>'
            f'<div>{screen}</div>'
            f'</div>')
    out.append(ds.page(S, "Arabic RTL Screen", body, "dark"))

    # ── 06.10  Empty States ────────────────────────────────────────────────
    def empty(icon_name, headline, sub, cta):
        return (f'<div style="background:{ds.PAPER};border-radius:0 24px 0 0;padding:36px 28px;flex:1;display:flex;flex-direction:column;align-items:center;text-align:center;gap:14px">'
                f'{ds.icon(icon_name, 48, ds.N300, ds.THREAD)}'
                f'<div style="font:600 16px Plex">{headline}</div>'
                f'<div style="font:400 13px Plex;color:{ds.N500};line-height:1.5;max-width:180px">{sub}</div>'
                f'<div style="background:{ds.THREAD};padding:8px 20px;font:600 11px Mono;letter-spacing:.12em;text-transform:uppercase;cursor:pointer;border-radius:0 12px 0 12px;color:{ds.INK}">{cta}</div>'
                f'</div>')
    empties = [
        empty("radar",   "No jobs yet",          "Complete your profile to unlock your first fit scores.", "Finish Profile"),
        empty("cv",      "No CV uploaded",        "Upload a CV or fill out your profile to get started.",   "Upload CV"),
        empty("filter",  "No matches found",      "Broaden your preferences or add more skills.",           "Edit Preferences"),
        empty("save",    "Nothing saved yet",     "Save interesting jobs from the Radar to track them.",    "Open Radar"),
    ]
    err_states = (
        f'<div style="border-left:3px solid {ds.ALARM};padding:16px 20px;background:{ds.PAPER};margin-bottom:10px">'
        f'<div style="font:600 14px Plex;margin-bottom:4px">Something went wrong</div>'
        f'<div style="font:400 13px Plex;color:{ds.N500};margin-bottom:10px">We couldn\'t load your jobs. This is on us — not you.</div>'
        f'<div style="font:600 11px Mono;letter-spacing:.1em;text-transform:uppercase;color:{ds.THREAD};cursor:pointer;border-radius:0 12px 0 12px">Try Again →</div>'
        f'</div>'
        f'<div style="border-left:3px solid {ds.AMBER};padding:16px 20px;background:{ds.PAPER}">'
        f'<div style="font:600 14px Plex;margin-bottom:4px">Credits running low</div>'
        f'<div style="font:400 13px Plex;color:{ds.N500};margin-bottom:10px">1 credit remaining this month. Upgrade to continue tailoring.</div>'
        f'<div style="font:600 11px Mono;letter-spacing:.1em;text-transform:uppercase;color:{ds.THREAD};cursor:pointer;border-radius:0 12px 0 12px">Upgrade Plan →</div>'
        f'</div>'
    )
    body = (f'<div class="eyebrow">Empty States & Errors</div>'
            f'<div class="h2" style="margin-bottom:28px">Silence is an opportunity.</div>'
            f'<div style="display:flex;gap:8px;margin-bottom:28px">' + "".join(empties) + f'</div>'
            f'<div class="row jb" style="gap:48px">'
            f'<div style="flex:1">'
            f'<div class="lab" style="margin-bottom:12px">Error & Warning States</div>'
            f'{err_states}'
            f'</div>'
            f'<div style="flex:1">'
            f'<div class="lab" style="margin-bottom:12px">Rules</div>'
            + "".join(
                f'<div style="padding:10px 0;border-bottom:1px solid {ds.N100};font:400 14px Plex;line-height:1.5">{r}</div>'
                for r in [
                    "Every empty state includes exactly one primary CTA.",
                    "Error messages are written in first person plural (we/us), never passive.",
                    "Errors use ALARM left-border. Warnings use AMBER left-border. Info uses DYE.",
                    "Icons in empty states are N300 (muted) with a THREAD notch accent.",
                ]
            )
            + f'</div></div>')
    out.append(ds.page(S, "Empty States & Errors", body, "light"))

    return out
