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
