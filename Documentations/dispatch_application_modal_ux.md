# Dispatch Application Modal — UI & UX Architecture Specification
**Design System:** Sage & Obsidian Atelier  
**Document Version:** 2.0.0  
**Target:** Master UI/UX Blueprint for the Application Dispatch & Email Outreach Engine  
**Trigger:** Activated when candidate clicks `[ ✉ DISPATCH APPLICATION ]` in CV Studio  
**Visual Standard:** Conforms strictly to `DESIGN(1).md` and the visual architecture of the Tailored Atelier platform.

---

## 1. Executive Philosophy: The Atelier Dispatch Engine

The **Dispatch Application Modal** represents the "final mile" of the candidate copilot journey. After tailoring an ATS resume to a 94%+ match in CV Studio, the dispatch experience must be **instantaneous, authoritative, and frictionless**.

### Core Architecture Tenets:
1. **Pre-Filled Intelligence:** Recruiter destination, ATS-standard subject line, executive outreach pitch, and verified candidate contact credentials (`+20` Egypt or `+966` Saudi phone numbers) are synthesized automatically from verified context.
2. **Multi-Protocol Delivery:** Overcomes web browser sandbox limitations by providing four distinct execution paths: **Gmail Web (Primary)**, **Default Mail Client (mailto)**, **Full Formatted Clipboard Copy**, and **Direct Board Application Link**.
3. **Automated Pipeline Synchronization:** Eliminates manual tracking fatigue; initiating dispatch automatically transitions the job from `in_process` to `applied` in PostgreSQL and updates telemetry across the workspace.

---

## 2. Design System Tokens (`Sage & Obsidian Atelier`)

The interface applies the formal design tokens defined in `DESIGN(1).md`:

### 2.1 Color Palette
* **Obsidian Charcoal (`#0d1513`):** Ambient dark backdrop canvas, monolithic frame enclosures, and deep contrast grounding.
* **British Racing Forest (`#142e23`):** Primary focal buttons, active radio indicators, and dominant commitment surfaces.
* **Atelier Dispatch Emerald (`#00a86b`):** Precision accent pings, verified status badges, active telemetry dots, and hover execution states.
* **Pure Alabaster & Crisp Ivory (`#ffffff` / `#fbfdfc`):** Central elevated modal surface card, ensuring paper-like tactile clarity.
* **Mineral Sage (`#eafef3` / `#dff3e7`):** Soft chip backgrounds, input container fills, and subtle focus halos.
* **Stone Mist (`#d8e2dc`):** Micro-fine `1px` structural hairline borders.
* **Deep Slate Ink (`#121815`):** High-contrast editorial typography, numerical figures, and input values.
* **Muted Lichen (`#63756c`):** Secondary metadata, inactive states, column headers, and input placeholders.

### 2.2 Typography Hierarchy
* **Headlines & Editorial Titles:** **Newsreader** (`fontFamily: Newsreader`, `fontWeight: 400`–`500`, negative tracking `-0.015em`).
* **Interface, Metrics & Inputs:** **Manrope** (`fontFamily: Manrope`, `fontWeight: 400`–`600`).
* **Badges & Micro-Labels:** **Manrope** uppercase with extended tracking (`letterSpacing: 0.06em`–`0.08em`).

### 2.3 Geometry & Elevation
* **Modal Enclosure:** `rounded-xl` ($32\text{px}$ softened architectural corners).
* **Action Buttons & Chips:** `rounded-full` (pure cylindrical pill geometry).
* **Form Inputs & Textareas:** `rounded-lg` ($8\text{px}$–$12\text{px}$) with Stone Mist (`#d8e2dc`) hairlines.
* **Ambient Atelier Occlusion:** `box-shadow: 0 24px 64px -12px rgba(13, 21, 19, 0.35), 0 4px 16px -2px rgba(13, 21, 19, 0.15)`.

---

## 3. Modal Visual Wireframe & Layout Architecture

The modal adopts the centered elevated Alabaster card structure established in the Atelier design system:

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ TAILORED  [PRIVATE ATELIER]                                                            [ RETURN TO STUDIO ✕ ]   │
│                                                                                                                  │
│                        ● Dispatch Verification: Swvl Mobility • Lead Data Scientist • Cairo                      │
│                                                                                                                  │
│ ┌──────────────────────────────────────────────────────────────────────────────────────────────────────────────┐ │
│ │                                                                                                              │ │
│ │                                            ★ ATELIER OUTREACH ENGINE                                         │ │
│ │                                       Dispatch Bespoke Application                                           │ │
│ │                      Verified ATS resume pairing and contextual executive outreach for Swvl.                 │ │
│ │                                                                                                              │ │
│ │ ┌──────────────────────────────────────────────┬───────────────────────────────────────────────────────────┐ │ │
│ │ │ COLUMN 1: TRANSMISSION & CREDENTIALS         │ COLUMN 2: CONTEXTUAL OUTREACH PITCH                       │ │ │
│ │ │ (42% Width)                                  │ (58% Width)                                               │ │ │
│ │ ├──────────────────────────────────────────────┼───────────────────────────────────────────────────────────┤ │ │
│ │ │ 1. RECIPIENT ("TO"):                         │ 4. EXECUTIVE COVER LETTER BODY:                           │ │ │
│ │ │ To: [ careers@swvl.com                     ] │ ┌───────────────────────────────────────────────────────┐ │ │ │
│ │ │ Badge: [ ✓ Extracted from Swvl Spec ]        │ │ Dear Swvl Talent Acquisition Team,                    │ │ │ │
│ │ │ CC: [ mostafa.eng@tailored.atelier         ] │ │                                                       │ │ │ │
│ │ │                                              │ │ I am writing to express my strong interest in the     │ │ │ │
│ │ │ 2. SUBJECT LINE:                             │ │ Lead Data Scientist position at Swvl. Having          │ │ │ │
│ │ │ [ Application: Lead Data Scientist — Mostafa]│ │ architected distributed ML inference pipelines and    │ │ │ │
│ │ │                                              │ │ dynamic pricing models across Egypt and Gulf markets, │ │ │ │
│ │ │ 3. VERIFIED ATTACHMENT DECK:                 │ │ I was particularly drawn to Swvl's transit challenges.│ │ │ │
│ │ │ ┌──────────────────────────────────────────┐ │ │                                                       │ │ │ │
│ │ │ │ 📄 Mostafa_Ibrahim_CV_Swvl.pdf           │ │ │ In my recent work, I spearheaded low-latency dynamic  │ │ │ │
│ │ │ │ 142 KB • 1-Page ATS Enforced • LaTeX OK  │ │ │ pricing algorithms using PyTorch and FastAPI, cutting │ │ │ │
│ │ │ │ [ 👁 Preview ]         [ 📥 Download ]   │ │ │ dispatch latency by 42% across 1,400 Cairo routes.    │ │ │ │
│ │ │ └──────────────────────────────────────────┘ │ │                                                       │ │ │ │
│ │ │ ┌──────────────────────────────────────────┐ │ │ My tailored ATS resume is attached for review.       │ │ │ │
│ │ │ │ 📝 Cover_Letter_Swvl.txt (2.1 KB)        │ │ │                                                       │ │ │ │
│ │ │ │ [ 📥 Download Text ]                     │ │ │ Sincerely,                                            │ │ │ │
│ │ │ └──────────────────────────────────────────┘ │ │ Mostafa Ibrahim — Senior AI & Infra Engineer          │ │ │ │
│ │ │                                              │ │ Phone: +20 100 482 9102 (Egypt Mobile)                │ │ │ │
│ │ │ CANDIDATE VERIFIED IDENTITY:                 │ │ Email: mostafa.eng@tailored.atelier                   │ │ │ │
│ │ │ • Phone: +20 100 482 9102 (EG Mobile)        │ │ LinkedIn: linkedin.com/in/mostafa-ai                  │ │ │ │
│ │ │ • LinkedIn: linkedin.com/in/mostafa-ai       │ └───────────────────────────────────────────────────────┘ │ │ │
│ │ │ • GitHub: github.com/m-ibrahim               │ Quick Polish Chips:                                       │ │ │ │
│ │ │                                              │ [ Make More Concise ]  [ Emphasize Scale ]  [ ↺ Reset ]   │ │ │ │
│ │ └──────────────────────────────────────────────┴───────────────────────────────────────────────────────────┘ │ │
│ │                                                                                                              │ │
│ │ ──────────────────────────────────────────────────────────────────────────────────────────────────────────── │ │
│ │ 5. DISPATCH EXECUTION CONTROLS:                                                                              │ │
│ │ [✓] Automatically advance this opportunity to "Applied" in Application Pipeline                              │ │
│ │                                                                                                              │ │
│ │ [ 📋 Copy Full Email ]      [ ✉ Default Mail App ]      [ 🚀 Open in Gmail Web ↗ (Recommended) ✦ ]           │ │
│ └──────────────────────────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                                                  │
│                        Bank-grade data isolation. Application telemetry recorded to PostgreSQL 15.               │
│                                                                                                                  │
│ © 2025 TAILORED Atelier Inc. All rights reserved.                                        Privacy • Terms • Security│
└──────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Component & Interactive Specifications

### 4.1 Ambient Enclosure & Header Architecture
* **Canvas Backdrop:** Obsidian Charcoal (`#0d1513`) with subtle deep forest mineral vignette (`radial-gradient(ellipse at 50% 20%, rgba(20, 46, 35, 0.4) 0%, #0d1513 100%)`).
* **Top Navigation:**
  - Left: `TAILORED` mark in bold Manrope + `PRIVATE ATELIER` pill badge.
  - Right: `RETURN TO STUDIO ✕` text link in Muted Lichen (`#63756c`).
* **Top Status Pill:** Centered cylindrical pill with a solid 6px Dispatch Emerald (`#00a86b`) indicator:  
  `● Dispatch Verification: Swvl Mobility • Lead Data Scientist • Cairo, Egypt`.

### 4.2 Central Alabaster Modal Card
* **Surface:** Pure Alabaster (`#ffffff`) background, `rounded-xl` ($32\text{px}$ radius), bordered by a crisp `1px` Stone Mist (`#d8e2dc`) hairline frame.
* **Header Tag:** Gold/bronze tracked small caps `★ ATELIER OUTREACH ENGINE` (`letterSpacing: 0.08em`).
* **Headline:** Newsreader serif (`display-lg` / $40\text{px}$): **"Dispatch Bespoke Application"**.
* **Subheadline:** Manrope regular (`body-md` / $15\text{px}$ in `#63756c`): *"Verified ATS resume pairing and contextual executive outreach for Swvl Mobility."*

---

### 4.3 Column 1: Transmission & Credentials (Left, 42% Width)

1. **Recipient ("To") Field:**
   - Pre-populated with extracted recruiter contact (`careers@swvl.com`).
   - Verified Badge: `rounded-full` pill in Mineral Sage (`#dff3e7`) with text in British Racing Forest (`#142e23`): `✓ Extracted from Swvl Spec`.
   - CC Field: Pre-populated with `mostafa.eng@tailored.atelier` ensuring the user receives a copy.
2. **Subject Line Field:**
   - Single-line input with pre-formatted corporate syntax:  
     `Application: Lead Data Scientist — Mostafa Ibrahim (Senior AI & Infrastructure Engineer)`.
3. **Verified Attachment Deck:**
   - **Card A (Tailored ATS CV):**
     - Title: `📄 Mostafa_Ibrahim_CV_Swvl.pdf`.
     - Metadata line: `142 KB • 1-Page ATS Enforced • LaTeX OK`.
     - Action Pills: `[ 👁 Preview PDF ]` (opens light-box) and `[ 📥 Download ]`.
   - **Card B (Cover Letter Text):**
     - Title: `📝 Cover_Letter_Swvl.txt (2.1 KB)`.
     - Action Pill: `[ 📥 Download Text ]`.
4. **Candidate Verified Identity Stamp:**
   - Compact reference block confirming which regional phone number was dynamically paired (`+20 100 482 9102 Egypt Mobile`), primary email, and clean portfolio URLs.

---

### 4.4 Column 2: Contextual Outreach Pitch (Right, 58% Width)

1. **Executive Pitch Textarea:**
   - Rendered inside an Alabaster container with Stone Mist border (`#d8e2dc`) and $16\text{px}$ padding.
   - Text rendered in Deep Slate Ink (`#121815`) with $24\text{px}$ line height (`body-md`).
   - Contextually emphasizes Swvl's exact keywords (dynamic pricing algorithms, PyTorch, FastAPI, 42% latency reduction).
   - Fully editable directly by the candidate before dispatching.
2. **Quick Polish Chips (One-Tap Action Pills):**
   - Positioned beneath the textarea in pure pill geometry (`rounded-full`):
     - `[ Make More Concise ]`: Compresses text into 2 high-density paragraphs.
     - `[ Emphasize Scale ]`: Injects high-throughput telemetry numbers.
     - `[ Add Notice Period ]`: Appends availability status.
     - `[ ↺ Reset to Draft ]`: Reverts custom edits back to original AI generation.

---

### 4.5 Dispatch Execution Controls (Footer)

1. **Pipeline Auto-Sync Checkbox:**
   - Soft squircle checkbox (`#142e23` active fill) with Manrope label:  
     `[✓] Automatically advance this opportunity to "Applied" in Application Pipeline`.
2. **The 3 Delivery Action Buttons:**
   - **Primary Action (Gmail Web):**  
     Solid British Racing Forest (`#142e23`) fill, pure white text (`#ffffff`), `rounded-full` pill:  
     👉 **`[ 🚀 Open in Gmail Web ↗ (Recommended) ✦ ]`**  
     *(Hover shifts to Obsidian Charcoal `#0d1513`). Automatically downloads the PDF and opens `mail.google.com` with To, Subject, and Body filled.*
   - **Secondary Action (Clipboard Copy):**  
     Crisp Ivory fill (`#fbfdfc`), `1px` Stone Mist border (`#d8e2dc`), Slate Ink typography (`#121815`), `rounded-full`:  
     `[ 📋 Copy Full Email ]` *(Copies formatted bundle with instant checkmark feedback).*
   - **Tertiary Action (Default Mail App):**  
     Ivory pill: `[ ✉ Default Mail App ]` *(Triggers system `mailto:` protocol).*

---

## 5. Multi-Channel Execution Protocols & Browser Bridges

Because web browsers prohibit scripts from programmatically attaching physical disk files into external applications without user confirmation, the dispatch actions execute through structured bridges:

| Protocol | User Trigger | Automated System Execution | Feedback Toast |
| :--- | :--- | :--- | :--- |
| **Protocol 1: Gmail Web (Recommended)** | Click `[ Open in Gmail Web ↗ ]` | 1. Background downloads `Mostafa_Ibrahim_CV_Swvl.pdf`.<br>2. Copies email body to clipboard.<br>3. Opens `mail.google.com/mail/?view=cm&fs=1&...` in new tab.<br>4. Advances pipeline status to `applied`. | *"Gmail compose opened! Drag the downloaded PDF from your browser tray to attach."* |
| **Protocol 2: Native Mail App** | Click `[ Default Mail App ]` | 1. Background downloads PDF.<br>2. Triggers `window.location.href = "mailto:..."`.<br>3. Advances pipeline status to `applied`. | *"Default mail client launched with pre-filled pitch and subject."* |
| **Protocol 3: Full Clipboard Copy** | Click `[ Copy Full Email ]` | 1. Copies To, Subject, and Body to system clipboard.<br>2. Advances pipeline status to `applied`. | *"✓ Complete application copied to clipboard!"* |
| **Protocol 4: Board Fallback** | Click `[ Apply on Swvl Careers ↗ ]` | 1. Downloads tailored ATS PDF.<br>2. Opens external careers portal in new tab.<br>3. Advances pipeline status to `applied`. | *"External careers page opened. Tailored PDF saved to your downloads."* |

---

## 6. Pipeline State Transitions & Data Synchronization

When dispatch is executed, the client triggers `POST /api/v1/pipeline/dispatch`:
* **Pipeline Status Transition:** `in_process` $\longrightarrow$ `applied`.
* **Applied Timestamp:** Recorded as `applied_at = NOW()`.
* **Outreach Channel:** Logged as `email_outreach_gmail`, `email_outreach_mailto`, or `external_board`.
* **Asset Immutability:** The dispatched LaTeX source and compiled PDF are frozen in PostgreSQL to maintain an immutable audit trail.
* **Modal Close:** Modal smoothly dismisses after $1.5\text{ seconds}$, returning the user to the workspace with an updated pipeline badge (`📋 Applied: 1`).
