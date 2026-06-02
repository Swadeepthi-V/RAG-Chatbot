---
name: Deep Space Portfolio
colors:
  surface: '#131314'
  surface-dim: '#131314'
  surface-bright: '#3a393a'
  surface-container-lowest: '#0e0e0f'
  surface-container-low: '#1c1b1c'
  surface-container: '#201f20'
  surface-container-high: '#2a2a2a'
  surface-container-highest: '#353435'
  on-surface: '#e5e2e2'
  on-surface-variant: '#c7c6cc'
  inverse-surface: '#e5e2e2'
  inverse-on-surface: '#313031'
  outline: '#909096'
  outline-variant: '#46464b'
  surface-tint: '#c4c6d1'
  primary: '#c4c6d1'
  on-primary: '#2d3039'
  primary-container: '#0f121a'
  on-primary-container: '#7b7d87'
  inverse-primary: '#5b5e68'
  secondary: '#c3c6d5'
  on-secondary: '#2c303c'
  secondary-container: '#434653'
  on-secondary-container: '#b1b4c3'
  tertiary: '#d6c3b3'
  on-tertiary: '#3a2e23'
  tertiary-container: '#191007'
  on-tertiary-container: '#8a7a6d'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#e0e2ee'
  primary-fixed-dim: '#c4c6d1'
  on-primary-fixed: '#181b24'
  on-primary-fixed-variant: '#444650'
  secondary-fixed: '#dfe2f1'
  secondary-fixed-dim: '#c3c6d5'
  on-secondary-fixed: '#171b26'
  on-secondary-fixed-variant: '#434653'
  tertiary-fixed: '#f3dfcf'
  tertiary-fixed-dim: '#d6c3b3'
  on-tertiary-fixed: '#241a10'
  on-tertiary-fixed-variant: '#514439'
  background: '#131314'
  on-background: '#e5e2e2'
  surface-variant: '#353435'
typography:
  headline-xl:
    fontFamily: Outfit
    fontSize: 40px
    fontWeight: '700'
    lineHeight: 48px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Outfit
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Outfit
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
  headline-md:
    fontFamily: Outfit
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.05em
  label-sm:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 14px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 40px
  gutter: 20px
  margin-mobile: 16px
  margin-desktop: 64px
---

## Brand & Style
The design system is engineered for a premium, high-performance investment experience. It targets a modern demographic that values clarity, speed, and sophistication. The personality is "Quiet Confidence"—avoiding unnecessary visual noise to focus on financial growth and data accuracy.

The aesthetic follows a **Modern Corporate** approach with **Glassmorphic** accents. It utilizes a high-contrast dark theme to reduce eye strain during deep-focus sessions. The interface relies on deep layering and vibrant mint accents to create a sense of technological advancement and financial "health."

## Colors
The palette is rooted in "Deep Space" (#0F121A), providing a bottomless foundation that makes financial data pop. 

- **Primary/Background:** Used for the lowest level of the application shell.
- **Secondary/Surface:** Used for cards, navigation bars, and content containers to create depth.
- **Accent (Vibrant Mint):** Reserved strictly for primary actions, success states, and growth indicators.
- **Typography:** A strict hierarchy of white-to-slate ensures that headings command attention while metadata remains unobtrusive.

## Typography
This design system pairs **Outfit** for headings to provide a modern, geometric flair with **Inter** for body text to ensure maximum legibility of complex financial data.

Headlines should use tight letter spacing to maintain a "premium" feel. Labels for data points (e.g., "Market Cap," "P/E Ratio") use `label-md` with uppercase styling to differentiate them from interactive body text.

## Layout & Spacing
The layout follows a **Fluid Grid** model with high-density spacing for data tables and generous whitespace for dashboard overviews. 

- **Desktop:** 12-column grid, 64px side margins, 20px gutters.
- **Mobile:** 4-column grid, 16px side margins, 12px gutters.
- **Logic:** Vertical rhythm is built on a 4px baseline. Components should generally use `md` (16px) padding for internal density.

## Elevation & Depth
Depth is communicated through **Tonal Layering** and **Glassmorphism**. Shadows are used sparingly to prevent the dark UI from feeling muddy.

- **Level 0 (Background):** #0F121A.
- **Level 1 (Cards/Surfaces):** #171B26. No shadow, but a 1px border of #262B3D to define edges.
- **Level 2 (Modals/Popovers):** #1C212E with an ambient shadow (0px 8px 24px rgba(0,0,0,0.5)).
- **Glassmorphic Overlays:** For high-priority alerts or "Quick Buy" sheets, use a background-blur (12px) with a semi-transparent Obsidian Gray (#171B26CC) and a subtle top-light inner stroke.

## Shapes
The shape language is "Soft-Modern." All primary containers (cards, graphs) use `rounded-lg` (16px) to soften the high-contrast color palette. Buttons use `rounded-xl` (24px) or full pill-shapes to invite interaction and distinguish them from static data containers.

## Components
- **Buttons:** Primary buttons are Solid Mint Green (#00D09C) with black text. Secondary buttons are outlined with a 1.5px Mint stroke. Text buttons are Pure White.
- **Input Fields:** Use the Obsidian Gray background with a subtle bottom border. On focus, the border transitions to Mint Green.
- **Chips/Badges:** For stock "Gainers," use a low-opacity Mint background (10%) with solid Mint text. For "Losers," use low-opacity Red.
- **Cards:** No external drop shadow; instead, use a 1px stroke (#262B3D) to separate from the background.
- **Lists:** Data rows should have a hover state that lightens the background to #1C212E, indicating interactivity.
- **Graphs:** Line charts should use a Mint Green stroke with a subtle gradient fill underneath, fading into the Obsidian Gray surface.

## Screens

![Stitch Screen Mockup](file:///c:/RAG%20chatbot/stitch_ui/screen.png)

### Chat Screen (`ChatScreen`)
The main conversation screen where users query scheme facts. It maintains a clean, immersive dark environment.

*   **Structure:**
    *   **Header Bar:** Fixed at the top. Uses `surface-container` background with a bottom border of `outline-variant` (1px). Displays the title "HDFC Mutual Fund FAQ Assistant" in `headline-md` (Outfit) and a subtitle status dot in Mint Green (`#00D09C`) with label "Facts-Only Agent".
    *   **Disclaimer Banner:** Immediately below the header. Styled with a low-opacity error-container background (`#93000a22`), a thin amber/red border (`error-container`), and text in `label-sm` (Inter) stating: *"Disclaimer: This bot provides facts-only grounded information. No advisory, predictions, or investment recommendations."*
    *   **Chat Message Stream:** Center scrollable area.
        *   *User Message Bubble:* Aligned to the right. Styled in `secondary-container` background with `rounded-xl` shape. Text uses `body-md` (Inter, color `on-surface`).
        *   *Assistant Message Bubble:* Aligned to the left. Styled in `surface-container-low` background with a subtle border of `outline-variant` (1px) and `rounded-xl`. Text uses `body-md` (Inter, color `on-surface`).
        *   *Citation pill:* Nested inside the assistant bubble at the bottom. Styled as a solid capsule badge using a low-opacity primary-container background (`#00D09C15`) with a solid Mint Green border and text `[Source Link]` (Inter `label-sm`) linking to the grounded HDFC page.
    *   **Suggested Prompts Area:** A horizontal scrolling tray of suggested query chips above the input bar. Chips are styled with `surface-container-high` background, a 1px border of `outline-variant`, and `rounded-full` (pill shape). Text uses `body-sm` (Inter, color `on-primary-container`).
    *   **Input Area:** Fixed at the bottom. Uses a capsule shape (`rounded-full`) containing a text input area with `surface-container-highest` background and a circular send button in solid Mint Green (`#00D09C`) containing an arrow icon. Appends a micro footer below the input in `label-sm` saying *"Last updated from sources: 02-Jun-2026"*.

### Factsheet Redirect Overlay (`FactsheetScreen`)
An alternative viewport shown when a user asks comparative performance or returns queries, bypassing semantic generation to prevent hallucinated predictions.

*   **Structure:**
    *   **Header:** Centered title "HDFC Mutual Fund Factsheets" in `headline-lg` (Outfit) with a descriptive body subtitle in `body-sm` directing users to raw official disclosures.
    *   **Link Cards Grid:** A 2-column grid of mutual fund category cards. Each card uses `surface-container-low` background, a thin border (`outline-variant`), and `rounded-lg` padding. The cards list categories like "HDFC Small Cap Fund", "HDFC Mid-Cap Opportunities Fund", each with a high-contrast chevron icon linking to the official URL.
