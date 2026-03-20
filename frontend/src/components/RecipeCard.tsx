import { useState } from "react";
import { RecipeResult } from "../api/client";

function isSpecialEquipmentPhrase(value: string): boolean {
  const lowered = value.trim().toLowerCase();
  return /\bspecial\s+equipment\b|^equipment\b/.test(lowered);
}

function ScoreBadge({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const color =
    pct >= 75 ? "bg-emerald-500" : pct >= 50 ? "bg-brand-500" : pct >= 25 ? "bg-yellow-500" : "bg-gray-400";
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold text-white ${color}`}>
      {pct}% match
    </span>
  );
}

interface Props {
  recipe: RecipeResult;
  rank: number;
  servingMultiplier: number;
}

const UNICODE_FRACTIONS: Record<string, number> = {
  "¼": 0.25,
  "½": 0.5,
  "¾": 0.75,
  "⅓": 1 / 3,
  "⅔": 2 / 3,
  "⅛": 0.125,
  "⅜": 0.375,
  "⅝": 0.625,
  "⅞": 0.875,
};

function parseQuantityToken(token: string): number | null {
  const clean = token.trim();
  if (!clean) return null;

  if (UNICODE_FRACTIONS[clean] != null) {
    return UNICODE_FRACTIONS[clean];
  }

  const mixedMatch = clean.match(/^(\d+)\s+(\d+)\/(\d+)$/);
  if (mixedMatch) {
    const whole = Number(mixedMatch[1]);
    const numerator = Number(mixedMatch[2]);
    const denominator = Number(mixedMatch[3]);
    if (denominator !== 0) {
      return whole + numerator / denominator;
    }
    return null;
  }

  const fractionMatch = clean.match(/^(\d+)\/(\d+)$/);
  if (fractionMatch) {
    const numerator = Number(fractionMatch[1]);
    const denominator = Number(fractionMatch[2]);
    if (denominator !== 0) {
      return numerator / denominator;
    }
    return null;
  }

  const asNumber = Number(clean);
  if (!Number.isNaN(asNumber)) {
    return asNumber;
  }

  return null;
}

function formatQuantity(value: number): string {
  if (!Number.isFinite(value)) return "";
  if (Math.abs(value) >= 10) {
    return String(Math.round(value * 10) / 10);
  }
  return String(Math.round(value * 100) / 100).replace(/\.00$/, "").replace(/(\.\d*[1-9])0$/, "$1");
}

function scaleIngredientText(ingredient: string, multiplier: number): string {
  if (multiplier === 1) return ingredient;

  const rangePattern =
    /^\s*([¼½¾⅓⅔⅛⅜⅝⅞]|\d+(?:\.\d+)?(?:\s+\d+\/\d+)?|\d+\/\d+)\s*(?:-|to)\s*([¼½¾⅓⅔⅛⅜⅝⅞]|\d+(?:\.\d+)?(?:\s+\d+\/\d+)?|\d+\/\d+)(\s+.*)$/i;
  const singlePattern = /^\s*([¼½¾⅓⅔⅛⅜⅝⅞]|\d+(?:\.\d+)?(?:\s+\d+\/\d+)?|\d+\/\d+)(\s+.*)$/i;

  const rangeMatch = ingredient.match(rangePattern);
  if (rangeMatch) {
    const left = parseQuantityToken(rangeMatch[1]);
    const right = parseQuantityToken(rangeMatch[2]);
    if (left != null && right != null) {
      return `${formatQuantity(left * multiplier)}-${formatQuantity(right * multiplier)}${rangeMatch[3]}`;
    }
  }

  const singleMatch = ingredient.match(singlePattern);
  if (singleMatch) {
    const value = parseQuantityToken(singleMatch[1]);
    if (value != null) {
      return `${formatQuantity(value * multiplier)}${singleMatch[2]}`;
    }
  }

  return ingredient;
}

function toInstructionSteps(instructions: RecipeResult["instructions"]): string[] {
  if (Array.isArray(instructions)) {
    const cleaned = instructions.map((step) => step.trim()).filter(Boolean);
    if (cleaned.length > 0) return cleaned;
  }

  if (typeof instructions !== "string" || !instructions.trim()) {
    return ["No instructions available."];
  }

  const normalized = instructions.replace(/\r/g, "").trim();

  const lineSteps = normalized
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);

  if (lineSteps.length > 1) {
    return lineSteps.map((line) => line.replace(/^(?:step\s*)?\d+[\).:\-]\s*/i, ""));
  }

  const numberedParts = normalized
    .split(/\s+(?=(?:step\s*)?\d+[\).:\-]\s+)/i)
    .map((part) => part.trim())
    .filter(Boolean)
    .map((part) => part.replace(/^(?:step\s*)?\d+[\).:\-]\s*/i, ""))
    .filter(Boolean);

  if (numberedParts.length > 1) {
    return numberedParts;
  }

  const sentenceSteps = normalized
    .split(/(?<=[.!?])\s+(?=[A-Z])/)
    .map((part) => part.trim())
    .filter(Boolean);

  return sentenceSteps.length > 0 ? sentenceSteps : [normalized];
}

export function RecipeCard({ recipe, rank, servingMultiplier }: Props) {
  const [open, setOpen] = useState(false);
  const isDatabaseRecipe = recipe.type === "database";
  const missingIngredients = (recipe.missing_ingredients ?? []).filter(
    (item) => !isSpecialEquipmentPhrase(item),
  );
  const instructionSteps = toInstructionSteps(recipe.instructions);
  const ingredientsForDisplay = recipe.ingredients;
  const scaledIngredients = isDatabaseRecipe
    ? ingredientsForDisplay.map((ingredient) => scaleIngredientText(ingredient, servingMultiplier))
    : ingredientsForDisplay;

  return (
    <article className="rounded-2xl border border-gray-200 bg-white shadow-sm hover:shadow-md transition-shadow overflow-hidden">
      {/* Header */}
      <div className="flex items-start justify-between gap-3 px-5 pt-5 pb-3">
        <div className="flex items-start gap-2.5 min-w-0">
          <span className="flex-none flex items-center justify-center w-7 h-7 rounded-full bg-brand-100 text-brand-700 text-xs font-bold">
            {rank}
          </span>
          <div className="min-w-0 flex-1">
            <h3 className="text-base font-semibold text-gray-900 whitespace-normal break-words leading-snug">
              {recipe.title}
            </h3>
          </div>
          <span className="mt-0.5 shrink-0 rounded-full bg-gray-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-gray-600">
            {recipe.type}
          </span>
        </div>
        <ScoreBadge score={recipe.score} />
      </div>

      <div className="px-5 pb-4 space-y-4">
        {/* Stats row */}
        <div className="flex items-center gap-4 text-xs text-gray-500">
          <span>
            <strong className="text-gray-700">{missingIngredients.length}</strong> missing ingredient
            {missingIngredients.length !== 1 ? "s" : ""}
          </span>
          {isDatabaseRecipe && recipe.servings != null && (
            <span>
              Serves: <strong className="text-gray-700">{recipe.servings}</strong>
            </span>
          )}
          {recipe.match_score != null && <span>Match score: <strong className="text-gray-700">{recipe.match_score.toFixed(2)}</strong></span>}
        </div>

        {missingIngredients.length > 0 && (
          <div className="rounded-lg border border-amber-100 bg-amber-50/70 px-3 py-2 text-sm text-amber-900">
            <p className="font-medium">You may need:</p>
            <p className="mt-0.5 text-amber-800">{missingIngredients.join(", ")}</p>
          </div>
        )}

        {/* Ingredients list */}
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-gray-400 mb-1.5">Ingredients</p>
          {isDatabaseRecipe && servingMultiplier !== 1 && (
            <p className="mb-1.5 text-xs text-gray-500">
              Amounts adjusted for <span className="font-semibold">{servingMultiplier}x servings</span>
            </p>
          )}
          <ul className="list-disc pl-5 space-y-1 text-sm text-gray-600 leading-relaxed">
            {scaledIngredients.map((ingredient, i) => (
              <li key={`${ingredient}-${i}`}>{ingredient}</li>
            ))}
          </ul>
        </div>

        {/* Collapsible instructions */}
        <div>
          <button
            type="button"
            onClick={() => setOpen((o) => !o)}
            className="flex items-center gap-1.5 text-sm font-medium text-brand-600 hover:text-brand-700 focus:outline-none focus-visible:underline"
            aria-expanded={open}
          >
            <svg
              className={`w-4 h-4 transition-transform ${open ? "rotate-180" : ""}`}
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

          {open && (
            <div className="mt-3 rounded-lg bg-gray-50 px-4 py-3 text-sm text-gray-700 leading-relaxed border border-gray-100">
              <ol className="list-decimal pl-5 space-y-2">
                {instructionSteps.map((step, i) => (
                  <li key={`${step}-${i}`}>{step}</li>
                ))}
              </ol>
            </div>
          )}
        </div>
      </div>
    </article>
  );
}
