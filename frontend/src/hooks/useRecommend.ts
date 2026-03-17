import { useCallback, useState } from "react";
import { api, RecipeResult, RecommendRequest } from "../api/client";

interface RecommendState {
  status: "idle" | "loading" | "success" | "error";
  onHandRecipes: RecipeResult[];
  relatedRecipes: RecipeResult[];
  normalizedIngredients: string[];
  usedFallback: boolean;
  fallbackReason: string | null;
  error: string | null;
}

interface UseRecommendReturn extends RecommendState {
  recommend: (req: RecommendRequest) => Promise<void>;
  reset: () => void;
}

const INITIAL: RecommendState = {
  status: "idle",
  onHandRecipes: [],
  relatedRecipes: [],
  normalizedIngredients: [],
  usedFallback: false,
  fallbackReason: null,
  error: null,
};

export function useRecommend(): UseRecommendReturn {
  const [state, setState] = useState<RecommendState>(INITIAL);

  const recommend = useCallback(async (req: RecommendRequest) => {
    setState({
      status: "loading",
      onHandRecipes: [],
      relatedRecipes: [],
      normalizedIngredients: [],
      usedFallback: false,
      fallbackReason: null,
      error: null,
    });
    try {
      const data = await api.recommendAI(req);
      setState({
        status: "success",
        onHandRecipes: data.on_hand_recipes,
        relatedRecipes: data.related_recipes,
        normalizedIngredients: data.normalized_ingredients,
        usedFallback: data.used_fallback,
        fallbackReason: data.fallback_reason ?? null,
        error: null,
      });
    } catch (err) {
      setState({
        status: "error",
        onHandRecipes: [],
        relatedRecipes: [],
        normalizedIngredients: [],
        usedFallback: false,
        fallbackReason: null,
        error: err instanceof Error ? err.message : "Unknown error",
      });
    }
  }, []);

  const reset = useCallback(() => setState(INITIAL), []);

  return { ...state, recommend, reset };
}
