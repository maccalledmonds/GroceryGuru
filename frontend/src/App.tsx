import { useEffect, useState } from "react";
import { api } from "./api/client";
import { FilterPanel } from "./components/FilterPanel";
import { IngredientInput } from "./components/IngredientInput";
import { RecipeCard } from "./components/RecipeCard";
import { useRecommend } from "./hooks/useRecommend";

const SPICE_OPTIONS = [
  "garlic",
  "ginger",
  "turmeric",
  "basil",
  "parsley",
  "cilantro",
  "vanilla extract",
  "cinnamon",
  "nutmeg",
  "cumin",
  "paprika",
  "oregano",
  "thyme",
  "rosemary",
  "dill",
  "bay leaf",
  "mustard",
  "hot sauce",
  "curry paste",
];

const AUTO_INCLUDED_PANTRY = ["salt", "black pepper", "water"] as const;

const ESSENTIAL_SPICES = [
  "black pepper",
  "cumin",
  "paprika",
  "garlic powder",
  "oregano",
  "coriander",
  "turmeric",
  "chili powder",
  "cayenne pepper",
  "cinnamon",
  "red pepper flakes",
  "salt",
] as const;

// Skeleton card for the loading state
function SkeletonCard() {
  return (
    <div className="rounded-2xl border border-gray-200 bg-white shadow-sm overflow-hidden animate-pulse">
      <div className="px-5 pt-5 pb-3 flex items-center gap-3">
        <div className="w-7 h-7 rounded-full bg-gray-200" />
        <div className="h-5 w-48 rounded bg-gray-200" />
      </div>
      <div className="px-5 pb-5 space-y-3">
        <div className="grid grid-cols-4 gap-2">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="h-12 rounded-lg bg-gray-100" />
          ))}
        </div>
        <div className="h-4 w-full rounded bg-gray-100" />
        <div className="h-4 w-2/3 rounded bg-gray-100" />
      </div>
    </div>
  );
}

export default function App() {
  const [ingredients, setIngredients] = useState<string[]>([]);
  const [selectedFilters, setSelectedFilters] = useState<string[]>([]);
  const [selectedSpices, setSelectedSpices] = useState<string[]>([]);
  const [topK, setTopK] = useState(5);
  const [servingMultiplier, setServingMultiplier] = useState(1);
  const [availableFilters, setAvailableFilters] = useState<string[]>([]);

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

  // Fetch available filters from the API once on mount
  useEffect(() => {
    api
      .getFilters()
      .then((data) => setAvailableFilters(data.filters))
      .catch(() => {
        // Fall back to known filters if the API is unreachable at startup
        setAvailableFilters(["gluten_free", "high_protein", "vegan", "vegetarian"]);
      });
  }, []);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const requestIngredients = Array.from(
      new Set([...ingredients, ...selectedSpices, ...AUTO_INCLUDED_PANTRY]),
    );
    if (requestIngredients.length === 0) return;
    recommend({ ingredients: requestIngredients, filters: selectedFilters, top_k: topK });
  }

  function addEssentialSpices() {
    const merged = Array.from(new Set([...ingredients, ...ESSENTIAL_SPICES]));
    setIngredients(merged);
  }

  const isLoading = status === "loading";
  const hasAnyIngredient = ingredients.length > 0 || selectedSpices.length > 0;
  const hasAllEssentialSpices = ESSENTIAL_SPICES.every((spice) => ingredients.includes(spice));

  return (
    <div className="min-h-dvh flex flex-col">
      {/* Top nav */}
      <header className="sticky top-0 z-20 border-b border-gray-200 bg-white/80 backdrop-blur-sm">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 h-14 flex items-center gap-3">
          <span className="text-2xl leading-none" aria-hidden>🥕</span>
          <span className="text-lg font-bold text-gray-900 tracking-tight">PantryPal</span>
          <span className="ml-auto text-xs text-gray-400 hidden sm:block">
            Recipe recommendations from your pantry
          </span>
        </div>
      </header>

      <div className="mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8 flex flex-1 gap-8 py-8">
        {/* Sidebar */}
        <aside className="hidden lg:block w-56 flex-none">
          <div className="sticky top-24 rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
            <FilterPanel
              availableFilters={availableFilters}
              selectedFilters={selectedFilters}
              spiceOptions={SPICE_OPTIONS}
              selectedSpices={selectedSpices}
              topK={topK}
              onFiltersChange={setSelectedFilters}
              onSpicesChange={setSelectedSpices}
              onTopKChange={setTopK}
              disabled={isLoading}
            />
          </div>
        </aside>

        {/* Main content */}
        <main className="flex-1 min-w-0 space-y-6">
          {/* Input form */}
          <section className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  What's in your pantry?
                </label>
                <IngredientInput
                  ingredients={ingredients}
                  onChange={setIngredients}
                  disabled={isLoading}
                />
                <div className="mt-2">
                  <button
                    type="button"
                    onClick={addEssentialSpices}
                    disabled={isLoading || hasAllEssentialSpices}
                    className="inline-flex items-center gap-2 rounded-lg border border-amber-300 bg-amber-50 px-3 py-1.5 text-xs font-semibold text-amber-800 shadow-sm transition-colors hover:bg-amber-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-amber-500 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    Add essential spices
                  </button>
                </div>
                <p className="mt-1.5 text-xs text-gray-400">
                  Press <kbd className="rounded bg-gray-100 px-1 py-0.5 text-gray-600 font-mono">Enter</kbd> or{" "}
                  <kbd className="rounded bg-gray-100 px-1 py-0.5 text-gray-600 font-mono">,</kbd> after each ingredient
                </p>
              </div>

              {/* Mobile filters inline */}
              <div className="lg:hidden">
                <FilterPanel
                  availableFilters={availableFilters}
                  selectedFilters={selectedFilters}
                  spiceOptions={SPICE_OPTIONS}
                  selectedSpices={selectedSpices}
                  topK={topK}
                  onFiltersChange={setSelectedFilters}
                  onSpicesChange={setSelectedSpices}
                  onTopKChange={setTopK}
                  disabled={isLoading}
                />
              </div>

              {/* Normalized ingredients feedback */}
              {status === "success" && normalizedIngredients.length > 0 && (
                <p className="text-xs text-gray-400">
                  Recognized as:{" "}
                  <span className="text-gray-600 font-medium">{normalizedIngredients.join(", ")}</span>
                </p>
              )}

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Serving size</label>
                <div className="inline-flex rounded-xl border border-gray-200 bg-gray-50 p-1">
                  {[1, 2, 4].map((multiplier) => (
                    <button
                      key={multiplier}
                      type="button"
                      onClick={() => setServingMultiplier(multiplier)}
                      className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                        servingMultiplier === multiplier
                          ? "bg-white text-brand-700 shadow-sm"
                          : "text-gray-600 hover:text-gray-800"
                      }`}
                    >
                      {multiplier}x
                    </button>
                  ))}
                </div>
                <p className="mt-1 text-xs text-gray-400">Ingredient quantities are scaled when numeric amounts are available.</p>
              </div>

              <button
                type="submit"
                disabled={isLoading || !hasAnyIngredient}
                className="inline-flex items-center gap-2 rounded-xl bg-brand-500 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-brand-600 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isLoading ? (
                  <>
                    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none" aria-hidden>
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
                    </svg>
                    Finding recipes…
                  </>
                ) : (
                  <>
                    <svg className="h-4 w-4" viewBox="0 0 16 16" fill="currentColor" aria-hidden>
                      <path d="M6.5 12a5.5 5.5 0 1 0 0-11 5.5 5.5 0 0 0 0 11ZM13 13l-2.5-2.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" fill="none" />
                    </svg>
                    Recommend Recipes
                  </>
                )}
              </button>
            </form>
          </section>

          {/* Error state */}
          {status === "error" && (
            <div role="alert" className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              <strong>Error: </strong>{error}
            </div>
          )}

          {/* Loading skeletons */}
          {isLoading && (
            <div className="grid gap-4 sm:grid-cols-2">
              {Array.from({ length: topK > 4 ? 4 : topK }).map((_, i) => (
                <SkeletonCard key={i} />
              ))}
            </div>
          )}

          {/* Results */}
          {status === "success" && (onHandRecipes.length > 0 || relatedRecipes.length > 0) && (
            <section aria-label="Recipe recommendations" className="space-y-6">
              {usedFallback && (
                <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
                  AI generation was unavailable, so these are database-backed results.
                  {fallbackReason ? ` Reason: ${fallbackReason}` : ""}
                </div>
              )}

              <div>
                <p className="mb-1 text-sm font-semibold text-gray-700">Cook Now</p>
                <p className="mb-3 text-xs text-gray-500">Recipes you can make with what you already have.</p>
                {onHandRecipes.length > 0 ? (
                  <div className="grid gap-4 sm:grid-cols-2">
                    {onHandRecipes.map((recipe, i) => (
                      <RecipeCard
                        key={`${recipe.id ?? recipe.title}-on-hand`}
                        recipe={recipe}
                        rank={i + 1}
                        servingMultiplier={servingMultiplier}
                      />
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-500">No Cook Now matches yet.</p>
                )}
              </div>

              <div>
                <p className="mb-1 text-sm font-semibold text-gray-700">Almost There</p>
                <p className="mb-3 text-xs text-gray-500">Recipes close to your pantry list with a few missing items.</p>
                {relatedRecipes.length > 0 ? (
                  <div className="grid gap-4 sm:grid-cols-2">
                    {relatedRecipes.map((recipe, i) => (
                      <RecipeCard
                        key={`${recipe.id ?? recipe.title}-related`}
                        recipe={recipe}
                        rank={i + 1}
                        servingMultiplier={servingMultiplier}
                      />
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-500">No Almost There recommendations found.</p>
                )}
              </div>
            </section>
          )}

          {/* Empty state */}
          {status === "success" && onHandRecipes.length === 0 && relatedRecipes.length === 0 && (
            <div className="rounded-2xl border border-dashed border-gray-300 bg-white px-6 py-16 text-center">
              <p className="text-4xl mb-3" aria-hidden>🔍</p>
              <p className="text-sm font-medium text-gray-700">No recipes matched your ingredients and filters.</p>
              <p className="mt-1 text-sm text-gray-400">Try removing some dietary filters or adding more ingredients.</p>
            </div>
          )}

          {/* Idle placeholder */}
          {status === "idle" && (
            <div className="rounded-2xl border border-dashed border-gray-200 bg-white px-6 py-16 text-center">
              <p className="text-5xl mb-4" aria-hidden>🥕</p>
              <p className="text-base font-medium text-gray-700">Add ingredients to get started</p>
              <p className="mt-1 text-sm text-gray-400">
                Enter what you have on hand and we'll find matching recipes.
              </p>
            </div>
          )}
        </main>
      </div>

      <footer className="border-t border-gray-200 py-4 text-center text-xs text-gray-400">
        PantryPal — Nutrition data from USDA FoodData Central
      </footer>
    </div>
  );
}
