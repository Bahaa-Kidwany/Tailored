"""Chapter 06 — Product UI  (p_ui.py) — ATELIER GRAPHITE v2"""
import ds

S = "06 — Product UI"

def _nav(active="Studio", dark=False):
    bg = ds.INK if dark else ds.CHALK
    fg = ds.CHALK if dark else ds.INK
    items = ["Radar", "Studio", "Pipeline", "Profile"]
    links = ""
    for it in items:
        is_a = it == active
        links += (f'<a style="font:{"600" if is_a else "400"} 13px Mono;letter-spacing:.1em;text-transform:uppercase;'
                  f'color:{ds.THREAD if is_a else fg};text-decoration:none;padding:0 16px;opacity:{"1" if is_a else ".7"}">{it}</a>')
    return (f'<div style="height:52px;background:{bg};border-bottom:1.5px solid rgba(20,17,15,.18);'
            f'display:flex;align-items:center;padding:0 28px;justify-content:space-between">'
            f'<div style="display:flex;align-items:center;gap:24px">'
            f'{ds.lockup_h(fg, 28, "knock")}'
            f'<div style="width:1.5px;height:22px;background:{fg};opacity:.2"></div>'
            f'<div style="display:flex">{links}</div>'
            f'</div>'
            f'<div style="width:30px;height:30px;border-radius:50%;background:{ds.THREAD};display:flex;align-items:center;justify-content:center;font:700 12px Plex;color:{ds.INK}">K</div>'
            f'</div>')

def pages():
    out = []

    # ── 06.01  UI Principles ────────────────────────────────────────────────
    principles = [
        ("Precision over flair",   "measure", "Every pixel must earn its place. The interface communicates job intelligence — clarity is the highest form of craft."),
        ("Sharp edges, soft tone", "needle",  "No rounded rectangles. No soft-focus. The voice is warm and direct, like a skilled tailor advising a client."),
        ("RTL first-class",        "globe",   "Arabic layouts are not mirrored afterthoughts. Every component is designed bidirectionally from the first commit."),
        ("Fit as north star",      "fit",     "The fit score is the product's heartbeat. UI hierarchy always surfaces relevance first, detail second."),
        ("Stitch, not chrome",     "tape",    "The only ornament is the stitch. No drop shadows on interactive elements, no decorative borders."),
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

    # ── 06.02  Component Foundations ────────────────────────────────────────
    btn_row = (
        f'<div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap">'
        f'<button style="background:{ds.THREAD};color:{ds.INK};border:none;padding:12px 32px;font:600 13px Mono;letter-spacing:.12em;text-transform:uppercase">Apply Now</button>'
        f'<button style="background:{ds.INK};color:{ds.CHALK};border:none;padding:12px 32px;font:600 13px Mono;letter-spacing:.12em;text-transform:uppercase">Save Draft</button>'
        f'<button style="background:transparent;color:{ds.INK};border:1.5px solid {ds.INK};padding:12px 32px;font:600 13px Mono;letter-spacing:.12em;text-transform:uppercase">View Job</button>'
        f'<button style="background:transparent;color:{ds.N500};border:1.5px solid {ds.N300};padding:12px 32px;font:500 13px Mono;letter-spacing:.12em;text-transform:uppercase;opacity:.6">Disabled</button>'
        f'<button style="background:{ds.AMBER};color:{ds.CHALK};border:none;padding:12px 32px;font:600 13px Mono;letter-spacing:.12em;text-transform:uppercase">Cobalt CTA</button>'
        f'</div>'
    )
    chip_row = (
        f'<div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:16px">'
        + "".join(
            f'<div style="display:inline-flex;align-items:center;gap:7px;padding:5px 14px;border:1.5px solid {col};font:500 11px Mono;letter-spacing:.1em;text-transform:uppercase;color:{fg};background:{bg}">'
            f'<div style="width:7px;height:6px;background:{dot};clip-path:polygon(0 0,100% 0,50% 100%)"></div>{label}</div>'
            for label, col, fg, bg, dot in [
                ("Python",      ds.INK,   ds.INK,   "transparent", ds.THREAD),
                ("Full-time",   ds.INK,   ds.INK,   "transparent", ds.THREAD),
                ("Cairo",       ds.N300,  ds.N500,  "transparent", ds.N300),
                ("Strong Fit",  ds.GREEN, ds.GREEN, "transparent", ds.GREEN),
                ("Partial Fit", ds.AMBER, ds.AMBER, "transparent", ds.AMBER),
                ("Remote",      ds.DYE,   ds.DYE,   "transparent", ds.DYE),
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
        f'<div style="background:{ds.THREAD};padding:11px 28px;font:600 13px Mono;letter-spacing:.12em;text-transform:uppercase;cursor:pointer;white-space:nowrap">Dispatch</div>'
        f'</div>'
    )
    body = (f'<div class="eyebrow">Component Foundations</div>'
            f'<div class="row jb" style="gap:60px">'
            f'<div class="col" style="flex:1;gap:28px">'
            f'<div><div class="lab" style="margin-bottom:12px">Buttons — zero border-radius</div>{btn_row}</div>'
            f'<div><div class="lab" style="margin-bottom:12px">Chips & Tags</div>{chip_row}</div>'
            f'<div><div class="lab" style="margin-bottom:12px">Form Inputs</div>{input_row}</div>'
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

    # ── 06.03  Fit Score Dial ────────────────────────────────────────────────
    scores = [(92,"Strong — Architecture match"),(74,"Partial — Mid-seniority gap"),(41,"Low — Domain mismatch")]
    dial_cells = ""
    for score, label in scores:
        col = ds.GREEN if score >= 75 else (ds.AMBER if score >= 50 else ds.ALARM)
        dial_cells += (f'<div style="text-align:center;padding:32px 20px;background:{ds.PAPER};flex:1">'
                       f'{ds.fit_dial(score, 180, ds.INK, col)}'
                       f'<div style="font:600 16px Plex;margin-top:16px">{label}</div>'
                       f'</div>')
    pillar_rows = ""
    for name, wt in [("Core Stack","30%"),("Projects","20%"),("Seniority","10%"),("Experience","10%"),
                     ("Domain","10%"),("Persona","5%"),("Education","5%"),("Work Mode","5%"),("Language","5%")]:
        pillar_rows += (f'<div style="display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid {ds.N100};font:400 14px Plex">'
                        f'<span>{name}</span><span style="font-family:Mono;font-weight:500;color:{ds.THREAD}">{wt}</span></div>')
    body = (f'<div class="eyebrow">Fit Score</div>'
            f'<div class="row jb" style="gap:60px">'
            f'<div class="col" style="flex:1">'
            f'<div class="h2" style="margin-bottom:8px">The dial is the product.</div>'
            f'<div class="lead thin" style="margin-bottom:28px">Every job card surfaces a half-moon fit gauge built from measuring-tape ticks. Colour shifts with score tier — COBALT for partial, GREEN for strong, CRIMSON for low.</div>'
            f'<div style="display:flex;gap:12px">{dial_cells}</div>'
            f'</div>'
            f'<div class="col" style="width:300px">'
            f'<div class="lab" style="margin-bottom:16px">Nine Pillars & Weights</div>'
            f'{pillar_rows}'
            f'</div></div>')
    out.append(ds.page(S, "Fit Score Dial", body, "light"))

    # ── 06.04  Radar Feed Card ───────────────────────────────────────────────
    def job_card(title, co, loc, score, tags, lang="en", w=440):
        is_ar = lang == "ar"
        col = ds.GREEN if score >= 75 else (ds.AMBER if score >= 50 else ds.ALARM)
        dir_ = "rtl" if is_ar else "ltr"
        chip_els = "".join(
            f'<div style="border:1.5px solid {ds.N300};padding:4px 10px;font:500 10px Mono;letter-spacing:.08em;text-transform:uppercase;color:{ds.N700}">{t}</div>'
            for t in tags)
        return (f'<div style="border:1.5px solid {ds.N300};padding:24px;background:{ds.PAPER};color:{ds.INK};width:{w}px;direction:{dir_}">'
                f'<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:14px">'
                f'<div>'
                f'<div style="font:600 18px {"PlexAr" if is_ar else "Plex"};margin-bottom:4px">{title}</div>'
                f'<div style="font:400 14px Mono;color:{ds.N500}">{co} · {loc}</div>'
                f'</div>'
                f'{ds.fit_dial(score, 72, ds.INK, col)}'
                f'</div>'
                f'<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px">{chip_els}</div>'
                f'<div style="display:flex;gap:10px">'
                f'<div style="flex:1;background:{ds.THREAD};padding:9px 0;font:600 11px Mono;letter-spacing:.12em;text-transform:uppercase;text-align:center;color:{ds.INK}">{"تقدم الآن" if is_ar else "Apply Now"}</div>'
                f'<div style="border:1.5px solid {ds.INK};padding:9px 20px;font:500 11px Mono;letter-spacing:.1em;text-transform:uppercase;text-align:center">{"حفظ" if is_ar else "Save"}</div>'
                f'</div></div>')
    en_card = job_card("Senior Product Designer","Noon","Cairo, Egypt",87,["Full-time","Cairo","UX","Figma","Strong Fit"])
    ar_card = job_card("مصمم منتج أول","نون","القاهرة، مصر",87,["دوام كامل","القاهرة","تجربة المستخدم","فيغما","توافق قوي"],"ar")
    body = (f'<div class="eyebrow">Radar Feed Card</div>'
            f'<div class="row jb" style="gap:60px">'
            f'<div class="col" style="flex:1">'
            f'<div class="h2" style="margin-bottom:28px">Every job is a card.<br>Every card scores the fit.</div>'
            f'<div style="display:flex;gap:24px;align-items:flex-start">'
            f'<div><div class="lab" style="margin-bottom:12px">English (LTR)</div>{en_card}</div>'
            f'<div><div class="lab" style="margin-bottom:12px">Arabic (RTL)</div>{ar_card}</div>'
            f'</div></div>'
            f'<div class="col" style="width:280px;gap:16px;justify-content:center">'
            f'<div class="lab">Card Anatomy</div>'
            + "".join(
                f'<div style="display:flex;gap:12px;align-items:flex-start">'
                f'<div style="width:20px;height:20px;background:{ds.THREAD};clip-path:polygon(0 0,100% 0,50% 100%);flex-shrink:0;margin-top:3px"></div>'
                f'<div style="font:400 14px Plex;line-height:1.4">{txt}</div>'
                f'</div>'
                for txt in [
                    "Job title + company + location (always above fold)",
                    "Fit dial — 72px, right-aligned, colour-coded by tier",
                    "Tag chips — skill, type, location, fit tier",
                    "CTA row — primary (THREAD) + secondary (outline)",
                    "Partial Fit shown in COBALT, not gold",
                ])
            + f'</div></div>')
    out.append(ds.page(S, "Radar Feed Card", body, "kraft"))

    # ── 06.05  CV Studio ─────────────────────────────────────────────────────
    studio_content = (
        _nav("Studio") +
        f'<div style="display:flex;height:572px">'
        f'<div style="width:200px;background:{ds.INK};padding:16px 0;flex-shrink:0">'
        + "".join(
            f'<div style="padding:9px 20px;font:{"600" if active else "400"} 12px Mono;letter-spacing:.1em;text-transform:uppercase;'
            f'color:{ds.CHALK if not active else ds.THREAD};opacity:{1 if active else .6}">{label}</div>'
            for label, active in [("Contact",False),("Summary",True),("Experience",False),("Projects",False),("Skills",False),("Education",False)]
        )
        + f'</div>'
        f'<div style="flex:1;background:{ds.PAPER};padding:28px 32px;overflow:hidden">'
        f'<div style="font:500 11px Mono;letter-spacing:.12em;text-transform:uppercase;margin-bottom:14px;color:{ds.N500}">Professional Summary</div>'
        f'<div style="border:1.5px solid {ds.THREAD};padding:16px;font:400 15px Plex;line-height:1.6;min-height:120px;background:white;position:relative">'
        f'Product designer with 7+ years building consumer fintech products across the MENA region.'
        f'<div style="position:absolute;bottom:8px;right:12px;font:400 11px Mono;color:{ds.N500}">212 / 500 chars</div>'
        f'</div>'
        f'<div style="display:flex;gap:10px;margin-top:12px">'
        f'<div style="background:{ds.THREAD};padding:8px 20px;font:600 11px Mono;letter-spacing:.12em;text-transform:uppercase;color:{ds.INK}">Regenerate ✦</div>'
        f'<div style="border:1.5px solid {ds.INK};padding:8px 20px;font:500 11px Mono;letter-spacing:.1em;text-transform:uppercase">Keep Draft</div>'
        f'</div>'
        f'<div style="margin-top:24px;padding:16px;background:{ds.CHALK};border-left:3px solid {ds.GREEN}">'
        f'<div style="font:500 11px Mono;letter-spacing:.12em;text-transform:uppercase;color:{ds.GREEN};margin-bottom:6px">Fit Analysis · 87</div>'
        f'<div style="font:400 14px Plex;line-height:1.5">Your summary addresses 6 of 7 key signals. Add "design systems" to reach top-tier phrasing.</div>'
        f'</div></div>'
        f'<div style="width:260px;background:{ds.N100};padding:16px;flex-shrink:0;overflow:hidden">'
        f'<div style="font:500 10px Mono;letter-spacing:.12em;text-transform:uppercase;margin-bottom:10px;opacity:.6">Live Preview</div>'
        f'<div style="background:white;padding:14px;font:400 12px Plex;line-height:1.5;transform:scale(.85);transform-origin:top left;width:280px">'
        f'<div style="font:700 16px Fraunces;margin-bottom:4px">Khalid Nasser</div>'
        f'<div style="font:400 10px Mono;color:{ds.N500};margin-bottom:8px">Senior Product Designer · Cairo</div>'
        f'<div style="height:1.5px;background:{ds.THREAD};margin-bottom:8px"></div>'
        f'<div style="font:400 11px Plex;line-height:1.5">Product designer with 7+ years building consumer fintech…</div>'
        f'</div></div>'
        f'</div>'
    )
    screen_w, screen_h = 1100, 624
    chrome = (f'<div style="background:{ds.N700};height:36px;display:flex;align-items:center;padding:0 14px;gap:8px">'
              f'<div style="width:11px;height:11px;border-radius:50%;background:#B3261E"></div>'
              f'<div style="width:11px;height:11px;border-radius:50%;background:#E8A317"></div>'
              f'<div style="width:11px;height:11px;border-radius:50%;background:#1E8A5A"></div>'
              f'<div style="flex:1;background:{ds.N900};height:20px;margin:0 20px;display:flex;align-items:center;padding:0 12px">'
              f'<span style="font:400 10px Mono;color:{ds.N300};letter-spacing:.06em">tailored.io/studio</span></div>'
              f'</div>')
    screen = (f'<div style="width:{screen_w}px;border:1.5px solid {ds.N300};box-shadow:0 24px 48px -16px rgba(20,17,15,.35)">'
              f'{chrome}<div style="background:{ds.PAPER};height:{screen_h}px;overflow:hidden">{studio_content}</div></div>')
    body = (f'<div class="eyebrow">CV Studio</div>'
            f'<div class="row jb" style="gap:48px">'
            f'<div class="col" style="width:280px;gap:16px;justify-content:center">'
            f'<div class="h2">Write once.<br>Tailor always.</div>'
            f'<div class="lead thin">Three-pane editor: sidebar navigation, AI-assisted draft area, and a live CV preview. ZINC background, INK chrome, THREAD active state.</div>'
            f'</div>'
            f'<div>{screen}</div></div>')
    out.append(ds.page(S, "CV Studio", body, "light"))

    # ── 06.06  Trial Gate Modal ──────────────────────────────────────────────
    plans = [
        ("Free",   "0",   "EGP", "2 credits / month", ds.N100,   ds.INK,   False),
        ("Starter","49",  "EGP", "5 credits / month",  ds.INK,    ds.CHALK, False),
        ("Hunter", "179", "EGP", "25 credits / month", ds.THREAD, ds.INK,   True),
        ("Sprint", "399", "EGP", "70 credits / month", ds.DYE,    ds.CHALK, False),
    ]
    plan_cards = ""
    for name, price, cur, creds, bg, fg, pop in plans:
        plan_cards += (f'<div style="background:{bg};padding:20px 16px;flex:1;position:relative;border:{"2px solid "+ds.THREAD if pop else "1.5px solid "+ds.N300}">'
                       + (f'<div style="position:absolute;top:-12px;left:50%;transform:translateX(-50%);background:{ds.THREAD};padding:3px 12px;font:600 10px Mono;letter-spacing:.12em;text-transform:uppercase;color:{ds.INK};white-space:nowrap">Popular</div>' if pop else "")
                       + f'<div style="font:600 14px Mono;color:{fg};margin-bottom:8px;text-transform:uppercase;letter-spacing:.1em">{name}</div>'
                       f'<div style="font:700 32px Fraunces;color:{fg};line-height:1">{price} <span style="font-size:14px;font-family:Mono;opacity:.7">{cur}</span></div>'
                       f'<div style="font:400 12px Plex;color:{fg};opacity:.7;margin-top:4px;margin-bottom:14px">{creds}</div>'
                       f'<div style="background:{fg};color:{bg};padding:8px 0;font:600 11px Mono;letter-spacing:.1em;text-transform:uppercase;text-align:center">{"Choose" if name!="Free" else "Current"}</div>'
                       f'</div>')
    modal = (f'<div style="background:rgba(20,17,15,.7);display:flex;align-items:center;justify-content:center;width:900px;height:520px">'
             f'<div style="background:{ds.CHALK};color:{ds.INK};width:720px;padding:40px;position:relative">'
             f'<div style="position:absolute;top:16px;right:16px;font:400 20px Mono;cursor:pointer;opacity:.4">✕</div>'
             f'<div style="font:500 11px Mono;letter-spacing:.14em;text-transform:uppercase;color:{ds.THREAD};margin-bottom:8px">Credits Exhausted</div>'
             f'<div style="font-family:Fraunces;font-weight:540;font-size:32px;line-height:1.1;margin-bottom:6px">Your 2 free credits<br>are spent.</div>'
             f'<div style="font:400 15px Plex;color:{ds.N500};margin-bottom:28px;line-height:1.5">Upgrade to keep tailoring. Cancel anytime.</div>'
             f'<div style="display:flex;gap:12px;margin-bottom:20px">{plan_cards}</div>'
             f'<div style="font:400 12px Plex;color:{ds.N500};text-align:center">All prices in EGP · VAT inclusive · Secure payment via Paymob</div>'
             f'</div></div>')
    body = (f'<div class="eyebrow">Trial Gate Modal</div>'
            f'<div class="row jb" style="gap:48px">'
            f'<div class="col" style="width:300px;gap:16px;justify-content:center">'
            f'<div class="h2">The upgrade moment.</div>'
            f'<div class="lead thin">Triggered when credits reach 0. Non-dismissable until a plan is chosen or ✕ is clicked.</div>'
            f'<div class="stitch" style="margin:8px 0"></div>'
            f'<div style="font:400 14px Plex;line-height:1.5">Background overlay: INK at 70% opacity. Modal background: ZINC. Pricing in EGP for Egypt; AED for UAE; SAR for KSA.</div>'
            f'</div>'
            f'<div>{modal}</div></div>')
    out.append(ds.page(S, "Trial Gate Modal", body, "dark"))

    # ── 06.07  Arabic RTL Screen ─────────────────────────────────────────────
    ar_nav = (f'<div style="height:52px;background:{ds.INK};border-bottom:1.5px solid rgba(236,234,229,.18);'
              f'display:flex;align-items:center;padding:0 28px;justify-content:space-between;direction:rtl">'
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
    def ar_job_card_mini(score, title, co):
        col = ds.GREEN if score >= 75 else (ds.AMBER if score >= 50 else ds.ALARM)
        return (f'<div style="direction:rtl;padding:16px;background:{ds.PAPER};color:{ds.INK};border:1.5px solid {ds.N300};margin-bottom:8px">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">'
                f'<div>'
                f'<div style="font:600 16px PlexAr">{title}</div>'
                f'<div style="font:400 12px Mono;color:{ds.N500}">{co}</div>'
                f'</div>'
                f'{ds.fit_dial(score, 56, ds.INK, col)}'
                f'</div>'
                f'<div style="display:flex;gap:8px">'
                f'<div style="flex:1;background:{ds.THREAD};padding:8px 0;font:600 12px PlexAr;text-align:center;color:{ds.INK}">تقدم الآن</div>'
                f'<div style="border:1.5px solid {ds.INK};padding:8px 16px;font:500 12px PlexAr;text-align:center;color:{ds.INK}">حفظ</div>'
                f'</div></div>')
    ar_screen = ar_nav + (f'<div style="padding:28px 32px;background:{ds.INK};height:572px">'
                          + ar_job_card_mini(87,"مصمم منتج أول","نون · القاهرة")
                          + ar_job_card_mini(74,"قائد تجربة المستخدم","كريم · دبي")
                          + ar_job_card_mini(41,"مدير تصميم","فوري · القاهرة")
                          + f'</div>')
    screen_ar = (f'<div style="width:900px;border:1.5px solid {ds.N300};box-shadow:0 24px 48px -16px rgba(20,17,15,.35)">'
                 f'<div style="background:{ds.N700};height:36px;display:flex;align-items:center;padding:0 14px;gap:8px">'
                 f'<div style="width:11px;height:11px;border-radius:50%;background:#B3261E"></div>'
                 f'<div style="width:11px;height:11px;border-radius:50%;background:#E8A317"></div>'
                 f'<div style="width:11px;height:11px;border-radius:50%;background:#1E8A5A"></div>'
                 f'<div style="flex:1;background:{ds.N900};height:20px;margin:0 20px;display:flex;align-items:center;padding:0 12px">'
                 f'<span style="font:400 10px Mono;color:{ds.N300};letter-spacing:.06em">tailored.io/radar (AR)</span></div></div>'
                 f'<div style="background:{ds.INK};height:624px;overflow:hidden">{ar_screen}</div></div>')
    body = (f'<div class="eyebrow">Arabic RTL Screen</div>'
            f'<div class="row jb" style="gap:48px">'
            f'<div class="col" style="width:300px;gap:16px;justify-content:center">'
            f'<div class="h2">عربي.<br>أولاً.</div>'
            f'<div class="lead thin">The Arabic interface is native RTL — not mirrored English. Navigation starts right. COBALT for partial fit reads differently in Arabic context: clinical and precise, not warm gold.</div>'
            f'<div style="font:400 14px PlexAr;direction:rtl;line-height:1.6;margin-top:12px;color:{ds.CHALK};opacity:.6">الواجهة بالعربية ليست ترجمة؛ هي تجربة مستقلة.</div>'
            f'</div>'
            f'<div>{screen_ar}</div></div>')
    out.append(ds.page(S, "Arabic RTL Screen", body, "dark"))

    # ── 06.08  Empty States & Errors ─────────────────────────────────────────
    def empty(icon_name, headline, sub, cta):
        return (f'<div style="background:{ds.PAPER};padding:36px 28px;flex:1;display:flex;flex-direction:column;align-items:center;text-align:center;gap:14px">'
                f'{ds.icon(icon_name, 48, ds.N300, ds.THREAD)}'
                f'<div style="font:600 16px Plex">{headline}</div>'
                f'<div style="font:400 13px Plex;color:{ds.N500};line-height:1.5;max-width:180px">{sub}</div>'
                f'<div style="background:{ds.THREAD};padding:8px 20px;font:600 11px Mono;letter-spacing:.12em;text-transform:uppercase;cursor:pointer;color:{ds.INK}">{cta}</div>'
                f'</div>')
    empties = [
        empty("radar",  "No jobs yet",       "Complete your profile to unlock your first fit scores.", "Finish Profile"),
        empty("cv",     "No CV uploaded",    "Upload a CV or fill out your profile to get started.",  "Upload CV"),
        empty("filter", "No matches found",  "Broaden your preferences or add more skills.",           "Edit Preferences"),
        empty("save",   "Nothing saved yet", "Save interesting jobs from the Radar to track them.",   "Open Radar"),
    ]
    err = (f'<div style="border-left:3px solid {ds.ALARM};padding:16px 20px;background:{ds.PAPER};margin-bottom:10px">'
           f'<div style="font:600 14px Plex;margin-bottom:4px">Something went wrong</div>'
           f'<div style="font:400 13px Plex;color:{ds.N500};margin-bottom:10px">We couldn\'t load your jobs. This is on us — not you.</div>'
           f'<div style="font:600 11px Mono;letter-spacing:.1em;text-transform:uppercase;color:{ds.THREAD};cursor:pointer">Try Again →</div>'
           f'</div>'
           f'<div style="border-left:3px solid {ds.AMBER};padding:16px 20px;background:{ds.PAPER}">'
           f'<div style="font:600 14px Plex;margin-bottom:4px">Credits running low</div>'
           f'<div style="font:400 13px Plex;color:{ds.N500};margin-bottom:10px">1 credit remaining. Upgrade to continue tailoring.</div>'
           f'<div style="font:600 11px Mono;letter-spacing:.1em;text-transform:uppercase;color:{ds.THREAD};cursor:pointer">Upgrade Plan →</div>'
           f'</div>')
    body = (f'<div class="eyebrow">Empty States & Errors</div>'
            f'<div class="h2" style="margin-bottom:28px">Silence is an opportunity.</div>'
            f'<div style="display:flex;gap:8px;margin-bottom:28px">{"".join(empties)}</div>'
            f'<div class="row jb" style="gap:48px">'
            f'<div style="flex:1"><div class="lab" style="margin-bottom:12px">Error & Warning States</div>{err}</div>'
            f'<div style="flex:1"><div class="lab" style="margin-bottom:12px">Rules</div>'
            + "".join(
                f'<div style="padding:10px 0;border-bottom:1px solid {ds.N100};font:400 14px Plex;line-height:1.5">{r}</div>'
                for r in [
                    "Every empty state includes exactly one primary CTA.",
                    "Error messages: first person plural (we/us), never passive voice.",
                    "Errors use CRIMSON left-border. Warnings use COBALT left-border.",
                    "Icons in empty states are N300 (muted) with THREAD notch accent.",
                ])
            + f'</div></div>')
    out.append(ds.page(S, "Empty States & Errors", body, "light"))

    return out
