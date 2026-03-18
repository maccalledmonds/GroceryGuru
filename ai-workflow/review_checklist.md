- Data Integrity: No hallucinated ingredients or recipes
- Matching Logic: Ingredient matching must be deterministic (not LLM-based)

## Ingredient Normalization & Canonical Mapping only (CRITICAL)

### Determinism
- Is the normalization pipeline strictly rule-based?
- Does it follow the exact specified order (lowercase → clean → singular → alias match → canonical)?
- Is there any use of LLMs, embeddings, or fuzzy guessing for normalization? (If yes → FAIL)

---

### Canonical Dataset Usage
- Are all mappings derived from the canonical ingredient dataset?
- Does each alias map to exactly one canonical ingredient?
- Are canonical IDs used where required?

---

### No Guessing / No Hallucination
- Does the system avoid inventing ingredients or mappings?
- If an ingredient is unknown, does it correctly fallback instead of guessing?
- Are there any implicit assumptions about ingredient relationships?

---

### Multi-word Ingredient Handling
- Are multi-word ingredients preserved correctly? (e.g. "soy sauce", "olive oil", "ice cream")
- Is there any incorrect token splitting that breaks meaning?

---

### Normalization Correctness
- Are descriptors properly removed? (fresh, chopped, etc.)
- Is singularization handled correctly?
- Are edge cases handled (plural + descriptor combinations)?

---

### Deduplication
- Are ingredients deduplicated AFTER normalization (not before)?
- Are equivalent inputs correctly collapsed into one canonical ingredient?

---

### Matching Integrity
- Are ALL downstream systems (matching, scoring, retrieval) using canonical ingredients instead of raw strings?
- Is there any fallback to raw string comparison? (If yes → FLAG)

---

### Edge Case Validation
Check against required cases:

- "Fresh Tomatoes" → "tomato"
- "garlic cloves" → "garlic"
- "extra virgin olive oil" → "olive oil"
- "soy sauce" → "soy sauce"
- "ice cream" → "ice cream"

Any failure → REJECT