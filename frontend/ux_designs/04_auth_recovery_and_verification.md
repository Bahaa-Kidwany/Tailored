# 04 — Auth Recovery & Email Verification (`/forgot-password`, `/reset-password`, `/verify-email`)

**Routes:** `/forgot-password`, `/reset-password`, `/verify-email`  
**Implementation Status:** **Never Implemented**  
**Primary User Goal:** Recover account access or verify an email address quickly without dead ends, multi-tab confusion, or losing queued onboarding/job actions.  
**Entry Points:** `/login` (`Forgot password?`), `/register` post-submit, email magic/reset link clicks, `/account` email change verification.  
**Exit Destinations:** `/login` (after reset), `/onboarding` (new verified user), `/dashboard` or `pendingIntent` destination.  
**Credit Model Impact:** None; preserves any pending starter credit allocation across verification.

---

## 1. UX Reference Benchmarks & Ergonomic Rationale

| Reference | Pattern Adopted | Ergonomic Benefit for Tailored |
| :--- | :--- | :--- |
| **Clerk & Linear Verification** | Paste-friendly 6-digit segmented OTP box with auto-advance & auto-submit + direct inbox launcher links | Eliminates manual copy-typing errors and reduces context switch friction when opening Gmail/Outlook. |
| **Stripe Password Reset** | Live inline requirement checklist + explicit invalid/expired token recovery card | Prevents users from guessing password rules or getting stuck on a dead link. |

---

## 2. Desktop Layout Architecture & ASCII Wireframes (`1440px`)

### Screen A: `/forgot-password` (Request Reset)
```
+---------------------------------------------------------------------------------------------------+
| MINIMAL HEADER: [Tailored Mark]                                                 [← Back to Sign In]|
+---------------------------------------------------------------------------------------------------+
|                                                                                                   |
|                          +---------------------------------------------+                          |
|                          |  Reset Your Password                        |                          |
|                          |  Enter your account email and we'll send    |                          |
|                          |  a 15-minute reset link.                    |                          |
|                          |                                             |                          |
|                          |  Email Address                              |                          |
|                          |  [ mostafa@example.com                    ] |                          |
|                          |                                             |                          |
|                          |  [ Send Reset Link →                      ] |                          |
|                          +---------------------------------------------+                          |
|                                                                                                   |
|  AFTER SUBMIT (In-Place Swap — Zero Page Jump):                                                   |
|                          +---------------------------------------------+                          |
|                          |  ✓ Check Your Inbox                         |                          |
|                          |  We sent a reset link to mostafa@example.com|                          |
|                          |  [Wrong email? Edit]                        |                          |
|                          |                                             |                          |
|                          |  [ Open Gmail ↗ ]     [ Open Outlook ↗ ]    |                          |
|                          |                                             |                          |
|                          |  Didn't arrive? Resend available in 00:42   |                          |
|                          +---------------------------------------------+                          |
+---------------------------------------------------------------------------------------------------+
```

### Screen B: `/reset-password?token=...` (Set New Password)
```
+---------------------------------------------------------------------------------------------------+
|                          +---------------------------------------------+                          |
|                          |  Create a New Password                      |                          |
|                          |  Account: mostafa@example.com               |                          |
|                          |                                             |                          |
|                          |  New Password                      [Show]   |                          |
|                          |  [ ••••••••••••••                         ] |                          |
|                          |  ✓ At least 8 characters                    |                          |
|                          |  ✓ Includes a number or symbol              |                          |
|                          |                                             |                          |
|                          |  Confirm New Password                       |                          |
|                          |  [ ••••••••••••••                         ] |                          |
|                          |                                             |                          |
|                          |  [ Save Password & Sign In →              ] |                          |
|                          +---------------------------------------------+                          |
+---------------------------------------------------------------------------------------------------+
```

### Screen C: `/verify-email` (OTP Code + Link Status)
```
+---------------------------------------------------------------------------------------------------+
|                          +---------------------------------------------+                          |
|                          |  Verify Your Email                          |                          |
|                          |  Enter the 6-digit code sent to:            |                          |
|                          |  mostafa@example.com   [Change email]       |                          |
|                          |                                             |                          |
|                          |  [ 4 ]  [ 8 ]  [ 2 ]  [ 9 ]  [ _ ]  [ _ ]   |                          |
|                          |  (Full 6-digit paste supported)             |                          |
|                          |                                             |                          |
|                          |  [ Verify & Continue →                    ] |                          |
|                          |                                             |                          |
|                          |  [ Open Gmail ↗ ]  ·  Resend code (00:38)   |                          |
|                          +---------------------------------------------+                          |
+---------------------------------------------------------------------------------------------------+
```

---

## 3. Eye-Scan Path & Anti-Saccade Map

1. **Fixation 1 (Card Heading & Target Email):** User immediately verifies the exact email address the code/link went to.
2. **Fixation 2 (Primary Input — Email / Password / 6-Digit OTP):** Centered directly beneath heading, autofocused on mount.
3. **Fixation 3 (Action & Escape Hatch):** Primary button directly below input; `[Edit email]` / `[Resend]` / `[Open Gmail]` anchored within `120px` vertically—zero scanning outside the card.

---

## 4. Proximity & Click-Depth Budget

| User Intent | Click / Keystroke Depth | Spatial Location |
| :--- | :--- | :--- |
| **Submit 6-digit verification code** | Paste 6 digits (`0` clicks — auto-submits!) | OTP segmented input |
| **Jump to email inbox** | `1` click (`[Open Gmail ↗]` / `[Open Outlook ↗]`) | Directly beneath OTP / Reset confirmation |
| **Fix typo in signup email** | `1` click on `[Change email]` inline edit | Directly next to masked email address |
| **Return to Sign In** | `1` click | Top-right header or card footer |

---

## 5. Detailed Zone-by-Zone Component & Interaction Spec

- **Pre-Fill Carryover:** Clicking `Forgot password?` from `/login` pre-populates the email input on `/forgot-password` if the user had already typed one.
- **OTP Input Ergonomics:**
  - Supports pasting full 6-digit string into any box (distributes across all 6 slots and triggers verification automatically).
  - `Backspace` on an empty slot steps focus cleanly to the previous slot.
  - Displays visible inline validation without wiping slots on mismatch unless user clicks clear or starts typing fresh.
- **Token Failure Recovery (`/reset-password`):** If token is missing, already used, or expired, immediately display a calm recovery state (*"This reset link has expired — links last 15 minutes for security."*) with an inline 1-click `[Send a Fresh Link →]` button.
- **Auto-Sign-In After Reset/Verify:** Completing `/reset-password` or `/verify-email` authenticates the session directly and resumes `pendingIntent` (or routes new users straight into `/onboarding` without forcing a second manual login).

---

## 6. Interactivity, Adjustability & Keyboard Shortcuts

| Shortcut / Control | Behavior |
| :--- | :--- |
| `Ctrl/Cmd + V` (in OTP) | Fills all 6 digits and auto-submits. |
| `ArrowLeft` / `ArrowRight` | Steps between OTP digit slots. |
| `Enter` | Submits email reset request or new password form. |

---

## 7. State Matrix & Edge Cases

| State | Behavior |
| :--- | :--- |
| **Anti-Enumeration Protection (`/forgot-password`)** | Shows identical confirmation screen regardless of whether the email exists, avoiding security leaks while keeping copy helpful (*"If an account exists for..., we sent instructions"*). |
| **Resend Cooldown** | Disables `[Resend]` for 60s with live countdown (`00:59`), then enables cleanly with toast confirmation on resend. |
| **Too Many Attempts** | Inline lock warning with exact wait duration (*"Too many code attempts — try again in 5 minutes or request a fresh code."*). |
| **Changed Email Mid-Verify** | Updates pending account email and immediately dispatches a new 6-digit code, resetting cooldown gracefully. |

---

## 8. Frontend UI Implementation Contract

- **Suggested Components:** `ForgotPasswordPage`, `ResetPasswordPage`, `VerifyEmailPage`, `OtpCodeInput`, `InboxQuickLaunchers`.
- **State:** `email`, `otpDigits[6]`, `resendSecondsRemaining`, `tokenStatus: 'valid' | 'expired' | 'checking'`, `isEditingEmail`.
- **Backend Hooks:**
  - `POST /api/v1/auth/forgot-password` `[New Endpoint Needed]`
  - `POST /api/v1/auth/reset-password` `[New Endpoint Needed]`
  - `POST /api/v1/auth/verify-email` & `POST /api/v1/auth/resend-verification` `[New Endpoint Needed]`
- **UX Acceptance Criteria:**
  1. Email typed on `/login` carries over automatically to `/forgot-password`.
  2. Pasting a 6-digit OTP submits automatically without requiring a separate button click.
  3. Expired reset tokens show a 1-click fresh-link trigger rather than a dead error screen.
