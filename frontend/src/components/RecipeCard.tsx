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

export function RecipeCard({ recipe, rank: _rank, servingMultiplier, variant }: Props) {
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
