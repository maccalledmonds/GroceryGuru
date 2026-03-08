import { useState } from "react";
import { RecipeResult } from "../api/client";
import { NutritionGrid } from "./NutritionGrid";

const DIET_TAG_STYLES: Record<string, string> = {
  vegetarian: "bg-emerald-100 text-emerald-700",
  vegan: "bg-green-100 text-green-700",
  gluten_free: "bg-yellow-100 text-yellow-700",
  high_protein: "bg-blue-100 text-blue-700",
};

const DIET_TAG_LABELS: Record<string, string> = {
  vegetarian: "Vegetarian",
  vegan: "Vegan",
  gluten_free: "Gluten-free",
  high_protein: "High-protein",
};

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
}

export function RecipeCard({ recipe, rank }: Props) {
  const [open, setOpen] = useState(false);

  return (
    <article className="rounded-2xl border border-gray-200 bg-white shadow-sm hover:shadow-md transition-shadow overflow-hidden">
      {/* Header */}
      <div className="flex items-start justify-between gap-3 px-5 pt-5 pb-3">
        <div className="flex items-center gap-2.5 min-w-0">
          <span className="flex-none flex items-center justify-center w-7 h-7 rounded-full bg-brand-100 text-brand-700 text-xs font-bold">
            {rank}
          </span>
          <h3 className="text-base font-semibold text-gray-900 truncate">{recipe.title}</h3>
        </div>
        <ScoreBadge score={recipe.score} />
      </div>

      <div className="px-5 pb-4 space-y-4">
        {/* Diet tags */}
        {recipe.diet_tags.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {recipe.diet_tags.map((tag) => (
              <span
                key={tag}
                className={`rounded-full px-2 py-0.5 text-[11px] font-medium ${
                  DIET_TAG_STYLES[tag] ?? "bg-gray-100 text-gray-600"
                }`}
              >
                {DIET_TAG_LABELS[tag] ?? tag}
              </span>
            ))}
          </div>
        )}

        {/* Nutrition */}
        <NutritionGrid nutrition={recipe.nutrition} />

        {/* Stats row */}
        <div className="flex items-center gap-4 text-xs text-gray-500">
          <span>
            <strong className="text-gray-700">{recipe.exact_match_count}</strong> ingredient
            {recipe.exact_match_count !== 1 ? "s" : ""} matched
          </span>
          <span>
            <strong className="text-gray-700">{recipe.match_percentage}%</strong> of recipe covered
          </span>
        </div>

        {/* Ingredients list */}
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-gray-400 mb-1.5">Ingredients</p>
          <p className="text-sm text-gray-600 leading-relaxed">{recipe.ingredients.join(", ")}</p>
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
            <div className="mt-3 rounded-lg bg-gray-50 px-4 py-3 text-sm text-gray-700 whitespace-pre-wrap leading-relaxed border border-gray-100">
              {recipe.instructions || "No instructions available."}
            </div>
          )}
        </div>
      </div>
    </article>
  );
}
