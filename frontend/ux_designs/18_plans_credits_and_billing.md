# 18 — Plans, Credit Packs, Checkout & Usage Ledger (`/plans`)

**Route:** `/plans`  
**Implementation Status:** Currently merged inside `AtelierAccountAndPlansPage.tsx` under a legacy recurring-plan model — **Dedicated Page Redesigned to Pay-As-You-Go Credit Packs**  
**Primary User Goal:** Check live credit balance, understand exact per-action credit value, switch regional market pricing (`EGP`, `SAR`, `AED`, `USD`), purchase non-expiring credit packs seamlessly via local/global methods, and audit every historical credit deduction or refund in a transparent ledger.  
**Entry Points:** Global Shell Credit Pill (`[⚡ X Credits]` → `[Top Up]`), Global Sidebar (`Plans & Credits`), Out-of-Credits Modal (`[See All Packs & Usage]`), `/account` link.  
**Exit Destinations:** Inline Checkout Slide-Over Drawer (stays on `/plans`), back to `/studio` or `/dashboard`.  
**Credit Model Impact:** Strictly Pay-Per-Use Credit Packs (`0` monthly auto-renewal, credits never expire).

---

## 1. UX Reference Benchmarks & Ergonomic Rationale

| Reference | Pattern Adopted | Ergonomic Benefit for Tailored |
| :--- | :--- | :--- |
| **ElevenLabs & OpenAI Usage Billing** | Top Credit Wallet Banner + Transparent Cost-Per-Action Table + Chronological Usage Audit Ledger | Eliminates all ambiguity about where credits went and proves credits aren't wasted on free discovery/chat edits. |
| **Stripe Billing & Paymob Checkout** | Inline Slide-Over Checkout Drawer with localized Egypt payment rails (Meeza, Vodafone Cash, Fawry, Cards) & GCC Apple Pay/Cards | Zero jarring third-party checkout maze; candidate picks a pack and pays in their native currency. |

---

## 2. Desktop Layout Architecture & ASCII Wireframe (`1440px`)

```
+---------------------------------------------------------------------------------------------------+
| GLOBAL SHELL (Left Nav 220px) | PLANS, CREDITS & BILLING (/plans, max-w: 1160px)                  |
|-------------------------------|-------------------------------------------------------------------|
|                               | 1. CREDIT WALLET HERO BANNER                                      |
|                               | +---------------------------------------------------------------+ |
|                               | | Available Balance: ⚡ 14 Credits  (~7 Complete Applications)    | |
|                               | | Total Tailored: 9 CVs · 4 Cover Letters  |  Credits Never Expire| |
|                               | | Market / Currency: [🇪🇬 Egypt (EGP) ▾]   [Low-Balance Alert: ≤2] | |
|                               | +---------------------------------------------------------------+ |
|                               |                                                                   |
|                               | 2. TABS: [Buy Credit Packs]  |  [Usage Ledger & Invoices (13)]    |
|                               |-------------------------------------------------------------------|
|                               | TAB A: PAY-AS-YOU-GO CREDIT PACKS (Zero Subscription Lock-In)     |
|                               |                                                                   |
|                               | +--------------------+ +--------------------+ +-----------------+ |
|                               | | STARTER            | | ★ JOB HUNTER       | | CAREER SPRINT   | |
|                               | | "Quick Apply"      | | (Most Popular)     | | "Active Search" | |
|                               | |                    | |                    | |                 | |
|                               | | 5 Credits          | | 25 Credits         | | 70 Credits      | |
|                               | | ~2–3 Applications  | | ~12–15 Applications| | ~35–40 Apps     | |
|                               | | 49 EGP (~9.8/cr)   | | 179 EGP (~7.1/cr)  | | 399 EGP (~5.7)  | |
|                               | | [ Buy 5 Credits ]  | | [ Buy 25 Credits ] | | [ Buy 70 Credits| |
|                               | +--------------------+ +--------------------+ +-----------------+ |
|                               | (Toggle to GCC/Global shows: Single Shot 10 cr / $4.99 ~19 SAR |   |
|                               |  & Pro Hunter 50 cr / $14.99 ~56 SAR, Apple Pay / Cards)          |
|                               |                                                                   |
|                               | TRANSPARENT ACTION COST SCHEDULE (Compact Reference Table):       |
|                               | • Radar Sweeps, Link/Screenshot Ingestion & 5-D Fit Score -> FREE |
|                               | • Tailored CV (.tex + PDF + Unlimited AI Chat Edits)      -> 1 cr |
|                               | • Tailored Cover Letter (+ AI Writing Coach Refinements)  -> 1 cr |
|                               | • Complete Application Package (CV + Cover Letter)        -> 2 cr |
|                               |-------------------------------------------------------------------|
|                               | TAB B: USAGE LEDGER & INVOICES                                    |
|                               | DATE       | ACTION                 | JOB TARGET        | DELTA | BAL|
|                               | Nov 20     | Tailored CV (v1..v3)   | Swvl — Lead DS    | -1 cr | 14 |
|                               | Nov 19     | Compile Error Refund   | Careem — AI Eng   | +1 cr | 15 |
|                               | Nov 15     | Job Hunter Pack (Inv#8)| 179 EGP (Paymob)  | +25 cr| 16 |
+---------------------------------------------------------------------------------------------------+
```

---

## 3. Eye-Scan Path & Anti-Saccade Map

1. **Fixation 1 (Wallet Hero Banner):** Immediate answer to *"How many credits do I have left, how many applications is that, and which currency am I viewing?"*
2. **Fixation 2 (Credit Pack Cards — Highlighted Popular Tier):** Clear side-by-side comparison of credits, application equivalents, effective cost-per-credit, and 1-click `[Buy]` button.
3. **Fixation 3 (Directly Below — Action Cost Schedule & Ledger Tab):** Reinforces fairness (free discovery, free iterative chat edits, automatic refunds on failures).

---

## 4. Proximity & Click-Depth Budget

| User Intent | Click / Keystroke Depth | Spatial Location |
| :--- | :--- | :--- |
| **Switch pricing region (`EGP` / `SAR` / `AED` / `USD`)** | `1` click dropdown | Top-right inside Wallet Hero Banner → updates all pack cards live |
| **Purchase a credit pack** | `1` click `[Buy Pack]` → opens inline Checkout Drawer (`1` confirm click) | Pack card → slide-over drawer (no loss of page context) |
| **Audit credit history / download invoice** | `1` click on `[Usage Ledger & Invoices]` tab | Directly under Wallet Banner |
| **Set low-credit notification threshold** | `1` click (`[Low-Balance Alert: ≤2 ▾]`) | Right inside Wallet Banner |

---

## 5. Detailed Zone-by-Zone Component & Interaction Spec

### 5.1 Inline Slide-Over Fast Checkout Drawer
- Opens cleanly on the right (`440px`) when user clicks `[Buy Pack]`—keeps pack summary visible on the left.
- **Egypt Payment Tabs (`EGP`):** Card / Meeza, Mobile Wallet (Vodafone Cash / Orange / Etisalat / InstaPay), Fawry Pay-at-Kiosk reference code.
- **GCC & Global Payment Tabs (`SAR`, `AED`, `USD`):** Apple Pay / Google Pay, Card, Saved Card.
- Shows explicit confirmation before charge: *"One-time payment of 179 EGP · Credits never expire · No recurring charges."*

### 5.2 Usage Ledger & Automatic Failure Refund Transparency
- Ledger distinguishes **Packs Purchased (`+`)**, **Document Unlocks (`-1 cr`)**, and **Automatic Failure Refunds (`+1 cr`)** with clickable links directly to the generated CV/Cover Letter in `/cvs` or `/studio`.
- Invoices include downloadable PDF receipts.

---

## 6. Interactivity, Adjustability & Keyboard Shortcuts

- **Regional Auto-Detection + Override:** Defaults currency from Master Profile country/phone, switchable anytime without locking account region.
- **Keyboard:** `Esc` closes Checkout Drawer safely; `1` / `2` switches between `Buy Credit Packs` and `Usage Ledger` tabs.

---

## 7. State Matrix & Edge Cases

| State | Behavior |
| :--- | :--- |
| **Zero Credits Balance (`0`)** | Wallet banner elevates a calm urgent callout (`"0 Credits Remaining — Top up anytime from 49 EGP to unlock your next CV or Cover Letter"`). Discovery & saved documents remain 100% accessible. |
| **Fawry / Pending Cash Payment** | Ledger shows `Pending Payment (Ref #...)` with `[View Fawry Code]` and `[Check Status]` trigger; credits arrive immediately on webhook confirmation. |
| **Payment Failed / Timeout** | Inline error inside Checkout Drawer with alternative method suggestions (e.g., *"Card declined — try Meeza or Vodafone Cash instead"*). |

---

## 8. Frontend UI Implementation Contract

- **Suggested Components:** `PlansAndCreditsPage`, `CreditWalletBanner`, `CreditPackGrid`, `ActionCostSchedule`, `FastCheckoutDrawer`, `CreditUsageLedgerTable`.
- **State:** `balance: number`, `currency: 'EGP' | 'SAR' | 'AED' | 'USD'`, `packs[]`, `ledgerEntries[]`, `checkoutPack: Pack | null`, `lowBalanceThreshold`.
- **Backend Hooks:**
  - `GET /api/v1/credits/balance` & `GET /api/v1/credits/packs?currency=...` `[New Endpoint Needed]`
  - `GET /api/v1/credits/ledger` & `POST /api/v1/credits/checkout` `[New Endpoint Needed]`
  - `GET /api/v1/credits/invoices/{id}/pdf` `[New Endpoint Needed]`
- **UX Acceptance Criteria:**
  1. Zero recurring monthly subscriptions or auto-renewal traps anywhere on `/plans`.
  2. Users clearly see application equivalents (`~12–15 Applications`) and per-credit cost before purchasing.
  3. Usage ledger links every `-1 cr` line back to the exact job/document unlocked and shows automatic refunds transparently.
