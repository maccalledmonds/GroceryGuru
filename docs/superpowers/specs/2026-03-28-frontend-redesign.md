# GroceryGuru Frontend Redesign

**Date:** 2026-03-28
**Status:** Approved

---

## Overview

A full visual and UX redesign of the GroceryGuru frontend. The goal is a sharp, minimal interface that feels professionally designed — not cookie-cutter or AI-generated. The design uses a single amber accent color, structural left-border details on cards, and a sticky top-bar input layout that gives maximum space to recipe results.

---

## Design System

### App Name
**GroceryGuru** — replaces "PantryPal" everywhere in the UI (header, footer, page title, meta tags).

### Color Palette

| Token | Value | Usage |
|---|---|---|
| `--page-bg` | `#FAF9F6` | Page background (warm white, not pure white) |
| `--surface` | `#FFFFFF` | Cards, nav, popover |
| `--text-primary` | `#1C1917` | Headings, labels, active states |
| `--text-secondary` | `#57534E` | Body text, instruction steps |
| `--text-muted` | `#A8A29E` | Meta, placeholders, counts |
| `--border` | `rgba(0,0,0,0.07)` | Card borders, dividers |
| `--border-interactive` | `rgba(0,0,0,0.12)` | Buttons, inputs, pills |
| `--accent` | `#D97706` | Find Recipes button, Options button (active), slider thumb/fill, Cook Now card border, amber popover top-border |
| `--accent-hover` | `#B45309` | Accent hover state |
| `--hover-bg` | `rgba(0,0,0,0.04)` | List item hover, chip hover |

**Color discipline:** Amber (`#D97706`) appears on exactly five elements: the Find Recipes button, the Options button border when open, the Cook Now card left-border, the popover top-border, and the results slider. Nowhere else. Active/selected states (filter pills, spice chips, serving size) use `#1C1917` black fill — not amber.

### Typography

- **Font:** Inter (already loaded), with `-webkit-font-smoothing: antialiased` globally
- **Letter-spacing:** `-0.02em` on all headings and card titles; `0.08em` on all uppercase labels
- **Font-weight:** `700` for logo/display, `600` for headings and section titles, `500` for UI labels and buttons, `400` for body and meta text
- **Body text:** Always `font-weight: 400` — never `500` for prose
- **Uppercase labels:** Always `11px`, `font-weight: 600`, `letter-spacing: 0.08em`, `text-transform: uppercase`

### Spacing

- Base unit: 4px
- Component internal padding: `16px` (sm), `20px` (md), `24px` (lg)
- Gap between components: `14px` (card grid), `28–36px` (section gaps)

### Border Radius

- Tags/chips: `5px`
- Buttons, pills, badges: `5–7px`
- Cards: `0 12px 12px 0` (flat left edge where accent border sits, rounded right)
- Popover: no radius (full-width)
- Serving toggle: `8px` outer container

### Shadows

- Cards: **no shadow** — border only (`1px solid rgba(0,0,0,0.07)`)
- Popover: `0 6px 20px rgba(0,0,0,0.09), 0 1px 4px rgba(0,0,0,0.05)`
- Nav: **no shadow** — `border-bottom: 1px solid rgba(0,0,0,0.07)` only

### Transitions

Always specify exact properties — never `transition-all`:
- Hover color/background: `150ms ease`
- Button press: `transform 80ms ease-in`
- Slider thumb scale: `120ms ease`

---

## Layout

### Top Navigation Bar (sticky)

Height: `64px` (tablet: `56px`, mobile: auto-height with wrapping)

Structure (left to right):
1. **Logo** — "GroceryGuru", `17px`, `font-weight: 700`, `letter-spacing: -0.035em`
2. **Vertical divider** — `1px`, `rgba(0,0,0,0.1)`, `20px` tall
3. **Ingredient input area** (flex-1) — tag chips + placeholder text, clickable to focus the hidden input
4. **Options button** — outlined, toggles the popover
5. **Find Recipes button** — amber fill, primary CTA, disabled until at least one ingredient is added

The nav is white with a bottom border. No dark background. No shadow.

### Options Popover

Opens directly below the nav bar, full-width. Closed by clicking Options again or clicking outside.

Contains three sections displayed in a horizontal flex row (wraps on smaller screens):

1. **Dietary filters** — pill toggles: Vegetarian, Vegan, Gluten-free, High-protein. Active = black fill.
2. **Pantry Spices** — pill toggles for all spice options (replaces the sidebar checkbox list). Active = black fill. Chips wrap naturally.
3. **Number of Results** — labeled slider, `min=1 max=20`, amber thumb and track fill, shows current value as a large number above the slider.

Top of the popover has a `3px solid #D97706` border to visually anchor it to the Options button. Box shadow for elevation.

On mobile: popover becomes a bottom sheet (slides up from bottom of screen).

### Main Content Area

`max-width: 1100px`, centered, `padding: 36px 32px` (tablet: `24px`, mobile: `16px`).

**Serving size control** — placed at the top of the results area (not in the input form). Three buttons: 1×, 2×, 4×. Active = black fill. Applies quantity scaling to displayed ingredient amounts.

**Cook Now section:**
- Section header: 4px amber vertical bar + "Cook Now" title + recipe count
- Card grid (see below)

**Almost There section:**
- Section header: 4px gray vertical bar + "Almost There" title + recipe count
- Card grid (see below)

**Idle state** (no search yet):
- Centered, `padding: 96px 40px`
- Thin-stroke document icon, `48px`, `opacity: 0.18`
- Heading: "Your pantry, your recipes" — `18px`, `font-weight: 600`, `letter-spacing: -0.025em`
- Subtext: "Add what's in your fridge and we'll find what's for dinner." — `14px`, muted

**Empty state** (search returned no results):
- Same centered layout as idle state
- Heading: "No recipes matched"
- Subtext: "Try removing a dietary filter or adding more ingredients."

**Error state:**
- Inline banner below the nav, amber-tinted background, no full-page takeover

### Recipe Cards

Cards sit in a responsive grid:
- Desktop (≥1024px): `repeat(auto-fill, minmax(320px, 1fr))` — typically 3 columns
- Tablet (≥768px): 2 columns
- Mobile (<640px): 1 column

**Cook Now card:**
- `border-left: 4px solid #D97706`
- `border-radius: 0 12px 12px 0`
- `border: 1px solid rgba(0,0,0,0.07)` (left overridden by amber)
- Hover: right border darkens to `rgba(0,0,0,0.13)`

**Almost There card:**
- `border-left: 4px solid rgba(0,0,0,0.15)`
- Same structure, gray accent instead of amber

**Card internals (top to bottom):**
1. **Card header row:** title (left) + match % badge (right)
   - Title: `15px`, `font-weight: 600`, `letter-spacing: -0.02em`
   - Meta: "Serves N · N missing" — `12px`, muted
   - Match badge: strong (≥75%) = black fill; weak (<75%) = outlined gray
2. **Ingredient chips:** small `rgba(0,0,0,0.04)` chips for present ingredients; dashed-border chips for missing ones
3. **Missing note:** "Need: **ingredient, ingredient**" — `12px`, with bold ingredient names
4. **Instructions toggle:** text button, reveals/hides step list. Default: collapsed.
5. **Instructions (expanded):** numbered list, `line-height: 1.75` (generous for cooking context). Ingredient names and time references **bolded** within step prose.

### Loading State

Skeleton cards instead of a spinner. Each skeleton matches the card proportions exactly:
- Shimmer animation: warm-tinted gradient (`#F0EDE8` → `#E6E2DB`), `1.5s ease-in-out infinite`
- Show skeletons only after 300ms delay (prevents flash for fast responses)
- Number of skeletons = current results count setting

---

## Ingredient Input

The ingredient input lives inside the nav bar. It is a visually invisible `<input>` that the user types into. As ingredients are added they appear as chips.

**Chips:**
- `border: 2px solid #1C1917` — black-outlined, `border-radius: 5px`
- Remove button (×) on each chip, `opacity: 0.35`, increases on hover
- Enter or comma commits the current draft as a chip
- Backspace on empty draft removes the last chip

**"Add essential spices" shortcut:** Removed from the main form. Essential spices are available via the Options popover Pantry Spices section.

---

## Responsive Breakpoints

| Breakpoint | Changes |
|---|---|
| `≥1024px` | Full layout: 3-col card grid, `64px` nav, `36px 32px` main padding |
| `768px–1023px` | 2-col card grid, `56px` nav, `24px` padding, font sizes step down 1–2px |
| `<768px` | Options popover → bottom sheet; 1-col card grid; nav wraps to 2 rows (logo row + input row); `16px` padding |
| `<480px` | Full-width chips, larger tap targets (`min-height: 44px` on all interactive elements) |

---

## Removed Elements

- **Sidebar** — replaced entirely by the Options popover
- **Spice checkbox list** — replaced by pill toggles in the popover
- **TopK slider in sidebar** — moved to popover as labeled range slider
- **"Add essential spices" button** — removed; spices are in the popover
- **Serving size in the input form** — moved to top of results area
- **Score badge color system** (green/yellow/gray) — replaced by black fill (strong) vs. outlined (weak) two-state system
- **`shadow-md` / `shadow-lg` on cards** — replaced by border-only treatment

---

## Files to Change

| File | Changes |
|---|---|
| `frontend/src/App.tsx` | New layout structure, name change, remove sidebar, serving size placement, idle/empty states |
| `frontend/src/index.css` | Global antialiasing, warm background, custom scrollbar, skeleton animation |
| `frontend/tailwind.config.ts` | Update brand color to amber `#D97706`, add zinc-based gray overrides, custom shadow tokens |
| `frontend/src/components/FilterPanel.tsx` | **Delete or repurpose** — functionality moves into new `OptionsPopover` component |
| `frontend/src/components/IngredientInput.tsx` | Restyle chips (black outline, square-ish radius); fits inside nav bar |
| `frontend/src/components/RecipeCard.tsx` | New card layout, match badge logic, dashed missing chips, bold ingredients in instructions |
| `frontend/index.html` | Update `<title>` to GroceryGuru |

**New components to create:**
- `frontend/src/components/OptionsPopover.tsx` — popover with dietary filters, spice pills, results slider
- `frontend/src/components/SkeletonCard.tsx` — extract from App.tsx with warm shimmer

---

## Spec Self-Review

- No TBDs or placeholders remaining
- Color values are specific hex/rgba — no vague references
- Responsive breakpoints are explicit
- Every removed element is listed
- Every new component is named
- No contradictions between sections
