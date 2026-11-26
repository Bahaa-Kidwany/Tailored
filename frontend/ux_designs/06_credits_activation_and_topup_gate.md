# 06 — Credits Activation & Out-of-Credits Top-Up Gate (`/trial` & Contextual Modal)

**Route / Trigger:** `/trial` (Post-Onboarding Credits Welcome) AND Contextual Overlay Modal (triggered mid-workflow when `credits === 0`)  
**Implementation Status:** Implemented as a legacy recurring-plan modal (`FreeTrialGateModal.tsx`) — **Completely Redesigned to Pay-As-You-Go Credit Packs**  
**Primary User Goal:** Understand clearly that Tailored has no subscription lock-in, claim/start using the 2 complimentary starter credits immediately (fulfilling `pendingIntent`), or top up a local/global credit pack in 2 clicks without losing work.  
**Entry Points:** Completion of `/onboarding` (Mode A), clicking `[⚡ Top Up]` or hitting a `1 Credit` action with `0` balance (Mode B).  
**Exit Destinations:** Exact `pendingIntent` destination (`/studio`, `/interest`, `/radar`, or `/dashboard`), or resumes exact paused action on current page.  
**Credit Model Impact:** Zero monthly auto-renewal; Free Starter = `2 Credits` (`1` complete application); Paid Packs start at `49 EGP` (`5 cr`) / `$4.99` (`10 cr`).

---

## 1. UX Reference Benchmarks & Ergonomic Rationale

| Reference | Pattern Adopted | Ergonomic Benefit for Tailored |
| :--- | :--- | :--- |
| **Clay & ElevenLabs** | Transparent credit-to-outcome conversion (*"2 Credits = 1 Full Tailored CV + Cover Letter"*) + non-destructive top-up modal | Converts abstract AI credits into clear job-application outcomes and prevents bill anxiety. |
| **Stripe / Paymob Ethical Checkout** | Explicit regional currency switcher (`EGP`, `SAR`, `AED`, `USD`) + instant escape hatch with zero dark patterns | Respects emerging-market realities (Egypt/MENA local cards, Meeza, Fawry, Vodafone Cash) and keeps trust high. |
| **Figma / Notion Safe-State Recovery** | Preserves unsaved edits/chat state before opening top-up modal and auto-resumes action post-checkout | Users never lose 20 minutes of work if they hit 0 credits mid-flow. |

---

## 2. Desktop Layout Architecture & ASCII Wireframes (`1440px`)

### Mode A: Post-Onboarding Credits Welcome (`/trial`)
```
+---------------------------------------------------------------------------------------------------+
| TOP BAR: [Tailored Mark]                                    [Skip Top-Up & Use 2 Free Credits →]  |
+---------------------------------------------------------------------------------------------------+
| AFFIRMATION RIBBON (Centered):                                                                    |
| ✓ Master Profile Ready: Mostafa Ibrahim · Senior AI Engineer · Cairo, Riyadh, Remote              |
+---------------------------------------------------------------------------------------------------+
| CENTERED SPLIT CONTAINER (Max-width: 1020px)                                                      |
|                                                                                                   |
|   HEADLINE: "Your Profile Is Ready. Start With 2 Free Credits."                                   |
|   SUBHEAD:  "Discovery, scraping, and 5-D fit scoring are always free. Use credits only when      |
|              generating tailored CVs (1 cr) or cover letters (1 cr). Credits never expire."       |
|                                                                                                   |
|   LEFT CARD: START FREE NOW (44% Width)            | RIGHT CARD: OPTIONAL TOP-UP PACKS (56% Width)|
|   -------------------------------------------------|----------------------------------------------|
|   ★ INCLUDED FREE WITH YOUR ACCOUNT                | OPTIONAL POWER PACKS  Region: [🇪🇬 EGP ▾]     |
|                                                    | (Zero subscription · Never expires)          |
|   Balance Ready: [ ⚡ 2 Free Credits ]             |                                              |
|   Includes:                                        | +------------------------------------------+ |
|   ✓ Unlimited LinkedIn & Wuzzuf Radar Discovery    | | Starter "Quick Apply"                    | |
|   ✓ Unlimited 5-D Fit Scoring & Gap Analysis       | | 5 Credits (~2–3 Apps) · 49 EGP   [Select]| |
|   ✓ 1 Tailored ATS CV (.pdf + .tex + AI Coach)     | +------------------------------------------+ |
|   ✓ 1 Tailored Cover Letter                        | | ★ Job Hunter Pack (Most Popular)         | |
|                                                    | | 25 Credits (~12–15 Apps) · 179 EGP [Select]| |
|   QUEUED NEXT STEP:                                | +------------------------------------------+ |
|   -> Open "Swvl — Lead Data Scientist" in Studio   | | Career Sprint Pack                       | |
|      (or Job Radar if no pending target)           | | 70 Credits (~35–40 Apps) · 399 EGP [Select]| |
|                                                    | +------------------------------------------+ |
|   PRIMARY CTA (No Card Required):                  |                                              |
|   [ Start Using My 2 Free Credits →              ] | [ Continue to Secure Top-Up (179 EGP) ]      |
|                                                    | Payments: Paymob · Meeza · Fawry · Cards     |
+---------------------------------------------------------------------------------------------------+
```

### Mode B: Contextual Out-of-Credits Modal (Triggered Mid-Workflow)
```
+-----------------------------------------------------------------------+
| TOP UP TO CONTINUE (Your Work Is Safely Saved)                   [✕]  |
|-----------------------------------------------------------------------|
| Current Balance: ⚡ 0 Credits                                         |
| Action Queued:   Tailor CV for "Noon — Senior ML Engineer" (1 Credit) |
| Status:          Your edits & profile context are preserved locally.  |
|-----------------------------------------------------------------------|
| Region: [🇪🇬 Egypt (EGP) ▾]   (Zero subscription · Credits never expire)|
|                                                                       |
|  ( ) Starter Pack       5 Credits   (~9.8 EGP/cr)            49 EGP   |
|  (•) Job Hunter ★      25 Credits   (~7.1 EGP/cr)           179 EGP   |
|  ( ) Career Sprint     70 Credits   (~5.7 EGP/cr)           399 EGP   |
|-----------------------------------------------------------------------|
| FAST CHECKOUT METHOD:                                                 |
| [• Saved Visa •••• 4242]   [Meeza / Card]   [Vodafone Cash / Wallet]  |
|                                                                       |
| [ Pay 179 EGP & Resume "Tailor CV for Noon" → ]     [Cancel & Return] |
+-----------------------------------------------------------------------+
```

---

## 3. Eye-Scan Path & Anti-Saccade Map

1. **Fixation 1 (Top Affirmation & Headline):** Validates profile creation success (Mode A) or reassures user that their draft is safe (Mode B).
2. **Fixation 2 (2 Free Credits Card — Left of Mode A / Selected Pack in Mode B):** Primary eye landing highlights the zero-card-required entry path first (`[Start Using My 2 Free Credits →]`), honoring zero dark patterns.
3. **Fixation 3 (Queued Destination / Action Resume):** Clearly tells the user *exact next step* awaiting them right below the CTA button.

---

## 4. Proximity & Click-Depth Budget

| User Intent | Click / Keystroke Depth | Spatial Location |
| :--- | :--- | :--- |
| **Start free with 2 starter credits** | `1` click on primary CTA (or top-right skip) | Bottom of Left Free Card (`Mode A`) |
| **Switch currency / market (`EGP`, `SAR`, `AED`, `USD`)** | `1` click dropdown | Top-right of Packs card |
| **Purchase pack with saved method & auto-resume** | `1` click pack + `1` click `[Pay & Resume]` | Inline inside `Mode B` Modal (zero page redirect!) |
| **Cancel without losing draft** | `1` click `[✕]` / `[Cancel]` or `Esc` | Top-right / footer of `Mode B` Modal |

---

## 5. Detailed Zone-by-Zone Component & Interaction Spec

### 5.1 Intent Preservation (`pendingIntent`) Fulfillment Router
Upon clicking `[Start Using My 2 Free Credits →]` or finishing optional pack purchase in Mode A:
- **`pendingIntent.type === 'tailor_job'`:** Routes directly to `/studio?job_id=...`, opens CV Studio with the exact job paired, and automatically pre-loads the base/tailor preview (prompts confirmation before consuming 1 credit, or immediately executes if user already explicitly triggered Tailor).
- **`pendingIntent.type === 'ingest_url' | 'ingest_jd'`:** Routes directly to `/interest?highlight=job_id` showing the scored opportunity ready to tailor.
- **`pendingIntent.type === 'search' | null`:** Routes to `/radar` (if query present) or `/dashboard` with all jobs scored against their brand-new Master Profile.

### 5.2 Transparent Cost Schedule Tooltip
- Hovering `Why 1 Credit?` expands an honest 3-line breakdown: *"Discovery, scraping, and 5-D fit scoring are always free. 1 Credit covers full LLM surgical bullet rewriting, zero-hallucination verification, LaTeX/PDF compilation, and unlimited AI chat refinements for that CV."*

### 5.3 Localized Payment Support
- Selecting **Egypt (`EGP`)** surfaces local methods: Cards (Visa/Mastercard), Meeza, Mobile Wallets (Vodafone Cash / InstaPay / Orange / Etisalat), Fawry Reference Code.
- Selecting **KSA (`SAR`), UAE (`AED`), or Global (`USD`)** displays Apple Pay, Google Pay, and international cards (`$4.99` for 10 credits, `$14.99` for 50 credits).

---

## 6. Interactivity, Adjustability & Keyboard Shortcuts

- **Region Auto-Detection + Manual Override:** Defaults currency from user's Master Profile `current_country` / regional phone (`+20` → `EGP`, `+966` → `SAR`, `+971` → `AED`), changeable in 1 click.
- **Keyboard:** `Esc` dismisses `Mode B` modal safely; `Enter` triggers primary action when focused.

---

## 7. State Matrix & Edge Cases

| State | Behavior |
| :--- | :--- |
| **Payment Processing** | Primary button shows spinner (*"Confirming payment with Paymob..."*); prevents double charge. |
| **Payment Declined** | Inline error directly inside modal (*"Your card couldn't be authorized — try another method or use Vodafone Cash/Fawry. Your draft is still saved."*). |
| **Fawry / Pending Offline Cash Code** | Shows reference code + `[Copy Code]` and keeps user's draft safely stored in `/interest` / `/cvs` until webhook credits arrive. |
| **Zero-Cost Failure Protection** | If CV generation/compilation fails after deducting 1 credit, system automatically refunds `1 Credit` with toast: *"Compile failed — we refunded your 1 credit automatically."* |

---

## 8. Frontend UI Implementation Contract

- **Suggested Components:** `CreditsWelcomePage`, `OutOfCreditsTopUpModal`, `CreditPackSelector`, `RegionalCurrencyToggle`, `InlineCheckoutForm`.
- **State:** `creditBalance: number`, `selectedRegion: 'EG' | 'SA' | 'AE' | 'GLOBAL'`, `selectedPackId`, `queuedAction: (() => void) | null`, `pendingIntent`.
- **Backend Hooks:**
  - `GET /api/v1/credits/balance` & `GET /api/v1/credits/packs` `[New Endpoint Needed]`
  - `POST /api/v1/credits/checkout` (Paymob / Stripe intent) `[New Endpoint Needed]`
- **UX Acceptance Criteria:**
  1. Zero mention of monthly subscriptions, trial expiry timers, or forced card inputs on onboarding completion.
  2. Hitting `0` credits mid-workflow preserves unsaved CV Studio / Cover Letter edits and resumes automatically after top-up.
  3. Fulfillment Router lands user cleanly on their preserved `pendingIntent` destination.
