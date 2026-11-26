# 03 — Authentication: Sign In & Create Account (`/login`, `/register`)

**Routes:** `/login` and `/register`  
**Implementation Status:** Implemented (`AuthPage.tsx`) — Ergonomic & Intent-Preserving Refinement  
**Primary User Goal:** Authenticate or create an account in minimal keystrokes while visually retaining confidence that any previously selected job or uploaded CV is waiting on the other side.  
**Entry Points:** Landing header/Omni-Bar, `/explore` Feature Gate Modal, direct URL, session expiry redirect, `/account` Sign Out.  
**Exit Destinations:** `/dashboard` or preserved target (returning Sign In), `/verify-email` or `/onboarding` (new Registration), `/forgot-password`, `/` (`Return to Command Center`).  
**Credit Model Impact:** Registration explicitly reinforces *"Includes 2 Free Credits on completion — no credit card required."*

---

## 1. UX Reference Benchmarks & Ergonomic Rationale

| Reference | Pattern Adopted | Ergonomic Benefit for Tailored |
| :--- | :--- | :--- |
| **Linear & Clerk** | Single-surface authentication with URL-synchronized mode switch (`/login` ↔ `/register`) & minimal fields | Eliminates jarring page reloads and multi-screen sign-up bloat. |
| **Figma / Notion Intent Carryover** | Contextual side reminder card showing the exact job/CV queued (`pendingIntent`) | Prevents sign-up drop-off by reminding users *why* they started signing up. |
| **Stripe Auth** | Inline real-time validation on blur + persistent inputs + accessible password reveal | Zero form-reset frustration on mistyped passwords or already-registered emails. |

---

## 2. Desktop Layout Architecture & ASCII Wireframe (`1440px`)

### Variant A: Direct Auth (No `pendingIntent`) — Centered Single Anchor
```
+---------------------------------------------------------------------------------------------------+
| MINIMAL AUTH HEADER (56px)                                                                        |
| [Tailored Mark]                                                      [← Back to Command Center]   |
+---------------------------------------------------------------------------------------------------+
|                                                                                                   |
|                          +---------------------------------------------+                          |
|                          |         [ Sign In ]  |  [ Create Account ]  |  (URL-synced tabs)       |
|                          |---------------------------------------------|                          |
|                          |  Create Your Verified Identity              |                          |
|                          |  Start with 2 Free Credits — zero card req. |                          |
|                          |                                             |                          |
|                          |  [ Continue with Google ]                   |                          |
|                          |  [ Continue with LinkedIn (Auto-fills Bio) ]|                          |
|                          |                                             |                          |
|                          |  --------------- or with email ------------ |                          |
|                          |                                             |                          |
|                          |  Full Name (Create Account only)            |                          |
|                          |  [ Mostafa Ibrahim                        ] |                          |
|                          |                                             |                          |
|                          |  Email Address                              |                          |
|                          |  [ mostafa@example.com                    ] |                          |
|                          |                                             |                          |
|                          |  Password                 [Forgot password?] |                          |
|                          |  [ ••••••••••••                    [Show] ] |                          |
|                          |  Strength: [████░] Strong (8+ chars, symbol)|                          |
|                          |                                             |                          |
|                          |  [✓] Private by design: never sold or shared|                          |
|                          |      with recruiters. (Terms · Privacy)     |                          |
|                          |                                             |                          |
|                          |  [ Create Account & Build Profile →       ] |                          |
|                          +---------------------------------------------+                          |
+---------------------------------------------------------------------------------------------------+
```

### Variant B: Contextual Intent-Preserving Split (Only when `pendingIntent` exists)
```
+---------------------------------------------------------------------------------------------------+
| MINIMAL AUTH HEADER (56px)                                                                        |
+---------------------------------------------------------------------------------------------------+
|        +-------------------------------------+   +---------------------------------------------+  |
|        | YOUR QUEUED ACTION (Context Card)   |   | [ Sign In ]  |  [ Create Account ]          |  |
|        |-------------------------------------|   |---------------------------------------------|  |
|        | Target Job:                         |   | Auth Form (Identical to Variant A)          |  |
|        | Swvl — Lead Data Scientist          |   |                                             |  |
|        | Cairo, Egypt (Hybrid)               |   |                                             |  |
|        |                                     |   |                                             |  |
|        | Queued:                             |   |                                             |  |
|        | 1. Build 6-step Profile (or drop CV)|   |                                             |  |
|        | 2. Claim 2 Free Credits             |   |                                             |  |
|        | 3. Open straight in CV Studio       |   |                                             |  |
|        +-------------------------------------+   +---------------------------------------------+  |
+---------------------------------------------------------------------------------------------------+
```

---

## 3. Eye-Scan Path & Anti-Saccade Map

1. **Fixation 1 (Auth Card Top Tabs & OAuth Buttons):** User immediately sees whether they are in Sign In or Create Account mode and sees the 1-click Google / LinkedIn shortcuts first.
2. **Fixation 2 (Vertical Field Stack):** Top-to-bottom single-column fields (`Name` → `Email` → `Password` → `Submit`). Never place multi-column form inputs inside auth cards.
3. **Fixation 3 (Only if Variant B):** Peripheral reassurance on the left (`320px`) sits immediately next to the form (`24px` gap) with zero interactive distractions competing with form completion.

---

## 4. Proximity & Click-Depth Budget

| User Intent | Click / Keystroke Depth | Spatial Location |
| :--- | :--- | :--- |
| **Sign up via OAuth** | `1` click (`[Continue with Google / LinkedIn]`) | Top of Auth Card |
| **Switch Sign In ↔ Create Account** | `1` click (updates browser URL `/login` ↔ `/register`) | Top segmented tab inside Auth Card |
| **Toggle password visibility** | `1` click | Right edge inside Password input |
| **Recover forgotten password** | `1` click | Directly inline above top-right of Password input (Sign In mode) |
| **Submit form** | `Enter` inside any input or `1` click | Bottom full-width primary button |

---

## 5. Detailed Zone-by-Zone Component & Interaction Spec

- **Autofocus Rule:** On `/login`, autofocus `Email`; on `/register`, autofocus `Full Name`.
- **OAuth Value Hint:** `[Continue with LinkedIn]` explicitly clarifies *"Imports name, email & headline"* to accelerate onboarding.
- **Smart Conflict Handling:** If user submits `/register` with an email that already exists, offer an inline 1-click prompt right below the field: *"An account with this email already exists. [Switch to Sign In with this email →]"* (retains typed email!).
- **Terms & Privacy Link Integrity:** `[Terms]` and `[Privacy]` open cleanly in a preview drawer or new tab so user doesn't lose form progress.
- **Session Persistence:** Sign In keeps a clear `Keep me signed in on this device` checkbox (default checked).

---

## 6. Interactivity, Adjustability & Keyboard Shortcuts

| Shortcut / Control | Behavior |
| :--- | :--- |
| `Enter` | Submits active auth form. |
| `Tab` | Clean linear focus traversal: Tabs → OAuth → Form Inputs → Show Toggle → Forgot Password → Submit. |
| Browser Back/Forward | Synchronized cleanly between `/login` and `/register` via History API. |

---

## 7. State Matrix & Edge Cases

| State | Behavior |
| :--- | :--- |
| **Submitting / OAuth Redirecting** | Button displays inline spinner (*"Signing you in..."*), disables double-submission while preserving typed values. |
| **Invalid Credentials** | Inline error directly above Submit button (*"Email or password didn't match — try again or [Reset password]."*). Never wipes the email field. |
| **OAuth Cancelled / Failed** | Inline dismissible notice (*"Google sign-in didn't finish. You can try again or use email below."*). |
| **Already Authenticated** | Visiting `/login` or `/register` redirects cleanly to `/dashboard` (or fulfills `pendingIntent`). |

---

## 8. Frontend UI Implementation Contract

- **Suggested Components:** `AuthPage`, `AuthModeTabs`, `OAuthButtonGroup`, `PasswordStrengthMeter`, `QueuedIntentContextCard`.
- **State:** `mode: 'signin' | 'signup'`, `email`, `fullName`, `password`, `showPassword`, `rememberMe`, `pendingIntent`, `fieldErrors`.
- **Backend Hooks:**
  - `POST /api/v1/auth/login` `[New Endpoint Needed]`
  - `POST /api/v1/auth/register` `[New Endpoint Needed]`
  - `GET /api/v1/auth/oauth/{google|linkedin}` `[New Endpoint Needed]`
- **UX Acceptance Criteria:**
  1. Toggling tabs immediately updates browser pathname (`/login` ↔ `/register`) and preserves already typed email.
  2. Error states never clear the email input or hide the `Forgot password?` link.
  3. OAuth and Email flows preserve `pendingIntent` across `/verify-email` and `/onboarding`.
