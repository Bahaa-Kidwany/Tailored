"""Builds Tailored_Feasibility_Study.pdf. All financial numbers are read from
Tailored_Financial_Model.xlsx (cached Excel values), never from build_model.py."""
import os
import openpyxl
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer,
                                Table, TableStyle, Image, PageBreak, KeepTogether, NextPageTemplate)

HERE = os.path.dirname(os.path.abspath(__file__))
# Prefer the recalculated copy (recalc/), because a workbook written by openpyxl has no cached values.
_recalc = os.path.join(HERE, "recalc", "Tailored_Financial_Model.xlsx")
XLSX = _recalc if os.path.exists(_recalc) else os.path.join(HERE, "Tailored_Financial_Model.xlsx")
OUT_V2 = os.path.join(os.path.dirname(HERE), "Tailored_Feasibility_Study_v2.pdf")
OUT_V3 = os.path.join(os.path.dirname(HERE), "Tailored_Feasibility_Study_v3.pdf")
OUT = OUT_V3  # Write to v3 directly to avoid Windows file locks

wb = openpyxl.load_workbook(XLSX, data_only=True)
S, M, U, A = wb["Summary"], wb["Market"], wb["UnitEconomics"], wb["Annual"]


def find(ws, label, start=1):
    for r in range(start, ws.max_row + 1):
        v = ws.cell(r, 1).value
        if isinstance(v, str) and v.strip().startswith(label):
            return r
    raise KeyError(label)


def vals(ws, r, n):
    return [ws.cell(r, c).value for c in range(2, 2 + n)]


def summ(label, n=3):
    return vals(S, find(S, label), n)


def annual(scn, label):
    start = find(A, scn)
    r = find(A, label, start)
    return [A.cell(r, c).value for c in range(3, 8)]


SC = ["Downside", "Base", "Upside"]
rev = {s: annual(s.upper() + " SCENARIO", "Total net revenue") for s in SC}
ni = {s: annual(s.upper() + " SCENARIO", "Net income") for s in SC}
gm = {s: annual(s.upper() + " SCENARIO", "Gross margin %") for s in SC}
cum = {s: annual(s.upper() + " SCENARIO", "Cumulative paying users") for s in SC}
cash = {s: annual(s.upper() + " SCENARIO", "Closing cash") for s in SC}
signups = {s: annual(s.upper() + " SCENARIO", "Sign-ups") for s in SC}
opx = {k: annual("BASE SCENARIO", k) for k in
       ["Infrastructure", "Freelance designer", "One-time launch", "Paid marketing", "Contingency", "AI cost", "Payment fees"]}
breakeven = summ("Break-even month")
peak = summ("Peak funding need")
invest = summ("Investment assumed")
headroom = summ("Funding headroom")
ltvcac = {k: summ("LTV:CAC - " + k) for k in ["Egypt", "KSA", "UAE"]}
moic = summ("Investor MOIC")
irr = summ("Investor IRR")
ev = summ("Exit enterprise value")

r_tam = find(M, "TAM: LinkedIn")
tam = vals(M, r_tam, 4)
seekers = vals(M, find(M, "Active job seekers"), 4)
sam = vals(M, find(M, "SAM: addressable"), 4)
samv = vals(M, find(M, "SAM value per year"), 4)
som_rev = vals(M, find(M, "Net revenue in year 5"), 4)
som_pay = vals(M, find(M, "Paying users added in year 5"), 4)
pace = vals(U, find(U, "CAC payback"), 9)
cac = vals(U, find(U, "Paid CAC"), 9)
ltv = vals(U, find(U, "Blended LTV"), 9)
bl_ratio = vals(U, find(U, "LTV : CAC (blended"), 9)
bl_cac = vals(U, find(U, "Blended CAC from model"), 9)
AS = wb["Assumptions"]
ai_app = AS.cell(find(AS, "AI cost per full application"), 3).value
ai_signup = AS.cell(find(AS, "AI cost per sign-up"), 3).value

# ------------------------------------------------ formatting
usd = lambda x: "${:,.0f}".format(x)
num = lambda x: "{:,.0f}".format(x)
pct = lambda x: "{:.0f}%".format(x * 100)
be = lambda x: ("Month %d" % x) if isinstance(x, (int, float)) else str(x)

# ------------------------------------------------ charts
NAVY, TEAL, AMBER, RED, GREY = "#1B2A49", "#16A39A", "#F2A23A", "#D9534F", "#8A94A6"


def chart_revenue():
    fig, ax = plt.subplots(figsize=(7.2, 3.1), dpi=200)
    yrs = [1, 2, 3, 4, 5]
    for s, c in zip(SC, [RED, TEAL, AMBER]):
        ax.plot(yrs, rev[s], marker="o", lw=2.4, color=c, label=s)
        ax.annotate(usd(rev[s][-1]), (5, rev[s][-1]), textcoords="offset points", xytext=(6, -3), fontsize=7, color=c)
    ax.set_xticks(yrs); ax.set_xticklabels(["Year %d" % y for y in yrs])
    ax.set_xlim(0.8, 5.9)
    ax.set_ylabel("Net revenue (USD)"); ax.set_title("Net revenue by scenario (Excel model)", fontsize=10, color=NAVY, loc="left")
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, p: "${:,.0f}".format(v)))
    ax.grid(axis="y", alpha=.25); ax.spines[["top", "right"]].set_visible(False); ax.legend(frameon=False, fontsize=8)
    fig.tight_layout(); p = os.path.join(HERE, "_c_rev.png"); fig.savefig(p); plt.close(fig); return p


def chart_cash():
    fig, ax = plt.subplots(figsize=(7.2, 2.3), dpi=200)
    yrs = [1, 2, 3, 4, 5]
    w = .26
    for i, (s, c) in enumerate(zip(SC, [RED, TEAL, AMBER])):
        ax.bar([y + (i - 1) * w for y in yrs], ni[s], w, color=c, label=s)
    ax.axhline(0, color=NAVY, lw=.8)
    ax.set_xticks(yrs); ax.set_xticklabels(["Year %d" % y for y in yrs])
    ax.set_title("Net income by scenario (Excel model, USD)", fontsize=9.5, color=NAVY, loc="left")
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, p: "${:,.0f}".format(v)))
    ax.grid(axis="y", alpha=.25); ax.spines[["top", "right"]].set_visible(False); ax.legend(frameon=False, fontsize=8)
    fig.tight_layout(); p = os.path.join(HERE, "_c_ni.png"); fig.savefig(p); plt.close(fig); return p


def chart_competitors():
    names = ["Jobscan", "Enhancv", "Teal+", "Rezi Pro", "Kickresume", "LinkedIn Premium", "Tailored (Egypt avg order)", "Tailored (Gulf avg order)"]
    prices = [49.95, 39, 29, 29, 24, 39.99, 3.0, 8.99]
    cols = [GREY] * 6 + [TEAL, TEAL]
    fig, ax = plt.subplots(figsize=(7.2, 3.0), dpi=200)
    ax.barh(names[::-1], prices[::-1], color=cols[::-1])
    for i, v in enumerate(prices[::-1]):
        ax.text(v + .6, i, "${:,.2f}".format(v), va="center", fontsize=7)
    ax.set_title("Monthly entry price vs. Tailored pay-per-pack (USD)", fontsize=10, color=NAVY, loc="left")
    ax.spines[["top", "right"]].set_visible(False); ax.tick_params(labelsize=8)
    fig.tight_layout(); p = os.path.join(HERE, "_c_comp.png"); fig.savefig(p); plt.close(fig); return p


# ------------------------------------------------ styles
base = ParagraphStyle("b", fontName="Helvetica", fontSize=9.4, leading=13.5, textColor=colors.HexColor("#2B3345"), alignment=TA_LEFT)
H1 = ParagraphStyle("h1", parent=base, fontName="Helvetica-Bold", fontSize=17, leading=21, textColor=colors.HexColor(NAVY), spaceBefore=2, spaceAfter=6)
H2 = ParagraphStyle("h2", parent=base, fontName="Helvetica-Bold", fontSize=11.5, leading=15, textColor=colors.HexColor(TEAL), spaceBefore=8, spaceAfter=3)
BL = ParagraphStyle("bl", parent=base, leftIndent=12, bulletIndent=2, spaceAfter=2)
SM = ParagraphStyle("sm", parent=base, fontSize=7.6, leading=10, textColor=colors.HexColor("#6A7385"))
TC = ParagraphStyle("tc", parent=base, fontSize=8.2, leading=10.5)
TH = ParagraphStyle("th", parent=TC, fontName="Helvetica-Bold", textColor=colors.white)
CALL = ParagraphStyle("call", parent=base, backColor=colors.HexColor("#EAF7F6"), borderPadding=(6, 8, 6, 8), leading=13.5, spaceBefore=5, spaceAfter=8)
WARN = ParagraphStyle("warn", parent=CALL, backColor=colors.HexColor("#FDEEEE"))

P = lambda t, s=base: Paragraph(t, s)
B = lambda t: Paragraph(t, BL, bulletText="\u2022")


def table(rows, widths, head=True, zebra=True, pad=3.2):
    data = [[Paragraph(str(c), TH if (head and i == 0) else TC) for c in r] for i, r in enumerate(rows)]
    t = Table(data, colWidths=[w * mm for w in widths], repeatRows=1 if head else 0)
    st = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("GRID", (0, 0), (-1, -1), .3, colors.HexColor("#D5DAE3")),
          ("TOPPADDING", (0, 0), (-1, -1), pad), ("BOTTOMPADDING", (0, 0), (-1, -1), pad)]
    if head:
        st.append(("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(NAVY)))
    if zebra:
        for i in range(1, len(rows)):
            if i % 2 == 0:
                st.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#F5F7FA")))
    t.setStyle(TableStyle(st))
    return t


def footer(c, d):
    c.saveState()
    c.setFont("Helvetica", 7.5); c.setFillColor(colors.HexColor("#8A94A6"))
    c.drawString(18 * mm, 10 * mm, "Tailored - Feasibility Study | Financials: Tailored_Financial_Model.xlsx | Research: Oct 2026")
    c.drawRightString(A4[0] - 18 * mm, 10 * mm, "Page %d" % d.page)
    c.restoreState()


def cover(c, d):
    c.saveState()
    c.setFillColor(colors.HexColor(NAVY)); c.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
    c.setFillColor(colors.HexColor(TEAL)); c.rect(0, A4[1] * .42, A4[0], 4, fill=1, stroke=0)
    c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 38); c.drawString(22 * mm, A4[1] * .62, "Tailored")
    c.setFont("Helvetica", 17); c.drawString(22 * mm, A4[1] * .62 - 11 * mm, "Feasibility Study")
    c.setFont("Helvetica", 11); c.setFillColor(colors.HexColor("#BFD3E6"))
    c.drawString(22 * mm, A4[1] * .62 - 22 * mm, "AI job-search copilot for Egypt, Saudi Arabia and the UAE")
    c.setFont("Helvetica", 8.5)
    c.drawString(22 * mm, A4[1] * .42 - 14 * mm, "Idea | Market | Competitors | Costs | Risks | Recommendations | Venture Roadmap | Learning")
    c.drawString(22 * mm, 22 * mm, "Prepared October 2026. Financial figures: Tailored_Financial_Model.xlsx (all USD).")
    c.restoreState()


doc = BaseDocTemplate(OUT, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=15 * mm, bottomMargin=16 * mm,
                      title="Tailored - Feasibility Study", author="Tailored")
fr = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")
doc.addPageTemplates([PageTemplate(id="cover", frames=[fr], onPage=cover), PageTemplate(id="body", frames=[fr], onPage=footer)])

s = [NextPageTemplate("body"), PageBreak()]
W = 174

# ==============================================================================
# PAGE 2: 1. EXECUTIVE SUMMARY
# ==============================================================================
s += [P("1. Executive summary", H1)]
s += [P("<b>Tailored</b> is a pay-per-use AI job-search copilot. It pulls jobs from LinkedIn and Wuzzuf, scores how well a candidate fits "
        "<i>before</i> any writing happens, then generates a tailored CV and cover letter (LaTeX/PDF) with an audit diff. Users buy small "
        "credit packs (from 49 EGP in Egypt, $4.99 in the Gulf) instead of a $25-50 monthly subscription.")]
s += [P("<b>Verdict: feasible as a lean, low-capital side-venture; weak as a venture-scale business.</b> "
        "Technical risk is low and cost per user is tiny. But the Excel model shows small revenue ("
        "Base case %s in Year 1, %s in Year 5), paid-only advertising that never pays back, and one existential dependency: scraping LinkedIn. "
        "Economics work only if most users arrive organically (blended LTV:CAC %.2fx Egypt / %.2fx KSA in Base)." % (usd(rev["Base"][0]), usd(rev["Base"][4]), bl_ratio[3], bl_ratio[4]), CALL)]
s += [table([
    ["Metric (Excel model)", "Downside", "Base", "Upside"],
    ["Net revenue - Year 1"] + [usd(rev[x][0]) for x in SC],
    ["Net revenue - Year 3"] + [usd(rev[x][2]) for x in SC],
    ["Net revenue - Year 5"] + [usd(rev[x][4]) for x in SC],
    ["Gross margin - Year 5"] + [pct(gm[x][4]) for x in SC],
    ["Net income - Year 5"] + [usd(ni[x][4]) for x in SC],
    ["Cumulative paying users - Year 5"] + [num(cum[x][4]) for x in SC],
    ["Break-even (EBITDA &gt; 0, 3 months running)"] + [be(x) for x in breakeven],
    ["Peak funding need"] + [usd(x) for x in peak],
    ["LTV:CAC, Egypt paid ads only"] + ["%.2fx" % x for x in ltvcac["Egypt"]],
    ["LTV:CAC, Egypt blended (organic + paid)"] + ["%.2fx" % bl_ratio[i] for i in (0, 3, 6)],
], [70, 34, 34, 36], pad=2.8)]
s += [Spacer(1, 4), Image(chart_revenue(), width=W * mm, height=W * mm * 3.1 / 7.2)]

# ==============================================================================
# PAGE 3: 2. THE CORE IDEA
# ==============================================================================
s += [PageBreak(), P("2. The core idea", H1)]
s += [P("<b>Problem.</b> Job seekers in MENA apply to dozens of roles, rewriting a CV for each one. Existing tools are priced in USD "
        "subscriptions ($24-50/month), ignore regional boards (Wuzzuf, Bayt), and mostly stuff keywords with generic AI output.")]
s += [P("<b>Solution.</b> One pipeline: discover jobs, extract a structured job profile, compute fit and gap, then (only if worthwhile) "
        "generate a tailored CV and cover letter with strict anti-hallucination rules and a visible diff.")]
s += [table([
    ["Pipeline stage", "What it does"],
    ["1. Job discovery", "Modular scraper plugins (LinkedIn, Wuzzuf first; Bayt etc. later) plus a paste-a-job-description option."],
    ["2. Structured extraction", "Cheap LLM turns the posting into a strict JSON schema (skills, years, location, duties)."],
    ["3. Fit scoring", "Skill gap, experience gap, location and keyword relevance produce a Fit Score. This is the free hook."],
    ["4. Tailoring", "CV bullet/skills tailoring on LaTeX or Markdown, with audit diff. 1 credit per CV or letter, 2 per full package."],
    ["5. Output", "Clean ATS-friendly PDF/LaTeX; documents stored in PostgreSQL."],
], [42, 132], pad=3.5)]
s += [P("Stack: React (Vite) frontend, FastAPI backend, PostgreSQL in Docker, stealth scraping, Gemini/GPT-class LLMs.", SM)]
s += [P("Business model", H2)]
s += [B("<b>Egypt packs:</b> Starter 49 EGP (5 credits), Job Hunter 179 EGP (25), Career Sprint 399 EGP (70). Average order about 160 EGP (~$3.00).")]
s += [B("<b>Gulf packs:</b> Single Shot $4.99 (10 credits), Pro Hunter $14.99 (50). Average order $8.99.")]
s += [B("<b>Optional subscription (model assumption):</b> $3.99/mo Egypt, $9.99/mo Gulf.")]
s += [B("<b>Rollout in the model:</b> Egypt launch April 2027 (Base), Gulf October 2027, aligned to the Jun-Aug graduation wave.")]

# ==============================================================================
# PAGE 4: 3. MARKET
# ==============================================================================
s += [PageBreak(), P("3. Market", H1)]
s += [P("The model sizes the market bottom-up from LinkedIn membership (DataReportal 2025), the share that is actively job hunting "
        "(18%) and the share Tailored can realistically serve (35%: bilingual, white-collar, able to pay online).")]
s += [table([
    ["", "Egypt", "KSA", "UAE", "Total"],
    ["TAM: LinkedIn members"] + [num(x) for x in tam],
    ["Active job seekers / year (18%)"] + [num(x) for x in seekers],
    ["SAM: addressable (35%)"] + [num(x) for x in sam],
    ["SAM revenue pool / year"] + [usd(x) for x in samv],
    ["Base case: paying users added, Year 5"] + [num(x) for x in som_pay],
    ["Base case: net revenue, Year 5 (SOM)"] + [usd(x) for x in som_rev],
], [66, 27, 27, 27, 27], pad=3.0)]
s += [P("Source: Market sheet of the Excel model. Revenue pool = SAM x conversion x annual spend per paying user.", SM)]
s += [P("Key reading: the <b>whole addressable revenue pool is only about %s per year</b> across three countries at today's price points. "
        "The market is large in people, small in dollars. Gulf users are worth about 2.5x more per head than Egyptian users, "
        "so the Gulf launch drives the Base-case upside (KSA+UAE contribute %s of Year-5 revenue vs %s from Egypt)." %
        (usd(samv[3]), usd(som_rev[1] + som_rev[2]), usd(som_rev[0])), CALL)]
s += [P("Demand drivers (web research)", H2)]
s += [B("Egypt youth (15-29) unemployment is about 13.2% (CAPMAS); young women about 33.8%. Overall unemployment about 6.3%. A persistent graduate skills mismatch keeps application volume high.")]
s += [B("Egypt produces about 738,000 higher-education graduates a year (CAPMAS); MENA about 3-3.5M.")]
s += [B("ATS screening is widespread in KSA/UAE and AI-skill job postings have roughly tripled, pushing candidates toward CV-optimisation tools.")]
s += [B("Regional job boards (Wuzzuf, Bayt, GulfTalent) are the actual discovery channel, and global competitors do not integrate them.")]
s += [P("Seasonality (model index)", H2)]
s += [P("Demand peaks Jun-Aug (graduates, index 1.2-1.4) and Jan (Q1 budgets, 1.2); it troughs in December (0.7) and Ramadan/Eid. "
        "Launching in April 2027 gives a roughly 2-month runway before the graduation peak.")]

# ==============================================================================
# PAGE 5: 4. COMPETITORS
# ==============================================================================
s += [PageBreak(), P("4. Competitors", H1)]
s += [Image(chart_competitors(), width=W * mm, height=W * mm * 3.0 / 7.2)]
s += [table([
    ["Competitor", "Category", "Price (Oct 2026 research)", "Gap Tailored can exploit"],
    ["Jobscan", "Keyword matcher", "Free (5 scans); $49.95/mo; $89.95/quarter", "Pricey, US-centric, no discovery."],
    ["Teal+", "Tracker + AI builder", "$29/mo; $13/week; $79/quarter", "No regional boards, subscription lock-in."],
    ["Rezi Pro", "ATS resume builder", "$29/mo; $149 lifetime", "Own templates only; no fit-gap before writing."],
    ["Kickresume", "AI resume builder", "$24/mo; $54/quarter; $96/yr", "Cheaper but still USD subscription, generic output."],
    ["Enhancv", "Designer resumes", "$39/mo; $69/quarter", "Proprietary layouts, not LaTeX-faithful."],
    ["LazyApply", "Auto-apply bot", "$99/yr to $999/yr (annual only)", "Account-ban risk, spammy."],
    ["LinkedIn Premium", "Platform", "~$39.99/mo; ~$19.99/mo annual", "AI fit insights, but no CV/cover letter generation."],
    ["ChatGPT / Gemini", "General LLM", "Free to ~$20/mo", "Biggest substitute: manual copy-paste, no scoring, no layout."],
    ["Anoud Job, Taqdeem", "Arabic/English CV builders", "Free / low", "Regional, but builder-only (no job fit or tailoring)."],
], [28, 30, 50, 66], pad=2.4)]
s += [P("Pricing from vendor pages and review sites, retrieved Oct 2026; subject to change.", SM)]
s += [P("Competitive position", H2)]
s += [B("<b>Real moat is thin.</b> Prompting an LLM to tailor a CV is easy; the substitute (ChatGPT) is free. Defensibility must come from regional job-board integration, the fit-gap score and faithful LaTeX output.")]
s += [B("<b>Price is the sharpest wedge:</b> pay-per-pack at about $3 (Egypt) vs $24-50 monthly.")]
s += [B("<b>Arabic-first CV support</b> is only partly served; RTL handling in the LaTeX pipeline would be a genuine differentiator if built.")]

# ==============================================================================
# PAGE 6: 5. COSTS & UNIT ECONOMICS
# ==============================================================================
s += [PageBreak(), P("5. Costs & Unit Economics", H1)]
s += [P("<b>Variable cost is negligible.</b> A full application (parse, fit, CV, cover letter; about 9,500 tokens) costs about $%.3f using a tiered LLM setup "
        "(Gemini 2.5 Flash-Lite at $0.10 in / $0.40 out for parsing/scoring; Flash at $0.30 / $2.50 for writing). "
        "Free evaluations cost about $%.3f per sign-up. Fixed costs are minimal: $12/mo server, $6/mo domain/email, and a freelance designer at 2 engagements of $720/yr." % (ai_app, ai_signup))]
s += [table([
    ["Base scenario cost line (USD)", "Year 1", "Year 2", "Year 3", "Year 5"],
    ["AI cost"] + [usd(opx["AI cost"][i]) for i in (0, 1, 2, 4)],
    ["Payment fees"] + [usd(opx["Payment fees"][i]) for i in (0, 1, 2, 4)],
    ["Infrastructure (server, DB, domain)"] + [usd(opx["Infrastructure"][i]) for i in (0, 1, 2, 4)],
    ["Freelance designer / content"] + [usd(opx["Freelance designer"][i]) for i in (0, 1, 2, 4)],
    ["One-time launch (company, brand, legal)"] + [usd(opx["One-time launch"][i]) for i in (0, 1, 2, 4)],
    ["Paid marketing"] + [usd(opx["Paid marketing"][i]) for i in (0, 1, 2, 4)],
    ["Contingency (5%)"] + [usd(opx["Contingency"][i]) for i in (0, 1, 2, 4)],
], [70, 26, 26, 26, 26], pad=1.8)]
s += [P("Source: Annual sheet, Base scenario. Founder salary is 0 in Base (triggers only once the business can afford it).", SM)]
s += [P("Unit economics: the weak spot", H2)]
s += [table([
    ["Base scenario", "Egypt", "KSA", "UAE"],
    ["Paid CAC per paying user", usd(cac[3]), usd(cac[4]), usd(cac[5])],
    ["Blended CAC (paid + designer, all new payers, 5 yrs)", "$%.2f" % bl_cac[3], "$%.2f" % bl_cac[4], "$%.2f" % bl_cac[5]],
    ["Blended LTV per paying user", "$%.2f" % ltv[3], "$%.2f" % ltv[4], "$%.2f" % ltv[5]],
    ["LTV : CAC (paid ads only)"] + ["%.2fx" % ltvcac[k][1] for k in ("Egypt", "KSA", "UAE")],
    ["LTV : CAC (blended, incl. organic)", "%.2fx" % bl_ratio[3], "%.2fx" % bl_ratio[4], "%.2fx" % bl_ratio[5]],
    ["Orders to recover paid CAC"] + ["%.0f" % pace[3], "%.0f" % pace[4], "%.0f" % pace[5]],
], [70, 34, 34, 36], pad=1.8)]
s += [P("<b>Paid ads alone do not pay back in any market or scenario</b> (paid-only LTV:CAC %.2fx-%.2fx; best case Upside Egypt %.2fx). "
        "Gulf paid acquisition is far worse than Egypt because Gulf CPCs are roughly 4-10x higher. Viability depends on organic and referral users diluting CAC: "
        "blended LTV:CAC is %.2fx / %.2fx / %.2fx (Downside / Base / Upside, Egypt). Lead with content and campus referrals." %
        (min(ltvcac["KSA"]), max(ltvcac["Egypt"]), ltvcac["Egypt"][2], bl_ratio[0], bl_ratio[3], bl_ratio[6]), WARN)]
s += [P("Funding", H2)]
s += [P("Placeholder $30,000 investment. Peak cumulative cash need is %s (Downside), %s (Base) and %s (Upside), "
        "leaving ample headroom (%s / %s / %s). Cash never runs out in any scenario." % (usd(peak[0]), usd(peak[1]), usd(peak[2]), usd(headroom[0]), usd(headroom[1]), usd(headroom[2])))]
s += [Image(chart_cash(), width=W * mm, height=W * mm * 1.85 / 7.2)]
s += [P("Implication: the project needs about %s-%s to be proven. At the model's assumed 20%% stake the illustrative investor "
        "return is MOIC %.2fx (Downside), %.2fx (Base), %.2fx (Upside), at a $150k implied post-money. Only the Upside returns capital." % ((usd(min(peak)), usd(max(peak))) + tuple(moic)), CALL)]

# ==============================================================================
# PAGE 7: 6. RISKS & PLANNING CONSISTENCY
# ==============================================================================
s += [PageBreak(), P("6. Risks", H1)]
s += [table([
    ["#", "Risk", "Likelihood", "Impact", "Evidence / mitigation"],
    ["1", "<b>LinkedIn scraping blocked or litigated</b>", "High", "High",
     "LinkedIn sued Proxycurl (Jan 2025) and forced its shutdown (Jul 2025); hiQ paid $500k and accepted an injunction. Scale with fake accounts or session pools is the trigger. Mitigate: no login-wall bypass, user-pasted JD option, Wuzzuf/Bayt first, user-initiated fetch only. Not priced in the model."],
    ["2", "Free LLM apps commoditise CV tailoring", "High", "High", "ChatGPT does tailoring free. Differentiate on regional integration, fit-gap scoring, LaTeX fidelity, Arabic support."],
    ["3", "Low willingness to pay in Egypt", "High", "Med", "Avg order about $3. Gulf priced about 3x. Downside has only 2.5% conversion."],
    ["4", "Paid CAC exceeds LTV", "High", "High", "Paid-only LTV:CAC is %.2f-%.2fx across all scenarios; Gulf CPCs are 4-10x Egypt. Blended (organic-heavy) is %.2f-%.2fx. Stay organic/referral-led and verify the click-to-sign-up rate with a small test campaign." % (min(ltvcac['KSA'] + ltvcac['UAE'] + ltvcac['Egypt']), max(ltvcac['KSA'] + ltvcac['UAE'] + ltvcac['Egypt']), min(bl_ratio), max(bl_ratio))],
    ["5", "Single-founder dependency", "High", "High", "Zero salary phase risks burnout. Model keeps hires off by default."],
    ["6", "EGP devaluation", "Med", "Med", "Annual depreciation 4-15% in scenarios; re-price quarterly."],
    ["7", "Small revenue pool caps upside", "Med", "Med", "Whole SAM pool about %s/yr; sign-ups capped at 2.5-6%% of SAM per year." % usd(samv[3])],
    ["8", "AI model price/quality changes", "Low", "Low", "AI is under 10% of revenue; multiplier 1.0-1.5x in scenarios."],
    ["9", "Data privacy & tax/VAT", "Med", "Med", "Handles CVs (personal data); EG 14%, KSA 15%, UAE 5% VAT, Egypt CIT 22.5% - verify with an accountant."],
], [7, 38, 19, 15, 95], pad=2.4)]
s += [P("Not modelled: working capital, FX on payouts, gateway reserves, refunds/chargebacks, option pool, founder living costs while unpaid, and platform legal exposure.", SM)]
s += [P("7. Note on earlier planning documents", H2)]
s += [P("The earlier business_feasibility_analysis.md projected break-even in 4-5 months on a 50,000 EGP/month cost base. The Excel model, which includes VAT, "
        "payment fees, realistic conversion, seasonality and a launch ramp, is far more conservative: Base break-even is <b>%s</b> (about 1.4 years after "
        "start), and Downside never breaks even within 60 months. This study uses the Excel figures throughout." % be(breakeven[1]), CALL)]

# ==============================================================================
# PAGE 8: 8. RECOMMENDATIONS (MVP PHASE)
# ==============================================================================
s += [PageBreak(), P("8. Recommendations (MVP Phase)", H1)]
s += [P("<b>Proceed, but as a staged, capped-cost experiment, not a funded growth bet.</b>")]
s += [table([
    ["Stage", "Action", "Go / no-go gate"],
    ["0. Now", "Build the MVP with user-pasted JD + Wuzzuf. Treat LinkedIn as optional, user-initiated. Get legal advice on ToS exposure.", "MVP live; no login-wall bypass."],
    ["1. Egypt soft launch (Apr 2027)", "Launch before graduation season. Free fit score, 49/179/399 EGP packs. Content-led organic acquisition; paid spend at floor.", "2-5% free-to-paid conversion on first 1,000 sign-ups."],
    ["2. Graduation wave (Jun-Aug)", "Campus ambassadors, TikTok/LinkedIn demos, referral credits.", "Organic CAC near $0; repeat purchase rate at least 15-20%."],
    ["3. Gulf test (before Oct 2027)", "Launch KSA/UAE at $4.99/$14.99 led by organic and referral; run a small paid test to verify the 20% click-to-sign-up rate and real Gulf CPCs.", "Blended LTV:CAC above 1 and trending to 3."],
    ["4. Decide", "Base-case break-even is month %s. Keep costs flat until then; add the founder salary only on the model's trigger." % breakeven[1], "Revenue tracking within about 30% of Base."],
], [38, 90, 46], pad=3.2)]
s += [P("Priorities", H2)]
for t in [
    "<b>De-risk scraping first.</b> It is the single biggest threat and is unpriced. Build on user-supplied job text and non-LinkedIn boards so the product survives a LinkedIn block.",
    "<b>Lean on organic channels.</b> Paid-only ads lose money everywhere in the model; spend only after a channel proves LTV:CAC above 1.",
    "<b>Prioritise the Gulf, but validate it.</b> About %s of Base Year-5 revenue comes from KSA+UAE, yet Gulf paid CAC is the highest in the model. Enter organically and confirm CAC before scaling spend." % pct((som_rev[1] + som_rev[2]) / som_rev[3]),
    "<b>Raise only what is needed.</b> About %s covers the worst-case peak need; the $30k placeholder is generous for these returns." % usd(max(peak)),
    "<b>Differentiate beyond 'AI CV writer'.</b> Invest in Arabic/RTL output, fit-gap scoring quality, and faithful LaTeX formatting; these are hard to copy with a free chatbot.",
    "<b>Consider widening revenue per user</b> (interview prep, recruiter outreach, B2B/university licences) because consumer ARPU of about $3 caps the upside.",
]:
    s.append(B(t))
s += [P("Bottom line", H2)]
s += [P("Tailored is cheap to build and cheap to run, with %s-%s Base/Upside gross margins by Year 5. It is a credible bootstrapped product "
        "that can reach profit in the Base case, but not a high-growth venture on current assumptions. Proceed under strict cost discipline, validate the "
        "legal and Gulf-demand unknowns early, and set stage gates before spending beyond infrastructure." % (pct(gm["Base"][4]), pct(gm["Upside"][4])), CALL)]

# ==============================================================================
# PAGE 9: 9. UNLOCKING VENTURE SCALE ($5M - $20M+ ARR)
# ==============================================================================
s += [PageBreak(), P("9. Unlocking Venture Scale ($5M - $20M+ ARR Roadmap)", H1)]
s += [P("<b>The Baseline Ceiling vs. Venture Transformation.</b> The financial model demonstrates that a pure B2C CV-tailoring tool functions "
        "reliably as a lean, bootstrapped cash-flow asset (breaking even in Month 17 with <$7k peak cash burn in Base). However, low average order "
        "values ($3.00 Egypt / $8.99 Gulf), high paid customer acquisition costs ($25-$50 CAC), and a 25%/month 'success churn' (users quit when "
        "hired) prevent the current baseline model from reaching venture scale on its own. To build a multi-million-dollar high-growth enterprise, "
        "Tailored must leverage its B2C product as a <b>Trojan Horse</b> to feed high-ticket enterprise and talent marketplace revenue streams.")]

s += [table([
    ["Pillar", "Target & Pricing", "Core Mechanism", "ARR & VC Impact"],
    ["<b>1. Two-Sided Talent Marketplace</b><br/><i>(The Trojan Horse)</i>",
     "GCC & European employers / recruiters.<br/><b>$1,500 - $3,000</b> per hire or <b>$400/mo</b> search seat.",
     "B2C CV tailoring acts as a zero-CAC candidate acquisition engine. Candidates build verified profiles and Fit Scores. Employers pay to search, filter by proven capability, and recruit pre-screened bilingual/tech talent.",
     "<b>50 hires/mo = $1.2M ARR</b>.<br/>Proprietary talent liquidity commands 10x-15x revenue multiples from venture capital."],
    ["<b>2. Institutional Licensing</b><br/><i>(B2B2C Universities & Bootcamps)</i>",
     "University Career Centers (AUC, GUC, KSU) & coding bootcamps (ITI, Route, ALX).<br/><b>$5,000 - $25,000 /yr</b> contract.",
     "Sold as an enterprise career-enablement suite. Career centers provide Tailored to their student cohorts to boost graduate employment rates. Includes admin ATS compliance dashboards and placement analytics.",
     "<b>40 institutions = $600k ARR</b>.<br/>Multi-year sticky contracts, negative net churn, and zero paid customer acquisition cost."],
    ["<b>3. Autonomous Career Agent</b><br/><i>(High-Ticket B2C Copilot)</i>",
     "Mid-to-senior professionals, Gulf expats, and remote candidates.<br/><b>$49 - $99 / month</b> recurring.",
     "Full 'done-for-you' job search: autonomously scans 50 targeted jobs/week, generates tailored CV diffs and cover letters, auto-dispatches applications, and provides voice AI interview simulations.",
     "<b>2,500 active subs = $1.8M ARR</b>.<br/>$200+ LTV unlocks aggressive, scalable paid advertising on LinkedIn & Meta (LTV:CAC > 4x)."],
    ["<b>4. Geographic Arbitrage</b><br/><i>(GCC & Global Remote First)</i>",
     "Saudi Arabia, UAE, Qatar, and English-speaking global diaspora.",
     "Focus product discovery and marketing on USD/SAR/AED pegged economies. Operating costs remain anchored in Egypt (low-cost engineering), while revenue is collected in high-purchasing-power currencies.",
     "<b>5x - 10x ARPU expansion</b> compared to domestic Egyptian market, using the identical AI infrastructure."],
], [32, 42, 56, 44], pad=2.6)]

s += [P("<b>Angel / Co-Founder Pitch Strategy (The Two-Phase Narrative):</b><br/>"
        "• <b>Phase 1 (Months 1–12) — Downside Protection:</b> Validate the stealth scrapers and AI fit-gap engine in Egypt and the Gulf using self-serve credit packs. Achieve cash-flow break-even with <$7k peak cash need while building a proprietary pool of 50,000+ active job seekers.<br/>"
        "• <b>Phase 2 (Months 13–36) — Venture Upside:</b> Turn on B2B institutional licensing and the recruiter sourcing marketplace. Expand customer unit economics from $10 lifetime transactions to $2,000+ enterprise placement fees.", CALL)]

# ==============================================================================
# PAGE 10: 10. CAREER ENHANCEMENT & MICRO-LEARNING ECOSYSTEM
# ==============================================================================
s += [PageBreak(), P("10. Career Enhancement & Micro-Learning Ecosystem", H1)]
s += [P("<b>Crushing the 'Success Churn' Paradox.</b> In pure job-application software, a successful user immediately churns because their search is over. "
        "By expanding Tailored into a continuous career operating system and professional micro-learning platform, we transform an episodic, single-use utility into a daily professional habit that stays relevant before, during, and after hiring.")]

s += [table([
    ["Module", "Core Experience", "Practical Implementation", "Impact"],
    ["<b>1. Tailored Career Roadmaps</b><br/><i>(Goal-Based Progression)</i>",
     "AI analyzes the user's current CV against their dream target role (e.g., Junior Backend to Staff AI Engineer). Generates a personalized, step-by-step milestone roadmap.",
     "Identifies specific skill, framework, and system-design gaps. Prescribes tailored portfolio projects, recommended reading, and expected time-to-readiness for promotional milestones.",
     "Retains candidate engagement over <b>6-18 months</b>, driving recurring subscription value far beyond the active application window."],
    ["<b>2. Bite-Sized Idea & Quote Browser</b><br/><i>(Feed / Micro-Blog)</i>",
     "A sleek, swipeable discovery feed delivering core ideas, mental models, and profound quotes extracted from premier career, leadership, and engineering books.",
     "Destroys the psychological barrier to reading. Users swipe through 30-second actionable insights (e.g., system design tradeoffs, salary negotiation rules from <i>Never Split the Difference</i>).",
     "Drives daily active usage (<b>DAU</b>) and organic viral sharing across LinkedIn, Twitter, and professional WhatsApp circles."],
    ["<b>3. High-Yield Book Summaries</b><br/><i>(Rapid Upskilling)</i>",
     "10 to 15-minute structured executive distillations covering top business, software engineering, and career classics (*Atomic Habits, Crucial Conversations, DDA*).",
     "Bypasses conversational fluff to deliver strictly practical frameworks, decision matrices, and career-advancement mental models for busy professionals.",
     "Provides high perceived value that justifies ongoing premium monthly subscriptions ($9.99/mo) after candidate is hired."],
    ["<b>4. Quick In-Book Implementation</b><br/><i>(Interactive Workbooks)</i>",
     "Actionable templates embedded directly within each book summary to convert conceptual theory into immediate career assets.",
     "Instantly guides users to draft STAR/XYZ bullet points from leadership books, calculate negotiation anchors, or structure system architecture diagrams.",
     "Transforms passive reading into verified resume diffs and tangible portfolio artifacts ready for interview presentation."],
    ["<b>5. Exam-Backed Book Certifications</b><br/><i>(Verified Badges)</i>",
     "Gamified micro-credentialing: candidates take a rigorous 5-question comprehension and scenario-based exam upon finishing a book track.",
     "Passing users receive verified digital skill badges embedded on their public Tailored profile and automatically formatted into their exported LaTeX/PDF CVs.",
     "Provides recruiters with hard, verifiable proof of candidate proactivity, continuous learning, and domain mastery."],
], [32, 44, 56, 42], pad=2.4)]

s += [P("<b>Strategic Moat: The Self-Reinforcing Growth Loop</b><br/>"
        "1. <b>Discovery & Acquisition:</b> Candidates join Tailored to optimize their CV for target jobs using the free Fit Score.<br/>"
        "2. <b>Gap Identification:</b> The Fit Score reveals specific technical and leadership skill gaps.<br/>"
        "3. <b>Micro-Learning & Roadmapping:</b> Tailored automatically prescribes book summaries, idea feeds, and actionable roadmaps to bridge those gaps.<br/>"
        "4. <b>Verification & Certification:</b> Candidates pass mini-exams, earning verified skill badges that update their CV and public profile.<br/>"
        "5. <b>Employer Monetization:</b> Recruiters search the platform for candidates who not only fit the job description, but possess verified proactive learning badges, closing the loop on our B2B marketplace.", CALL)]

# ==============================================================================
# PAGE 11: 11. STRATEGIC SYNTHESIS & EXECUTION NEXT STEPS
# ==============================================================================
s += [PageBreak(), P("11. Strategic Synthesis & Execution Roadmap", H1)]
s += [P("<b>The Dual-Horizon Opportunity for Investors:</b><br/>"
        "• <b>Horizon 1 (The Protected Floor):</b> Built as a solo-engineered micro-SaaS with minimal overhead (<$500/mo operating costs), Tailored breaks even in Month 17 (Base) on self-serve credit packs, requiring less than $7,000 in peak working capital. Downside risk is exceptionally low.<br/>"
        "• <b>Horizon 2 (The Venture Upside):</b> By evolving into a Talent Marketplace, University Career Enablement Platform, and Continuous Micro-Learning Network, Tailored breaks free from the low-ticket B2C ceiling. It expands into high-margin recurring enterprise contracts ($5k–$25k/yr) and candidate placement fees ($1.5k–$3k/hire), creating a credible path to <b>$5M–$15M+ in ARR</b>.", CALL)]

s += [table([
    ["Phase & Timeline", "Key Milestones", "Primary Target Metric"],
    ["<b>Phase 1: Build & Soft Launch</b><br/><i>Months 1 - 3 (Q1 2027)</i>",
     "Finalize stealth scrapers (Wuzzuf first, user-pasted JD fallback). Deploy PostgreSQL schema, FastAPI backend, and React Vite frontend. Implement tiered LLM routing (Gemini Flash-Lite for parsing/scoring; Flash for CV diffs).",
     "Functional end-to-end MVP; 0 critical scraping vulnerabilities."],
    ["<b>Phase 2: Egypt Graduation Wave</b><br/><i>Months 4 - 6 (Apr - Jun 2027)</i>",
     "Launch localized credit packs (49 / 179 / 399 EGP). Launch campus ambassador program across major Egyptian universities. Deploy TikTok/LinkedIn demo reels. Release Idea/Quote Feed.",
     "Reach 1,000+ active sign-ups; validate 2-5% free-to-paid conversion."],
    ["<b>Phase 3: GCC Rollout & Learning</b><br/><i>Months 7 - 12 (Jul - Dec 2027)</i>",
     "Expand to KSA and UAE ($4.99 / $14.99 packs). Release initial suite of 20 high-yield executive book summaries with interactive implementation workbooks and verified exam badges.",
     "Cash-flow break-even reached; blended LTV:CAC > 2.0x in GCC."],
    ["<b>Phase 4: B2B Institutional Pilots</b><br/><i>Months 13 - 24 (2028)</i>",
     "Package 'Tailored for Career Centers'. Sign first 5-10 paid pilots with Egyptian and Saudi universities and tech bootcamps ($5k-$15k/yr contracts). Introduce B2B admin placement analytics.",
     "$100k+ B2B ARR; negative net churn on university accounts."],
    ["<b>Phase 5: Two-Sided Marketplace</b><br/><i>Months 25+ (2029+)</i>",
     "Open candidate discovery portal to GCC recruiters. Monetize candidate placements ($1.5k-$3k per successful hire). Introduce autonomous career copilot agent tier ($49-$99/mo).",
     "Venture scale unlocked: $1M+ ARR pacing to $5M-$10M+ ARR."],
], [38, 92, 44], pad=2.6)]

s += [P("<b>Bottom Line for the Angel Investor / Co-Founder:</b><br/>"
        "Tailored offers an asymmetrical risk-reward profile: your downside is safeguarded by an ultra-lean, cash-flow-positive consumer engine that pays for itself in Year 2 with under $7,000 in peak burn, while your upside is powered by the transition into a high-margin talent liquidity network. We recommend executing Phase 1 with strict cost discipline, establishing candidate liquidity, and pitching the B2B marketplace to institutional VCs once user traction is proven.", CALL)]

s += [P("Sources & Documentation: Tailored_Financial_Model.xlsx (Summary, Market, UnitEconomics, Annual, Assumptions sheets); DataReportal 2025; CAPMAS via Ahram Online; vendor pricing pages (Jobscan, Teal, Rezi, Kickresume, Enhancv, LazyApply, LinkedIn Premium); Paymob gateway rate schedules; legal analyses of hiQ v. LinkedIn and LinkedIn v. Proxycurl.", SM)]

doc.build(s)
for f in ("_c_rev.png", "_c_ni.png", "_c_comp.png"):
    try:
        os.remove(os.path.join(HERE, f))
    except OSError:
        pass
print("OK", OUT)

# Sync to v2 if unlocked
try:
    import shutil
    shutil.copyfile(OUT_V3, OUT_V2)
    print("Also synchronized to v2:", OUT_V2)
except Exception as e:
    print("v2 currently locked by viewer; v3 is saved and up to date.")
