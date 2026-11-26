from ds import *


def pages():
    P = []

    # 01 COVER ---------------------------------------------------------------
    lp = layplan(1000, 900, seed=11, stroke=CHALK, accent=THREAD, scale_range=(.9, 1.7), fills=['none'], txt=CHALK, margin=14)
    P.append(page("", "", f'''
      <div class="abs" style="right:-60px;top:0;opacity:.28">{lp}</div>
      <div class="abs" style="left:0;top:0;opacity:.95">{sweep(1600, 700, THREAD, 5, 3, 16)}</div>
      <div class="abs" style="right:150px;bottom:90px;transform:rotate(-8deg)">{fcurve(430, CHALK, THREAD)}</div>
      <div class="abs" style="left:96px;top:90px">{lockup_h(CHALK, 70, 'thread')}</div>
      <div class="abs" style="left:96px;top:300px;width:900px">
        <div class="eyebrow" style="color:var(--chalk)">Brand Book &middot; Version 1.2 &middot; 2026</div>
        <div class="display" style="font-size:150px;line-height:.88">Made to<br><em style="color:var(--thread)">measure.</em></div>
      </div>
      <div class="abs ar kufi" style="left:96px;bottom:150px;font-size:64px;color:var(--chalk)">&#1593;&#1604;&#1609; &#1605;&#1602;&#1575;&#1587;&#1603;</div>
      <div class="abs lab" style="left:96px;bottom:104px;opacity:.7">Identity &middot; Strategy &middot; Voice &middot; Logo &middot; Colour &middot; Type &middot; Graphics &middot; UI &middot; Applications</div>
    ''', "dark", bleed=True, hdr=False, num=False))

    # 02 CONTENTS ------------------------------------------------------------
    items = [("01", "Foundations", "Why we start over, market, audience, positioning, idea, personality, voice"),
             ("02", "Identity", "Name, logo, anatomy, lockups (EN / AR), usage, clear space, misuse"),
             ("03", "Colour", "Palette, ratios, accessibility, tints, semantic colour"),
             ("04", "Typography", "Tailored Stitch (custom display), type families, scale, Arabic, rules"),
             ("05", "Graphic language", "Stitch, notch, pattern pieces, tape, chalk, patterns, icons, photography, motion"),
             ("06", "Product", "UI principles, components, Radar, Studio, onboarding, dispatch, mobile, Arabic"),
             ("07", "Applications", "Web, social, cards, covers, documents, merchandise, rollout, tokens")]
    rows = ''.join(f'''<div class="row ac" style="padding:20px 0;border-bottom:2px solid rgba(26,20,18,.85)">
        <div class="mono" style="width:90px;font-size:18px">{n}</div>
        <div class="h2" style="width:430px">{t}</div>
        <div class="body f1" style="opacity:.8">{d}</div></div>''' for n, t, d in items)
    P.append(page("Contents", "", f'''
      <div class="row" style="gap:80px">
        <div style="width:420px"><div class="eyebrow">Contents</div><div class="h1">Seven<br>chapters,<br>one <em>fit.</em></div>
          <div class="abs" style="left:96px;bottom:150px;width:360px" class="body"><div class="stitch" style="margin-bottom:18px"></div><div class="sm thin">Everything here was written for Tailored specifically, from the product documentation up. Nothing is borrowed from the previous UI.</div></div></div>
        <div class="f1" style="padding-top:20px">{rows}</div></div>
    '''))

    # 03 WHY START OVER ---------------------------------------------------------
    drop = ["Purple-to-blue gradients and glowing orbs", "Frosted-glass cards on dark mode by default", "Sparkle icons and robot mascots standing in for &ldquo;AI&rdquo;",
            "Inter on white, rounded 12px cards, pill buttons", "Stock handshakes, laptops on desks", "Slogans about &ldquo;supercharging&rdquo; your career"]
    keep = ["A real trade with real tools: pattern, chalk, tape, notch, thread", "Warm greige, espresso ink and one confident red thread", "A custom stitched letterform nobody else owns",
            "Sharp corners with deliberate notches", "Numbers shown as measurements, not marketing", "Arabic designed first-class, not translated after"]
    P.append(page("01 Foundations", "", f'''
      <div class="eyebrow">Foundations &middot; The reset</div>
      <div class="h1" style="max-width:1100px">The category looks the same everywhere.<br><em>We will not.</em></div>
      <div class="row g48" style="margin-top:56px">
        <div class="f1"><div class="lab" style="margin-bottom:14px;color:var(--alarm)">&times; We drop</div><div class="stitch" style="margin-bottom:22px"></div>
          <ul class="b body" style="--x:1">{''.join(f"<li>{d}</li>" for d in drop)}</ul></div>
        <div class="f1"><div class="lab" style="margin-bottom:14px;color:var(--green)">&#10003; We build from</div><div class="stitch" style="margin-bottom:22px"></div>
          <ul class="b body">{''.join(f"<li>{d}</li>" for d in keep)}</ul></div>
      </div>
      <div class="abs sm thin" style="left:96px;bottom:64px;max-width:900px">Test for every future design decision: if it could be pasted onto any other AI product and still look right, it is wrong for Tailored.</div>
    '''))

    # 04 MARKET CONTEXT ---------------------------------------------------------
    stats = [("61–65M", "professionals on LinkedIn across MENA"), ("~738K", "Egyptian higher-education graduates every year"),
             ("3–3.5M", "graduates entering the MENA market annually"), ("0.27", "EGP of AI compute per complete application")]
    st = ''.join(f'''<div class="f1 col g8" style="border-top:3px solid var(--ink);padding-top:18px">
        {S.text_svg(v.replace("–","-").replace("~","").replace("K","k").replace("M","m"), INK, 62, 12, True) if False else f'<div class="h1" style="font-size:84px;letter-spacing:-.03em">{v}</div>'}
        <div class="sm">{d}</div></div>''' for v, d in stats)
    P.append(page("01 Foundations", "", f'''
      <div class="eyebrow">Foundations &middot; Context</div>
      <div class="h1" style="max-width:1200px">A huge, bilingual, price-sensitive<br>job market, applying with <em>off-the-rack</em> CVs.</div>
      <div class="row g32" style="margin-top:64px">{st}</div>
      <div class="row g48" style="margin-top:56px">
        <div class="f1 body"><b>Beachhead:</b> Egypt and the Gulf. English-first professionals who live on LinkedIn and Wuzzuf, read Arabic at home, and hate paying US-dollar subscriptions on local salaries.</div>
        <div class="f1 body"><b>Model:</b> pay-per-application credit packs from 49 EGP. No lock-in. The brand must feel as fair as the pricing: generous, transparent, never pushy.</div>
        <div class="f1 body"><b>Rhythm:</b> graduate wave Jun&ndash;Aug, layoff and restructuring wave Nov&ndash;Jan, hiring surge Jan&ndash;Mar. Brand tone shifts between hopeful and urgent.</div>
      </div>
    '''))

    # 05 INSIGHT ----------------------------------------------------------------
    P.append(page("01 Foundations", "", f'''
      <div class="row" style="height:100%;gap:80px;align-items:center">
        <div style="width:700px"><div class="eyebrow">Foundations &middot; The insight</div>
          <div class="display" style="font-size:96px">One CV,<br>a hundred<br>jobs, <em>zero</em><br>fit.</div></div>
        <div class="f1 col g24">
          <div class="lead">Recruiters skim for seconds. They are not rejecting people, they are rejecting <b>mismatch</b>: the wrong keywords, the wrong emphasis, the right skills hidden on page two.</div>
          <div class="stitch"></div>
          <div class="body">Job seekers know this, so they either send the same document everywhere and hope, or burn hours rewriting by hand. Existing AI tools make it worse: generic paragraphs, invented achievements, and a monthly bill.</div>
          <div class="stitch"></div>
          <div class="body"><b>Our insight:</b> a good application is not <em>written</em>, it is <em>tailored</em>. Measured once, cut per job, every stitch visible and checkable.</div>
        </div></div>
    '''))

    # 06 AUDIENCE ----------------------------------------------------------------
    def persona(name, ar, age, city, role, quote, needs, fears, tag, theme_c):
        return f'''<div class="card f1 col g16" style="border-top:8px solid {theme_c}">
          <div class="row jb ac"><div class="h3">{name} <span class="ar" style="font-size:22px;opacity:.7">&middot; {ar}</span></div><span class="tag">{tag}</span></div>
          <div class="lab thin">{age} &middot; {city} &middot; {role}</div>
          <div class="it" style="font-size:22px;line-height:1.3">&ldquo;{quote}&rdquo;</div>
          <div class="stitch" style="opacity:.5"></div>
          <div class="sm"><b>Needs</b><br>{needs}</div>
          <div class="sm"><b>Fears</b><br>{fears}</div></div>'''
    P.append(page("01 Foundations", "", f'''
      <div class="eyebrow">Foundations &middot; Audience</div>
      <div class="h1">Three people we <em>measure</em> first.</div>
      <div class="row g24" style="margin-top:40px;height:560px;font-size:18px">
        {persona("Mariam", "&#1605;&#1585;&#1610;&#1605;", 22, "Cairo", "Business graduate", "I sent 40 applications and heard back from two.", "A CV that does not look empty. A price she can afford. Proof it is her, only sharper.", "Looking naive. Wasting money. Being ghosted again.", "Primary", THREAD)}
        {persona("Karim", "&#1603;&#1585;&#1610;&#1605;", 31, "Riyadh / remote", "Senior backend engineer", "I do not have time to rewrite this for every role.", "Speed, precision, a clear score on which roles are worth it, outputs he can trust.", "Hallucinated skills. Wasted hours. Signing up for another subscription.", "Primary", DYE)}
        {persona("Nour", "&#1606;&#1608;&#1585;", 27, "Dubai", "Marketer moving to product", "I am two different candidates and one CV.", "Multiple career personas, each with its own emphasis. Bilingual cover letters.", "Being boxed in. Sounding like a template. Missing the Gulf hiring window.", "Growth", AMBER)}
      </div>
    '''))

    # 07 AUDIENCE INSIGHTS ---------------------------------------------------------
    P.append(page("01 Foundations", "", f'''
      <div class="eyebrow">Foundations &middot; Audience truths</div>
      <div class="h1" style="max-width:1100px">What they feel, where they are,<br>what <em>moves</em> them.</div>
      <div class="row g32" style="margin-top:50px">
        <div class="f1 col g16"><div class="lab">Emotional truths</div><div class="stitch"></div>
          <ul class="b body"><li>Applying is lonely and judged in silence.</li><li>They do not trust AI to be honest about them.</li><li>Money is tight; paying per result feels fair.</li><li>They are proud of their English and their Arabic.</li></ul></div>
        <div class="f1 col g16"><div class="lab">Where we meet them</div><div class="stitch"></div>
          <ul class="b body"><li>LinkedIn and Wuzzuf feeds</li><li>Facebook groups, Telegram, WhatsApp referrals</li><li>Instagram and TikTok career creators</li><li>University career offices, graduation season</li></ul></div>
        <div class="f1 col g16"><div class="lab">What makes them act</div><div class="stitch"></div>
          <ul class="b body"><li>Seeing a before/after of <i>their own</i> CV, instantly</li><li>A score that tells them where to spend effort</li><li>A visible diff proving nothing was invented</li><li>A free first application, no card</li></ul></div>
      </div>
      <div class="card row jb ac" style="margin-top:44px"><div class="h3">Job to be done</div>
        <div class="lead f1" style="margin-left:60px">&ldquo;Help me send an application that looks like it was made for this job, without lying, in minutes, for what I can afford.&rdquo;</div></div>
    '''))

    # 08 POSITIONING ------------------------------------------------------------------
    P.append(page("01 Foundations", "", f'''
      <div class="eyebrow">Foundations &middot; Positioning</div>
      <div class="row g48">
        <div class="f1" style="max-width:860px">
          <div class="h2" style="font-size:36px;line-height:1.2">For ambitious job seekers in Egypt and the Gulf who are tired of sending one CV to every job, <em>Tailored</em> is the made-to-measure application studio that reads each job, scores your fit honestly, and re-cuts your CV and cover letter to match &mdash; <em>without inventing a single thread.</em></div>
          <div class="stitch" style="margin:30px 0"></div>
          <div class="body">Unlike subscription r&eacute;sum&eacute; builders that spray generic AI text, we charge per application, show every change, and treat Arabic as a first language.</div>
        </div>
        <div style="width:520px" class="col g16">
          <div class="lab">Reasons to believe</div>
          {''.join(f'<div class="row g16 as"><div class="mono" style="width:34px;font-size:18px;color:var(--thread)">0{i}</div><div class="sm">{t}</div></div>' for i,t in enumerate(["9-pillar fit score: skills, proof of work, seniority, domain, language and more.","Audit diff shows every edit; anti-hallucination guardrails forbid invented claims.","Credit packs from 49 EGP. No subscription, no lock-in.","LinkedIn + Wuzzuf discovery, tailoring and dispatch in one place.","Built bilingual: English and Arabic, LTR and RTL."],1))}
        </div></div>
      <div class="row g24" style="margin-top:44px">
        <div class="card f1"><div class="lab thin">Category</div><div class="h3" style="margin-top:6px">Application studio, not r&eacute;sum&eacute; builder</div></div>
        <div class="card f1"><div class="lab thin">Frame of reference</div><div class="h3" style="margin-top:6px">The tailor, not the template</div></div>
        <div class="card f1"><div class="lab thin">Promise</div><div class="h3" style="margin-top:6px">It fits. And you can see why.</div></div>
      </div>
    '''))

    # 09 COMPETITIVE MAP ----------------------------------------------------------------
    def dotp(x, y, label, hot=False):
        c = THREAD if hot else INK
        s = 26 if hot else 16
        return f'<div class="abs row ac g12" style="left:{x}px;top:{y}px;transform:translate(-{s/2}px,-{s/2}px)"><div style="width:{s}px;height:{s}px;background:{c};clip-path:polygon(0 0,100% 0,50% 100%)"></div><div class="{"h3" if hot else "sm"}" style="white-space:nowrap">{label}</div></div>'
    P.append(page("01 Foundations", "", f'''
      <div class="row g48">
        <div style="width:480px"><div class="eyebrow">Foundations &middot; Landscape</div><div class="h1">Where we <em>stand</em> apart.</div>
          <div class="body" style="margin-top:28px">The field splits into off-the-rack tools and expensive human help. Nobody owns affordable, per-job, transparent tailoring, and nobody does it in Arabic.</div>
          <div class="stitch" style="margin:28px 0"></div><div class="sm thin">Competitors shown by type, not by name. Positions are strategic judgments, not market data.</div></div>
        <div class="f1 abs" style="left:640px;top:130px;width:850px;height:640px">
          <div class="abs" style="inset:0;border:2px solid var(--ink)"></div>
          <div class="abs" style="left:50%;top:0;bottom:0;border-left:2px dashed var(--ink);opacity:.4"></div>
          <div class="abs" style="top:50%;left:0;right:0;border-top:2px dashed var(--ink);opacity:.4"></div>
          <div class="abs lab" style="left:12px;bottom:-30px">&larr; Off-the-rack (one CV for all)</div>
          <div class="abs lab" style="right:12px;bottom:-30px">Made to measure (one CV per job) &rarr;</div>
          <div class="abs lab" style="left:12px;top:-30px">&uarr; Affordable, pay-as-you-go</div>
          <div class="abs lab" style="left:12px;bottom:12px;display:none"></div>
          <div class="abs lab" style="left:12px;bottom:-62px;display:none"></div><div class="abs lab" style="right:12px;top:-30px">Expensive, subscription &darr; (bottom)</div>
          {dotp(130, 190, "R&eacute;sum&eacute; template builders")}
          {dotp(250, 110, "Free keyword scanners")}
          {dotp(190, 520, "Subscription AI writers ($29&ndash;49/mo)")}
          {dotp(560, 540, "Career coaches &amp; CV writers")}
          {dotp(160, 310, "Job-board quick apply")}
          {dotp(640, 100, "Tailored", True)}
        </div></div>
    '''))

    # 10 BRAND IDEA ----------------------------------------------------------------------
    P.append(page("01 Foundations", "", f'''
      <div class="abs" style="left:96px;top:110px"><div class="eyebrow">Foundations &middot; The brand idea</div></div>
      <div class="abs display" style="left:96px;top:190px;font-size:230px;line-height:.85">Made to<br>measure.</div>
      <div class="abs ar kufi" style="right:96px;top:170px;font-size:130px;line-height:1">&#1593;&#1604;&#1609;<br>&#1605;&#1602;&#1575;&#1587;&#1603;</div>
      <div class="abs row g48" style="left:96px;right:96px;bottom:90px">
        <div class="f1 body"><b>The idea.</b> Every job is a different body. A good application is cut for it: measured, pattern-marked, stitched, pressed. Tailored makes that craft available to everyone, in minutes.</div>
        <div class="f1 body"><b>The feeling.</b> The quiet confidence of a garment that fits. Calm, exact, a little proud. Never hype.</div>
        <div class="f1 ar body" style="font-size:22px;line-height:1.7"><b>&#1575;&#1604;&#1601;&#1603;&#1585;&#1577;.</b> &#1604;&#1603;&#1604; &#1608;&#1592;&#1610;&#1601;&#1577; &#1605;&#1602;&#1575;&#1587;&#1548; &#1608;&#1587;&#1610;&#1585;&#1578;&#1603; &#1575;&#1604;&#1584;&#1575;&#1578;&#1610;&#1577; &#1578;&#1587;&#1578;&#1581;&#1602; &#1571;&#1606; &#1578;&#1615;&#1601;&#1589;&#1617;&#1614;&#1604; &#1593;&#1604;&#1610;&#1607;.</div>
      </div>
    ''', "paper"))

    # 11 TAILORING FRAMEWORK -----------------------------------------------------------------
    steps = [("01", "Measure", "&#1602;&#1610;&#1575;&#1587;", "You, once, properly: profile, personas, preferences, base CV.", "Master Profile &middot; Onboarding quiz", 'measure'),
             ("02", "Cut", "&#1602;&#1589;", "Each job read as a pattern; fit scored across nine pillars; poor fits discarded.", "Radar &middot; Fit score", 'scissors'),
             ("03", "Stitch", "&#1582;&#1610;&#1575;&#1591;&#1577;", "CV bullets and cover letter re-sewn to the pattern. Nothing invented.", "CV Studio &middot; Audit diff", 'needle'),
             ("04", "Send", "&#1573;&#1585;&#1587;&#1575;&#1604;", "Final fitting, then dispatch to the recruiter and track the thread.", "Dispatch &middot; Pipeline", 'send')]
    cards = ''.join(f'''<div class="card f1 col g16" style="height:560px;{'background:var(--ink);color:var(--chalk)' if i==1 else ''}">
        <div class="row jb ac"><div class="mono" style="font-size:20px;color:var(--thread)">{n}</div>{icon(ic,52, CHALK if i==1 else INK)}</div>
        <div class="display" style="font-size:84px">{t}</div><div class="ar kufi" style="font-size:36px">{a}</div>
        <div class="stitch" style="opacity:.5"></div><div class="body f1">{d}</div><div class="lab" style="opacity:.8">{m}</div></div>''' for i, (n, t, a, d, m, ic) in enumerate(steps))
    P.append(page("01 Foundations", "", f'''
      <div class="eyebrow">Foundations &middot; The tailoring framework</div>
      <div class="h1">Four verbs run the brand <em>and</em> the product.</div>
      <div class="row g16" style="margin-top:36px">{cards}</div>
    '''))

    # 12 PILLARS ---------------------------------------------------------------------------------
    pil = [("Precise", "We measure, then cut. Scores, diffs and numbers are exact and explained.", "No vague 'optimised for ATS' claims. Every number has a reason."),
           ("Honest", "We refuse to invent. A skill you do not have is never added.", "Guardrails are a brand promise, not a footnote."),
           ("Fair", "Pay per application. Free first try. Local prices.", "Never dark patterns. Never countdown timers."),
           ("Crafted", "Considered details: notches, seams, kerning, rhythm.", "We sweat what is invisible."),
           ("Bilingual", "Arabic and English are equals in layout, type and voice.", "We design RTL first-class, never mirrored as an afterthought.")]
    P.append(page("01 Foundations", "", f'''
      <div class="eyebrow">Foundations &middot; Brand pillars</div>
      <div class="h1">Five things we <em>always</em> are.</div>
      <div class="row g16" style="margin-top:40px">{''.join(f'<div class="card f1 col g16" style="height:540px"><div class="mono" style="color:var(--thread);font-size:18px">0{i}</div><div class="h2">{t}</div><div class="stitch" style="opacity:.5"></div><div class="body">{d}</div><div class="sm thin" style="margin-top:auto">{n}</div></div>' for i,(t,d,n) in enumerate(pil,1))}</div>
    '''))

    # 13 PERSONALITY -----------------------------------------------------------------------------------
    sl = [("Formal", "Casual", 62), ("Playful", "Serious", 66), ("Loud", "Quiet", 72), ("Luxury", "Everyday", 70), ("Technical", "Human", 52), ("Traditional", "Modern", 45)]
    sliders = ''.join(f'''<div class="row ac g16" style="margin-bottom:26px"><div class="lab" style="width:110px;text-align:right">{a}</div>
        <div class="f1 abs-wrap" style="position:relative;height:22px"><div class="abs" style="left:0;right:0;top:10px;height:2px;background:var(--ink)"></div>
         {ruler(560,12,INK,labels=False,unit_px=14,opacity=.6)}<div class="abs" style="left:{v}%;top:0;transform:translateX(-50%)"><div class="notch" style="width:22px;height:18px"></div></div></div>
        <div class="lab" style="width:110px">{b}</div></div>''' for a, b, v in sl)
    P.append(page("01 Foundations", "", f'''
      <div class="row g48">
        <div style="width:620px"><div class="eyebrow">Foundations &middot; Personality</div><div class="h1">The master tailor,<br>with an <em>apprentice&rsquo;s</em> hustle.</div>
          <div class="body" style="margin:28px 0">Archetype: <b>The Craftsperson</b>, with a streak of <b>the Everyman&rsquo;s champion</b>. Quiet competence, direct talk, warm eyes. Takes your measurements gently, tells you the truth about the fit, then gets it done by Thursday.</div>
          <div class="row g12 wrap">{''.join(f'<span class="chip">{w}</span>' for w in ["Exact","Warm","Dry wit","Unfussy","Proud","Generous"])}</div></div>
        <div class="f1" style="padding-top:60px">{sliders}
          <div class="card" style="margin-top:30px"><div class="lab thin">Like</div><div class="body">A great neighbourhood tailor with a very good website.</div><div class="lab thin" style="margin-top:14px">Not like</div><div class="body">A motivational poster, a robot, a recruiter, a bank.</div></div></div></div>
    '''))

    # 14 VOICE ------------------------------------------------------------------------------------------------
    P.append(page("01 Foundations", "", f'''
      <div class="eyebrow">Foundations &middot; Voice &amp; tone</div>
      <div class="h1">Plain-spoken. Precise. <em>Warm.</em></div>
      <div class="row g24" style="margin-top:36px">
        <div class="card f1"><div class="h3">Say it plainly</div><div class="sm" style="margin-top:10px">Short sentences. Concrete nouns. One idea per line. No jargon unless the user used it first.</div></div>
        <div class="card f1"><div class="h3">Show the work</div><div class="sm" style="margin-top:10px">Every claim travels with a number, a reason, or a diff. If we cannot prove it we do not say it.</div></div>
        <div class="card f1"><div class="h3">Be kind about the fit</div><div class="sm" style="margin-top:10px">A 48 is not a failure, it is information. We say what to fix, never what is wrong with them.</div></div>
        <div class="card f1"><div class="h3">Dry, never silly</div><div class="sm" style="margin-top:10px">A little wit in empty states and success. None in errors or payments.</div></div>
      </div>
      <table style="margin-top:36px"><tr><th style="width:170px">Moment</th><th>Tone</th><th>Example (EN)</th><th class="ar" style="text-align:right">&#1605;&#1579;&#1575;&#1604; (AR)</th></tr>
      <tr><td>Welcome</td><td>Warm, brief</td><td>Let&rsquo;s take your measurements.</td><td class="ar" style="text-align:right">&#1610;&#1604;&#1575; &#1606;&#1587;&#1580;&#1617;&#1604; &#1605;&#1602;&#1575;&#1587;&#1575;&#1578;&#1603;.</td></tr>
      <tr><td>Strong match</td><td>Confident, proud</td><td>87 fit. This one is cut for you.</td><td class="ar" style="text-align:right">&#1578;&#1608;&#1575;&#1601;&#1602; 87. &#1575;&#1604;&#1608;&#1592;&#1610;&#1601;&#1577; &#1583;&#1610; &#1593;&#1604;&#1609; &#1605;&#1602;&#1575;&#1587;&#1603;.</td></tr>
      <tr><td>Weak match</td><td>Honest, useful</td><td>48 fit. Two gaps worth closing, or skip it.</td><td class="ar" style="text-align:right">&#1578;&#1608;&#1575;&#1601;&#1602; 48. &#1601;&#1580;&#1608;&#1578;&#1575;&#1606; &#1610;&#1587;&#1578;&#1581;&#1602;&#1575;&#1606; &#1575;&#1604;&#1593;&#1604;&#1575;&#1580;&#1548; &#1571;&#1608; &#1578;&#1580;&#1575;&#1608;&#1586;&#1607;&#1575;.</td></tr>
      <tr><td>Error</td><td>Calm, specific</td><td>We could not read that PDF. Try a .docx or paste the text.</td><td class="ar" style="text-align:right">&#1604;&#1605; &#1606;&#1587;&#1578;&#1591;&#1593; &#1602;&#1585;&#1575;&#1569;&#1577; &#1575;&#1604;&#1605;&#1604;&#1601;. &#1580;&#1585;&#1617;&#1576; Word &#1571;&#1608; &#1575;&#1604;&#1589;&#1602; &#1575;&#1604;&#1606;&#1589;.</td></tr>
      </table>
    '''))

    # 15 LEXICON -------------------------------------------------------------------------------------------------------
    lex = [("Measurements", "&#1605;&#1602;&#1575;&#1587;&#1575;&#1578;", "Master profile and quiz answers", "Profile"), ("Pattern", "&#1575;&#1604;&#1576;&#1575;&#1578;&#1585;&#1608;&#1606;", "A parsed job description", "Job details"),
           ("Fit", "&#1575;&#1604;&#1578;&#1608;&#1575;&#1601;&#1602;", "The 0&ndash;100 match score", "Match score"), ("Cut", "&#1602;&#1589;", "Creating a tailored version", "Generate"),
           ("Fitting", "&#1578;&#1580;&#1585;&#1576;&#1577;", "Reviewing the audit diff", "Review changes"), ("Stitch", "&#1582;&#1610;&#1575;&#1591;&#1577;", "Applying accepted edits", "Apply"),
           ("Dispatch", "&#1573;&#1585;&#1587;&#1575;&#1604;", "Sending the application", "Submit"), ("Credit", "&#1585;&#1589;&#1610;&#1583;", "Unit of payment", "Token")]
    P.append(page("01 Foundations", "", f'''
      <div class="eyebrow">Foundations &middot; Lexicon</div>
      <div class="row g48"><div style="width:540px"><div class="h1">The tailor&rsquo;s words,<br>used <em>sparingly.</em></div>
        <div class="body" style="margin-top:26px">A small vocabulary borrowed from the trade gives the product a point of view. Rule: use the craft word where it is clear; add a plain gloss on first use; never force a metaphor into error messages, legal copy or billing.</div></div>
        <div class="f1"><table><tr><th>Craft word</th><th class="ar" style="text-align:right">&#1593;&#1585;&#1576;&#1610;</th><th>Means</th><th>Instead of</th></tr>
        {''.join(f'<tr><td><b>{a}</b></td><td class="ar" style="text-align:right;font-size:20px">{b}</td><td>{c}</td><td class="thin">{d}</td></tr>' for a,b,c,d in lex)}</table></div></div>
    '''))

    # 16 MANIFESTO --------------------------------------------------------------------------------------------------------
    P.append(page("01 Foundations", "", f'''
      <div class="abs" style="right:-40px;top:-20px;opacity:.16">{layplan(780, 940, seed=5, stroke=INK, accent=INK, scale_range=(1, 1.7), margin=14, labels=False)}</div>
      <div class="eyebrow">Foundations &middot; Manifesto</div>
      <div class="display" style="font-size:66px;line-height:1.08;max-width:1150px;letter-spacing:-.02em">
        Nobody gets hired by the average CV.<br>One document sent to a hundred jobs fits none of them.<br>
        So we measure you once, properly.<br>We read each job like a pattern.<br>
        We cut. We stitch. We never add a thread that is not yours.<br>
        <em>And when it fits, you can feel it.</em><br>Then you send.</div>
      <div class="abs ar amiri" style="left:96px;bottom:110px;font-size:38px;font-weight:700">&#1604;&#1603;&#1604; &#1608;&#1592;&#1610;&#1601;&#1577; &#1605;&#1602;&#1575;&#1587;&#1548; &#1608;&#1604;&#1603; &#1587;&#1610;&#1585;&#1577; &#1578;&#1615;&#1601;&#1589;&#1617;&#1614;&#1604; &#1593;&#1604;&#1610;&#1607;&#1575;.</div>
    ''', "thread"))

    return P

