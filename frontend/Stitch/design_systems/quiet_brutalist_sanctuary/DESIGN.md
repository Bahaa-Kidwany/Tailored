---
name: Quiet Brutalist Sanctuary
colors:
  surface: '#0d1513'
  surface-dim: '#0d1513'
  surface-bright: '#333b38'
  surface-container-lowest: '#08100e'
  surface-container-low: '#151d1b'
  surface-container: '#19211f'
  surface-container-high: '#232c29'
  surface-container-highest: '#2e3634'
  on-surface: '#dce4e1'
  on-surface-variant: '#d0c5b6'
  inverse-surface: '#dce4e1'
  inverse-on-surface: '#2a3230'
  outline: '#998f82'
  outline-variant: '#4d463a'
  surface-tint: '#e2c289'
  primary: '#e2c289'
  on-primary: '#402d02'
  primary-container: '#bfa16b'
  on-primary-container: '#4c370b'
  inverse-primary: '#735b2c'
  secondary: '#accebe'
  on-secondary: '#17362b'
  secondary-container: '#2e4d40'
  on-secondary-container: '#9bbdad'
  tertiary: '#e3c286'
  on-tertiary: '#412d00'
  tertiary-container: '#bfa168'
  on-tertiary-container: '#4c3707'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#ffdea5'
  primary-fixed-dim: '#e2c289'
  on-primary-fixed: '#271900'
  on-primary-fixed-variant: '#594316'
  secondary-fixed: '#c8ead9'
  secondary-fixed-dim: '#accebe'
  on-secondary-fixed: '#012116'
  on-secondary-fixed-variant: '#2e4d40'
  tertiary-fixed: '#ffdea4'
  tertiary-fixed-dim: '#e3c286'
  on-tertiary-fixed: '#261900'
  on-tertiary-fixed-variant: '#594313'
  background: '#0d1513'
  on-background: '#dce4e1'
  surface-variant: '#2e3634'
typography:
  display-lg:
    fontFamily: Syne
    fontSize: 56px
    fontWeight: '800'
    lineHeight: 64px
    letterSpacing: -0.03em
  display-lg-mobile:
    fontFamily: Syne
    fontSize: 38px
    fontWeight: '800'
    lineHeight: 44px
    letterSpacing: -0.02em
  display-md:
    fontFamily: Syne
    fontSize: 40px
    fontWeight: '700'
    lineHeight: 48px
    letterSpacing: -0.02em
  display-md-mobile:
    fontFamily: Syne
    fontSize: 30px
    fontWeight: '700'
    lineHeight: 36px
    letterSpacing: -0.01em
  headline-lg:
    fontFamily: Syne
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.015em
  headline-md:
    fontFamily: Syne
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Newsreader
    fontSize: 20px
    fontWeight: '500'
    lineHeight: 28px
  body-lg:
    fontFamily: Newsreader
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Newsreader
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Newsreader
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: Space Mono
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
    letterSpacing: 0.08em
  label-sm:
    fontFamily: Space Mono
    fontSize: 10px
    fontWeight: '400'
    lineHeight: 14px
    letterSpacing: 0.12em
spacing:
  gutter: 1.5rem
  gutter-mobile: 1rem
  margin: 3rem
  margin-mobile: 1.25rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.75rem
  space-xl: 3rem
---

## Brand & Style

This design system targets patrons, architects, and technologists who demand computational rigor wrapped in monastic, material luxury. The visual atmosphere rejects the sterile white-and-electric-blue trope of modern artificial intelligence, replacing it with an earthen, grounded brutalism. It evokes the stillness of an obsidian megalith hidden within an ancient primeval forest: disciplined, architectural, dense, and permanent.

The aesthetic philosophy fuses **Quiet Brutalism** with **Atmospheric Luxury**:
- **Monolithic Geometry:** Interfaces are built from deliberate planar volumes and heavy structural borders rather than ephemeral, weightless sheets.
- **Organic Gravity:** Color and spatial composition borrow from wet stone, deep forest canopies, and oxidized metallic alloys.
- **Editorial Authority:** Bold display titling juxtaposed with utilitarian technical micro-copy creates an unhurried, scholarly elegance.
- **Zero Digital Glitz:** Absolute ban on neon accents, high-frequency lens flares, cyan glows, or synthetic gradients. Luminosity comes solely through soft ivory parchment and antique bronze brushing against moss-blackened stone.

## Colors

The palette establishes an introspective, low-key luminance model built from deep forest silicates and warm historic metals.

### Palette Architecture
- **Canvas & Obsidian Baselines:** 
  - Void Canvas: `#0f1715` (deep obsidian pine)
  - Surface Mid: `#14211d` (submerged basalt jade)
  - Surface Raised: `#1b2e28` (elevated moss shale)
- **Primary Accent (Antique Bronze):** `#bfa16b` serves as the primary focal point, representing brushed warm metal and refined architectural hardware.
- **Secondary Accent (Rich Sage):** `#3b5a4d` anchors technical badges, structural grid guides, and quiet status indicators.
- **Tertiary Accent (Muted Ochre):** `#9e824c` provides deeper metallic framing, selected states, and warm linear demarcation.
- **High-Contrast Value (Soft Parchment):** `#e8ede9` is reserved for authoritative typography, focal metrics, and high-priority reads, preventing optical fatigue while maintaining strong legibility.

### Usage Directives
- Surfaces never use pure pitch black (`#000000`); every dark tone carries a cold pine-green and peat undertone.
- Interactive states shift toward warmer bronze or deeper jade values—never saturation bursts or high-chroma glows.

## Typography

Typography establishes an intentional tension between monumental structural forms and historical, literary depth:

- **Syne (Display & Headlines):** Used for architectural declarations and monolithic focal titles. Its geometric, heavy-chiseled glyphs set an avant-garde brutalist tone.
- **Newsreader (Body & Prose):** Replaces the expected utilitarian sans with a warm, intellectual serif. It evokes foundational texts, archival research, and editorial gravitas within complex AI interfaces.
- **Space Mono (Metadata & System Interfaces):** Applied strictly to computational markers, timestamps, coordinates, status tokens, and tabular readings. Always uppercase with generous tracking.

## Layout & Spacing

The spatial model enforces rigid, proportional discipline inspired by brutalist architecture and classical grid construction.

- **Canvas Architecture:** Layouts adhere to a 12-column grid on desktop displays with explicit, structural columns. Elements align firmly to horizontal and vertical datum lines.
- **Margins & Gutters:** Desktop experiences demand generous outer gutters (`margin: 3rem`) to frame interfaces like bespoke printed editions. Mobile transitions down to compact boundaries (`margin-mobile: 1.25rem`) without breaking alignment.
- **Rhythm & Density:** Layout elements avoid arbitrary padding. Instead, internal spacing uses the deliberate stepped scale (`space-xs` through `space-xl`) to establish dense data groupings bounded by wide, quiet zones.

## Elevation & Depth

Visual hierarchy does not rely on faux elevation drops, floaty shadows, or blurred transparency layers. Instead, depth is conveyed through **monolithic planar strata and hairline mineral boundaries**:

- **Tonal Stepping:** Surfaces elevate strictly by shifting baseline color from `#0f1715` (deep canvas) to `#14211d` (mid layer), up to `#1b2e28` (active interactive planes).
- **Hairline Framing:** In place of drop shadows, separation is created using 1px borders colored with muted bronze (`rgba(191, 161, 107, 0.2)`) or deep moss green (`rgba(59, 90, 77, 0.35)`).
- **Atmospheric Recedence:** Inactive or background panes exhibit lower contrast and darker green-tinted tones, while focused workspaces rise to the fore with crisp parchment borders (`#e8ede9` at low opacities).
- **No Diffusion Shadows:** Diffuse, colored glow shadows are entirely omitted. Where shadow is structurally critical for overlays, use a crisp, zero-blur directional offset shadow: `4px 4px 0px rgba(7, 11, 10, 0.85)`.

## Shapes

Shape rules strictly enforce **Level 0 (Sharp)** corner geometries across all modules, inputs, containers, and dialogs.

- Every corner is cut at precise 90-degree right angles (`border-radius: 0px`).
- No pills, rounded buttons, or squirkled corners are permitted anywhere in the system.
- Structural elements project stone-masonry permanence: razor-sharp corners highlight the deliberate editorial brutality of the layout and reinforce the computational authority of the product.

## Components

### Buttons
- **Primary:** Sharp rectangular container filled with Antique Bronze (`#bfa16b`), text in Void Obsidian (`#0f1715`) using Space Mono uppercase. Hover shifts to Muted Ochre (`#9e824c`) with zero movement or scale transforms.
- **Secondary / Ghost:** Transparent background enclosed by a 1px border in Rich Sage (`#3b5a4d`), text in Soft Parchment (`#e8ede9`). Hover triggers an internal fill of `#1b2e28` with border transition to `#bfa16b`.
- **System Padding:** Strict vertical padding (`space-sm`) and generous horizontal framing (`space-lg`).

### Input Fields & Controls
- **Text Inputs:** Sharp containers framed in 1px `#1b2e28` with background `#14211d`. Active focus yields an immediate 1px border of `#bfa16b` with no glow rings. Typography is set in Space Mono for values, Newsreader for placeholder hints.
- **Checkboxes & Radios:** Rigid square boxes (16px x 16px) bounded by 1px `#3b5a4d`. Selected states fill the center with an inner solid square of `#bfa16b`. No circles; radio buttons remain square with a centered inner diamond mark.

### Chips & Badges
- Compact rectangular chips with zero border-radius.
- Built from a solid `#14211d` base bordered by 1px `#3b5a4d`.
- Metadata labels set in `label-sm` Space Mono, text color Soft Parchment (`#e8ede9`), prefixed with a bronze dot indicator (`#bfa16b`).

### Cards & Structural Modules
- Modular containers rendered in `#14211d` with 1px structural outer borders (`rgba(191, 161, 107, 0.15)`).
- Headers separated from content blocks by a continuous 1px horizontal rule across the entire card width.
- Padded with `space-lg` internally, enforcing strict alignment against the 12-column grid.

### Lists & Data Panes
- Dividers between table rows or list items use 1px solid lines tinted in `#1b2e28`.
- Alternating row states are discouraged; instead, hover triggers a flat plane highlight of `#1b2e28` across the whole line segment.
- Key figures and metrics utilize Syne bold figures, flanked by Space Mono labels.