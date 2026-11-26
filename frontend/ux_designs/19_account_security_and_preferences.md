# 19 — Account, Security, Workspace Ergonomics & Privacy (`/account`)

**Route:** `/account`  
**Implementation Status:** Currently merged inside `AtelierAccountAndPlansPage.tsx` — **Dedicated Account, Security, Workspace Defaults & Data Ownership Hub**  
**Primary User Goal:** Control authentication security (email, password, 2FA, active sessions), manage connected Google/LinkedIn SSO, customize default workspace ergonomics (default start page, density, pane reset), configure alerts, and export or erase personal data cleanly.  
**Entry Points:** Global Sidebar (`Account & Security`), Avatar/Command Palette (`Go to Account`), `/plans` cross-link.  
**Exit Destinations:** `/login` (on Sign Out or Account Deletion), `/verify-email` (on email change), `/plans`.  
**Credit Model Impact:** **100% Free**; explicitly shows zero data monetization guarantee (*"Your data is never sold or used for recruiter screening"*).

---

## 1. UX Reference Benchmarks & Ergonomic Rationale

| Reference | Pattern Adopted | Ergonomic Benefit for Tailored |
| :--- | :--- | :--- |
| **Linear Workspace & Account Settings** | Sticky inner left category menu (`220px`) + crisp single-column cards (`max-w: 740px`) + dedicated **Workspace Ergonomics** section | Separates security controls cleanly from workflow defaults like `Default Density` and `Reset Saved Pane Widths`. |
| **GitHub & Clerk Security** | Active Device Sessions list (`Revoke`) + step-by-step TOTP 2FA with recovery codes + OAuth unlink guard | Prevents users from locking themselves out by accidentally disconnecting their sole login method. |

---

## 2. Desktop Layout Architecture & ASCII Wireframe (`1440px`)

```
+---------------------------------------------------------------------------------------------------+
| GLOBAL SHELL (Left Nav 220px) | ACCOUNT & PREFERENCES (/account, flex-1)                          |
|-------------------------------|-------------------------------------------------------------------|
|                               | HEADER: Account, Security & Workspace Preferences   [Sign Out]    |
|                               |-------------------------------------------------------------------|
|                               | 2-COLUMN SETTINGS WORKSPACE                                       |
|                               |                                                                   |
|                               | INNER NAV (210px, Sticky) | SINGLE-COLUMN SETTINGS CARDS (740px)  |
|                               |---------------------------|---------------------------------------|
|                               | • Credentials & 2FA       | 1. CREDENTIALS & TWO-FACTOR AUTH      |
|                               | • Connected SSO Accounts  | Email: mostafa@tailored.atelier [Edit]|
|                               | • Active Sessions         | Password: Last changed 2m ago [Change]|
|                               | • Workspace Ergonomics    | 2FA (Authenticator App): [Enabled ✓]  |
|                               | • Notification Rules      |   [View Recovery Codes] [Disable 2FA] |
|                               | • Data Export & Privacy   |                                       |
|                               |                           | 2. CONNECTED SSO ACCOUNTS             |
|                               |                           | • Google (mostafa@gmail) [Disconnect] |
|                               |                           | • LinkedIn (in/mostafa-ai) [Connect]  |
|                               |                           |                                       |
|                               |                           | 3. WORKSPACE ERGONOMICS & DEFAULTS    |
|                               |                           | Default Home Route: [/dashboard ▾]    |
|                               |                           | List Density:       (•) Cozy ( ) Dense|
|                               |                           | Default Studio Mode:(•) Surgical      |
|                               |                           | Layout Reset: [Reset All Pane Widths] |
|                               |                           |                                       |
|                               |                           | 4. NOTIFICATION PREFERENCES           |
|                               |                           | High-Fit Match Alerts: [≥ 85% ▾]      |
|                               |                           | Digest Cadence: [Daily 9AM ▾]         |
|                               |                           | [✓] 7-Day Pipeline Follow-Up Reminders|
|                               |                           | [✓] Low Credit Balance Alerts (≤ 2 cr)|
|                               |                           |                                       |
|                               |                           | 5. DATA OWNERSHIP & DANGER ZONE       |
|                               |                           | [Export Complete Archive (JSON+.tex)] |
|                               |                           | [Delete Account & Erase All Data]     |
+-------------------------------+---------------------------+---------------------------------------+
```

---

## 3. Eye-Scan Path & Anti-Saccade Map

1. **Fixation 1 (Left Sticky Settings Nav):** Click any of the 6 topics (`Credentials`, `SSO`, `Sessions`, `Ergonomics`, `Notifications`, `Privacy`) to jump directly without endless scrolling.
2. **Fixation 2 (Centered Single-Column Card Stack):** Narrow `740px` measure makes reading toggles and security actions comfortable with zero horizontal scanning.
3. **Fixation 3 (Section-Scoped Save Controls):** Simple switches (`Density`, `Notification toggles`, `Default Route`) save optimistically with inline `"Saved ✓"` micro-feedback; sensitive changes (`Password`, `Email`, `Delete Account`) open focused inline confirmation drawers.

---

## 4. Proximity & Click-Depth Budget

| User Intent | Click / Keystroke Depth | Spatial Location |
| :--- | :--- | :--- |
| **Reset custom split-pane sizes across all pages** | `1` click (`[Reset All Pane Widths]`) | Card 3 (`Workspace Ergonomics`) |
| **Switch default post-login page (`/dashboard` vs `/studio`)** | `1` click dropdown | Card 3 (`Default Home Route`) |
| **Adjust High-Fit alert threshold & email cadence** | `1` click | Card 4 (`Notification Preferences`) |
| **Export full JSON + `.tex` + PDF personal archive** | `1` click (`[Export Complete Archive]`) | Card 5 (`Data Ownership`) |
| **Revoke an unknown session / Sign out everywhere** | `1` click (`[Revoke]`) | `Active Sessions` card |

---

## 5. Detailed Zone-by-Zone Component & Interaction Spec

### 5.1 Workspace Ergonomics & Adjustability Hub (Card 3)
Gives explicit control over the system's adaptive UX:
- **Default Landing After Login:** `/dashboard` (Recommended), `/radar`, or `/studio`.
- **Default List Density:** `Comfortable` vs. `Compact` across Radar, Interest, Saved CVs, and Pipeline.
- **Default Studio Tailoring Intensity:** `Surgical` / `Metrics+` / `Executive`.
- **Keyboard Shortcuts Guide:** `[View All Shortcuts (?)]` opens a quick modal cheat-sheet.
- **Reset Saved Layouts:** Clears persisted pane widths & collapsed rail overrides in `localStorage` back to ergonomic defaults with 1 click.

### 5.2 SSO Unlink Guardrail
- If a user signed up exclusively via Google OAuth and never set a password, clicking `[Disconnect Google]` explains calmly: *"Set an account password first so you don't lock yourself out."* and expands an inline `Set Password` trigger right inside the card.

### 5.3 Guarded Account Deletion & Complete Export
- **`[Export Complete Archive]`** bundles `master_profile.json`, all tailored `.tex` sources, compiled PDFs, cover letters, and pipeline JSON into a downloadable `.zip` (with client-side JSON fallback if offline).
- **`[Delete Account]`** opens a focused confirmation modal displaying exact impact (`Profile, X tailored CVs, Y credits remaining — irreversible`) and requires typing `DELETE` before enabling confirmation.

---

## 6. Interactivity, Adjustability & Keyboard Shortcuts

- **Keyboard:** `?` opens Global Keyboard Shortcuts modal; `Esc` closes active password/2FA/delete dialogs cleanly.

---

## 7. State Matrix & Edge Cases

| State | Behavior |
| :--- | :--- |
| **Changing Email Address** | Keeps old email active until user verifies new email via 6-digit OTP (`/verify-email`), preventing accidental lockout. |
| **2FA Activation** | Displays QR + manual secret key + mandatory backup recovery codes download confirmation before enabling 2FA enforcement. |
| **Zero-Backend Offline Mode** | Workspace Ergonomics & JSON Export still work locally via browser storage; Credential/2FA actions display clear *"Reconnect to update security credentials"* notice. |

---

## 8. Frontend UI Implementation Contract

- **Suggested Components:** `AccountSecurityPage`, `SettingsInnerNav`, `CredentialsAnd2FaCard`, `ConnectedSsoCard`, `ActiveSessionsCard`, `WorkspaceErgonomicsCard`, `NotificationRulesCard`, `DataOwnershipCard`.
- **State:** `securityState`, `sessions[]`, `workspaceDefaults: { homeRoute, density, defaultIntensity }`, `notificationRules`, `activeModal: 'password' | '2fa' | 'delete' | null`.
- **Backend Hooks:**
  - `GET/PATCH /api/v1/account/preferences`, `POST /api/v1/account/change-password`, `POST /api/v1/account/2fa/*`, `GET/DELETE /api/v1/account/sessions`, `GET /api/v1/account/export`, `DELETE /api/v1/account` `[New Endpoints Needed]`
- **UX Acceptance Criteria:**
  1. Cannot disconnect sole OAuth login without first setting a fallback password.
  2. Ergonomics controls (`Density`, `Reset Pane Widths`, `Default Home Route`) synchronize immediately across the shell.
  3. Full GDPR export delivers real downloadable user data cleanly.
