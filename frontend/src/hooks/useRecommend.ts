import { useCallback, useState } from "react";
import { api, RecipeResult, RecommendRequest } from "../api/client";

interface RecommendState {
  status: "idle" | "loading" | "success" | "error";
  recipes: RecipeResult[];
  normalizedIngredients: string[];
  error: string | null;
}

interface UseRecommendReturn extends RecommendState {
  recommend: (req: RecommendRequest) => Promise<void>;
  reset: () => void;
}

const INITIAL: RecommendState = {
  status: "idle",
  recipes: [],
  normalizedIngredients: [],
  error: null,
};

export function useRecommend(): UseRecommendReturn {
  const [state, setState] = useState<RecommendState>(INITIAL);

  const recommend = useCallback(async (req: RecommendRequest) => {
    setState({ status: "loading", recipes: [], normalizedIngredients: [], error: null });
    try {
      const data = await api.recommend(req);
      setState({
        status: "success",
        recipes: data.recipes,
        normalizedIngredients: data.normalized_ingredients,
        error: null,
      });
    } catch (err) {
      setState({
        status: "error",
        recipes: [],
        normalizedIngredients: [],
        error: err instanceof Error ? err.message : "Unknown error",
      });
    }
  }, []);

  const reset = useCallback(() => setState(INITIAL), []);

  return { ...state, recommend, reset };
}
