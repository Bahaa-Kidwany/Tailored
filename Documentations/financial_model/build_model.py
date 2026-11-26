"""Builds Tailored_Financial_Model.xlsx (all calculations are live Excel formulas).
Run: python build_model.py
"""
import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter as L
from openpyxl.chart import BarChart, LineChart, Reference

OUT = "Tailored_Financial_Model.xlsx"
NM = 60  # months
FIRST = 3  # first month column (C)
LASTC = L(FIRST + NM - 1)  # BJ
SCN = ["Downside", "Base", "Upside"]
SC = ["C", "D", "E"]

# ---------- styles ----------
NAVY = "1F2A44"
f_title = Font(name="Calibri", size=16, bold=True, color=NAVY)
f_hdr = Font(name="Calibri", bold=True, color="FFFFFF")
f_in = Font(name="Calibri", color="0000FF")
f_b = Font(name="Calibri", bold=True)
f_note = Font(name="Calibri", italic=True, color="666666", size=9)
fill_hdr = PatternFill("solid", fgColor=NAVY)
fill_sec = PatternFill("solid", fgColor="DCE6F2")
fill_in = PatternFill("solid", fgColor="FFF9E5")
fill_key = PatternFill("solid", fgColor="E8F5E9")
thin = Side(style="thin", color="BBBBBB")
USD = '$#,##0;[Red]($#,##0);-'
USD2 = '$#,##0.00;[Red]($#,##0.00);-'
USD4 = '$#,##0.0000'
NUM = '#,##0;[Red](#,##0);-'
NUM1 = '#,##0.0'
PCT = '0.0%'
GEN = 'General'

wb = Workbook()
wb.remove(wb.active)


def hdr_row(ws, r, c1, c2):
    for c in range(c1, c2 + 1):
        cell = ws.cell(r, c)
        cell.fill = fill_hdr
        cell.font = f_hdr
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)


def sec_row(ws, r, text, c2):
    ws.cell(r, 1, text).font = f_b
    for c in range(1, c2 + 1):
        ws.cell(r, c).fill = fill_sec


# =====================================================================
# ASSUMPTIONS
# =====================================================================
A = wb.create_sheet("Assumptions")
A.sheet_view.showGridLines = False
A["A1"] = "Assumptions"; A["A1"].font = f_title
A["A2"] = ("All money in USD unless stated. Blue cells on yellow = inputs you can change. "
           "Basis: Sourced = researched external data | Doc = your feasibility doc | Estimate = my judgement, validate before pitching.")
A["A2"].font = f_note
A.column_dimensions["A"].width = 52
A.column_dimensions["B"].width = 12
for c in "CDE":
    A.column_dimensions[c].width = 13
A.column_dimensions["F"].width = 11
A.column_dimensions["G"].width = 95
AR = {}
ar = [4]


def a_sec(title, scen=False):
    r = ar[0]
    sec_row(A, r, title, 7)
    if scen:
        for i, n in enumerate(SCN):
            A.cell(r, 3 + i, n).font = f_b
            A.cell(r, 3 + i).alignment = Alignment(horizontal="center")
    else:
        A.cell(r, 3, "Value").font = f_b
        A.cell(r, 3).alignment = Alignment(horizontal="center")
    A.cell(r, 6, "Basis").font = f_b
    A.cell(r, 7, "Source / note").font = f_b
    ar[0] += 1


def a_row(key, label, unit, vals, fmt, basis, note=""):
    r = ar[0]
    A.cell(r, 1, label)
    A.cell(r, 2, unit).font = f_note
    if not isinstance(vals, (list, tuple)):
        vals = [vals]
    for i, v in enumerate(vals):
        c = A.cell(r, 3 + i, v)
        c.number_format = fmt
        if isinstance(v, str) and v.startswith("="):
            c.font = Font(name="Calibri", color="000000")
        else:
            c.font = f_in
            c.fill = fill_in
        c.alignment = Alignment(horizontal="right")
    A.cell(r, 6, basis).font = f_note
    A.cell(r, 7, note).font = f_note
    AR[key] = r
    ar[0] += 1
    return r


def ref(key):  # common value
    return f"Assumptions!$C${AR[key]}"


def sref(key, s):  # scenario value
    return f"Assumptions!${SC[s]}${AR[key]}"


def lref(key):  # local (same sheet) common value
    return f"$C${AR[key]}"


# ---- General ----
a_sec("1. General & FX")
a_row("start", "Model start date (month 1)", "date", datetime.date(2027, 1, 1), "mmm-yyyy", "Estimate",
      "Jan-2027 start: 3 months build -> Egypt launch in Apr-2027, just before the graduation season.")
a_row("fx_egp", "EGP per 1 USD", "EGP", 53.4, '0.00', "Sourced", "Oct-2026 market rate ~53.4 (tradingeconomics / CBE / Banque Misr).")
a_row("fx_sar", "SAR per 1 USD (peg)", "SAR", 3.75, '0.0000', "Sourced", "Official fixed peg.")
a_row("fx_aed", "AED per 1 USD (peg)", "AED", 3.6725, '0.0000', "Sourced", "Official fixed peg.")
a_row("decay", "Annual decay of organic growth rate", "factor", 0.6, '0.00', "Estimate",
      "Organic monthly growth rate is multiplied by this each year after launch (growth slows as channels saturate).")
ar[0] += 1

# ---- Seasonality ----
a_sec("2. Seasonality index by calendar month (relative demand / signups)")
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
sea = [1.2, 1.1, 1.0, 0.9, 1.0, 1.2, 1.4, 1.4, 1.2, 1.1, 0.9, 0.7]
sea_note = {
    0: "Q1 hiring budgets unlock + year-end layoffs searching (your doc, section 3).",
    5: "Graduation season begins (Jun-Aug) - your doc section 3.1.",
    6: "Peak: new graduates flood LinkedIn/Wuzzuf.",
    7: "Peak: new graduates flood LinkedIn/Wuzzuf.",
    11: "Hiring freeze + holidays; low activity.",
}
r_sea1 = ar[0]
for i, m in enumerate(months):
    a_row(f"sea{i}", m, "index", sea[i], '0.00', "Estimate", sea_note.get(i, ""))
r_sea2 = ar[0] - 1
SEA_RANGE = f"Assumptions!$C${r_sea1}:$C${r_sea2}"
ar[0] += 1

# ---- Pricing ----
a_sec("3. Pricing (VAT-inclusive consumer prices)")
a_row("p1", "Egypt pack 1: Starter - price", "EGP", 49, NUM, "Doc", "5 credits. Your doc, section 8.2.")
a_row("p2", "Egypt pack 2: Job Hunter - price", "EGP", 179, NUM, "Doc", "25 credits.")
a_row("p3", "Egypt pack 3: Career Sprint - price", "EGP", 399, NUM, "Doc", "70 credits.")
a_row("c1", "Egypt pack 1 credits", "credits", 5, NUM, "Doc")
a_row("c2", "Egypt pack 2 credits", "credits", 25, NUM, "Doc")
a_row("c3", "Egypt pack 3 credits", "credits", 70, NUM, "Doc")
a_row("m1", "Egypt pack mix: Starter", "%", 0.40, PCT, "Estimate", "Share of orders. Must sum to 100%.")
a_row("m2", "Egypt pack mix: Job Hunter", "%", 0.45, PCT, "Estimate")
a_row("m3", "Egypt pack mix: Career Sprint", "%", 0.15, PCT, "Estimate")
a_row("aov_eg_egp", "Egypt average order value", "EGP",
      f"={lref('p1')}*{lref('m1')}+{lref('p2')}*{lref('m2')}+{lref('p3')}*{lref('m3')}", NUM, "Calc")
a_row("aov_eg", "Egypt average order value", "USD", f"={lref('aov_eg_egp')}/{lref('fx_egp')}", USD2, "Calc")
a_row("cred_eg", "Egypt average credits per order", "credits",
      f"={lref('c1')}*{lref('m1')}+{lref('c2')}*{lref('m2')}+{lref('c3')}*{lref('m3')}", NUM1, "Calc")
a_row("g1", "Gulf pack 1: Single Shot - price", "USD", 4.99, USD2, "Doc", "10 credits (~19 SAR / ~18 AED). Doc section 8.3.")
a_row("g2", "Gulf pack 2: Pro Hunter - price", "USD", 14.99, USD2, "Doc", "50 credits (~56 SAR / ~55 AED).")
a_row("gc1", "Gulf pack 1 credits", "credits", 10, NUM, "Doc")
a_row("gc2", "Gulf pack 2 credits", "credits", 50, NUM, "Doc")
a_row("gm1", "Gulf pack mix: Single Shot", "%", 0.60, PCT, "Estimate", "Share of orders. Pro Hunter = remainder.")
a_row("aov_gulf", "Gulf average order value", "USD", f"={lref('g1')}*{lref('gm1')}+{lref('g2')}*(1-{lref('gm1')})", USD2, "Calc")
a_row("cred_gulf", "Gulf average credits per order", "credits", f"={lref('gc1')}*{lref('gm1')}+{lref('gc2')}*(1-{lref('gm1')})", NUM1, "Calc")
a_row("subp_eg", "Optional monthly subscription - Egypt", "USD", 3.99, USD2, "Estimate", f"~213 EGP/mo; includes the credits below. You asked for an optional subscription alongside packs.")
a_row("subp_gulf", "Optional monthly subscription - Gulf", "USD", 9.99, USD2, "Estimate", "~37 SAR / ~37 AED per month.")
a_row("subc_eg", "Subscription credits per month - Egypt", "credits", 30, NUM, "Estimate")
a_row("subc_gulf", "Subscription credits per month - Gulf", "credits", 60, NUM, "Estimate")
a_row("util", "Subscription credit utilisation", "%", 0.60, PCT, "Estimate", "Subscribers rarely use all credits - lowers AI cost per sub.")
a_row("cpa_credit", "Credits per full application (tailored CV + cover letter)", "credits", 2, NUM, "Doc", "Doc section 8.1.")
a_row("apps_order_eg", "Applications generated per pack order - Egypt", "apps", f"={lref('cred_eg')}/{lref('cpa_credit')}", NUM1, "Calc", "Assumes buyers use all credits they buy.")
a_row("apps_order_gulf", "Applications generated per pack order - Gulf", "apps", f"={lref('cred_gulf')}/{lref('cpa_credit')}", NUM1, "Calc")
a_row("apps_sub_eg", "Applications generated per subscriber-month - Egypt", "apps", f"={lref('subc_eg')}*{lref('util')}/{lref('cpa_credit')}", NUM1, "Calc")
a_row("apps_sub_gulf", "Applications generated per subscriber-month - Gulf", "apps", f"={lref('subc_gulf')}*{lref('util')}/{lref('cpa_credit')}", NUM1, "Calc")
a_row("vat_eg", "VAT / sales tax - Egypt", "%", 0.14, PCT, "Estimate", "Prices assumed VAT-inclusive; revenue shown net of VAT. Verify digital-services VAT treatment with an accountant.")
a_row("vat_ks", "VAT - Saudi Arabia", "%", 0.15, PCT, "Estimate", "Standard KSA VAT.")
a_row("vat_ua", "VAT - UAE", "%", 0.05, PCT, "Estimate", "Standard UAE VAT.")
ar[0] += 1

# ---- AI cost ----
a_sec("4. AI & variable cost per unit")
a_row("tok_in_l", "Light LLM price: input (steps 1-2: parsing, fit scoring)", "$ / 1M tokens", 0.10, USD2, "Sourced", "Gemini 2.5 Flash-Lite list price. Structured extraction/scoring does not need a premium model.")
a_row("tok_out_l", "Light LLM price: output (steps 1-2)", "$ / 1M tokens", 0.40, USD2, "Sourced", "Gemini 2.5 Flash-Lite list price (GPT-4o-mini is similar: $0.15 / $0.60).")
a_row("tok_in", "Writing LLM price: input (steps 3-4: CV, cover letter)", "$ / 1M tokens", 0.30, USD2, "Sourced", "Gemini 2.5 Flash list price. Kept as a mid-tier model for writing quality.")
a_row("tok_out", "Writing LLM price: output (steps 3-4)", "$ / 1M tokens", 2.50, USD2, "Sourced", "Gemini 2.5 Flash list price (batch is 50% cheaper; cached input is 90% cheaper - not assumed).")
a_row("t1i", "Step 1 JD parsing - input tokens", "tokens", 1500, NUM, "Doc", "Token counts per pipeline step from your feasibility doc, section 5.1.")
a_row("t1o", "Step 1 JD parsing - output tokens", "tokens", 300, NUM, "Doc")
a_row("t2i", "Step 2 Fit evaluation - input tokens", "tokens", 2500, NUM, "Doc")
a_row("t2o", "Step 2 Fit evaluation - output tokens", "tokens", 500, NUM, "Doc")
a_row("t3i", "Step 3 CV tailoring - input tokens", "tokens", 3000, NUM, "Doc")
a_row("t3o", "Step 3 CV tailoring - output tokens", "tokens", 1200, NUM, "Doc")
a_row("t4i", "Step 4 Cover letter - input tokens", "tokens", 2500, NUM, "Doc")
a_row("t4o", "Step 4 Cover letter - output tokens", "tokens", 600, NUM, "Doc")
a_row("cost_app", "AI cost per full application (before multiplier)", "USD",
      f"=(({lref('t1i')}+{lref('t2i')})*{lref('tok_in_l')}+({lref('t1o')}+{lref('t2o')})*{lref('tok_out_l')}+({lref('t3i')}+{lref('t4i')})*{lref('tok_in')}+({lref('t3o')}+{lref('t4o')})*{lref('tok_out')})/1000000", USD4, "Calc",
      "Two-tier routing: light model for parsing/scoring, mid-tier for writing. Your doc estimated $0.0052.")
a_row("evals", "Free job evaluations per sign-up (steps 1-2 only)", "jobs", 8, NUM, "Estimate", "Free hook: each new user evaluates ~8 jobs before buying.")
a_row("cost_free", "AI cost per sign-up (free evaluations)", "USD",
      f"={lref('evals')}*(({lref('t1i')}+{lref('t2i')})*{lref('tok_in_l')}+({lref('t1o')}+{lref('t2o')})*{lref('tok_out_l')})/1000000", USD4, "Calc")
a_row("cpj", "Scraping / proxy cost per job fetched", "USD", 0, USD4, "Estimate", "Set to 0 by you (own scraping setup, no paid proxies). If blocking forces residential proxies expect ~$0.006/job.")
a_row("pf_eg", "Payment fee % - Egypt (Paymob)", "%", 0.0275, '0.00%', "Sourced", "Paymob Egypt cards: 2.75% + 3 EGP.")
a_row("pf_ks", "Payment fee % - Saudi Arabia", "%", 0.027, '0.00%', "Sourced", "Paymob KSA: Mada 1% + 1 SAR, international cards 2.7-3.5% + 1 SAR. 2.7% used for blended.")
a_row("pf_ua", "Payment fee % - UAE", "%", 0.029, '0.00%', "Sourced", "Paymob / Stripe UAE: 2.9% + 1 AED.")
a_row("ff_eg", "Payment fixed fee - Egypt", "USD", f"=3/{lref('fx_egp')}", USD4, "Calc", "3 EGP per transaction.")
a_row("ff_ks", "Payment fixed fee - Saudi Arabia", "USD", f"=1/{lref('fx_sar')}", USD4, "Calc", "1 SAR per transaction.")
a_row("ff_ua", "Payment fixed fee - UAE", "USD", f"=1/{lref('fx_aed')}", USD4, "Calc", "1 AED per transaction.")
ar[0] += 1

# ---- Fixed costs ----
a_sec("5. Fixed & people costs (monthly)")
a_row("vps", "Cloud server + database (single small VPS)", "USD/mo", 12, USD, "Estimate", "Lean: one small Hetzner/DO VPS (~$6-12) with dockerised Postgres on the same box. Cut from $25.")
a_row("proxy", "Scraping base plan (proxies / stealth tooling)", "USD/mo", 0, USD, "Estimate", "Set to 0 by you.")
a_row("dns", "Domain, DNS, email, monitoring", "USD/mo", 6, USD, "Estimate", "Domain ~$1.5/mo + Cloudflare free + transactional email free tier + free uptime monitor. Cut from $20.")
a_row("varinfra", "Extra infra per 1,000 monthly sign-ups", "USD", 5, USD, "Estimate", "Edited by you ($10 -> $5). Scales hosting/DB as volume grows.")
a_row("tools", "Software tools (Figma, analytics, GitHub, etc.)", "USD/mo", 0, USD, "Estimate", "Set to 0 by you (free tiers).")
a_row("legal", "Accounting & legal retainer", "USD/mo", 0, USD, "Estimate", "Set to 0 by you. Note: a registered company still needs yearly bookkeeping/tax filing - covered only by the one-time cost below.")
a_row("designer", "Freelance designer / content creator: cost per engagement", "USD", 720, USD, "Estimate", "Per-project, not monthly. You edited this to $120/mo (= $1,440/yr) -> modelled as 2 engagements x $720.")
a_row("des_n", "  Designer engagements per year (1 or 2)", "per year", 2, NUM, "Estimate", "First engagement in the Egypt launch month, then every 12/n months.")
a_row("onetime", "One-time launch costs (month 1)", "USD", 2900, USD, "Estimate", "Company registration/licences ~$1,500, brand & landing ~$800, ToS/privacy ~$600.")
a_row("cont", "Contingency on operating costs", "%", 0.05, PCT, "Estimate", "Applied to infrastructure, tools, legal, designer and hires. Cut from 8%.")
a_row("sal", "Founder market salary (when triggered)", "USD/mo", 1000, USD, "Estimate", "Edited by you (was $2,500). Paid only after trigger below.")
a_row("sal_g", "Salary growth per year", "%", 0.10, PCT, "Estimate", "Egypt wage inflation.")
a_row("oncost", "Employer on-cost (social insurance etc.)", "%", 0.1875, PCT, "Estimate", "Egypt employer social insurance ~18.75% - verify.")
a_row("sal_trig", "Salary trigger: trailing-3-mo avg profit before salary must exceed salary cost x", "x", 1.5, '0.0', "Estimate", "Zero salary at first, then market salary once the business can afford it (your choice). Once triggered it stays on.")
a_row("h1_on", "Optional hire 1: part-time support/QA (1 = on)", "flag", 0, GEN, "Estimate", "Off by default (you asked for solo + designer). Switch on to see team-expansion impact.")
a_row("h1_trig", "  Hire 1 trigger: prior-month revenue >=", "USD/mo", 8000, USD, "Estimate")
a_row("h1_cost", "  Hire 1 monthly cost", "USD/mo", 600, USD, "Estimate")
a_row("h2_on", "Optional hire 2: second engineer (1 = on)", "flag", 0, GEN, "Estimate", "Off by default.")
a_row("h2_trig", "  Hire 2 trigger: prior-month revenue >=", "USD/mo", 25000, USD, "Estimate")
a_row("h2_cost", "  Hire 2 monthly cost", "USD/mo", 3000, USD, "Estimate")
a_row("tax", "Corporate income tax rate", "%", 0.225, PCT, "Estimate", "Egypt standard 22.5% (small-business regimes may be lower). Losses carried forward.")
ar[0] += 1

# ---- Market ----
a_sec("6. Market inputs")
a_row("li_eg", "LinkedIn members - Egypt", "people", 13500000, NUM, "Sourced", "DataReportal 2025: 13.0-13.7M.")
a_row("li_ks", "LinkedIn members - Saudi Arabia", "people", 11200000, NUM, "Sourced", "DataReportal 2025: 11.0-11.3M.")
a_row("li_ua", "LinkedIn members - UAE", "people", 9600000, NUM, "Sourced", "DataReportal 2025: 9.4-9.7M (very high penetration, many expats).")
a_row("seek", "Share of members actively job-seeking per year", "%", 0.18, PCT, "Doc", "Doc section 2.2 uses 18%.")
a_row("addr", "Share of seekers addressable by Tailored", "%", 0.35, PCT, "Estimate", "English/bilingual white-collar, digitally able to pay online by card/wallet.")
a_row("spend_eg", "Expected annual spend per paying user - Egypt", "USD", 8, USD, "Estimate", "Used only for SAM value.")
a_row("spend_gulf", "Expected annual spend per paying user - Gulf", "USD", 22, USD, "Estimate")
a_row("grads_eg", "Egypt higher-ed graduates per year (reference)", "people", 738000, NUM, "Doc", "CAPMAS, per doc section 2.1.")
ar[0] += 1

# ---- Marketing split ----
a_sec("7. Paid marketing allocation")
a_row("sh_eg", "Share of paid budget - Egypt", "%", 0.40, PCT, "Estimate", "Redistributed automatically to launched markets only.")
a_row("sh_ks", "Share of paid budget - Saudi Arabia", "%", 0.30, PCT, "Estimate")
a_row("sh_ua", "Share of paid budget - UAE", "%", 0.30, PCT, "Estimate")
a_row("clk2sign", "Ad click -> free sign-up rate", "%", 0.20, PCT, "Sourced", "Job-seeker landing page with free evaluation hook; resume-tool funnels see ~10-20% visitor-to-signup. Cost per sign-up = CPC / this rate.")
ar[0] += 1

# ---- Funding ----
a_sec("8. Funding (angel / co-founder investment)")
a_row("raise", "Investment amount", "USD", 30000, USD, "Estimate", "PLACEHOLDER - set the real ticket size. Model shows whether it is enough (see Summary).")
a_row("raise_m", "Month received", "month #", 1, NUM, "Estimate")
a_row("stake", "Investor equity for this investment", "%", 0.20, PCT, "Estimate", "PLACEHOLDER - change to the agreed co-founder split.")
ar[0] += 1

# ---- Scenario drivers ----
a_sec("9. Scenario drivers (Downside / Base / Upside)", scen=True)
a_row("launch_eg", "Egypt launch month (month # of model)", "month #", [5, 4, 4], NUM, "Estimate", "Base: 3 months build, launch Apr-2027.")
a_row("launch_gcc", "Gulf (KSA + UAE) launch month", "month #", [16, 10, 7], NUM, "Estimate", "Base: Oct-2027, after Egypt validation.")
a_row("org_eg", "Egypt organic sign-ups in launch month", "users", [150, 300, 500], NUM, "Estimate", "LinkedIn/TikTok content, campus communities, referrals.")
a_row("org_ks", "KSA organic sign-ups in launch month", "users", [50, 120, 200], NUM, "Estimate")
a_row("org_ua", "UAE organic sign-ups in launch month", "users", [50, 120, 200], NUM, "Estimate")
a_row("org_g", "Organic growth per month (year 1 after launch)", "%", [0.05, 0.08, 0.11], PCT, "Estimate", "Decays each year by the factor in section 1.")
a_row("paid_floor", "Paid marketing budget (minimum, per month)", "USD/mo", [200, 350, 500], USD, "Doc", "Your stated range: $200-500/month.")
a_row("paid_pct", "Paid budget: reinvest % of prior-month revenue (if higher)", "%", [0.10, 0.15, 0.20], PCT, "Estimate", "Budget = max(minimum, % of last month's revenue).")
a_row("cpc_eg", "Meta ad cost per click - Egypt", "USD", [0.30, 0.20, 0.12], USD2, "Sourced", "Egypt CPC $0.05-0.35 (CPM $1.0-2.8) - lebesgue/adamigo benchmarks. Base = mid-range.")
a_row("cpc_ks", "Meta ad cost per click - KSA", "USD", [2.00, 1.20, 0.80], USD2, "Sourced", "KSA CPC $0.80-2.00 (CPM $10-13.5).")
a_row("cpc_ua", "Meta ad cost per click - UAE", "USD", [1.80, 1.10, 0.70], USD2, "Sourced", "UAE CPC $0.70-1.80 (CPM $9-11.5).")
a_row("cpa_eg", "Cost per paid sign-up - Egypt", "USD", [f"={SC[i]}{AR['cpc_eg']}/$C${AR['clk2sign']}" for i in range(3)], USD2, "Calc", "CPC / click-to-signup rate. Lowered from $2.0 to ~$1.0 based on Egypt CPC data.")
a_row("cpa_ks", "Cost per paid sign-up - KSA", "USD", [f"={SC[i]}{AR['cpc_ks']}/$C${AR['clk2sign']}" for i in range(3)], USD2, "Calc", "Raised vs. my first estimate ($4): researched Gulf CPCs are ~5x Egypt's.")
a_row("cpa_ua", "Cost per paid sign-up - UAE", "USD", [f"={SC[i]}{AR['cpc_ua']}/$C${AR['clk2sign']}" for i in range(3)], USD2, "Calc", "Gulf paid ads are structurally expensive - organic should lead there.")
a_row("conv_eg", "Free -> paid conversion - Egypt", "%", [0.025, 0.04, 0.06], PCT, "Sourced", "Pay-per-use utilities: 3-8% free-to-paid (vs 2-5% for subscription freemium). Egypt = lower end.")
a_row("conv_ks", "Free -> paid conversion - KSA", "%", [0.035, 0.05, 0.075], PCT, "Sourced", "Same 3-8% range; higher purchasing power.")
a_row("conv_ua", "Free -> paid conversion - UAE", "%", [0.04, 0.06, 0.08], PCT, "Sourced", "Same 3-8% range; expat professionals with urgent job-search need.")
a_row("pen", "Max sign-ups per rolling 12 months, % of SAM", "%", [0.025, 0.04, 0.06], PCT, "Estimate", "Realism cap tied to market size - growth stops when this share of the market is reached each year.")
a_row("rep", "Pack buyers: monthly repeat-purchase rate (of buyer pool)", "%", [0.15, 0.20, 0.25], PCT, "Estimate", "Job seekers re-buy credits while searching.")
a_row("pchurn", "Pack buyer pool: monthly churn (got hired / stopped)", "%", [0.45, 0.35, 0.30], PCT, "Estimate", "Avg job search ~3 months.")
a_row("subshare", "Share of new paying users choosing subscription", "%", [0.10, 0.20, 0.30], PCT, "Estimate")
a_row("subchurn", "Subscription monthly churn", "%", [0.35, 0.25, 0.18], PCT, "Sourced", "General B2C subs 10-15%/mo, but job-seekers have 'success churn' (1-3 month lifecycle) -> 25% base (avg 4 months). Raised from 12%: my first value was too optimistic.")
a_row("dep", "EGP annual depreciation vs USD", "%", [0.15, 0.08, 0.04], PCT, "Estimate", "Egypt has a history of devaluation - key risk for Egypt USD revenue.")
a_row("pass", "Share of depreciation recovered via EGP price increases", "%", [0.50, 0.60, 0.70], PCT, "Estimate")
a_row("llm_mult", "AI cost multiplier (retries, longer CVs, price changes)", "x", [1.5, 1.2, 1.0], '0.00', "Estimate")
a_row("exit_mult", "Exit valuation: EV / revenue multiple (year 5)", "x", [1.5, 2.5, 3.5], '0.0', "Estimate", "Small bootstrapped B2C SaaS typically 1-4x revenue. Illustrative only.")
A.freeze_panes = "C4"

# =====================================================================
# MARKET
# =====================================================================
M = wb.create_sheet("Market")
M.sheet_view.showGridLines = False
M["A1"] = "Market sizing"; M["A1"].font = f_title
M["A2"] = "TAM -> SAM -> SOM per country. SOM is pulled from the Base scenario (year 5)."; M["A2"].font = f_note
M.column_dimensions["A"].width = 52
for c in "BCDE":
    M.column_dimensions[c].width = 16
M.column_dimensions["F"].width = 70
for i, h in enumerate(["Metric", "Egypt", "KSA", "UAE", "Total"]):
    M.cell(4, 1 + i, h)
hdr_row(M, 4, 1, 5)
rows = {}
mr = 5


def m_row(key, label, f_eg, f_ks, f_ua, fmt, total=True, note=""):
    global mr
    M.cell(mr, 1, label)
    for i, f in enumerate([f_eg, f_ks, f_ua]):
        c = M.cell(mr, 2 + i, f)
        c.number_format = fmt
    if total:
        M.cell(mr, 5, f"=SUM(B{mr}:D{mr})").number_format = fmt
    M.cell(mr, 6, note).font = f_note
    rows[key] = mr
    mr += 1


m_row("tam", "TAM: LinkedIn professionals (members)", f"={ref('li_eg')}", f"={ref('li_ks')}", f"={ref('li_ua')}", NUM, note="DataReportal 2025")
m_row("seek", "Active job seekers per year", *[f"={c}{rows['tam']}*{ref('seek')}" for c in "BCD"], NUM, note="18% of members (doc)")
m_row("sam", "SAM: addressable seekers (English/bilingual, can pay online)", *[f"={c}{rows['seek']}*{ref('addr')}" for c in "BCD"], NUM, note="35% of active seekers (estimate)")
m_row("spend", "Annual spend per paying user", f"={ref('spend_eg')}", f"={ref('spend_gulf')}", f"={ref('spend_gulf')}", USD, total=False)
m_row("conv", "Base free->paid conversion", f"={sref('conv_eg', 1)}", f"={sref('conv_ks', 1)}", f"={sref('conv_ua', 1)}", PCT, total=False)
m_row("samv", "SAM value per year (SAM x conversion x spend)", *[f"={c}{rows['sam']}*{c}{rows['conv']}*{c}{rows['spend']}" for c in "BCD"], USD, note="Annual revenue pool if you served the whole SAM once")
m_row("tamv", "TAM value per year (members x seek% x conv x spend)", *[f"={c}{rows['seek']}*{c}{rows['conv']}*{c}{rows['spend']}" for c in "BCD"], USD, note="Upper bound incl. users outside current positioning")
SAM = {"eg": f"Market!$B${rows['sam']}", "ks": f"Market!$C${rows['sam']}", "ua": f"Market!$D${rows['sam']}"}
mr += 1
M.cell(mr, 1, "SOM (Base scenario, year 5)").font = f_b
for c in range(1, 6):
    M.cell(mr, c).fill = fill_sec
mr += 1
M_SOM_START = mr

# =====================================================================
# MODEL ENGINE (one sheet per scenario)
# =====================================================================
CTRY = {
    "eg": dict(name="Egypt", launch="launch_eg", org="org_eg", cpa="cpa_eg", conv="conv_eg", vat="vat_eg",
               aov="aov_eg", subp="subp_eg", ao="apps_order_eg", asub="apps_sub_eg", pf="pf_eg", ff="ff_eg", share="sh_eg"),
    "ks": dict(name="Saudi Arabia", launch="launch_gcc", org="org_ks", cpa="cpa_ks", conv="conv_ks", vat="vat_ks",
               aov="aov_gulf", subp="subp_gulf", ao="apps_order_gulf", asub="apps_sub_gulf", pf="pf_ks", ff="ff_ks", share="sh_ks"),
    "ua": dict(name="UAE", launch="launch_gcc", org="org_ua", cpa="cpa_ua", conv="conv_ua", vat="vat_ua",
               aov="aov_gulf", subp="subp_gulf", ao="apps_order_gulf", asub="apps_sub_gulf", pf="pf_ua", ff="ff_ua", share="sh_ua"),
}
CK = ["eg", "ks", "ua"]


def build_engine(s):
    ws = wb.create_sheet(f"Model_{SCN[s]}")
    ws.sheet_view.showGridLines = False
    ws["A1"] = f"Monthly engine - {SCN[s]} scenario (60 months)"; ws["A1"].font = f_title
    ws["A2"] = "All cells are formulas driven by the Assumptions sheet. Do not type over them."; ws["A2"].font = f_note
    ws.column_dimensions["A"].width = 46
    ws.column_dimensions["B"].width = 10
    for t in range(1, NM + 1):
        ws.column_dimensions[L(FIRST + t - 1)].width = 11

    spec = []  # (key,label,unit,fmt) or ('sec',title)

    def sec(t):
        spec.append(("sec", t))

    def r_(k, label, unit, fmt):
        spec.append((k, label, unit, fmt))

    sec("TIMING & FLAGS")
    for c in CK:
        r_(f"f_{c}", f"{CTRY[c]['name']} launched (1/0)", "flag", GEN)
    r_("f_any", "Any market launched", "flag", GEN)
    r_("season", "Seasonality factor", "x", '0.00')
    sec("PAID MARKETING")
    r_("budget", "Total paid marketing budget", "USD", USD)
    for c in CK:
        r_(f"al_{c}", f"  Allocated - {CTRY[c]['name']}", "USD", USD)
    for c in CK:
        spec_c = CTRY[c]
        sec(f"CUSTOMERS & REVENUE - {spec_c['name'].upper()}")
        r_(f"ob_{c}", "Organic base level (before seasonality)", "users", NUM)
        r_(f"og_{c}", "Organic sign-ups", "users", NUM)
        r_(f"pd_{c}", "Paid sign-ups (uncapped)", "users", NUM)
        r_(f"cap_{c}", "Headroom under rolling 12m market cap", "users", NUM)
        r_(f"sg_{c}", "Sign-ups (free users)", "users", NUM)
        r_(f"np_{c}", "New paying users", "users", NUM1)
        r_(f"ns_{c}", "  of which choose subscription", "users", NUM1)
        r_(f"nk_{c}", "  of which choose credit packs", "users", NUM1)
        r_(f"sb_{c}", "Active subscribers (end of month)", "users", NUM1)
        r_(f"pl_{c}", "Pack-buyer pool (end of month)", "users", NUM1)
        r_(f"rp_{c}", "Repeat pack buyers", "users", NUM1)
        r_(f"od_{c}", "Pack orders", "orders", NUM1)
        if c == "eg":
            r_("fxf", "EGP depreciation factor on Egypt prices (USD value)", "x", '0.000')
        r_(f"bl_{c}", "Gross billings incl. VAT", "USD", USD)
        r_(f"rv_{c}", "Net revenue (ex-VAT)", "USD", USD)
        r_(f"fe_{c}", "Payment processing fees", "USD", USD)
        r_(f"ap_{c}", "Applications generated", "apps", NUM)
        r_(f"ai_{c}", "AI cost", "USD", USD)
    sec("TOTALS")
    r_("sg", "Total sign-ups", "users", NUM)
    r_("np", "Total new paying users", "users", NUM1)
    r_("sb", "Total active subscribers", "users", NUM1)
    r_("npc", "Cumulative paying users", "users", NUM)
    r_("ap", "Total applications generated", "apps", NUM)
    sec("PROFIT & LOSS")
    r_("rev", "Net revenue", "USD", USD)
    r_("c_ai", "AI cost", "USD", USD)
    r_("c_fee", "Payment fees", "USD", USD)
    r_("c_scr", "Scraping / proxy variable cost", "USD", USD)
    r_("gp", "Gross profit", "USD", USD)
    r_("gm", "Gross margin %", "%", PCT)
    r_("infra", "Infrastructure (fixed + volume)", "USD", USD)
    r_("tl", "Tools + accounting/legal", "USD", USD)
    r_("des", "Freelance designer / content", "USD", USD)
    r_("h1f", "  Hire 1 active flag", "flag", GEN)
    r_("h2f", "  Hire 2 active flag", "flag", GEN)
    r_("hire", "Optional hires", "USD", USD)
    r_("ot", "One-time launch costs", "USD", USD)
    r_("mk", "Paid marketing", "USD", USD)
    r_("ct", "Contingency", "USD", USD)
    r_("pre", "EBITDA before founder salary", "USD", USD)
    r_("sf", "  Founder salary active flag", "flag", GEN)
    r_("sfull", "  Founder market salary cost (incl. on-cost)", "USD", USD)
    r_("sl", "Founder salary paid", "USD", USD)
    r_("eb", "EBITDA / pre-tax profit", "USD", USD)
    r_("cum", "Cumulative pre-tax profit", "USD", USD)
    r_("tx", "Income tax (after loss carry-forward)", "USD", USD)
    r_("ni", "Net income", "USD", USD)
    sec("CASH")
    r_("fund", "Investment received", "USD", USD)
    r_("cfo", "Operating cash flow (= net income)", "USD", USD)
    r_("cumo", "Cumulative operating cash flow (funding need)", "USD", USD)
    r_("cash", "Closing cash balance", "USD", USD)
    sec("FLAGS FOR SUMMARY")
    r_("be", "Break-even flag (EBITDA > 0 for this + next 2 months)", "flag", GEN)
    r_("cn", "Cash negative flag", "flag", GEN)

    # header rows
    ws.cell(3, 1, "Month #")
    ws.cell(4, 1, "Month")
    ws.cell(5, 1, "Calendar month")
    ws.cell(6, 1, "Model year")
    for t in range(1, NM + 1):
        c = L(FIRST + t - 1)
        ws[f"{c}3"] = t
        ws[f"{c}4"] = f"=EDATE({ref('start')},{c}3-1)"
        ws[f"{c}4"].number_format = "mmm-yy"
        ws[f"{c}5"] = f"=MONTH({c}4)"
        ws[f"{c}6"] = f"=INT(({c}3-1)/12)+1"
    hdr_row(ws, 3, 1, FIRST + NM - 1)
    for r in (4, 5, 6):
        for cc in range(1, FIRST + NM):
            ws.cell(r, cc).font = f_b
            ws.cell(r, cc).fill = fill_sec
            if cc >= FIRST:
                ws.cell(r, cc).alignment = Alignment(horizontal="center")
    R = {}
    r = 8
    sec_rows = []
    for item in spec:
        if item[0] == "sec":
            sec_row(ws, r, item[1], FIRST + NM - 1)
            r += 1
        else:
            R[item[0]] = r
            ws.cell(r, 1, item[1])
            ws.cell(r, 2, item[2]).font = f_note
            r += 1

    def X(k, c):
        return f"{c}{R[k]}"

    def rng(k, t1, t2):
        return f"{L(FIRST + t1 - 1)}{R[k]}:{L(FIRST + t2 - 1)}{R[k]}"

    S = lambda k: sref(k, s)
    for t in range(1, NM + 1):
        c = L(FIRST + t - 1)
        p = L(FIRST + t - 2) if t > 1 else None
        n1 = L(FIRST + t) if t < NM else None
        mm = f"{c}$3"
        fm = {}
        for k in CK:
            P = CTRY[k]
            fm[f"f_{k}"] = f"=IF({mm}>={S(P['launch'])},1,0)"
        fm["f_any"] = f"=MAX({X('f_eg', c)},{X('f_ks', c)},{X('f_ua', c)})"
        fm["season"] = f"=INDEX({SEA_RANGE},{c}$5)/AVERAGE({SEA_RANGE})"
        if t == 1:
            fm["budget"] = f"={X('f_any', c)}*{S('paid_floor')}"
        else:
            fm["budget"] = f"={X('f_any', c)}*MAX({S('paid_floor')},{S('paid_pct')}*{X('rev', p)})"
        den = "+".join(f"{ref(CTRY[k]['share'])}*{X('f_' + k, c)}" for k in CK)
        for k in CK:
            fm[f"al_{k}"] = f"=IFERROR({X('budget', c)}*{ref(CTRY[k]['share'])}*{X('f_' + k, c)}/({den}),0)"
        for k in CK:
            P = CTRY[k]
            g = S("org_g")
            if t == 1:
                fm[f"ob_{k}"] = f"=IF({mm}={S(P['launch'])},{S(P['org'])},0)"
            else:
                fm[f"ob_{k}"] = (f"=IF({mm}<{S(P['launch'])},0,IF({mm}={S(P['launch'])},{S(P['org'])},"
                                 f"{X('ob_' + k, p)}*(1+{g}*{ref('decay')}^INT(({mm}-{S(P['launch'])})/12))))")
            fm[f"og_{k}"] = f"={X('ob_' + k, c)}*{X('season', c)}"
            fm[f"pd_{k}"] = f"={X('al_' + k, c)}/{S(P['cpa'])}"
            if t == 1:
                fm[f"cap_{k}"] = f"=MAX(0,{SAM[k]}*{S('pen')})"
            else:
                t1 = max(1, t - 11)
                fm[f"cap_{k}"] = f"=MAX(0,{SAM[k]}*{S('pen')}-SUM({rng('sg_' + k, t1, t - 1)}))"
            fm[f"sg_{k}"] = f"=MIN({X('og_' + k, c)}+{X('pd_' + k, c)},{X('cap_' + k, c)})*{X('f_' + k, c)}"
            fm[f"np_{k}"] = f"={X('sg_' + k, c)}*{S(P['conv'])}"
            fm[f"ns_{k}"] = f"={X('np_' + k, c)}*{S('subshare')}"
            fm[f"nk_{k}"] = f"={X('np_' + k, c)}-{X('ns_' + k, c)}"
            if t == 1:
                fm[f"sb_{k}"] = f"={X('ns_' + k, c)}"
                fm[f"pl_{k}"] = f"={X('nk_' + k, c)}"
                fm[f"rp_{k}"] = "=0"
            else:
                fm[f"sb_{k}"] = f"={X('sb_' + k, p)}*(1-{S('subchurn')})+{X('ns_' + k, c)}"
                fm[f"pl_{k}"] = f"={X('pl_' + k, p)}*(1-{S('pchurn')})+{X('nk_' + k, c)}"
                fm[f"rp_{k}"] = f"={X('pl_' + k, p)}*{S('rep')}"
            fm[f"od_{k}"] = f"={X('nk_' + k, c)}+{X('rp_' + k, c)}"
            fx = X("fxf", c) if k == "eg" else "1"
            if k == "eg":
                fm["fxf"] = f"=1/(1+{S('dep')}*(1-{S('pass')}))^(({mm}-1)/12)"
            fm[f"bl_{k}"] = f"=({X('od_' + k, c)}*{ref(P['aov'])}+{X('sb_' + k, c)}*{ref(P['subp'])})*{fx}"
            fm[f"rv_{k}"] = f"={X('bl_' + k, c)}/(1+{ref(P['vat'])})"
            fm[f"fe_{k}"] = f"={X('bl_' + k, c)}*{ref(P['pf'])}+({X('od_' + k, c)}+{X('sb_' + k, c)})*{ref(P['ff'])}"
            fm[f"ap_{k}"] = f"={X('od_' + k, c)}*{ref(P['ao'])}+{X('sb_' + k, c)}*{ref(P['asub'])}"
            fm[f"ai_{k}"] = f"=({X('ap_' + k, c)}*{ref('cost_app')}+{X('sg_' + k, c)}*{ref('cost_free')})*{S('llm_mult')}"
        fm["sg"] = "=" + "+".join(X(f"sg_{k}", c) for k in CK)
        fm["np"] = "=" + "+".join(X(f"np_{k}", c) for k in CK)
        fm["sb"] = "=" + "+".join(X(f"sb_{k}", c) for k in CK)
        fm["npc"] = f"={X('np', c)}" if t == 1 else f"={X('npc', p)}+{X('np', c)}"
        fm["ap"] = "=" + "+".join(X(f"ap_{k}", c) for k in CK)
        fm["rev"] = "=" + "+".join(X(f"rv_{k}", c) for k in CK)
        fm["c_ai"] = "=" + "+".join(X(f"ai_{k}", c) for k in CK)
        fm["c_fee"] = "=" + "+".join(X(f"fe_{k}", c) for k in CK)
        fm["c_scr"] = f"={X('sg', c)}*{ref('evals')}*{ref('cpj')}"
        fm["gp"] = f"={X('rev', c)}-{X('c_ai', c)}-{X('c_fee', c)}-{X('c_scr', c)}"
        fm["gm"] = f"=IFERROR({X('gp', c)}/{X('rev', c)},0)"
        fm["infra"] = f"={ref('vps')}+{ref('proxy')}+{ref('dns')}+{X('sg', c)}/1000*{ref('varinfra')}"
        fm["tl"] = f"={ref('tools')}+{ref('legal')}"
        fm["des"] = (f"=IF(AND({X('f_eg', c)}=1,MOD({mm}-{S('launch_eg')},ROUND(12/{ref('des_n')},0))=0),{ref('designer')},0)")
        if t == 1:
            fm["h1f"] = "=0"
            fm["h2f"] = "=0"
        else:
            fm["h1f"] = f"=IF({X('h1f', p)}=1,1,IF(AND({ref('h1_on')}=1,{X('rev', p)}>={ref('h1_trig')}),1,0))"
            fm["h2f"] = f"=IF({X('h2f', p)}=1,1,IF(AND({ref('h2_on')}=1,{X('rev', p)}>={ref('h2_trig')}),1,0))"
        fm["hire"] = f"={X('h1f', c)}*{ref('h1_cost')}+{X('h2f', c)}*{ref('h2_cost')}"
        fm["ot"] = f"=IF({mm}=1,{ref('onetime')},0)"
        fm["mk"] = f"={X('budget', c)}"
        fm["ct"] = f"=({X('infra', c)}+{X('tl', c)}+{X('des', c)}+{X('hire', c)})*{ref('cont')}"
        fm["pre"] = (f"={X('gp', c)}-{X('infra', c)}-{X('tl', c)}-{X('des', c)}-{X('hire', c)}-{X('ot', c)}-{X('mk', c)}-{X('ct', c)}")
        fm["sfull"] = f"={ref('sal')}*(1+{ref('sal_g')})^({c}$6-1)*(1+{ref('oncost')})"
        if t == 1:
            fm["sf"] = "=0"
        else:
            t1 = max(1, t - 3)
            fm["sf"] = f"=IF({X('sf', p)}=1,1,IF(AVERAGE({rng('pre', t1, t - 1)})>={ref('sal_trig')}*{X('sfull', c)},1,0))"
        fm["sl"] = f"={X('sf', c)}*{X('sfull', c)}"
        fm["eb"] = f"={X('pre', c)}-{X('sl', c)}"
        fm["cum"] = f"={X('eb', c)}" if t == 1 else f"={X('cum', p)}+{X('eb', c)}"
        if t == 1:
            fm["tx"] = f"=MAX(0,{ref('tax')}*MAX(0,{X('cum', c)}))"
        else:
            fm["tx"] = f"=MAX(0,{ref('tax')}*(MAX(0,{X('cum', c)})-MAX(0,{X('cum', p)})))"
        fm["ni"] = f"={X('eb', c)}-{X('tx', c)}"
        fm["fund"] = f"=IF({mm}={ref('raise_m')},{ref('raise')},0)"
        fm["cfo"] = f"={X('ni', c)}"
        fm["cumo"] = f"={X('cfo', c)}" if t == 1 else f"={X('cumo', p)}+{X('cfo', c)}"
        fm["cash"] = f"={X('fund', c)}+{X('cfo', c)}" if t == 1 else f"={X('cash', p)}+{X('fund', c)}+{X('cfo', c)}"
        if t <= NM - 2:
            n2 = L(FIRST + t + 1)
            fm["be"] = f"=IF(AND({X('eb', c)}>0,{X('eb', n1)}>0,{X('eb', n2)}>0),1,0)"
        else:
            fm["be"] = "=0"
        fm["cn"] = f"=IF({X('cash', c)}<0,1,0)"
        for k, f in fm.items():
            cell = ws[f"{c}{R[k]}"]
            cell.value = f
    # formats
    fmt_map = {i[0]: i[3] for i in spec if i[0] != "sec"}
    for k, rr in R.items():
        for t in range(1, NM + 1):
            ws.cell(rr, FIRST + t - 1).number_format = fmt_map[k]
    for k in ("rev", "gp", "eb", "ni", "cash"):
        for cc in range(1, FIRST + NM):
            ws.cell(R[k], cc).font = f_b
    ws.freeze_panes = "C7"
    return ws.title, R


ENG = {}
for s in range(3):
    ENG[s] = build_engine(s)


def eref(s, key, row_only=False):
    name, R = ENG[s]
    return f"{name}!${FIRST_COL}${R[key]}:${LASTC}${R[key]}"


FIRST_COL = L(FIRST)


def full(s, key):
    name, R = ENG[s]
    return f"{name}!${FIRST_COL}${R[key]}:${LASTC}${R[key]}"


def yrrow(s):
    name, R = ENG[s]
    return f"{name}!${FIRST_COL}$6:${LASTC}$6"


def mrow(s):
    name, R = ENG[s]
    return f"{name}!${FIRST_COL}$3:${LASTC}$3"


# =====================================================================
# ANNUAL
# =====================================================================
AN = wb.create_sheet("Annual")
AN.sheet_view.showGridLines = False
AN["A1"] = "Annual summary - all scenarios (Year 1 = first 12 months from model start)"; AN["A1"].font = f_title
AN.column_dimensions["A"].width = 44
for i in range(3, 8):
    AN.column_dimensions[L(i)].width = 14
AN.column_dimensions["B"].width = 8
ANR = {}
alines = [
    ("sg", "Sign-ups (free users)", "flow", "sg", NUM),
    ("np", "New paying users", "flow", "np", NUM),
    ("sb", "Active subscribers (end of year)", "stock", "sb", NUM),
    ("npc", "Cumulative paying users (end of year)", "stock", "npc", NUM),
    ("sec1", "Revenue (net of VAT)", None, None, None),
    ("rv_eg", "  Egypt", "flow", "rv_eg", USD),
    ("rv_ks", "  Saudi Arabia", "flow", "rv_ks", USD),
    ("rv_ua", "  UAE", "flow", "rv_ua", USD),
    ("rev", "Total net revenue", "flow", "rev", USD),
    ("c_ai", "AI cost", "flow", "c_ai", USD),
    ("c_fee", "Payment fees", "flow", "c_fee", USD),
    ("c_scr", "Scraping / proxy variable cost", "flow", "c_scr", USD),
    ("gp", "Gross profit", "flow", "gp", USD),
    ("gm", "Gross margin %", "calc", "=IFERROR({gp}/{rev},0)", PCT),
    ("sec2", "Operating costs", None, None, None),
    ("infra", "  Infrastructure", "flow", "infra", USD),
    ("tl", "  Tools, accounting & legal", "flow", "tl", USD),
    ("des", "  Freelance designer / content", "flow", "des", USD),
    ("hire", "  Optional hires", "flow", "hire", USD),
    ("ot", "  One-time launch costs", "flow", "ot", USD),
    ("mk", "  Paid marketing", "flow", "mk", USD),
    ("ct", "  Contingency", "flow", "ct", USD),
    ("sl", "  Founder salary", "flow", "sl", USD),
    ("eb", "EBITDA / pre-tax profit", "flow", "eb", USD),
    ("ebm", "EBITDA margin %", "calc", "=IFERROR({eb}/{rev},0)", PCT),
    ("tx", "Income tax", "flow", "tx", USD),
    ("ni", "Net income", "flow", "ni", USD),
    ("cash", "Closing cash (end of year)", "stock", "cash", USD),
    ("cac", "Blended CAC (paid marketing / new paying users)", "calc", "=IFERROR({mk}/{np},0)", USD2),
]
ar_ = 3
for s in range(3):
    AN.cell(ar_, 1, f"{SCN[s].upper()} SCENARIO").font = f_b
    for i in range(5):
        AN.cell(ar_, 3 + i, i + 1)
        AN.cell(ar_, 3 + i).number_format = '"Year "0'
    hdr_row(AN, ar_, 1, 7)
    hrow = ar_
    ar_ += 1
    ANR[s] = {}
    for key, label, kind, src, fmt in alines:
        if kind is None:
            sec_row(AN, ar_, label, 7)
            ar_ += 1
            continue
        ANR[s][key] = ar_
        ar_ += 1
    # now write formulas
    for key, label, kind, src, fmt in alines:
        if kind is None:
            continue
        rr = ANR[s][key]
        AN.cell(rr, 1, label)
        for i in range(5):
            col = L(3 + i)
            if kind == "flow":
                f = f"=SUMIFS({full(s, src)},{yrrow(s)},{col}${hrow})"
            elif kind == "stock":
                f = f"=INDEX({full(s, src)},{col}${hrow}*12)"
            else:
                f = src
                for kk, vv in ANR[s].items():
                    f = f.replace("{" + kk + "}", f"{col}{vv}")
            cell = AN.cell(rr, 3 + i, f)
            cell.number_format = fmt
        if key in ("rev", "gp", "eb", "ni"):
            for cc in range(1, 8):
                AN.cell(rr, cc).font = f_b
    ar_ += 1
AN.freeze_panes = "C3"


def anc(s, key, year):  # Annual cell ref
    return f"Annual!${L(2 + year)}${ANR[s][key]}"


# SOM on market sheet (Base, Y5)
r = M_SOM_START
som_lines = [
    ("Sign-ups in year 5", [f"=SUMIFS({full(1, 'sg_' + k)},{yrrow(1)},5)" for k in CK], NUM),
    ("Paying users added in year 5", [f"=SUMIFS({full(1, 'np_' + k)},{yrrow(1)},5)" for k in CK], NUM),
    ("Net revenue in year 5", [f"=SUMIFS({full(1, 'rv_' + k)},{yrrow(1)},5)" for k in CK], USD),
]
for label, fs, fmt in som_lines:
    M.cell(r, 1, label)
    for i, f in enumerate(fs):
        M.cell(r, 2 + i, f).number_format = fmt
    M.cell(r, 5, f"=SUM(B{r}:D{r})").number_format = fmt
    r += 1
M.cell(r, 1, "Year-5 sign-ups as % of SAM")
for i, c in enumerate("BCD"):
    M.cell(r, 2 + i, f"=IFERROR({c}{M_SOM_START}/{c}{rows['sam']},0)").number_format = PCT
M.cell(r, 5, f"=IFERROR(E{M_SOM_START}/E{rows['sam']},0)").number_format = PCT
M.cell(r, 6, "Share of the addressable market reached in a single year").font = f_note
r += 1
M.cell(r, 1, "Year-5 revenue as % of SAM value")
for i, c in enumerate("BCD"):
    M.cell(r, 2 + i, f"=IFERROR({c}{M_SOM_START + 2}/{c}{rows['samv']},0)").number_format = PCT
M.cell(r, 5, f"=IFERROR(E{M_SOM_START + 2}/E{rows['samv']},0)").number_format = PCT
r += 2
M.cell(r, 1, "Reference: Egypt higher-ed graduates / year (doc)")
M.cell(r, 2, f"={ref('grads_eg')}").number_format = NUM
M.cell(r, 6, "Graduation wave (Jun-Aug) is the best acquisition window.").font = f_note

# =====================================================================
# UNIT ECONOMICS
# =====================================================================
U = wb.create_sheet("UnitEconomics")
U.sheet_view.showGridLines = False
U["A1"] = "Unit economics per paying customer"; U["A1"].font = f_title
U["A2"] = ("Year-1 prices (no FX drift). LTV = lifetime contribution after VAT, payment fees and AI cost. "
           "CAC (paid) = cost per sign-up / conversion rate. Organic users cost ~$0 in cash."); U["A2"].font = f_note
U.column_dimensions["A"].width = 52
for i in range(2, 12):
    U.column_dimensions[L(i)].width = 11
r = 4
U.cell(r, 1, "")
for s in range(3):
    U.cell(r, 2 + s * 3, SCN[s])
    U.merge_cells(start_row=r, start_column=2 + s * 3, end_row=r, end_column=4 + s * 3)
hdr_row(U, r, 1, 10)
r += 1
U.cell(r, 1, "Metric")
for s in range(3):
    for i, k in enumerate(CK):
        U.cell(r, 2 + s * 3 + i, CTRY[k]["name"].replace("Saudi Arabia", "KSA"))
hdr_row(U, r, 1, 10)
r += 1
UR = {}
ulines = [
    ("cac", "Paid CAC per paying user", USD2),
    ("cor", "Contribution per pack order (net of VAT, fees, AI)", USD2),
    ("eo", "Expected orders per pack buyer (1 + repeat/churn)", '0.00'),
    ("ltvp", "LTV - pack buyer", USD2),
    ("cos", "Contribution per subscriber-month", USD2),
    ("ltvs", "LTV - subscriber (contribution x 1/churn)", USD2),
    ("fe", "Free-evaluation AI cost per paying user (cost of free hook)", USD2),
    ("ltv", "Blended LTV per paying user (after free-hook cost)", USD2),
    ("ratio", "LTV : CAC (paid ads only)", '0.0"x"'),
    ("pb", "CAC payback (orders needed to recover paid CAC)", '0.0'),
    ("bcac", "Blended CAC from model (paid + designer spend / all new paying users, 5 yrs)", USD2),
    ("bratio", "LTV : CAC (blended, all channels incl. organic)", '0.0"x"'),
]
for key, label, fmt in ulines:
    UR[key] = r
    U.cell(r, 1, label)
    r += 1
for s in range(3):
    S = lambda k: sref(k, s)
    for i, k in enumerate(CK):
        P = CTRY[k]
        col = L(2 + s * 3 + i)
        cell = lambda key: f"{col}{UR[key]}"
        U[f"{col}{UR['cac']}"] = f"={S(P['cpa'])}/{S(P['conv'])}"
        U[f"{col}{UR['cor']}"] = (f"={ref(P['aov'])}/(1+{ref(P['vat'])})-{ref(P['aov'])}*{ref(P['pf'])}-{ref(P['ff'])}"
                                  f"-{ref(P['ao'])}*{ref('cost_app')}*{S('llm_mult')}")
        U[f"{col}{UR['eo']}"] = f"=1+{S('rep')}/{S('pchurn')}"
        U[f"{col}{UR['ltvp']}"] = f"={cell('cor')}*{cell('eo')}"
        U[f"{col}{UR['cos']}"] = (f"={ref(P['subp'])}/(1+{ref(P['vat'])})-{ref(P['subp'])}*{ref(P['pf'])}-{ref(P['ff'])}"
                                  f"-{ref(P['asub'])}*{ref('cost_app')}*{S('llm_mult')}")
        U[f"{col}{UR['ltvs']}"] = f"={cell('cos')}/{S('subchurn')}"
        U[f"{col}{UR['fe']}"] = f"={ref('cost_free')}*{S('llm_mult')}/{S(P['conv'])}"
        U[f"{col}{UR['ltv']}"] = f"=(1-{S('subshare')})*{cell('ltvp')}+{S('subshare')}*{cell('ltvs')}-{cell('fe')}"
        U[f"{col}{UR['ratio']}"] = f"=IFERROR({cell('ltv')}/{cell('cac')},0)"
        U[f"{col}{UR['pb']}"] = f"=IFERROR({cell('cac')}/{cell('cor')},0)"
        a_mk, a_ds, a_np = ANR[s]['mk'], ANR[s]['des'], ANR[s]['np']
        U[f"{col}{UR['bcac']}"] = (f"=IFERROR((SUM(Annual!$C${a_mk}:$G${a_mk})+SUM(Annual!$C${a_ds}:$G${a_ds}))"
                                   f"/SUM(Annual!$C${a_np}:$G${a_np}),0)")
        U[f"{col}{UR['bratio']}"] = f"=IFERROR({cell('ltv')}/{cell('bcac')},0)"
        for key, label, fmt in ulines:
            U[f"{col}{UR[key]}"].number_format = fmt
for cc in range(1, 11):
    for kk in ("ratio", "bratio"):
        U.cell(UR[kk], cc).font = f_b
        U.cell(UR[kk], cc).fill = fill_key
U.cell(r + 1, 1, "Rule of thumb: LTV:CAC > 3x is healthy. Below 1x means paid ads lose money - rely on organic/referral in that market.").font = f_note

# =====================================================================
# SUMMARY
# =====================================================================
SM = wb.create_sheet("Summary")
SM.sheet_view.showGridLines = False
SM.column_dimensions["A"].width = 54
for c in "BCDE":
    SM.column_dimensions[c].width = 16
SM.column_dimensions["F"].width = 3
for c in "GHIJKL":
    SM.column_dimensions[c].width = 14
SM["A1"] = "TAILORED - Investor Summary"; SM["A1"].font = Font(name="Calibri", size=20, bold=True, color=NAVY)
SM["A2"] = ("AI job-search copilot for MENA (Egypt, KSA, UAE). Credit packs + optional subscription. Solo founder (AI engineer) + freelance designer. "
            "All figures USD, live formulas - change inputs on the Assumptions sheet.")
SM["A2"].font = f_note
r = 4
SM.cell(r, 1, "HEADLINE METRICS")
for i, n in enumerate(SCN):
    SM.cell(r, 2 + i, n)
SM.cell(r, 5, "Note")
hdr_row(SM, r, 1, 5)
r += 1


def nm(s):
    return ENG[s][0]


def Rr(s, k):
    return ENG[s][1][k]


kp = []


def kpi(label, fn, fmt, note=""):
    global r
    SM.cell(r, 1, label)
    for s in range(3):
        c = SM.cell(r, 2 + s, fn(s))
        c.number_format = fmt
        c.alignment = Alignment(horizontal="right")
    SM.cell(r, 5, note).font = f_note
    r += 1
    return r - 1


kpi("Revenue - Year 1", lambda s: f"={anc(s, 'rev', 1)}", USD)
kpi("Revenue - Year 3", lambda s: f"={anc(s, 'rev', 3)}", USD)
kRev5 = kpi("Revenue - Year 5", lambda s: f"={anc(s, 'rev', 5)}", USD)
kpi("Gross margin - Year 5", lambda s: f"={anc(s, 'gm', 5)}", PCT)
kpi("EBITDA margin - Year 5", lambda s: f"={anc(s, 'ebm', 5)}", PCT)
kNI5 = kpi("Net income - Year 5", lambda s: f"={anc(s, 'ni', 5)}", USD)
kpi("Cumulative paying users - Year 5", lambda s: f"={anc(s, 'npc', 5)}", NUM)
kpi("Break-even month (EBITDA > 0, 3 months running)",
    lambda s: f'=IFERROR(INDEX({mrow(s)},MATCH(1,{full(s, "be")},0)),"Not in 60m")', NUM, "Month # since model start (1 = Jan-2027)")
kpi("Founder salary starts (month #)",
    lambda s: f'=IFERROR(INDEX({mrow(s)},MATCH(1,{full(s, "sf")},0)),"Not in 60m")', NUM, "Triggers once business can afford market salary")
kPeak = kpi("Peak funding need (max cumulative cash burn)", lambda s: f"=MAX(0,-MIN({full(s, 'cumo')}))", USD, "Money the business needs before it self-funds")
kRaise = kpi("Investment assumed", lambda s: f"={ref('raise')}", USD, "Placeholder - edit on Assumptions")
kpi("Funding headroom (investment - peak need)", lambda s: f"={ref('raise')}-{'%s%d' % (L(2 + s), kPeak)}", USD, "Negative = investment is not enough")
kpi("Minimum cash balance", lambda s: f"=MIN({full(s, 'cash')})", USD)
kpi("Cash-out month (first month cash < 0)",
    lambda s: f'=IFERROR(INDEX({mrow(s)},MATCH(1,{full(s, "cn")},0)),"Never")', NUM)
kpi("Cash balance - end of Year 5", lambda s: f"={anc(s, 'cash', 5)}", USD)
kpi("LTV:CAC - Egypt (paid)", lambda s: f"=UnitEconomics!{L(2 + s * 3)}{UR['ratio']}", '0.0"x"')
kpi("LTV:CAC - KSA (paid)", lambda s: f"=UnitEconomics!{L(3 + s * 3)}{UR['ratio']}", '0.0"x"')
kpi("LTV:CAC - UAE (paid)", lambda s: f"=UnitEconomics!{L(4 + s * 3)}{UR['ratio']}", '0.0"x"')
kpi("LTV:CAC - blended, all channels (Egypt LTV)", lambda s: f"=UnitEconomics!{L(2 + s * 3)}{UR['bratio']}", '0.0"x"', "Organic + referral dilute paid CAC - the realistic figure")
kpi("Blended CAC per paying user (5-yr)", lambda s: f"=UnitEconomics!{L(2 + s * 3)}{UR['bcac']}", USD2)
r += 1
SM.cell(r, 1, "INVESTOR RETURN (illustrative, year-5 exit)")
for i, n in enumerate(SCN):
    SM.cell(r, 2 + i, n)
SM.cell(r, 5, "Note")
hdr_row(SM, r, 1, 5)
r += 1
kEV = kpi("Exit enterprise value (revenue multiple x Year-5 revenue)", lambda s: f"={sref('exit_mult', s)}*{anc(s, 'rev', 5)}", USD, "Multiple set per scenario on Assumptions")
kEq = kpi("Equity value (EV + Year-5 cash)", lambda s: f"={L(2 + s)}{kEV}+{anc(s, 'cash', 5)}", USD)
kInv = kpi("Investor share of equity value", lambda s: f"={ref('stake')}*{L(2 + s)}{kEq}", USD, "Stake % set on Assumptions (placeholder)")
kMo = kpi("Investor MOIC", lambda s: f"={L(2 + s)}{kInv}/{ref('raise')}", '0.0"x"')
kpi("Investor IRR (5 years)", lambda s: f"=IF({L(2 + s)}{kMo}>0,{L(2 + s)}{kMo}^(1/5)-1,-1)", PCT, "Ignores dividends / interim distributions")
kpi("Implied post-money valuation", lambda s: f"={ref('raise')}/{ref('stake')}", USD)
for rr in (kMo,):
    for cc in range(1, 5):
        SM.cell(rr, cc).font = f_b
        SM.cell(rr, cc).fill = fill_key
r += 1

# yearly table for charts
SM.cell(r, 1, "REVENUE BY YEAR (USD)")
for i in range(5):
    SM.cell(r, 2 + i, f"Year {i + 1}")
hdr_row(SM, r, 1, 6)
chart_hdr = r
r += 1
rev_rows = []
for s in range(3):
    SM.cell(r, 1, SCN[s])
    for i in range(5):
        SM.cell(r, 2 + i, f"={anc(s, 'rev', i + 1)}").number_format = USD
    rev_rows.append(r)
    r += 1
r += 1
SM.cell(r, 1, "NET INCOME BY YEAR (USD)")
for i in range(5):
    SM.cell(r, 2 + i, f"Year {i + 1}")
hdr_row(SM, r, 1, 6)
r += 1
ni_rows = []
for s in range(3):
    SM.cell(r, 1, SCN[s])
    for i in range(5):
        SM.cell(r, 2 + i, f"={anc(s, 'ni', i + 1)}").number_format = USD
    ni_rows.append(r)
    r += 1
ni_hdr = r - 4
r += 1

# risks
SM.cell(r, 1, "KEY RISKS & MITIGATIONS")
SM.cell(r, 2, "Likelihood")
SM.cell(r, 3, "Impact")
SM.cell(r, 4, "Mitigation / where it shows in model")
hdr_row(SM, r, 1, 5)
r += 1
risks = [
    ("1. Scraping blocked / LinkedIn legal action (ToS)", "High", "High", "Modular scraper plugins; Wuzzuf/Bayt as fallbacks; user-pasted JD option. Not priced in model - biggest existential risk."),
    ("2. Low willingness to pay in Egypt (ARPU ~$3 per order)", "High", "Med", "Conversion 2-5% in scenarios; Gulf priced ~3x higher. See Downside column."),
    ("3. EGP devaluation erodes USD revenue", "Med", "Med", "Annual depreciation x pass-through in scenario drivers; prices in EGP re-set quarterly."),
    ("4. Customer acquisition costs higher than organic reach", "Med", "High", "Paid CAC vs blended CAC on UnitEconomics. Gulf paid CPCs are 4-10x Egypt - lead with organic/referral there."),
    ("5. Free LLM-apps (ChatGPT etc.) commoditise CV tailoring", "High", "High", "Differentiate on regional job-board integration + fit-gap scoring + LaTeX output."),
    ("6. Small addressable revenue pool caps upside", "Med", "Med", "Annual sign-up cap tied to SAM (Market sheet). Upside scenario needs Gulf traction."),
    ("7. Single-founder dependency (key-person risk)", "High", "High", "Zero salary phase protects cash but risks burnout; hires toggle in Assumptions shows cost of expansion."),
    ("8. AI model price or quality changes", "Low", "Low", "AI is <10% of revenue; multiplier 1.0-1.5x in scenarios."),
]
for a, b, c_, d in risks:
    SM.cell(r, 1, a)
    SM.cell(r, 2, b)
    SM.cell(r, 3, c_)
    SM.cell(r, 4, d).font = f_note
    for cc in (2, 3):
        SM.cell(r, cc).alignment = Alignment(horizontal="center")
    r += 1
r += 1
SM.cell(r, 1, "How to read: Base = most likely case; Downside = slow organic growth + weak conversion + devaluation; Upside = strong graduation-season virality + early Gulf launch.").font = f_note

# charts
ch = BarChart()
ch.type = "col"
ch.title = "Net revenue by year (USD)"
data = Reference(SM, min_col=1, max_col=6, min_row=rev_rows[0], max_row=rev_rows[-1])
ch.add_data(data, from_rows=True, titles_from_data=True)
ch.set_categories(Reference(SM, min_col=2, max_col=6, min_row=chart_hdr))
ch.height, ch.width = 7.5, 15
SM.add_chart(ch, "G4")
lc = LineChart()
lc.title = "Closing cash balance - monthly (USD)"
name_base, RB = ENG[1]
mb = wb[name_base]
for s in range(3):
    nme, RR = ENG[s]
    ws_ = wb[nme]
    ref_ = Reference(ws_, min_col=FIRST, max_col=FIRST + NM - 1, min_row=RR["cash"])
    lc.add_data(ref_, from_rows=True, titles_from_data=False)
from openpyxl.chart.series import SeriesLabel
for i, ser in enumerate(lc.series):
    ser.tx = SeriesLabel(v=SCN[i])
lc.set_categories(Reference(mb, min_col=FIRST, max_col=FIRST + NM - 1, min_row=3))
lc.height, lc.width = 7.5, 15
SM.add_chart(lc, "G20")
SM.freeze_panes = "A4"

# =====================================================================
# SOURCES
# =====================================================================
SO = wb.create_sheet("Sources")
SO.sheet_view.showGridLines = False
SO["A1"] = "Sources, research notes & confidence"; SO["A1"].font = f_title
SO.column_dimensions["A"].width = 38
SO.column_dimensions["B"].width = 60
SO.column_dimensions["C"].width = 55
SO.column_dimensions["D"].width = 12
for i, h in enumerate(["Item", "Finding (researched Oct-2026)", "Source", "Confidence"]):
    SO.cell(3, 1 + i, h)
hdr_row(SO, 3, 1, 4)
src = [
    ("LLM pricing", "Gemini 2.5 Flash $0.30 in / $2.50 out per 1M tokens (batch 50% off). GPT-4o-mini $0.15 / $0.60.", "Google AI pricing; OpenAI pricing (via cabina.ai, pecollective.com)", "High"),
    ("LinkedIn members", "Egypt 13.0-13.7M; UAE 9.4-9.7M; KSA 11.0-11.3M.", "DataReportal / LinkedIn ad audience (2025)", "High"),
    ("Internet users", "Egypt ~98M (82%); UAE ~11M (99%); KSA ~36-37M (99%).", "DataReportal 2025", "High"),
    ("Payment fees", "Paymob Egypt 2.75% + 3 EGP; UAE 2.9% + 1 AED; KSA Mada 1% + 1 SAR, intl cards 2.7-3.5% + 1 SAR. Stripe does not support Egypt-based merchants.", "paymob.sa / paymob.ae / paymentreview.com", "Medium-High"),
    ("FX", "USD/EGP ~53.4; SAR peg 3.75; AED peg 3.6725.", "tradingeconomics.com, CBE, Banque Misr", "High"),
    ("Freemium conversion", "Consumer freemium 2-5% (median); pay-per-use with free hook can reach upper end.", "bolderapps.com, saasfactor.co", "Medium"),
    ("Meta ads Egypt", "CPM $0.80-2.50; CPC $0.10-0.50 (conversion campaigns $0.20-0.70); cost per signup $1.5-3.", "digitology.co and industry benchmarks", "Medium"),
    ("Ad costs (CPM/CPC)", "Egypt CPC $0.05-0.35, CPM $1.0-2.8; KSA CPC $0.80-2.00, CPM $10-13.5; UAE CPC $0.70-1.80, CPM $9-11.5. Click->sign-up 20% is an estimate (resume-funnel visitor-to-signup 10-20%).", "lebesgue.io, adamigo.ai, stackmatix.com, adkit.so", "Medium"),
    ("LLM tiers", "Gemini 2.5 Flash-Lite $0.10 in / $0.40 out (parsing, scoring); Flash $0.30 / $2.50 (writing). Cached input -90%, batch -50% (not assumed).", "Google AI pricing, aipricing.guru, cloudzero.com", "High"),
    ("Pay-per-use conversion", "Free-to-paid 3-8% for transactional utilities (resume tools); 2-5% for subscription freemium.", "stackmatix.com, kickresume.com, draftcareer.com", "Medium"),
    ("Subscription churn", "B2C subscription apps 10-15%/mo; career apps suffer 'success churn' (job found in 1-3 months) -> 25%/mo base.", "elenaverna.com, revenuecat.com", "Medium"),
    ("Organic share", "Emerging-market consumer apps: organic 40-60%, referral 20-35%, paid 15-30%. Blended CAC typically $0.20-1.20 vs paid $0.80-3.50.", "embertribe.com, kpitree.co", "Low-Medium"),
    ("Active job seekers 18%", "Taken from your feasibility doc.", "Documentations/business_feasibility_analysis.md", "Medium"),
    ("Pack prices, token counts, infra costs", "Taken from your feasibility doc (sections 5, 8).", "Documentations/business_feasibility_analysis.md", "Medium"),
    ("Founder salary benchmark", "Senior architect Egypt 60-100k EGP local, 90-140k EGP VC-funded.", "Your doc section 7.1", "Medium"),
    ("VAT / tax rates", "Egypt 14% VAT, KSA 15%, UAE 5%; Egypt CIT 22.5%. Digital-services rules for foreign/local B2C sellers need an accountant.", "General knowledge - verify", "Medium"),
    ("Seasonality", "Graduation Jun-Aug; hiring surges Q1 and Sep-Nov; slump in Ramadan/Eid and late Dec.", "Your doc section 3", "Medium"),
    ("Not modelled", "Working capital, FX on payouts, gateway reserves, refunds/chargebacks, ESOP/option pool, founder personal living costs while unpaid, platform legal risk.", "-", "-"),
]
for i, row_ in enumerate(src):
    for j, v in enumerate(row_):
        c = SO.cell(4 + i, 1 + j, v)
        c.alignment = Alignment(wrap_text=True, vertical="top")

# order sheets
order = ["Summary", "Assumptions", "Market", "UnitEconomics", "Annual", "Model_Downside", "Model_Base", "Model_Upside", "Sources"]
wb._sheets = [wb[n] for n in order]
wb["Summary"].sheet_properties.tabColor = "1F2A44"
wb["Assumptions"].sheet_properties.tabColor = "F4B400"
wb.save(OUT)
print("saved", OUT)
