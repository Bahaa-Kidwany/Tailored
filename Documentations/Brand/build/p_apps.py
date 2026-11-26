"""Chapter 07 — Applications  (p_apps.py)"""
import ds

S = "07 — Applications"


def pages():
    out = []

    # ── 07.01  Landing Page Hero ────────────────────────────────────────────
    # Simulated browser hero + layplan bg
    lay = ds.layplan(900, 680, seed=7, fills=["none", "none", f"{ds.CHALK}22"],
                     stroke=ds.CHALK, accent=f"{ds.CHALK}55", seam=True, labels=False, maxn=18)
    hero_content = (
        f'<div style="position:relative;width:900px;height:520px;background:{ds.INK};overflow:hidden">'
        f'<div style="position:absolute;top:0;right:0;bottom:0;width:900px;opacity:.18">{lay}</div>'
        f'<div style="position:relative;padding:60px 64px;height:100%">'
        f'<div style="margin-bottom:32px">{ds.lockup_h(ds.CHALK, 36, "knock")}</div>'
        f'<div style="font-family:Fraunces;font-weight:540;font-size:62px;line-height:.95;color:{ds.CHALK};margin-bottom:20px;letter-spacing:-.02em;font-variation-settings:\'SOFT\' 100,\'opsz\' 144">'
        f'your cv,<br>tailored to<br>every job.</div>'
        f'<div style="font:400 18px Plex;color:{ds.CHALK};opacity:.7;margin-bottom:28px;max-width:420px;line-height:1.5">'
        f'AI-powered fit scoring and CV tailoring for job seekers in Egypt and the Gulf.</div>'
        f'<div style="display:flex;gap:12px;align-items:center">'
        f'<div style="background:{ds.THREAD};padding:14px 36px;font:600 14px Mono;letter-spacing:.12em;text-transform:uppercase;cursor:pointer;border-radius:0 12px 0 12px;color:{ds.INK}">Start Free — 2 Credits</div>'
        f'<div style="font:400 14px Plex;color:{ds.CHALK};opacity:.6">No credit card needed</div>'
        f'</div>'
        f'</div>'
        f'<div style="position:absolute;bottom:40px;right:60px;text-align:right">'
        f'{ds.fit_dial(87, 180, ds.CHALK, ds.THREAD)}'
        f'</div>'
        f'</div>'
    )
    body = (f'<div class="eyebrow">Applications</div>'
            f'<div class="row jb" style="gap:60px">'
            f'<div class="col" style="width:280px;gap:16px;justify-content:center">'
            f'<div class="h2">Landing Page<br>Hero.</div>'
            f'<div class="lead thin">Dark INK field. Layplan pattern at 18% opacity. Fraunces heading. Single THREAD CTA.</div>'
            f'<div class="stitch" style="margin:8px 0"></div>'
            f'<div style="font:400 14px Plex;line-height:1.5">The hero communicates product value in under four seconds. No imagery. No stock photos. The pattern and the dial are the only decoration.</div>'
            f'</div>'
            f'<div style="border:1.5px solid {ds.N300};box-shadow:0 24px 48px -16px rgba(26,20,18,.35);border-radius:0 40px 0 0;overflow:hidden">{hero_content}</div>'
            f'</div>')
    out.append(ds.page(S, "Landing Page Hero", body, "dark"))

    # ── 07.02  Social Media Covers ─────────────────────────────────────────
    # LinkedIn banner 1584×396 → scaled 760×190
    # Instagram square 1080×1080 → scaled 300×300
    li_bg = ds.swatch_pat("notch", 760, 190, ds.CHALK, ds.INK, .08)
    li = (f'<div style="position:relative;width:760px;height:190px;background:{ds.INK};overflow:hidden;border-radius:0 44px 0 0">'
          f'<div style="position:absolute;top:0;left:0">{li_bg}</div>'
          f'<div style="position:relative;display:flex;align-items:center;height:100%;padding:0 48px;justify-content:space-between">'
          f'{ds.lockup_bi(ds.CHALK, 48, "knock")}'
          f'<div style="text-align:right">'
          f'<div style="font:400 16px Fraunces;color:{ds.CHALK};font-style:italic;line-height:1.3;font-variation-settings:\'SOFT\' 100,\'WONK\' 1,\'opsz\' 48">your cv, tailored<br>to every job.</div>'
          f'<div style="font:500 11px Mono;letter-spacing:.14em;text-transform:uppercase;color:{ds.THREAD};margin-top:8px">tailored.io</div>'
          f'</div>'
          f'</div>'
          f'</div>')

    ig_lay = ds.layplan(300, 300, seed=12, fills=["none"], stroke=ds.CHALK, accent=f"{ds.CHALK}44", seam=False, labels=False, maxn=8)
    ig = (f'<div style="position:relative;width:300px;height:300px;background:{ds.THREAD};overflow:hidden;border-radius:0 56px 0 0">'
          f'<div style="position:absolute;top:0;left:0;opacity:.15">{ig_lay}</div>'
          f'<div style="position:relative;display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;gap:16px">'
          f'{ds.lockup_stack(ds.INK, 80, "solid")}'
          f'<div style="font:500 11px Mono;letter-spacing:.14em;text-transform:uppercase;color:{ds.INK};opacity:.7">tailored.io</div>'
          f'</div>'
          f'</div>')

    # Story 1080×1920 → 180×320
    st_lay = ds.layplan(180, 320, seed=5, fills=["none"], stroke=ds.CHALK, accent=f"{ds.CHALK}33", seam=False, labels=False, maxn=6)
    story = (f'<div style="position:relative;width:180px;height:320px;background:{ds.INK};overflow:hidden;border-radius:0 36px 0 0">'
             f'<div style="position:absolute;top:0;left:0;opacity:.14">{st_lay}</div>'
             f'<div style="position:relative;display:flex;flex-direction:column;align-items:center;justify-content:space-between;height:100%;padding:32px 20px">'
             f'{ds.lockup_stack(ds.CHALK, 48, "knock")}'
             f'<div style="text-align:center">'
             f'<div style="font-family:Fraunces;font-weight:540;font-size:22px;color:{ds.CHALK};line-height:1.1;font-variation-settings:\'SOFT\' 100,\'opsz\' 48;margin-bottom:10px">your cv,<br>tailored.</div>'
             f'<div style="background:{ds.THREAD};padding:8px 20px;font:600 10px Mono;letter-spacing:.12em;text-transform:uppercase;color:{ds.INK}">Start Free</div>'
             f'</div>'
             f'<div style="font:500 10px Mono;letter-spacing:.12em;text-transform:uppercase;color:{ds.CHALK};opacity:.5">tailored.io</div>'
             f'</div>'
             f'</div>')

    body = (f'<div class="eyebrow">Social Media</div>'
            f'<div class="h2" style="margin-bottom:36px">Consistent across every feed.</div>'
            f'<div class="col" style="gap:24px">'
            f'<div>'
            f'<div class="lab" style="margin-bottom:10px">LinkedIn Banner — 1584 × 396 px</div>'
            f'{li}'
            f'</div>'
            f'<div style="display:flex;gap:24px;align-items:flex-end">'
            f'<div>'
            f'<div class="lab" style="margin-bottom:10px">Instagram Square — 1080 × 1080 px</div>'
            f'{ig}'
            f'</div>'
            f'<div>'
            f'<div class="lab" style="margin-bottom:10px">Instagram Story — 1080 × 1920 px</div>'
            f'{story}'
            f'</div>'
            f'<div style="flex:1;padding-left:32px;align-self:center">'
            f'<div class="lab" style="margin-bottom:12px">Rules</div>'
            + "".join(
                f'<div style="padding:9px 0;border-bottom:1px solid {ds.N100};font:400 14px Plex;line-height:1.4">{r}</div>'
                for r in [
                    "Background: always INK or THREAD. Never CHALK alone on social — too low contrast in dark-mode feeds.",
                    "Pattern overlay: notch or layplan at 8–18% opacity only.",
                    "Tagline in italic Fraunces. URL in uppercase Mono.",
                    "No photography in social frames — the brand is not a lifestyle brand.",
                ]
            )
            + f'</div>'
            f'</div>'
            f'</div>')
    out.append(ds.page(S, "Social Media Covers", body, "light"))

    # ── 07.03  Business Card ───────────────────────────────────────────────
    card_w, card_h = 420, 240
    # Front: INK
    front_bg = ds.swatch_pat("notch", card_w, card_h, ds.CHALK, ds.INK, .07)
    front = (f'<div style="position:relative;width:{card_w}px;height:{card_h}px;background:{ds.INK};overflow:hidden;border-radius:0 36px 0 0">'
             f'<div style="position:absolute;top:0;left:0">{front_bg}</div>'
             f'<div style="position:relative;padding:28px 32px;height:100%;display:flex;flex-direction:column;justify-content:space-between">'
             f'{ds.lockup_h(ds.CHALK, 32, "knock")}'
             f'<div>'
             f'<div style="font:600 17px Plex;color:{ds.CHALK};margin-bottom:4px">Khalid Nasser</div>'
             f'<div style="font:400 13px Mono;color:{ds.CHALK};opacity:.6;letter-spacing:.06em">Senior Product Designer</div>'
             f'</div>'
             f'<div>'
             f'<div style="font:400 12px Mono;color:{ds.CHALK};opacity:.5;letter-spacing:.06em">khalid@tailored.io</div>'
             f'<div style="font:400 12px Mono;color:{ds.CHALK};opacity:.5;letter-spacing:.06em">tailored.io</div>'
             f'</div>'
             f'<div style="position:absolute;bottom:0;right:0;width:0;height:0;border-style:solid;border-width:0 0 36px 36px;border-color:transparent transparent {ds.THREAD} transparent"></div>'
             f'</div>'
             f'</div>')
    # Back: CHALK with Arabic
    back_bg = ds.swatch_pat("cross", card_w, card_h, ds.INK, ds.CHALK, .05)
    back = (f'<div style="position:relative;width:{card_w}px;height:{card_h}px;background:{ds.CHALK};overflow:hidden;border-radius:36px 0 0 0">'
            f'<div style="position:absolute;top:0;left:0">{back_bg}</div>'
            f'<div style="position:relative;padding:28px 32px;height:100%;display:flex;flex-direction:column;justify-content:space-between;direction:rtl">'
            f'{ds.lockup_ar_h(ds.INK, 32, "knock")}'
            f'<div>'
            f'<div style="font:600 17px PlexAr;color:{ds.INK};margin-bottom:4px">خالد ناصر</div>'
            f'<div style="font:400 13px PlexAr;color:{ds.INK};opacity:.6">مصمم منتج أول</div>'
            f'</div>'
            f'<div>'
            f'<div style="font:400 12px Mono;color:{ds.INK};opacity:.5;letter-spacing:.06em">khalid@tailored.io</div>'
            f'<div style="font:400 12px Mono;color:{ds.INK};opacity:.5;letter-spacing:.06em">tailored.io</div>'
            f'</div>'
            f'<div style="position:absolute;bottom:0;left:0;width:0;height:0;border-style:solid;border-width:36px 0 0 36px;border-color:transparent transparent transparent {ds.THREAD}"></div>'
            f'</div>'
            f'</div>')
    body = (f'<div class="eyebrow">Business Card</div>'
            f'<div class="row jb" style="gap:60px">'
            f'<div class="col" style="flex:1;gap:28px">'
            f'<div class="h2">85 × 55 mm.<br>Both sides speak.</div>'
            f'<div style="display:flex;gap:24px">'
            f'<div><div class="lab" style="margin-bottom:10px">Front — INK</div>'
            f'<div style="box-shadow:0 16px 32px -10px rgba(26,20,18,.4)">{front}</div></div>'
            f'<div><div class="lab" style="margin-bottom:10px">Back — CHALK / Arabic</div>'
            f'<div style="box-shadow:0 16px 32px -10px rgba(26,20,18,.2)">{back}</div></div>'
            f'</div>'
            f'</div>'
            f'<div class="col" style="width:300px;gap:12px;justify-content:center">'
            f'<div class="lab">Specs</div>'
            + "".join(
                f'<div style="display:flex;justify-content:space-between;padding:9px 0;border-bottom:1px solid {ds.N100};font:400 14px Plex">'
                f'<span style="opacity:.7">{k}</span><span style="font-family:Mono;font-size:13px">{v}</span></div>'
                for k, v in [
                    ("Size", "85 × 55 mm"),
                    ("Bleed", "3 mm all sides"),
                    ("Print", "400 gsm, soft-touch"),
                    ("Finish", "Spot UV on THREAD corner"),
                    ("Front bg", "INK #1A1412"),
                    ("Back bg", "CHALK #E5E0DA"),
                    ("Corner notch", "THREAD cut, 10mm"),
                    ("Typeface EN", "Fraunces + Mono"),
                    ("Typeface AR", "IBM Plex Arabic"),
                ]
            )
            + f'</div></div>')
    out.append(ds.page(S, "Business Card", body, "paper"))

    # ── 07.04  CV Document Header ───────────────────────────────────────────
    cv_w = 1100
    cv_header = (
        f'<div style="background:{ds.INK};width:{cv_w}px;padding:28px 48px;display:flex;justify-content:space-between;align-items:flex-end">'
        f'<div>'
        f'{ds.lockup_h(ds.CHALK, 28, "knock")}'
        f'</div>'
        f'<div style="text-align:right">'
        f'<div style="font:700 24px Fraunces;color:{ds.CHALK};letter-spacing:-.01em">Khalid Nasser</div>'
        f'<div style="font:400 13px Mono;color:{ds.CHALK};opacity:.5;letter-spacing:.08em;margin-top:4px">Senior Product Designer · Cairo</div>'
        f'</div>'
        f'</div>'
        f'<div style="background:{ds.THREAD};width:{cv_w}px;height:4px"></div>'
        f'<div style="background:{ds.PAPER};width:{cv_w}px;padding:28px 48px 20px">'
        f'<div style="display:flex;gap:40px;font:400 13px Mono;color:{ds.N500};letter-spacing:.06em">'
        f'<span>khalid@tailored.io</span><span>+20 100 000 0000</span><span>tailored.io/khalid</span><span>Cairo, Egypt</span>'
        f'</div>'
        f'</div>'
    )
    cv_body = (
        f'<div style="background:{ds.PAPER};width:{cv_w}px;padding:0 48px 28px">'
        f'<div style="display:flex;gap:40px">'
        f'<div style="flex:1">'
        f'<div style="font:500 11px Mono;letter-spacing:.14em;text-transform:uppercase;color:{ds.THREAD};margin-bottom:8px;margin-top:24px">Summary</div>'
        f'<div style="font:400 14px Plex;line-height:1.6">Product designer with 7+ years building consumer fintech products across the MENA region, with deep expertise in research-led design systems and cross-functional delivery at scale.</div>'
        f'<div style="font:500 11px Mono;letter-spacing:.14em;text-transform:uppercase;color:{ds.THREAD};margin-bottom:8px;margin-top:24px">Experience</div>'
        f'<div style="margin-bottom:14px">'
        f'<div style="font:600 15px Plex">Senior Product Designer — Noon</div>'
        f'<div style="font:400 12px Mono;color:{ds.N500}">2021 – Present · Cairo</div>'
        f'<div style="font:400 13px Plex;line-height:1.5;margin-top:4px">Led redesign of the checkout flow reducing drop-off by 23%. Built the design system adopted across 4 product squads.</div>'
        f'</div>'
        f'</div>'
        f'<div style="width:220px;padding-top:24px">'
        f'<div style="font:500 11px Mono;letter-spacing:.14em;text-transform:uppercase;color:{ds.THREAD};margin-bottom:8px">Skills</div>'
        + "".join(
            f'<div style="font:400 13px Plex;padding:5px 0;border-bottom:1px solid {ds.N100}">{sk}</div>'
            for sk in ["Figma","Design Systems","User Research","Prototyping","Framer","SQL basics"]
        )
        + f'<div style="font:500 11px Mono;letter-spacing:.14em;text-transform:uppercase;color:{ds.THREAD};margin-top:16px;margin-bottom:8px">Languages</div>'
        f'<div style="font:400 13px Plex;padding:5px 0;border-bottom:1px solid {ds.N100}">Arabic — Native</div>'
        f'<div style="font:400 13px Plex;padding:5px 0;border-bottom:1px solid {ds.N100}">English — Fluent</div>'
        f'</div>'
        f'</div>'
        f'</div>'
    )
    cv_footer = (
        f'<div style="background:{ds.INK};width:{cv_w}px;padding:12px 48px;display:flex;justify-content:space-between;align-items:center">'
        f'<div style="font:400 11px Mono;color:{ds.CHALK};opacity:.4;letter-spacing:.06em">Generated with Tailored · tailored.io</div>'
        f'<div>{ds.mk(ds.CHALK, 20, "knock")}</div>'
        f'</div>'
    )
    cv_doc = f'<div style="border:1.5px solid {ds.N300};box-shadow:0 24px 48px -16px rgba(26,20,18,.3)">{cv_header}{cv_body}{cv_footer}</div>'
    body = (f'<div class="eyebrow">CV Document</div>'
            f'<div class="row jb" style="gap:48px">'
            f'<div class="col" style="width:260px;gap:16px;justify-content:center">'
            f'<div class="h2">The brand extends<br>into the output.</div>'
            f'<div class="lead thin">Every CV generated by Tailored carries the brand. The header is INK, the THREAD rule marks the break, and the footer is signed.</div>'
            f'<div class="stitch" style="margin:8px 0"></div>'
            f'<div style="font:400 14px Plex;line-height:1.5">The CV itself is designed in a clean, ATS-safe layout. The branding lives in the envelope — not in the content.</div>'
            f'</div>'
            f'<div>{cv_doc}</div>'
            f'</div>')
    out.append(ds.page(S, "CV Document", body, "light"))

    # ── 07.05  Email Signature ─────────────────────────────────────────────
    sig_w = 500
    sig = (f'<div style="border:1.5px solid {ds.N300};width:{sig_w}px;font-family:Arial,sans-serif;background:{ds.PAPER}">'
           f'<div style="background:{ds.INK};padding:16px 20px;display:flex;align-items:center;gap:16px">'
           f'{ds.lockup_h(ds.CHALK, 24, "knock")}'
           f'<div style="width:1.5px;height:28px;background:{ds.CHALK};opacity:.2"></div>'
           f'<div style="font:600 14px Arial;color:{ds.CHALK}">Khalid Nasser</div>'
           f'</div>'
           f'<div style="padding:16px 20px;border-top:3px solid {ds.THREAD}">'
           f'<div style="font:400 13px Arial;color:{ds.N500};margin-bottom:4px">Senior Product Designer</div>'
           f'<div style="font:400 12px Arial;color:{ds.N700};margin-bottom:12px">khalid@tailored.io · +20 100 000 0000</div>'
           f'<div style="display:flex;gap:12px">'
           f'<a style="font:600 11px Mono;letter-spacing:.1em;text-transform:uppercase;color:{ds.INK};text-decoration:none;border-bottom:1.5px solid {ds.THREAD}">tailored.io</a>'
           f'<span style="color:{ds.N300}">|</span>'
           f'<a style="font:600 11px Mono;letter-spacing:.1em;text-transform:uppercase;color:{ds.INK};text-decoration:none">LinkedIn</a>'
           f'</div>'
           f'</div>'
           f'</div>')
    letterhead_w = 760
    letterhead = (
        f'<div style="border:1.5px solid {ds.N300};width:{letterhead_w}px;background:white">'
        f'<div style="background:{ds.INK};padding:24px 40px;display:flex;justify-content:space-between;align-items:center">'
        f'{ds.lockup_h(ds.CHALK, 32, "knock")}'
        f'<div style="text-align:right;font:400 12px Mono;color:{ds.CHALK};opacity:.5;letter-spacing:.06em;line-height:1.6">'
        f'tailored.io<br>hello@tailored.io'
        f'</div>'
        f'</div>'
        f'<div style="background:{ds.THREAD};height:4px"></div>'
        f'<div style="padding:32px 40px 24px;min-height:260px">'
        f'<div style="font:400 12px Mono;color:{ds.N500};margin-bottom:20px;letter-spacing:.04em">19 November 2026</div>'
        f'<div style="font:400 15px Plex;line-height:1.6;max-width:580px">'
        f'Dear Hiring Manager,<br><br>'
        f'I am writing to express my interest in the Senior Product Designer role at your company. '
        f'With seven years of experience in consumer-facing fintech products across the MENA region…'
        f'</div>'
        f'</div>'
        f'<div style="background:{ds.N100};padding:12px 40px;display:flex;justify-content:space-between;align-items:center;border-top:1.5px solid {ds.N300}">'
        f'<div style="font:400 11px Mono;color:{ds.N500};letter-spacing:.06em">Generated with Tailored · tailored.io</div>'
        f'{ds.mk(ds.N500, 18, "solid")}'
        f'</div>'
        f'</div>'
    )
    body = (f'<div class="eyebrow">Stationery</div>'
            f'<div class="h2" style="margin-bottom:36px">Every touchpoint, branded.</div>'
            f'<div class="row jb" style="gap:48px">'
            f'<div class="col" style="gap:12px">'
            f'<div class="lab" style="margin-bottom:8px">Email Signature</div>'
            f'{sig}'
            f'<div class="body thin" style="max-width:{sig_w}px;margin-top:8px">INK header with THREAD rule. No imagery — just type, structure, and the logo. Compatible with Gmail / Outlook.</div>'
            f'</div>'
            f'<div class="col" style="gap:12px">'
            f'<div class="lab" style="margin-bottom:8px">Cover Letter / Letterhead</div>'
            f'{letterhead}'
            f'</div>'
            f'</div>')
    out.append(ds.page(S, "Stationery", body, "light"))

    # ── 07.06  Merchandise ─────────────────────────────────────────────────
    # Tote bag illustration (simplified)
    tote_w, tote_h = 340, 400
    # Bag shape
    bag_body = (
        f'<rect x="30" y="120" width="280" height="260" fill="{ds.KRAFT}" stroke="{ds.INK}" stroke-width="2.5" stroke-linejoin="round"/>'
        f'<path d="M80,120 Q80,60 170,50 Q260,60 260,120" fill="none" stroke="{ds.INK}" stroke-width="2.5" stroke-linejoin="round"/>'
        f'<path d="M100,120 Q100,70 170,60 Q240,70 240,120" fill="none" stroke="{ds.INK}" stroke-width="2" stroke-dasharray="6 5" opacity=".5"/>'
    )
    # Pattern on bag - layplan
    lay_bag = ds.layplan(260, 180, seed=3, fills=["none"], stroke=ds.INK, accent=f"{ds.THREAD}66",
                         seam=True, labels=False, maxn=12, scale_range=(.4, .9))
    # Logo on bag
    tote_svg = (
        f'<svg width="{tote_w}" height="{tote_h}" viewBox="0 0 {tote_w} {tote_h}">'
        f'{bag_body}'
        f'<foreignObject x="35" y="140" width="260" height="180" opacity=".45">'
        f'<div xmlns="http://www.w3.org/1999/xhtml">{lay_bag}</div>'
        f'</foreignObject>'
        f'</svg>'
    )
    # T-shirt mockup (simplified rectangular)
    shirt_w, shirt_h = 320, 360
    shirt_svg = (
        f'<svg width="{shirt_w}" height="{shirt_h}" viewBox="0 0 {shirt_w} {shirt_h}">'
        f'<path d="M60,40 L0,100 L60,120 L60,340 L260,340 L260,120 L320,100 L260,40 Q220,20 190,50 Q160,70 130,50 Q100,20 60,40Z" '
        f'fill="{ds.INK}" stroke="{ds.INK}" stroke-width="1.5" stroke-linejoin="round"/>'
        f'<foreignObject x="90" y="160" width="140" height="80">'
        f'<div xmlns="http://www.w3.org/1999/xhtml" style="display:flex;flex-direction:column;align-items:center;gap:8px">'
        f'{ds.lockup_stack(ds.CHALK, 48, "knock")}'
        f'</div>'
        f'</foreignObject>'
        f'</svg>'
    )
    sticker = (
        f'<div style="width:160px;height:160px;background:{ds.THREAD};display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px">'
        f'{ds.lockup_stack(ds.INK, 56, "solid")}'
        f'<div style="font:500 10px Mono;letter-spacing:.14em;text-transform:uppercase;color:{ds.INK};opacity:.6">tailored.io</div>'
        f'</div>'
    )
    body = (f'<div class="eyebrow">Merchandise</div>'
            f'<div class="h2" style="margin-bottom:36px">The brand off-screen.</div>'
            f'<div style="display:flex;gap:40px;align-items:flex-end">'
            f'<div><div class="lab" style="margin-bottom:10px">Tote Bag — KRAFT</div>'
            f'<div style="border:1.5px solid {ds.N300};padding:12px;background:{ds.PAPER}">{tote_svg}</div></div>'
            f'<div><div class="lab" style="margin-bottom:10px">T-Shirt — INK</div>'
            f'<div style="border:1.5px solid {ds.N300};padding:12px;background:{ds.CHALK}">{shirt_svg}</div></div>'
            f'<div class="col" style="gap:16px">'
            f'<div class="lab" style="margin-bottom:4px">Square Sticker — THREAD</div>'
            f'{sticker}'
            f'<div class="body thin" style="max-width:200px;margin-top:8px">Square, no die-cut. The shape is the brand. The notch lives in the logo — not in the sticker outline.</div>'
            f'</div>'
            f'<div class="col" style="width:280px;gap:10px;align-self:center">'
            f'<div class="lab">Merch Rules</div>'
            + "".join(
                f'<div style="padding:8px 0;border-bottom:1px solid {ds.N100};font:400 14px Plex;line-height:1.4">{r}</div>'
                for r in [
                    "Tote: KRAFT base, layplan pattern at 45% opacity, INK logo centred.",
                    "T-shirt: INK base only. Stacked lockup on chest in CHALK.",
                    "Sticker: THREAD background, INK stacked lockup. No photography.",
                    "Embroidery: stacked lockup in CHALK thread on INK fabric.",
                    "No logo on MIST, GREEN, AMBER, or ALARM merchandise — semantic colours only in product.",
                ]
            )
            + f'</div>'
            f'</div>')
    out.append(ds.page(S, "Merchandise", body, "kraft"))

    # ── 07.07  Brand Token Export ───────────────────────────────────────────
    # CSS tokens + file structure
    css_tokens = """:root {
  /* Primary */
  --ink:    #1A1412;
  --chalk:  #E5E0DA;
  --thread: #E9453F;

  /* Extended */
  --kraft:  #CDAE88;
  --dye:    #23325E;
  --mist:   #C7D2DF;

  /* Semantic */
  --green:  #1E8A5A;   /* strong fit  */
  --amber:  #E39A1B;   /* partial fit */
  --alarm:  #8F1D2C;   /* low fit     */
  --paper:  #F5F3EF;   /* reading bg  */

  /* Neutral scale */
  --n900:   #1A1412;
  --n700:   #3A322D;
  --n500:   #7A7068;
  --n300:   #CBC3BA;
  --n100:   #D9D3CB;

  /* Typography */
  --font-display: 'Fraunces', serif;
  --font-body:    'Plex', sans-serif;
  --font-ar:      'PlexAr', sans-serif;
  --font-mono:    'Mono', monospace;

  /* Spacing */
  --sp-4:   4px;    --sp-8:  8px;
  --sp-12:  12px;   --sp-16: 16px;
  --sp-24:  24px;   --sp-32: 32px;
  --sp-48:  48px;   --sp-64: 64px;
  --sp-96:  96px;
}"""
    file_tree = [
        ("Brand/", "root"),
        ("  build/", "dir"),
        ("    stitch.py", "file"),
        ("    stitch_defs.py", "file"),
        ("    arabic.py", "file"),
        ("    ds.py", "file"),
        ("    build.py", "file"),
        ("    p_strategy.py", "ch"),
        ("    p_identity.py", "ch"),
        ("    p_type.py", "ch"),
        ("    p_system.py", "ch"),
        ("    p_ui.py", "ch"),
        ("    p_apps.py", "ch"),
        ("  fonts/", "dir"),
        ("    Fraunces.ttf", "file"),
        ("    PlexSans.ttf", "file"),
        ("    PlexSansArabic-*.ttf", "file"),
        ("    PlexMono-*.ttf", "file"),
        ("    ReemKufi.ttf", "file"),
        ("  Tailored_Brand_Book.pdf", "out"),
    ]
    tree_items = ""
    colors = {"root": ds.THREAD, "dir": ds.AMBER, "ch": ds.GREEN, "out": ds.MIST, "file": ds.N500}
    for name, kind in file_tree:
        col = colors.get(kind, ds.N500)
        tree_items += f'<div style="font:400 13px Mono;color:{col};padding:2px 0;letter-spacing:.04em">{name}</div>'
    body = (f'<div class="eyebrow">Handoff</div>'
            f'<div class="row jb" style="gap:48px">'
            f'<div class="col" style="flex:1">'
            f'<div class="h2" style="margin-bottom:20px">Token Export<br>& File Structure.</div>'
            f'<div class="lead thin" style="margin-bottom:20px">Reference the CSS custom properties in every product, document, and motion file. Never hardcode hex.</div>'
            f'<div style="background:{ds.INK};color:{ds.CHALK};padding:24px 28px;font:400 12px Mono;line-height:1.9;white-space:pre;overflow:auto">{css_tokens}</div>'
            f'</div>'
            f'<div class="col" style="width:340px">'
            f'<div class="lab" style="margin-bottom:16px">File Structure</div>'
            f'<div style="background:{ds.INK};padding:20px 24px;min-height:400px">{tree_items}</div>'
            f'<div style="margin-top:16px;font:400 13px Plex;line-height:1.5;color:{ds.N700}">'
            f'All brand assets are generated by running <span style="font-family:Mono;color:{ds.THREAD}">python build.py</span> in the <span style="font-family:Mono">build/</span> directory. No design tools required.</div>'
            f'</div>'
            f'</div>')
    out.append(ds.page(S, "Token Export", body, "dark"))

    # ── 07.08  Rollout Roadmap ──────────────────────────────────────────────
    phases = [
        ("Phase 0", "Now",         ds.THREAD, [
            "Brand book v1.0 published (this document)",
            "Design tokens committed to repo",
            "Tailored Stitch glyph engine locked",
        ]),
        ("Phase 1", "Q1 2027",     ds.DYE, [
            "Landing page live at tailored.io",
            "Social media profiles launched (LinkedIn, Instagram, X)",
            "Business card print run — 500 units",
            "Arabic brand assets finalised",
        ]),
        ("Phase 2", "Q2 2027",     ds.INK, [
            "Product beta launch (Radar + Studio)",
            "Onboarding flow live for Egypt & UAE",
            "Pricing pages EN + AR",
            "First merchandise batch (tote + sticker)",
        ]),
        ("Phase 3", "Q3 2027",     ds.N700, [
            "Saudi Arabia localisation",
            "Brand motion guidelines (Lottie components)",
            "Brand book v2.0 — updated with product learnings",
        ]),
    ]
    phase_els = ""
    for ph, when, col, items in phases:
        fg = ds.CHALK if ds.lum(col) < 0.2 else ds.INK
        items_html = "".join(
            f'<div style="padding:7px 0;border-bottom:1px solid rgba(229,224,218,.15);font:400 13px Plex;line-height:1.4;color:{fg};opacity:.85">{it}</div>'
            for it in items
        )
        phase_els += (f'<div style="background:{col};padding:28px 24px;flex:1">'
                      f'<div style="font:500 11px Mono;letter-spacing:.14em;text-transform:uppercase;color:{fg};opacity:.6;margin-bottom:4px">{when}</div>'
                      f'<div style="font:700 20px Plex;color:{fg};margin-bottom:16px">{ph}</div>'
                      f'{items_html}'
                      f'</div>')
    body = (f'<div class="eyebrow">Rollout Roadmap</div>'
            f'<div class="h2" style="margin-bottom:36px">The brand is a living system.</div>'
            f'<div style="display:flex;gap:8px;margin-bottom:32px">{phase_els}</div>'
            f'<div class="row jb" style="gap:48px">'
            f'<div style="flex:1;font:400 15px Plex;line-height:1.6">'
            f'This roadmap is not a waterfall — phases can overlap. The constraint is <em>consistency</em>: every new touchpoint must reference the tokens, never introduce new colours, typefaces, or shapes without a brand book update.'
            f'</div>'
            f'<div style="flex:1;font:400 15px Plex;line-height:1.6">'
            f'Brand book versions are tied to major product milestones. Version 2.0 will incorporate learnings from live user interactions, particularly around the Arabic experience and the fit-score visualisation at smaller screen sizes.'
            f'</div>'
            f'</div>')
    out.append(ds.page(S, "Rollout Roadmap", body, "paper"))

    # ── 07.09  Brand Closing Page ───────────────────────────────────────────
    lay_close = ds.layplan(1600, 900, seed=99, fills=["none"], stroke=ds.CHALK,
                           accent=f"{ds.CHALK}33", seam=True, labels=False, maxn=28, scale_range=(.6, 1.8))
    closing_body = (
        f'<div style="position:absolute;top:0;left:0;right:0;bottom:0;opacity:.12">{lay_close}</div>'
        f'<div style="position:relative;display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;text-align:center;gap:32px">'
        f'{ds.lockup_bi(ds.CHALK, 80, "knock")}'
        f'<div style="width:120px;height:2px;background:{ds.THREAD}"></div>'
        f'<div style="font-family:Fraunces;font-weight:540;font-size:52px;color:{ds.CHALK};line-height:1.05;'
        f'font-variation-settings:\'SOFT\' 100,\'opsz\' 96;letter-spacing:-.02em">'
        f'precision-fitted<br>for every job.</div>'
        f'<div style="font:400 20px Plex;color:{ds.CHALK};opacity:.5;letter-spacing:.04em">tailored.io</div>'
        f'<div style="font:500 11px Mono;letter-spacing:.18em;text-transform:uppercase;color:{ds.CHALK};opacity:.35;margin-top:12px">Brand Book 1.2 · November 2026</div>'
        f'</div>'
    )
    out.append(ds.page(S, "End", closing_body, "dark", bleed=True, num=False, hdr=False))

    return out
