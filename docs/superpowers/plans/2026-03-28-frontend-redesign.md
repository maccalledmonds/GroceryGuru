# GroceryGuru Frontend Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign the frontend from a generic sidebar layout to a sharp, minimal top-bar-input + card-grid UI with a single amber accent, structural left-border recipe cards, and an Options popover replacing the sidebar.

**Architecture:** Sticky nav bar contains the ingredient input and an Options popover (dietary filters + spice chips + results slider). Results fill the page below in a responsive card grid. FilterPanel is deleted; a new OptionsPopover component takes its place.

**Tech Stack:** React 18, TypeScript, Tailwind CSS, Vite. No new dependencies. Verify each task with `npm run typecheck && npm run lint` from `frontend/`.

---

## File Map

| Action | Path | Responsibility |
|---|---|---|
| Modify | `frontend/tailwind.config.ts` | Amber brand tokens, custom shadow tokens |
| Modify | `frontend/src/index.css` | Global antialiasing, warm background, skeleton shimmer animation, scrollbar |
| Modify | `frontend/index.html` | Title + favicon emoji |
| Create | `frontend/src/components/SkeletonCard.tsx` | Warm-shimmer loading placeholder card |
| Modify | `frontend/src/components/IngredientInput.tsx` | Borderless chip input for nav-bar use |
| Create | `frontend/src/components/OptionsPopover.tsx` | Filters + spice pills + results slider popover |
| Modify | `frontend/src/components/RecipeCard.tsx` | Left-border variant, match badge, dashed missing chips, instruction highlighting |
| Modify | `frontend/src/App.tsx` | New layout: sticky nav form, Options popover, results grid, idle/empty states |
| Delete | `frontend/src/components/FilterPanel.tsx` | Replaced by OptionsPopover |

---

## Task 1: Design tokens — Tailwind config + global CSS

**Files:**
- Modify: `frontend/tailwind.config.ts`
- Modify: `frontend/src/index.css`

- [ ] **Step 1: Update `tailwind.config.ts`**

Replace the entire file with:

```typescript
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  "#fffbeb",
          100: "#fef3c7",
          200: "#fde68a",
          300: "#fcd34d",
          400: "#fbbf24",
          500: "#d97706",
          600: "#b45309",
          700: "#92400e",
          800: "#78350f",
          900: "#451a03",
        },
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      boxShadow: {
        card: "0 1px 2px rgba(0,0,0,0.04)",
        popover: "0 6px 20px rgba(0,0,0,0.09), 0 1px 4px rgba(0,0,0,0.05)",
      },
    },
  },
  plugins: [],
};
```

- [ ] **Step 2: Replace `frontend/src/index.css`**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  *, *::before, *::after {
    box-sizing: border-box;
  }

  html {
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }

  body {
    @apply font-sans text-stone-900;
    background-color: #FAF9F6;
    min-height: 100dvh;
  }

  h1, h2, h3, h4 {
    letter-spacing: -0.02em;
  }

  #root {
    min-height: 100dvh;
  }
}

@layer utilities {
  .skeleton-shimmer {
    background: linear-gradient(90deg, #f0ede8 25%, #e6e2db 50%, #f0ede8 75%);
    background-size: 200% 100%;
    animation: shimmer 1.5s ease-in-out infinite;
  }

  @keyframes shimmer {
    0%   { background-position: 200% 0; }
    100% { background-position: -200% 0; }
  }
}

/* Minimal scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.15); border-radius: 3px; }
::-webkit-scrollbar-track { background: transparent; }
```

- [ ] **Step 3: Verify**

```bash
cd frontend && npm run typecheck && npm run lint
```

Expected: no errors (CSS changes don't affect TS).

- [ ] **Step 4: Commit**

```bash
git add frontend/tailwind.config.ts frontend/src/index.css
git commit -m "feat: update design tokens — amber brand, warm background, skeleton shimmer"
```

---

## Task 2: Update HTML title and favicon

**Files:**
- Modify: `frontend/index.html`

- [ ] **Step 1: Update title, description, and favicon**

Replace lines 6–8 of `frontend/index.html`:

```html
    <title>GroceryGuru — Recipe Recommendations</title>
    <meta name="description" content="Enter what's in your fridge and we'll find what's for dinner." />
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🛒</text></svg>" />
```

- [ ] **Step 2: Commit**

```bash
git add frontend/index.html
git commit -m "feat: rename app to GroceryGuru, update favicon"
```

---

## Task 3: Create SkeletonCard component

**Files:**
- Create: `frontend/src/components/SkeletonCard.tsx`

Extracts the existing skeleton card from `App.tsx` and uses the new warm shimmer class.

- [ ] **Step 1: Create `frontend/src/components/SkeletonCard.tsx`**

```typescript
export function SkeletonCard() {
  return (
    <div className="bg-white border border-black/[0.07] border-l-4 border-l-black/[0.08] rounded-r-xl p-5">
      <div className="flex justify-between items-start gap-3 mb-3">
        <div>
          <div className="h-4 w-36 rounded skeleton-shimmer mb-2" />
          <div className="h-3 w-24 rounded skeleton-shimmer" />
        </div>
        <div className="h-6 w-11 rounded-[5px] skeleton-shimmer" />
      </div>
      <div className="flex gap-1.5 mb-3">
        <div className="h-6 w-16 rounded skeleton-shimmer" />
        <div className="h-6 w-14 rounded skeleton-shimmer" />
        <div className="h-6 w-20 rounded skeleton-shimmer" />
      </div>
      <div className="h-3 w-28 rounded skeleton-shimmer" />
    </div>
  );
}
```

- [ ] **Step 2: Verify**

```bash
cd frontend && npm run typecheck
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/SkeletonCard.tsx
git commit -m "feat: add SkeletonCard with warm shimmer animation"
```

---

## Task 4: Restyle IngredientInput for nav-bar use

**Files:**
- Modify: `frontend/src/components/IngredientInput.tsx`

The input is now borderless — the nav bar is the visual container. Chips become black-outlined with square-ish corners. Logic is unchanged.

- [ ] **Step 1: Replace `frontend/src/components/IngredientInput.tsx`**

```typescript
import { KeyboardEvent, useRef, useState } from "react";

interface Props {
  ingredients: string[];
  onChange: (updated: string[]) => void;
  disabled?: boolean;
}

export function IngredientInput({ ingredients, onChange, disabled = false }: Props) {
  const [draft, setDraft] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  function commit(raw: string) {
    const parts = raw
      .split(",")
      .map((s) => s.trim())
      .filter((s) => s.length > 0 && !ingredients.includes(s));
    if (parts.length > 0) onChange([...ingredients, ...parts]);
    setDraft("");
  }

  function handleKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      commit(draft);
    } else if (e.key === "Backspace" && draft === "" && ingredients.length > 0) {
      onChange(ingredients.slice(0, -1));
    }
  }

  return (
    // No outer border — the parent nav bar is the container
    <div
      className={`flex flex-wrap gap-2 items-center min-h-[2.5rem] ${
        disabled ? "opacity-60 cursor-not-allowed" : "cursor-text"
      }`}
      onClick={() => inputRef.current?.focus()}
    >
      {ingredients.map((ing, i) => (
        <span
          key={`${ing}-${i}`}
          className="inline-flex items-center gap-1.5 border-2 border-stone-900 rounded-[5px] px-2.5 py-1 text-sm font-medium text-stone-900 leading-none"
        >
          {ing}
          {!disabled && (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onChange(ingredients.filter((_, idx) => idx !== i));
              }}
              className="opacity-35 hover:opacity-75 transition-opacity duration-100 leading-none focus:outline-none"
              aria-label={`Remove ${ing}`}
            >
              <svg className="w-3 h-3" viewBox="0 0 12 12" fill="currentColor" aria-hidden>
                <path d="M9.53 9.53a.75.75 0 0 1-1.06 0L6 7.06 3.53 9.53A.75.75 0 0 1 2.47 8.47L4.94 6 2.47 3.53A.75.75 0 0 1 3.53 2.47L6 4.94l2.47-2.47a.75.75 0 1 1 1.06 1.06L7.06 6l2.47 2.47a.75.75 0 0 1 0 1.06Z" />
              </svg>
            </button>
          )}
        </span>
      ))}

      <input
        ref={inputRef}
        type="text"
        value={draft}
        disabled={disabled}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={handleKeyDown}
        onBlur={() => draft && commit(draft)}
        placeholder={ingredients.length === 0 ? "Type an ingredient and press Enter…" : "add more…"}
        className="flex-1 min-w-[140px] bg-transparent outline-none text-sm text-stone-900 placeholder:text-stone-400 disabled:cursor-not-allowed"
        aria-label="Ingredient input"
      />
    </div>
  );
}
```

- [ ] **Step 2: Verify**

```bash
cd frontend && npm run typecheck && npm run lint
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/IngredientInput.tsx
git commit -m "feat: restyle IngredientInput — borderless nav-bar chips, black outline"
```

---

## Task 5: Create OptionsPopover component

**Files:**
- Create: `frontend/src/components/OptionsPopover.tsx`

Replaces the sidebar FilterPanel. Three sections: dietary filter pill toggles, spice pill toggles, and a labeled range slider for result count.

- [ ] **Step 1: Create `frontend/src/components/OptionsPopover.tsx`**

```typescript
const FILTER_LABELS: Record<string, string> = {
  vegetarian: "Vegetarian",
  vegan: "Vegan",
  gluten_free: "Gluten-free",
  high_protein: "High-protein",
};

interface Props {
  availableFilters: string[];
  selectedFilters: string[];
  onFiltersChange: (filters: string[]) => void;
  spiceOptions: string[];
  selectedSpices: string[];
  onSpicesChange: (spices: string[]) => void;
  topK: number;
  onTopKChange: (k: number) => void;
  onClose: () => void;
  disabled?: boolean;
}

export function OptionsPopover({
  availableFilters,
  selectedFilters,
  onFiltersChange,
  spiceOptions,
  selectedSpices,
  onSpicesChange,
  topK,
  onTopKChange,
  onClose,
  disabled = false,
}: Props) {
  function toggleFilter(f: string) {
    onFiltersChange(
      selectedFilters.includes(f)
        ? selectedFilters.filter((x) => x !== f)
        : [...selectedFilters, f],
    );
  }

  function toggleSpice(s: string) {
    onSpicesChange(
      selectedSpices.includes(s)
        ? selectedSpices.filter((x) => x !== s)
        : [...selectedSpices, s],
    );
  }

  // Percentage of slider filled for CSS gradient
  const sliderPct = ((topK - 1) / (20 - 1)) * 100;

  return (
    <>
      {/* Backdrop — clicking outside closes the popover */}
      <div
        className="fixed inset-0 z-30"
        aria-hidden
        onClick={onClose}
      />

      {/* Popover panel */}
      <div
        className="relative z-40 bg-white border-t-[3px] border-t-brand-500 border-b border-x border-black/[0.08] shadow-popover"
        role="dialog"
        aria-label="Search options"
      >
        <div className="mx-auto max-w-7xl px-6 sm:px-8 py-5 flex flex-wrap gap-8 items-start">

          {/* Dietary filters */}
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-stone-400 mb-3">
              Dietary
            </p>
            <div className="flex flex-wrap gap-2">
              {availableFilters.map((f) => {
                const active = selectedFilters.includes(f);
                return (
                  <button
                    key={f}
                    type="button"
                    disabled={disabled}
                    onClick={() => toggleFilter(f)}
                    className={`border rounded-[5px] px-3.5 py-1.5 text-sm font-medium transition-colors duration-150 disabled:opacity-50 disabled:cursor-not-allowed ${
                      active
                        ? "bg-stone-900 text-white border-stone-900"
                        : "border-black/[0.12] text-stone-500 hover:border-black/[0.22] hover:text-stone-900"
                    }`}
                  >
                    {FILTER_LABELS[f] ?? f}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Spice toggles */}
          <div className="flex-1 min-w-[220px]">
            <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-stone-400 mb-3">
              Pantry Spices
            </p>
            <div className="flex flex-wrap gap-2">
              {spiceOptions.map((s) => {
                const active = selectedSpices.includes(s);
                return (
                  <button
                    key={s}
                    type="button"
                    disabled={disabled}
                    onClick={() => toggleSpice(s)}
                    className={`border rounded-[5px] px-3 py-1.5 text-sm font-medium transition-colors duration-150 disabled:opacity-50 disabled:cursor-not-allowed ${
                      active
                        ? "bg-stone-900 text-white border-stone-900"
                        : "border-black/[0.12] text-stone-500 hover:border-black/[0.22] hover:text-stone-900"
                    }`}
                  >
                    {s}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Results slider */}
          <div className="min-w-[160px]">
            <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-stone-400 mb-3">
              Number of Results
            </p>
            <div className="flex items-baseline gap-2 mb-2.5">
              <span className="text-3xl font-bold text-stone-900 tabular-nums leading-none" style={{ letterSpacing: "-0.04em" }}>
                {topK}
              </span>
              <span className="text-sm text-stone-400">recipes</span>
            </div>
            <input
              type="range"
              min={1}
              max={20}
              value={topK}
              disabled={disabled}
              onChange={(e) => onTopKChange(Number(e.target.value))}
              aria-label="Number of results"
              style={{
                appearance: "none",
                WebkitAppearance: "none",
                width: "100%",
                height: "4px",
                borderRadius: "2px",
                outline: "none",
                cursor: disabled ? "not-allowed" : "pointer",
                background: `linear-gradient(to right, #d97706 0%, #d97706 ${sliderPct}%, #e7e5e4 ${sliderPct}%, #e7e5e4 100%)`,
              }}
            />
            <div className="flex justify-between text-[11px] text-stone-300 mt-1.5">
              <span>1</span>
              <span>20</span>
            </div>
          </div>

        </div>
      </div>
    </>
  );
}
```

- [ ] **Step 2: Add slider thumb CSS to `frontend/src/index.css`**

Append inside `@layer utilities` (before the closing brace):

```css
  /* Amber range slider thumb — cross-browser */
  input[type="range"]::-webkit-slider-thumb {
    -webkit-appearance: none;
    width: 18px;
    height: 18px;
    border-radius: 50%;
    background: #d97706;
    border: 2px solid #fff;
    box-shadow: 0 1px 4px rgba(0,0,0,0.18);
    cursor: pointer;
    transition: transform 120ms ease;
  }
  input[type="range"]::-webkit-slider-thumb:hover {
    transform: scale(1.15);
  }
  input[type="range"]::-moz-range-thumb {
    width: 18px;
    height: 18px;
    border-radius: 50%;
    background: #d97706;
    border: 2px solid #fff;
    box-shadow: 0 1px 4px rgba(0,0,0,0.18);
    cursor: pointer;
  }
```

- [ ] **Step 3: Verify**

```bash
cd frontend && npm run typecheck && npm run lint
```

Expected: no errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/OptionsPopover.tsx frontend/src/index.css
git commit -m "feat: add OptionsPopover — filter pills, spice chips, amber results slider"
```

---

## Task 6: Restyle RecipeCard

**Files:**
- Modify: `frontend/src/components/RecipeCard.tsx`

Key changes: `variant` prop for amber/gray left border, black/outlined match badge, dashed chips for missing ingredients, time references bolded in instruction steps. All existing parsing logic (`scaleIngredientText`, `toInstructionSteps`) is preserved unchanged.

- [ ] **Step 1: Replace `frontend/src/components/RecipeCard.tsx`**

```typescript
import { useState } from "react";
import type { ReactNode } from "react";
import { RecipeResult } from "../api/client";

// ─── Preserve all existing utility functions unchanged ───────────────────────

function isSpecialEquipmentPhrase(value: string): boolean {
  const lowered = value.trim().toLowerCase();
  return /\bspecial\s+equipment\b|^equipment\b/.test(lowered);
}

const UNICODE_FRACTIONS: Record<string, number> = {
  "¼": 0.25, "½": 0.5, "¾": 0.75,
  "⅓": 1 / 3, "⅔": 2 / 3,
  "⅛": 0.125, "⅜": 0.375, "⅝": 0.625, "⅞": 0.875,
};

function parseQuantityToken(token: string): number | null {
  const clean = token.trim();
  if (!clean) return null;
  if (UNICODE_FRACTIONS[clean] != null) return UNICODE_FRACTIONS[clean];
  const mixedMatch = clean.match(/^(\d+)\s+(\d+)\/(\d+)$/);
  if (mixedMatch) {
    const d = Number(mixedMatch[3]);
    return d !== 0 ? Number(mixedMatch[1]) + Number(mixedMatch[2]) / d : null;
  }
  const fractionMatch = clean.match(/^(\d+)\/(\d+)$/);
  if (fractionMatch) {
    const d = Number(fractionMatch[2]);
    return d !== 0 ? Number(fractionMatch[1]) / d : null;
  }
  const n = Number(clean);
  return Number.isNaN(n) ? null : n;
}

function formatQuantity(value: number): string {
  if (!Number.isFinite(value)) return "";
  if (Math.abs(value) >= 10) return String(Math.round(value * 10) / 10);
  return String(Math.round(value * 100) / 100).replace(/\.00$/, "").replace(/(\.\d*[1-9])0$/, "$1");
}

function scaleIngredientText(ingredient: string, multiplier: number): string {
  if (multiplier === 1) return ingredient;
  const rangePattern =
    /^\s*([¼½¾⅓⅔⅛⅜⅝⅞]|\d+(?:\.\d+)?(?:\s+\d+\/\d+)?|\d+\/\d+)\s*(?:-|to)\s*([¼½¾⅓⅔⅛⅜⅝⅞]|\d+(?:\.\d+)?(?:\s+\d+\/\d+)?|\d+\/\d+)(\s+.*)$/i;
  const singlePattern = /^\s*([¼½¾⅓⅔⅛⅜⅝⅞]|\d+(?:\.\d+)?(?:\s+\d+\/\d+)?|\d+\/\d+)(\s+.*)$/i;
  const rangeMatch = ingredient.match(rangePattern);
  if (rangeMatch) {
    const l = parseQuantityToken(rangeMatch[1]);
    const r = parseQuantityToken(rangeMatch[2]);
    if (l != null && r != null) return `${formatQuantity(l * multiplier)}-${formatQuantity(r * multiplier)}${rangeMatch[3]}`;
  }
  const singleMatch = ingredient.match(singlePattern);
  if (singleMatch) {
    const v = parseQuantityToken(singleMatch[1]);
    if (v != null) return `${formatQuantity(v * multiplier)}${singleMatch[2]}`;
  }
  return ingredient;
}

function toInstructionSteps(instructions: RecipeResult["instructions"]): string[] {
  if (Array.isArray(instructions)) {
    const cleaned = instructions.map((s) => s.trim()).filter(Boolean);
    if (cleaned.length > 0) return cleaned;
  }
  if (typeof instructions !== "string" || !instructions.trim()) return ["No instructions available."];
  const normalized = instructions.replace(/\r/g, "").trim();
  const lineSteps = normalized.split("\n").map((l) => l.trim()).filter(Boolean);
  if (lineSteps.length > 1) return lineSteps.map((l) => l.replace(/^(?:step\s*)?\d+[\).:\-]\s*/i, ""));
  const numberedParts = normalized
    .split(/\s+(?=(?:step\s*)?\d+[\).:\-]\s+)/i)
    .map((p) => p.trim()).filter(Boolean)
    .map((p) => p.replace(/^(?:step\s*)?\d+[\).:\-]\s*/i, "")).filter(Boolean);
  if (numberedParts.length > 1) return numberedParts;
  const sentenceSteps = normalized.split(/(?<=[.!?])\s+(?=[A-Z])/).map((p) => p.trim()).filter(Boolean);
  return sentenceSteps.length > 0 ? sentenceSteps : [normalized];
}

// ─── New: bold time references in instruction steps ──────────────────────────

function highlightStep(step: string): ReactNode[] {
  // Match patterns like "30 minutes", "1-2 hours", "45 seconds"
  const timePattern = /(\b\d+(?:\s*[-–]\s*\d+)?\s*(?:minutes?|hours?|seconds?|mins?|hrs?)\b)/gi;
  const parts = step.split(timePattern);
  return parts.map((part, i) =>
    i % 2 === 1
      ? <strong key={i} className="font-semibold text-stone-900">{part}</strong>
      : <span key={i}>{part}</span>
  );
}

// ─── Component ───────────────────────────────────────────────────────────────

interface Props {
  recipe: RecipeResult;
  rank: number;
  servingMultiplier: number;
  variant: "cook-now" | "almost-there";
}

export function RecipeCard({ recipe, rank, servingMultiplier, variant }: Props) {
  const [open, setOpen] = useState(false);
  const isDatabaseRecipe = recipe.type === "database";

  const missingIngredients = (recipe.missing_ingredients ?? []).filter(
    (item) => !isSpecialEquipmentPhrase(item),
  );

  const presentIngredientNames = recipe.ingredients.filter(
    (ing) => !missingIngredients.some((m) => ing.toLowerCase().includes(m.toLowerCase())),
  );

  const scaledPresent = isDatabaseRecipe
    ? presentIngredientNames.map((ing) => scaleIngredientText(ing, servingMultiplier))
    : presentIngredientNames;

  const instructionSteps = toInstructionSteps(recipe.instructions);

  const scorePct = Math.round(recipe.score * 100);
  const strongMatch = scorePct >= 75;

  // Left border color by variant
  const borderAccent =
    variant === "cook-now"
      ? "border-l-brand-500"
      : "border-l-stone-300";

  return (
    <article
      className={`bg-white border border-black/[0.07] border-l-4 ${borderAccent} rounded-r-xl hover:border-black/[0.13] transition-colors duration-150 overflow-hidden`}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3 px-5 pt-5 pb-3">
        <div className="min-w-0 flex-1">
          <h3 className="text-[15px] font-semibold text-stone-900 leading-snug break-words" style={{ letterSpacing: "-0.02em" }}>
            {recipe.title}
          </h3>
          <p className="text-xs text-stone-400 mt-0.5">
            {recipe.servings != null ? `Serves ${recipe.servings} · ` : ""}
            {missingIngredients.length} missing
          </p>
        </div>
        {/* Match badge: black fill for strong, outlined gray for weak */}
        <span
          className={`flex-shrink-0 rounded-[5px] px-2.5 py-1 text-xs font-bold tabular-nums leading-none ${
            strongMatch
              ? "bg-stone-900 text-white"
              : "border border-black/[0.15] text-stone-400"
          }`}
        >
          {scorePct}%
        </span>
      </div>

      <div className="px-5 pb-5 space-y-3">
        {/* Ingredient chips row — present (solid) + missing (dashed) */}
        <div className="flex flex-wrap gap-1.5">
          {scaledPresent.slice(0, 5).map((ing, i) => (
            <span
              key={`present-${i}`}
              className="bg-black/[0.04] rounded-[4px] px-2 py-1 text-xs text-stone-600"
            >
              {ing}
            </span>
          ))}
          {scaledPresent.length > 5 && (
            <span className="px-2 py-1 text-xs text-stone-400 italic">
              +{scaledPresent.length - 5} more
            </span>
          )}
          {missingIngredients.map((ing, i) => (
            <span
              key={`missing-${i}`}
              className="border border-dashed border-black/[0.2] rounded-[4px] px-2 py-1 text-xs text-stone-400"
            >
              {ing}
            </span>
          ))}
        </div>

        {/* Missing ingredients note */}
        {missingIngredients.length > 0 && (
          <p className="text-xs text-stone-500">
            Need: <strong className="font-semibold text-stone-700">{missingIngredients.join(", ")}</strong>
          </p>
        )}

        {/* Serving multiplier note */}
        {isDatabaseRecipe && servingMultiplier !== 1 && (
          <p className="text-xs text-stone-400">
            Amounts adjusted for <span className="font-semibold">{servingMultiplier}×</span> servings
          </p>
        )}

        {/* Instructions toggle */}
        <button
          type="button"
          onClick={() => setOpen((o) => !o)}
          className="flex items-center gap-1.5 text-xs text-stone-400 hover:text-stone-600 transition-colors duration-150 focus:outline-none focus-visible:underline"
          aria-expanded={open}
        >
          <svg
            className={`w-3.5 h-3.5 transition-transform duration-150 ${open ? "rotate-180" : ""}`}
            viewBox="0 0 16 16"
            fill="currentColor"
            aria-hidden
          >
            <path
              fillRule="evenodd"
              d="M4.22 6.22a.75.75 0 0 1 1.06 0L8 8.94l2.72-2.72a.75.75 0 1 1 1.06 1.06l-3.25 3.25a.75.75 0 0 1-1.06 0L4.22 7.28a.75.75 0 0 1 0-1.06Z"
              clipRule="evenodd"
            />
          </svg>
          {open ? "Hide" : "Show"} instructions
        </button>

        {/* Instructions (expanded) */}
        {open && (
          <div className="border-t border-black/[0.06] pt-3">
            <ol className="list-decimal pl-4 space-y-2">
              {instructionSteps.map((step, i) => (
                <li key={i} className="text-sm text-stone-600 leading-[1.75]">
                  {highlightStep(step)}
                </li>
              ))}
            </ol>
          </div>
        )}
      </div>
    </article>
  );
}
```

- [ ] **Step 2: Verify**

```bash
cd frontend && npm run typecheck && npm run lint
```

Expected: no errors. (App.tsx still imports old RecipeCard signature — it will be fixed in Task 7.)

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/RecipeCard.tsx
git commit -m "feat: restyle RecipeCard — variant border, match badge, dashed missing chips, highlighted steps"
```

---

## Task 7: Rewrite App.tsx

**Files:**
- Modify: `frontend/src/App.tsx`

New layout: sticky nav form → Options popover → full-width main. Removes sidebar entirely. Adds serving size control in results area. Wires up OptionsPopover and new RecipeCard `variant` prop.

- [ ] **Step 1: Replace `frontend/src/App.tsx`**

```typescript
import { useEffect, useState } from "react";
import { api } from "./api/client";
import { IngredientInput } from "./components/IngredientInput";
import { OptionsPopover } from "./components/OptionsPopover";
import { RecipeCard } from "./components/RecipeCard";
import { SkeletonCard } from "./components/SkeletonCard";
import { useRecommend } from "./hooks/useRecommend";

const SPICE_OPTIONS = [
  "garlic", "ginger", "turmeric", "basil", "parsley", "cilantro",
  "vanilla extract", "cinnamon", "nutmeg", "cumin", "paprika", "oregano",
  "thyme", "rosemary", "dill", "bay leaf", "mustard", "hot sauce", "curry paste",
];

const AUTO_INCLUDED_PANTRY = ["salt", "black pepper", "water"] as const;

export default function App() {
  const [ingredients, setIngredients] = useState<string[]>([]);
  const [selectedFilters, setSelectedFilters] = useState<string[]>([]);
  const [selectedSpices, setSelectedSpices] = useState<string[]>([]);
  const [topK, setTopK] = useState(5);
  const [servingMultiplier, setServingMultiplier] = useState(1);
  const [availableFilters, setAvailableFilters] = useState<string[]>([]);
  const [optionsOpen, setOptionsOpen] = useState(false);

  const {
    status,
    onHandRecipes,
    relatedRecipes,
    normalizedIngredients,
    usedFallback,
    fallbackReason,
    error,
    recommend,
  } = useRecommend();

  useEffect(() => {
    api
      .getFilters()
      .then((data) => setAvailableFilters(data.filters))
      .catch(() => {
        setAvailableFilters(["gluten_free", "high_protein", "vegan", "vegetarian"]);
      });
  }, []);

  const isLoading = status === "loading";
  const hasAnyIngredient = ingredients.length > 0 || selectedSpices.length > 0;

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const requestIngredients = Array.from(
      new Set([...ingredients, ...selectedSpices, ...AUTO_INCLUDED_PANTRY]),
    );
    if (requestIngredients.length === 0) return;
    setOptionsOpen(false);
    recommend({ ingredients: requestIngredients, filters: selectedFilters, top_k: topK });
  }

  return (
    <div className="min-h-dvh flex flex-col">

      {/* ── Sticky nav + popover ── */}
      <div className="sticky top-0 z-40">
        <form onSubmit={handleSubmit}>
          <header className="bg-white border-b border-black/[0.07] px-4 sm:px-6 lg:px-8 h-16 flex items-center gap-3 sm:gap-4">
            {/* Logo */}
            <span className="text-[17px] font-bold text-stone-900 tracking-[-0.035em] whitespace-nowrap flex-shrink-0">
              GroceryGuru
            </span>

            {/* Divider */}
            <div className="hidden sm:block w-px h-5 bg-black/[0.1] flex-shrink-0" />

            {/* Ingredient input (takes remaining space) */}
            <div className="flex-1 min-w-0">
              <IngredientInput
                ingredients={ingredients}
                onChange={setIngredients}
                disabled={isLoading}
              />
            </div>

            {/* Options toggle */}
            <button
              type="button"
              onClick={() => setOptionsOpen((o) => !o)}
              disabled={isLoading}
              className={`flex-shrink-0 hidden sm:inline-flex items-center gap-1.5 border rounded-[7px] px-3.5 h-[38px] text-sm font-medium transition-colors duration-150 disabled:opacity-50 disabled:cursor-not-allowed ${
                optionsOpen
                  ? "border-brand-500 text-brand-500 bg-brand-500/[0.05]"
                  : "border-black/[0.12] text-stone-500 hover:border-black/[0.22] hover:text-stone-900"
              }`}
              aria-expanded={optionsOpen}
              aria-controls="options-popover"
            >
              Options
              <svg
                className={`w-3.5 h-3.5 transition-transform duration-150 ${optionsOpen ? "rotate-180" : ""}`}
                viewBox="0 0 16 16"
                fill="currentColor"
                aria-hidden
              >
                <path fillRule="evenodd" d="M4.22 6.22a.75.75 0 0 1 1.06 0L8 8.94l2.72-2.72a.75.75 0 1 1 1.06 1.06l-3.25 3.25a.75.75 0 0 1-1.06 0L4.22 7.28a.75.75 0 0 1 0-1.06Z" clipRule="evenodd" />
              </svg>
            </button>

            {/* Find Recipes CTA */}
            <button
              type="submit"
              disabled={isLoading || !hasAnyIngredient}
              className="flex-shrink-0 inline-flex items-center gap-2 bg-brand-500 hover:bg-brand-600 text-white rounded-[7px] px-4 sm:px-5 h-[38px] text-sm font-semibold transition-colors duration-150 disabled:opacity-40 disabled:cursor-not-allowed active:scale-[0.98]"
            >
              {isLoading ? (
                <>
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none" aria-hidden>
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
                  </svg>
                  <span className="hidden sm:inline">Finding…</span>
                </>
              ) : (
                <>
                  <svg className="h-4 w-4" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" aria-hidden>
                    <circle cx="6.5" cy="6.5" r="5" />
                    <path d="M11 11l2.5 2.5" />
                  </svg>
                  <span className="hidden sm:inline">Find Recipes</span>
                  <span className="sm:hidden">Find</span>
                </>
              )}
            </button>
          </header>
        </form>

        {/* Options popover — conditionally rendered below the nav */}
        {optionsOpen && (
          <div id="options-popover">
            <OptionsPopover
              availableFilters={availableFilters}
              selectedFilters={selectedFilters}
              onFiltersChange={setSelectedFilters}
              spiceOptions={SPICE_OPTIONS}
              selectedSpices={selectedSpices}
              onSpicesChange={setSelectedSpices}
              topK={topK}
              onTopKChange={setTopK}
              onClose={() => setOptionsOpen(false)}
              disabled={isLoading}
            />
          </div>
        )}
      </div>

      {/* ── Main content ── */}
      <main className="flex-1 mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8 py-8 sm:py-10">

        {/* Error */}
        {status === "error" && (
          <div role="alert" className="mb-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            <strong>Error: </strong>{error}
          </div>
        )}

        {/* AI fallback notice */}
        {status === "success" && usedFallback && (
          <div className="mb-6 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
            AI generation was unavailable — showing database results.
            {fallbackReason ? ` Reason: ${fallbackReason}` : ""}
          </div>
        )}

        {/* Normalized ingredients feedback */}
        {status === "success" && normalizedIngredients.length > 0 && (
          <p className="mb-6 text-xs text-stone-400">
            Recognized as:{" "}
            <span className="text-stone-600 font-medium">{normalizedIngredients.join(", ")}</span>
          </p>
        )}

        {/* Results */}
        {status === "success" && (onHandRecipes.length > 0 || relatedRecipes.length > 0) && (
          <section aria-label="Recipe recommendations">

            {/* Serving size — near results, not in the form */}
            <div className="mb-7">
              <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-stone-400 mb-2">
                Serving size
              </p>
              <div className="inline-flex border border-black/[0.12] rounded-lg overflow-hidden">
                {[1, 2, 4].map((m) => (
                  <button
                    key={m}
                    type="button"
                    onClick={() => setServingMultiplier(m)}
                    className={`px-5 py-2 text-sm font-medium transition-colors duration-150 ${
                      servingMultiplier === m
                        ? "bg-stone-900 text-white"
                        : "text-stone-500 hover:bg-black/[0.04] hover:text-stone-900"
                    } [&+button]:border-l [&+button]:border-l-black/[0.08]`}
                  >
                    {m}×
                  </button>
                ))}
              </div>
            </div>

            {/* Cook Now */}
            {onHandRecipes.length > 0 && (
              <div className="mb-9">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-1 h-5 rounded-sm bg-brand-500 flex-shrink-0" />
                  <span className="text-[15px] font-semibold text-stone-900" style={{ letterSpacing: "-0.015em" }}>
                    Cook Now
                  </span>
                  <span className="text-xs text-stone-400">{onHandRecipes.length} recipe{onHandRecipes.length !== 1 ? "s" : ""}</span>
                </div>
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {onHandRecipes.map((recipe, i) => (
                    <RecipeCard
                      key={`${recipe.id ?? recipe.title}-on-hand`}
                      recipe={recipe}
                      rank={i + 1}
                      servingMultiplier={servingMultiplier}
                      variant="cook-now"
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Almost There */}
            {relatedRecipes.length > 0 && (
              <div className="mb-9">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-1 h-5 rounded-sm bg-stone-300 flex-shrink-0" />
                  <span className="text-[15px] font-semibold text-stone-900" style={{ letterSpacing: "-0.015em" }}>
                    Almost There
                  </span>
                  <span className="text-xs text-stone-400">{relatedRecipes.length} recipe{relatedRecipes.length !== 1 ? "s" : ""}</span>
                </div>
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {relatedRecipes.map((recipe, i) => (
                    <RecipeCard
                      key={`${recipe.id ?? recipe.title}-related`}
                      recipe={recipe}
                      rank={i + 1}
                      servingMultiplier={servingMultiplier}
                      variant="almost-there"
                    />
                  ))}
                </div>
              </div>
            )}

          </section>
        )}

        {/* Empty state — search ran but no results */}
        {status === "success" && onHandRecipes.length === 0 && relatedRecipes.length === 0 && (
          <div className="text-center py-24 px-6">
            <svg
              className="w-12 h-12 mx-auto mb-5 text-stone-300"
              viewBox="0 0 48 48"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.25"
              aria-hidden
            >
              <circle cx="22" cy="22" r="14" />
              <path d="M32 32l8 8" strokeLinecap="round" />
              <path d="M16 22h12M22 16v12" strokeLinecap="round" />
            </svg>
            <p className="text-[17px] font-semibold text-stone-900 mb-2" style={{ letterSpacing: "-0.02em" }}>
              No recipes matched
            </p>
            <p className="text-sm text-stone-400">
              Try removing a dietary filter or adding more ingredients.
            </p>
          </div>
        )}

        {/* Loading skeletons */}
        {isLoading && (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: Math.min(topK, 6) }).map((_, i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
        )}

        {/* Idle state */}
        {status === "idle" && (
          <div className="text-center py-24 px-6">
            <svg
              className="w-12 h-12 mx-auto mb-5 opacity-[0.18]"
              viewBox="0 0 48 48"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.25"
              aria-hidden
            >
              <rect x="7" y="9" width="34" height="32" rx="4" />
              <line x1="14" y1="20" x2="34" y2="20" strokeLinecap="round" />
              <line x1="14" y1="27" x2="27" y2="27" strokeLinecap="round" />
              <line x1="14" y1="34" x2="22" y2="34" strokeLinecap="round" />
            </svg>
            <p className="text-[18px] font-semibold text-stone-900 mb-2" style={{ letterSpacing: "-0.025em" }}>
              Your pantry, your recipes
            </p>
            <p className="text-sm text-stone-400">
              Add what's in your fridge and we'll find what's for dinner.
            </p>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-black/[0.06] py-4 text-center text-xs text-stone-400">
        GroceryGuru — Nutrition data from USDA FoodData Central
      </footer>
    </div>
  );
}
```

- [ ] **Step 2: Verify**

```bash
cd frontend && npm run typecheck && npm run lint
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/App.tsx
git commit -m "feat: rewrite App layout — sticky nav input, Options popover, amber/gray card grid"
```

---

## Task 8: Delete FilterPanel

**Files:**
- Delete: `frontend/src/components/FilterPanel.tsx`

FilterPanel is no longer imported anywhere (App.tsx was rewritten in Task 7 to use OptionsPopover).

- [ ] **Step 1: Confirm nothing imports FilterPanel**

```bash
cd frontend && grep -r "FilterPanel" src/
```

Expected: no output (zero matches).

- [ ] **Step 2: Delete the file**

```bash
git rm frontend/src/components/FilterPanel.tsx
```

- [ ] **Step 3: Commit**

```bash
git commit -m "chore: remove FilterPanel — replaced by OptionsPopover"
```

---

## Task 9: Final verification

- [ ] **Step 1: Run frontend checks**

```bash
cd frontend && npm run typecheck && npm run lint
```

Expected: no errors, no warnings.

- [ ] **Step 2: Run backend test suites (no-regression check)**

```bash
cd .. && PYTHONPATH=. pytest -q pantrypal/tests && PYTHONPATH=. pytest -q backend/tests
```

Expected: all tests pass (backend is unchanged).

- [ ] **Step 3: Smoke test in browser**

```bash
cd frontend && npm run dev
```

Open `http://localhost:5173` and verify:
- Page title shows "GroceryGuru"
- Nav bar is white, sticky, with correct logo and button sizing
- Typing an ingredient and pressing Enter creates a black-outlined chip
- Options button opens the popover; clicking outside closes it
- Dietary filter pills and spice chips toggle between outlined and black-filled
- Results slider moves from 1–20 with amber fill
- Find Recipes button is disabled until at least one ingredient is added
- Submitting shows warm-shimmer skeleton cards, then results
- Cook Now cards have amber left border; Almost There cards have gray
- Strong matches (≥75%) get black fill badge; weak matches get outlined badge
- Missing ingredient chips are dashed-border
- Show instructions reveals numbered steps with time references bolded
- Serving size toggle is in the results area, not the form
- Idle state shows the document icon + editorial copy
- Footer reads "GroceryGuru"
- Responsive: grid is 3-col at large, 2-col at tablet, 1-col at mobile

- [ ] **Step 4: Final commit (if any last fixes needed)**

```bash
git add -p  # stage only intentional changes
git commit -m "fix: post-smoke-test adjustments"
```

---

## Self-Review

**Spec coverage check:**
- App name "GroceryGuru" everywhere → Task 2 (HTML), Task 7 (App.tsx)
- Warm white `#FAF9F6` background → Task 1 (index.css)
- Letter-spacing -0.02em on headings → Task 1 (global h1–h4), Task 6 & 7 (inline style on card titles/section titles)
- Amber only on 5 elements → Task 7 (Find Recipes btn, Options btn active), Task 6 (Cook Now border), Task 5 (popover top-border + slider) ✓
- Active states use black fill → Task 5 (pills/spices), Task 7 (serving size) ✓
- Options popover: filter pills, spice chips, slider → Task 5 ✓
- Results slider (not +/−) → Task 5 ✓
- Structural left-border cards → Task 6 ✓
- Cook Now = amber border, Almost There = gray border → Task 6 & 7 ✓
- Match badge: black fill ≥75%, outlined <75% → Task 6 ✓
- Dashed chips for missing ingredients → Task 6 ✓
- Bold time references in instructions → Task 6 (`highlightStep`) ✓
- Serving size in results area → Task 7 ✓
- Skeleton with warm shimmer → Task 1 (CSS) + Task 3 (component) ✓
- Responsive: 3-col/2-col/1-col grid → Task 7 (`sm:grid-cols-2 lg:grid-cols-3`) ✓
- Options popover closes on backdrop click → Task 5 (fixed backdrop div) ✓
- FilterPanel deleted → Task 8 ✓
- `border` not `shadow` on cards → Task 6 ✓
- Idle state with editorial copy → Task 7 ✓

**No placeholders found.**

**Type consistency:** `variant: "cook-now" | "almost-there"` defined in Task 6 interface and used in Task 7 — consistent. `OptionsPopover` props defined in Task 5, wired in Task 7 — consistent. `SkeletonCard` created in Task 3, imported in Task 7 — consistent.
