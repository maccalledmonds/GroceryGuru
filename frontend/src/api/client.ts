/** Shared TypeScript types mirroring the FastAPI response schemas. */

export interface Nutrition {
  calories: number;
  protein: number;
  fat: number;
  carbs: number;
}

export interface RecipeResult {
  id?: number | null;
  type: "database" | "generated";
  title: string;
  score: number;
  match_score?: number | null;
  ingredients: string[];
  ingredients_normalized?: string[];
  servings?: number | null;
  instructions?: string[] | string | null;
  missing_ingredients?: string[];
}

export interface RecommendRequest {
  ingredients: string[];
  filters?: string[];
  top_k?: number;
}

export interface RecommendResponse {
  on_hand_recipes: RecipeResult[];
  related_recipes: RecipeResult[];
  normalized_ingredients: string[];
  used_fallback: boolean;
  fallback_reason?: string | null;
}

export interface FiltersResponse {
  filters: string[];
}

// ---------------------------------------------------------------------------
// API client
// ---------------------------------------------------------------------------

const BASE_URL = (import.meta.env.VITE_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      detail = body?.detail ?? detail;
    } catch {
      // ignore parse errors
    }
    throw new Error(String(detail));
  }

  return res.json() as Promise<T>;
}

export const api = {
  getFilters(): Promise<FiltersResponse> {
    return apiFetch<FiltersResponse>("/api/filters");
  },

  recommend(req: RecommendRequest): Promise<RecommendResponse> {
    return apiFetch<RecommendResponse>("/api/recommend", {
      method: "POST",
      body: JSON.stringify(req),
    });
  },

  recommendAI(req: RecommendRequest): Promise<RecommendResponse> {
    return apiFetch<RecommendResponse>("/api/recommend/ai", {
      method: "POST",
      body: JSON.stringify(req),
    });
  },
};
