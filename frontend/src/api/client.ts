/** Shared TypeScript types mirroring the FastAPI response schemas. */

export interface Nutrition {
  calories: number;
  protein: number;
  fat: number;
  carbs: number;
}

export interface RecipeResult {
  id: number;
  title: string;
  score: number;
  match_percentage: number;
  exact_match_count: number;
  coverage: number;
  ingredient_match_ratio: number;
  ingredients: string[];
  instructions: string;
  diet_tags: string[];
  nutrition: Nutrition;
}

export interface RecommendRequest {
  ingredients: string[];
  filters?: string[];
  top_k?: number;
}

export interface RecommendResponse {
  recipes: RecipeResult[];
  normalized_ingredients: string[];
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
};
