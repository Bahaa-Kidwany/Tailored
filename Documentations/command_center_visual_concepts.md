# Command Center (Approach 3): Architecture & 3D Cover Flow Specification

**Document Version:** 3.0.0  
**Scope:** Landing Page Architecture — Universal 4-Mode Omni-Bar & 3D Cover Flow Carousel  
**Visual Tokens:** Typography and color palette are **strictly undefined** (to be finalized in a dedicated design phase).

---

## 1. Executive Structural Overview

Approach 3 (The Command Center) organizes the entry experience around three structural anchors:
1. **The 3-Layer Visual Depth Stack:** A background photographic image, separated from the foreground UI by a dedicated effects layer.
2. **The Universal Omni-Bar:** A single, multi-modal input dock supporting four distinct user intents without tab switching.
3. **The 3D Cover Flow Carousel:** A true spatial 3D stage showcasing Tailored's three core features with prominent center focus and angled, receding side cards in an infinite loop.

---

## 2. The 3-Tier Layered Visual Architecture

To achieve depth and visual separation while supporting any photographic background, the viewport is structured into three physical layers:

```
┌────────────────────────────────────────────────────────────────────────┐
│  LAYER 3: Foreground Interactive Components                            │
│  • Floating Universal Omni-Bar                                         │
│  • 3D Cover Flow Carousel (Feature Showcase)                           │
│  • Header Navigation & Global Actions                                  │
├────────────────────────────────────────────────────────────────────────┤
│  LAYER 2: Dedicated Effects Layer (Backdrop Scrim)                     │
│  • Positioned directly above the background image and below the UI     │
│  • Frosted glass / Gaussian backdrop blur scrim with subtle gradient   │
│  • Guarantees text contrast and separation from photographic detail    │
├────────────────────────────────────────────────────────────────────────┤
│  LAYER 1: Background Photographic Image                                │
│  • Full-bleed architectural / environmental imagery                    │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. The Universal Omni-Bar (4 Input Modes)

The primary user action bar sits centered above the fold. It features an intelligent parser that automatically handles four distinct input modalities:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│  [ 📎 Upload CV ]  |  Type a role, paste a link, or ask the AI copilot...               [ ⚡ Execute ↵ ] │
│                                                                                                        │
│  Mode Indicators:                                                                                      │
│  [ 1. Search Roles ]   [ 2. AI Prompt ]   [ 3. CV Ingestion ]   [ 4. Paste Job Link ]     │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.1 Mode Specifications

| Mode | Trigger / Action | System Behavior |
| :--- | :--- | :--- |
| **1. Search** | Typing role, keyword, or location (e.g. *"Data Scientist in Cairo"*) | Filters and re-orders the live job radar feed. |
| **2. AI Prompt** | Typing natural language (e.g. *"Find remote roles using FastAPI"*) | Queries LLM router to surface context-aware opportunities. |
| **3. CV Upload** | Dragging `.pdf`, `.tex`, `.docx` or clicking `[📎 Upload CV]` | Extracts skills and personas; unlocks personalized match scores. |
| **4. Link Paste** | Pasting external URL (LinkedIn, Wuzzuf, Greenhouse, Lever) | Stealth-scrapes, deduplicates, and saves to **"List of Interest"**. |

---

## 4. The 3D Cover Flow Carousel Engine

Directly beneath the Omni-Bar, the three core value propositions are showcased inside a **spatial 3D Cover Flow stage** (`perspective: 1200px`).

### 4.1 Spatial Stage Geometry

```
       LEFT CARD (Receded)              CENTER CARD (Prominent)             RIGHT CARD (Receded)
   ┌───────────────────────────┐     ┌─────────────────────────────┐     ┌───────────────────────────┐
   │ 01 • Multi-Source Radar   │     │ 02 • Candidate Match Engine │     │ 03 • Surgical CV Studio   │
   │                           │     │                             │     │                           │
   │  rotateY(32deg)           │     │  rotateY(0deg)              │     │  rotateY(-32deg)          │
   │  translateZ(-140px)       │     │  translateZ(0px)            │     │  translateZ(-140px)       │
   │  scale(0.86)              │     │  scale(1.05)                │     │  scale(0.86)              │
   │  opacity: 0.50            │     │  opacity: 1.0 (Full Focus)  │     │  opacity: 0.50            │
   └───────────────────────────┘     └─────────────────────────────┘     └───────────────────────────┘
                 ▲                                  ▲                                  ▲
                 └────────────── Seamless Infinite Looping Transition ─────────────────┘
                                   (Cycles smoothly every 3.5s; hover to pause)
```

### 4.2 Behavior & Motion Rules
* **Prominent Center Focus:** The active card faces straight ahead (`rotateY: 0deg`), scaled up (`1.05x`) with high visual priority and elevated shadow.
* **Receding 3D Side Cards:** The left and right cards are angled inward (`rotateY(32deg)` and `rotateY(-32deg)`), receded backward in Z-space (`translateZ(-140px)`), scaled down (`0.86x`), and dimmed (`0.50 opacity`).
* **Infinite Cycling:** The three cards continuously cycle in a seamless loop (`index = (index + 1) % 3`).
* **Interactive Overrides:**
  - **Hover to Pause:** Hovering over the carousel pauses automatic rotation.
  - **Click to Focus:** Clicking either angled side card immediately rotates it to the center stage.
  - **Manual Navigation:** Left (`‹`) and right (`›`) navigation triggers and dot indicators.

### 4.3 The 3 Core Feature Slides

1. **Card 1: Multi-Source Job Discovery & Stealth Radar**
   - Ingestion from LinkedIn and Wuzzuf with deep-description page fetching.
   - SHA-256 canonical deduplication key merging cross-posted listings.
   - Status: Real-time crawl volume and freshness indicator.

2. **Card 2: Candidate-Centric 5-Dimensional Fit Engine**
   - Radial composite match score ($0\text{--}100\%$).
   - 5 transparent dimension breakdowns: Skills Overlap (35%), Title Alignment (20%), Experience Proximity (20%), Projects & Impact (15%), Location & Mobility (10%).
   - Constructive gap framing (actionable guidance rather than binary disqualification).

3. **Card 3: Surgical ATS CV Studio & AI Bullet Tailoring**
   - Side-by-side bullet diff view (baseline wording vs. tailored additions with highlighted keywords).
   - High-fidelity live ATS LaTeX / PDF preview canvas.
   - Conversational AI assistant prompt integration.

---

## 5. Styling & Visual Tokens (Undefined / Abstract)

Per project guidelines, all typography, font pairings, and color palettes are **intentionally left undefined** and decoupled from layout geometry. Components must reference semantic variables only:

```css
/* Semantic Theme Tokens (Values to be assigned in design phase) */
:root {
  /* Typography Tokens (Undefined) */
  --font-family-display: /* TO BE DEFINED */;
  --font-family-body:    /* TO BE DEFINED */;
  --font-family-mono:    /* TO BE DEFINED */;

  /* Surface & Scrim Tokens (Undefined) */
  --surface-canvas:      /* TO BE DEFINED */;
  --surface-card:        /* TO BE DEFINED */;
  --surface-input:       /* TO BE DEFINED */;
  --effects-scrim:       /* TO BE DEFINED (Layer 2 Backdrop Filter & Gradient) */;

  /* Text & Border Tokens (Undefined) */
  --text-primary:        /* TO BE DEFINED */;
  --text-secondary:      /* TO BE DEFINED */;
  --border-card:         /* TO BE DEFINED */;
  --border-focus:        /* TO BE DEFINED */;

  /* Accent & Action Tokens (Undefined) */
  --accent-action:       /* TO BE DEFINED */;
  --accent-pill:         /* TO BE DEFINED */;
  --accent-score:        /* TO BE DEFINED */;
}
```

---

## 6. CSS Reference Implementation for the 3D Stage

```css
/* 3D Perspective Stage */
.coverflow-stage {
  perspective: 1200px;
  perspective-origin: 50% 50%;
  transform-style: preserve-3d;
  position: relative;
  height: 320px;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Base Card */
.cf-card {
  position: absolute;
  width: 380px;
  height: 250px;
  border-radius: 20px;
  transition: all 0.75s cubic-bezier(0.25, 1, 0.5, 1);
  transform-style: preserve-3d;
  cursor: pointer;
  user-select: none;
}

/* Center Stage (Prominent) */
.cf-card.pos-center {
  transform: translate3d(0, 0, 40px) scale(1.05);
  z-index: 30;
  opacity: 1;
  filter: none;
}

/* Left Card (Receding 3D) */
.cf-card.pos-left {
  transform: translate3d(-64%, 0, -140px) rotateY(32deg) scale(0.86);
  z-index: 10;
  opacity: 0.50;
  filter: blur(0.5px);
}

/* Right Card (Receding 3D) */
.cf-card.pos-right {
  transform: translate3d(64%, 0, -140px) rotateY(-32deg) scale(0.86);
  z-index: 10;
  opacity: 0.50;
  filter: blur(0.5px);
}
```
