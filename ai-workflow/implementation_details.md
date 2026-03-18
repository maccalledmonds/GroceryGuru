# Technical Details

- Backend: Python 3.11 on Render, FastAPI API service served with Uvicorn, Pydantic models for request/response validation, CORS middleware configured for localhost + Vercel preview URLs, AI/recommendation components include FAISS, sentence-transformers, Groq client, and httpx

- Recipe dataset: structured local JSON
    - Primary source: recipes.json
    - Supporting AI index assets: recipes.faiss, recipes_rag_metadata.json

- Canonical ingredient dataset (NEW):
    - structured JSON (e.g. canonical_ingredients.json)
    - Each ingredient:
        - id
        - canonical_name
        - aliases[]

- Each recipe:
    - id
    - title
    - ingredients[]
    - ingredients_normalized[]
    - instructions
    - diet_tags[]
    - nutrition { calories, protein, fat, carbs }


## Ingredient Normalization System (CRITICAL)

### Core Principle
- Deterministic, rule-based normalization FIRST
- Dataset-driven canonical mapping SECOND
- AI/semantic methods are NOT used for final mapping decisions

---

### Normalization Pipeline (STRICT ORDER)

For each input ingredient:

1. **Trim + lowercase**
   - "  Fresh Tomatoes  " → "fresh tomatoes"

2. **Remove punctuation**
   - commas, parentheses, special characters

3. **Descriptor removal**
   Remove non-essential modifiers:
   - fresh, chopped, diced, sliced, organic, large, small, extra, virgin

   Example:
   - "fresh chopped tomatoes" → "tomatoes"

4. **Normalize whitespace**
   - collapse multiple spaces → single space

5. **Singularization**
   - tomatoes → tomato
   - eggs → egg
   - peppers → pepper

6. **Alias matching (PRIMARY STEP)**
   - Match cleaned string against canonical dataset:
     - direct match to canonical_name
     - OR match to any alias

   Example:
   - "chicken breast" → "chicken"
   - "garlic cloves" → "garlic"

7. **Canonical mapping**
   - If match found:
       - return canonical_name + canonical_id
   - If no match:
       - return cleaned ingredient
       - canonical_id = null

---

### Output Format (internal)

{
  raw: string,
  normalized: string,
  canonical_name: string | null,
  canonical_id: string | null
}

---

### Output Format (API-level)

normalized_ingredients: string[]

- MUST use canonical_name if available
- OTHERWISE fallback to normalized string

---

### Multi-word Ingredient Handling

- Preserve meaningful multi-word ingredients:
    - "soy sauce"
    - "olive oil"
    - "ice cream"

- DO NOT split into individual tokens
- Matching must operate on full phrases first before fallback

---

### Synonym Strategy

- Canonical dataset is the single source of truth
- Aliases must map to exactly one canonical ingredient
- No dynamic synonym generation at runtime

---

### Hard Constraints

- DO NOT hallucinate ingredients
- DO NOT guess canonical mappings
- DO NOT rely on embeddings or FAISS for normalization
- FAISS and sentence-transformers are ONLY for recipe retrieval, NOT ingredient normalization

---

### Failure Handling

If ingredient cannot be mapped:
- Return cleaned normalized string
- canonical_id = null
- Do NOT attempt semantic guessing

---

### Deduplication Rules

- Deduplicate AFTER normalization
- Example:
    - ["Tomatoes", "tomato", "fresh tomatoes"] → ["tomato"]

---

### Edge Cases (MUST PASS)

"Fresh Tomatoes" → "tomato"  
"chopped onions" → "onion"  
"garlic cloves" → "garlic"  
"chicken breasts" → "chicken"  
"extra virgin olive oil" → "olive oil"  
"soy sauce" → "soy sauce"  
"ice cream" → "ice cream"  

---

## Requirements

### Exact Match
- Generated recipe candidates intended to use as many user ingredients as possible
- Generate nutrition information { calories, protein, fat, carbs }
- Ranked with overlap/coverage-based scoring
- MUST use canonical ingredients for matching
- Returned in on_hand_recipes

---

### Related Recipes
- Allow missing ingredients
- Rank by:
   - score = (# matched canonical ingredients) / (total ingredients)

- Retrieved from local recipe database
- Requires at least 1 overlapping canonical ingredient
- Recommend real meals (avoid condiments, drinks, trivial recipes)
- Penalize missing ingredients
- Returned in related_recipes

---

### Output format:

{
on_hand_recipes: [
{
id: number | null,
type: "generated" | "database",
title: string,
ingredients: string[],
missing_ingredients: string[],
instructions: string[] | string | null,
score: number,
match_score: number | null
}
],
related_recipes: [
{
id: number | null,
type: "database" | "generated",
title: string,
ingredients: string[],
missing_ingredients: string[],
instructions: string[] | string | null,
score: number,
match_score: number | null
}
],
normalized_ingredients: string[],
used_fallback: boolean,
fallback_reason: string | null
}

---

## Constraints

- Input validation:
  - Reject empty/whitespace-only ingredient input
  - Reject unsupported dietary filters

- Ingredient handling:
  - Normalize using defined pipeline ONLY
  - Deduplicate AFTER normalization
  - Use canonical ingredients for ALL matching logic

- Reliability/fallback:
  - If LLM fails, return database-backed results
  - Always return normalized ingredients

- Data integrity:
  - Missing ingredients must come from known recipe ingredients
  - Generated recipes must explicitly list missing ingredients
  - No hallucinated ingredients

- Separation of concerns:
  - Normalization = deterministic pipeline
  - Retrieval = FAISS / embeddings
  - Generation = LLM

- Code quality:
  - No pseudocode
  - Generate production-ready Python code