# GroceryGuru AI Workflow Log

## Date
2026-03-17

## Status
Planning complete for multi-phase implementation. No code or data changes executed.

## Structured Phase-by-Phase Plan

### Phase 0: Canonical Ingredient Dataset (Gatekeeper Phase)
Objective:
- Define and approve a canonical ingredient source of truth used by all downstream systems.

Deliverables:
- Canonical schema definition (`id`, `canonical_name`, `aliases[]`)
- Initial canonical ingredient catalog covering core food domains
- Validation checklist for uniqueness and alias integrity
- Approval artifact that allows progression to Phase 1

Exit Criteria:
- No duplicate canonical names
- Every alias maps to exactly one canonical ingredient
- Multi-word ingredients are preserved and represented explicitly
- Dataset approved for use by normalization logic

Dependencies:
- None

Risks:
- Alias collisions (same alias mapping to multiple canonicals)
- Overly broad canonicals that reduce matching precision

---

### Phase 1: Ingredient Normalization System
Objective:
- Build deterministic normalization pipeline that maps raw input to canonical ingredients when possible.

Deliverables:
- Ordered normalization pipeline (lowercase -> punctuation removal -> descriptor removal -> whitespace normalization -> singularization -> alias lookup -> canonical mapping)
- Internal normalized output structure with canonical id presence/absence
- Clear fallback behavior when no canonical match exists

Exit Criteria:
- Pipeline order enforced exactly
- No LLM/embedding dependency in normalization decisions
- Required edge cases pass (including multi-word preservation)

Dependencies:
- Approved Phase 0 dataset

Risks:
- Descriptor stripping that removes meaning
- Singularization errors for irregular nouns

---

### Phase 2: Ingredient Matching Core
Objective:
- Ensure matching logic operates strictly on canonical ingredients for exact-style coverage.

Deliverables:
- Canonical-only matching logic for generated/exact candidate flow
- Distinctness handling for near-duplicate recipe outputs
- Match metrics inputs for scoring phase

Exit Criteria:
- No raw-string matching in core logic
- Canonical overlap is traceable per recipe

Dependencies:
- Phase 1 canonicalized ingredient outputs

Risks:
- Drift between generated ingredient terms and canonical set

---

### Phase 3: Similar Recipe Retrieval
Objective:
- Retrieve database recipes with partial overlap and minimal additional requirements.

Deliverables:
- Retrieval flow requiring at least one canonical overlap
- Missing-ingredient derivation using canonical ingredients
- Candidate set suitable for scoring/ranking

Exit Criteria:
- Similar results based on canonical overlap, not raw strings
- Trivial/non-meal recommendations reduced

Dependencies:
- Phases 0-2

Risks:
- Candidate quality issues from weak overlap thresholds

---

### Phase 4: Scoring and Ranking
Objective:
- Rank candidates using transparent overlap-based scoring with missing-ingredient penalties.

Deliverables:
- Formula implementation alignment: score = matched / total required
- Penalty integration for missing ingredients
- Tie-breaking policy for stable ranking

Exit Criteria:
- Scores are reproducible and explainable
- Higher overlap consistently ranks above lower overlap

Dependencies:
- Phases 2-3 candidate generation

Risks:
- Score inflation for low-ingredient recipes without guardrails

---

### Phase 5: API Layer
Objective:
- Expose exact/on-hand and similar/related recommendations in contract-compliant response shape.

Deliverables:
- Endpoint contract for on-hand and related recipe arrays
- Normalized ingredients returned on every response
- Fallback metadata (`used_fallback`, `fallback_reason`) returned reliably

Exit Criteria:
- Response schema is stable and validated
- Error handling and fallback behavior are deterministic

Dependencies:
- Phases 1-4

Risks:
- Contract drift between backend models and frontend expectations

---

### Phase 6: Frontend Integration
Objective:
- Present recommendations as actionable UI sections with clear distinction between exact and similar matches.

Deliverables:
- Two-section render model: "Cook Now" and "Almost There"
- Missing ingredients and score presentation
- UX handling for empty states and fallback states

Exit Criteria:
- Sections map correctly to backend response partitions
- Users can understand why recipes are suggested

Dependencies:
- Phase 5 API readiness

Risks:
- Mislabeling or conflation of exact vs similar groups

---

### Phase 7: Testing and Edge-Case Hardening
Objective:
- Validate reliability, correctness, and regression safety across normalization, matching, scoring, and API output.

Deliverables:
- Test coverage for listed edge cases (empty pantry, duplicates, unknown ingredients, ambiguous terms, large lists)
- Deterministic tests for normalization and canonical mapping behavior
- Integration checks for fallback and response integrity

Exit Criteria:
- Critical edge cases pass
- No regressions in canonical-first matching behavior

Dependencies:
- Phases 0-6

Risks:
- Hidden regressions from dataset updates or alias additions

## Expanded Phase 0: Actionable Execution Plan (No Implementation Yet)

### 0.1 Scope and Taxonomy Definition
Action:
- Define ingredient domain boundaries for v1 (proteins, vegetables, grains, oils, condiments, common staples, multi-word ingredients).

Output:
- Written scope statement listing included and excluded categories.

Done When:
- Team agrees on v1 boundaries and avoids scope creep during dataset build.

---

### 0.2 Canonical Schema Finalization
Action:
- Finalize record contract:
	- `id`: stable string identifier (e.g., `ing_0001`)
	- `canonical_name`: unique normalized phrase
	- `aliases`: list of alternate forms

Output:
- Schema spec with field rules and examples.

Done When:
- Rules are explicit for naming, casing, spacing, and id format.

---

### 0.3 Canonical Naming Rules
Action:
- Define canonical naming conventions:
	- lowercase names
	- preserve meaningful multi-word phrases
	- avoid preparation/state descriptors in canonicals
	- singular base form where appropriate

Output:
- Canonical naming guideline sheet.

Done When:
- Naming decisions are consistent across sample entries.

---

### 0.4 Alias Policy and Collision Rules
Action:
- Define alias standards:
	- one alias -> one canonical only
	- include common plural, regional, and phrase variants
	- exclude ambiguous aliases unless disambiguated

Output:
- Alias acceptance rules plus collision-handling protocol.

Done When:
- Protocol exists for resolving conflicting aliases before approval.

---

### 0.5 Seed List Creation (Core Ingredients)
Action:
- Build first-pass canonical list from common pantry and recipe staples across required categories.

Output:
- Seed catalog draft with prioritized high-frequency ingredients.

Done When:
- Each required category has minimum viable representation.

---

### 0.6 Multi-word Ingredient Protection Pass
Action:
- Identify and explicitly include phrase-level ingredients that must remain intact (e.g., olive oil, soy sauce, ice cream).

Output:
- Protected multi-word list appended to canonical dataset draft.

Done When:
- Protected phrases are represented as canonicals or aliases with no token-splitting ambiguity.

---

### 0.7 Dataset Validation Checklist (Pre-Approval)
Action:
- Run structured validation review for:
	- duplicate `canonical_name`
	- duplicate `id`
	- alias collisions
	- empty alias arrays where coverage is expected
	- formatting consistency

Output:
- Validation report with pass/fail status and issue list.

Done When:
- All blocking issues resolved.

---

### 0.8 Edge-Case Coverage Review
Action:
- Verify dataset supports known normalization targets:
	- tomatoes -> tomato
	- chopped onions -> onion
	- garlic cloves -> garlic
	- chicken breasts -> chicken
	- extra virgin olive oil -> olive oil
	- soy sauce -> soy sauce
	- ice cream -> ice cream

Output:
- Coverage matrix mapping edge-case input families to canonical targets.

Done When:
- Edge-case families have explicit canonical/alias support.

---

## Plan Review Feedback (2026-03-17)

Decision: **REJECT (revise then re-submit)**

Reason:
- The overall direction is strong, but Phase 0 and Phase 1 still leave room for implementation-time guessing. The plan is close, but not yet enforceable as a strict engineering contract.

### 1) Phase 0 (Canonical Dataset) Assessment

Status: **Partially sufficient**

What is good:
- Clear schema shape (`id`, `canonical_name`, `aliases[]`).
- Correct uniqueness intent (no duplicate canonical names, one alias -> one canonical).
- Explicit multi-word protection requirements.
- Pre-approval validation checklist exists.

Blocking gaps (ambiguity risk):
- Missing storage/contract location: no required canonical dataset file path/name is mandated.
- Missing schema strictness:
	- No regex/format rule for `id` (example shown, but not enforced).
	- No rule for whether aliases are required, optional, or allowed empty.
	- No rule for max/min alias length or duplicate aliases within one record.
- Missing normalization boundary for dataset content:
	- It is not explicit whether `canonical_name` and each alias must already be normalized (lowercase, trimmed, single-space).
	- If this is not enforced in Phase 0, Phase 1 behavior can drift.
- Missing collision precedence protocol details:
	- Collision handling is mentioned, but no deterministic resolution policy is defined.
	- Need explicit fail-fast rule (build/validation fails on any alias collision).
- Missing versioning/change-control gate:
	- No required dataset version field/changelog or explicit re-validation trigger after edits.

Required additions for approval:
- Define canonical dataset artifact path and ownership (single source of truth).
- Add strict schema contract:
	- `id` format (e.g., `^ing_[0-9]{4,}$`), uniqueness required.
	- `canonical_name` required, normalized, unique.
	- `aliases` required array (can be empty only if explicitly justified) and globally unique across all aliases and canonical names.
- Add Phase 0 validator acceptance criteria:
	- hard-fail on duplicates, collisions, invalid casing/spacing, invalid id format.
- Add dataset versioning rule:
	- every dataset edit requires validator pass + edge-case matrix re-check.

### 2) Phase 1 (Normalization) Assessment

Status: **Strong direction but not fully enforceable/deterministic yet**

What is good:
- Correct strict-order intent for deterministic pipeline.
- Explicit ban on LLM/embedding for normalization decisions.
- Clear fallback (`canonical_id = null`) and edge-case examples.

Blocking gaps (determinism risk):
- Descriptor removal is underspecified:
	- Uses "etc." language, which allows implementer interpretation drift.
	- Needs a frozen descriptor lexicon for v1.
- Singularization is underspecified:
	- No exact algorithm or irregular dictionary defined.
	- Different libraries/rules will produce different outputs.
- Alias/canonical matching precedence is not fully explicit:
	- Need deterministic order: exact canonical match vs alias match, and phrase-level vs token-level handling.
	- Need explicit tie behavior (should be impossible if Phase 0 uniqueness holds; otherwise fail-fast).
- Phrase protection timing not fully encoded in pipeline steps:
	- Multi-word protection is stated separately, but not encoded as a formal step before destructive transforms.
- Punctuation removal behavior can alter tokens unpredictably:
	- Need exact character policy (remove vs replace with space), especially around hyphens/slashes.
- Output contract inconsistency across docs:
	- One spec states `canonical_name: string`, another states `canonical_name: string | null`.
	- Must be unified to avoid API/model divergence.

Required additions for approval:
- Freeze exact v1 normalization spec as code-level contract:
	- Ordered step list with no "etc." wording.
	- Explicit descriptor set.
	- Explicit singularization strategy (rule set + irregular map).
	- Explicit punctuation/whitespace transformation table.
	- Explicit full-phrase-first matching policy.
- Add deterministic matching precedence:
	1. exact `canonical_name` match
	2. exact alias match
	3. otherwise no canonical mapping (`canonical_id = null`)
- Enforce no partial token guessing in canonical mapping.
- Align output schema to one canonical definition across all documents.

### 3) Approval Summary

Decision: **REJECT**

Approval condition:
- Re-submit with the above Phase 0 and Phase 1 contract-level clarifications, then this can move to **APPROVE** without requiring architecture changes.

---

### 0.9 Approval Gate
Action:
- Conduct formal review and lock Phase 0 dataset as source of truth for normalization.

Output:
- Approval note with version tag and change-control rule for future additions.

Done When:
- Stakeholder sign-off recorded; Phase 1 may begin.

## Non-Implementation Confirmation
- No code written
- No dataset files created or modified
- No API/frontend/test changes executed
- This entry is planning-only, as requested

---

## Plan Revision v2 (Reviewer-Addressed, 2026-03-17)

Status:
- Revised for re-submission.
- This is a planning update only. No implementation performed.

### A) Updated Phase-by-Phase Plan (Contract-Oriented)

#### Phase 0: Canonical Ingredient Dataset (Approval Gate)
Objective:
- Define a single, enforceable source of truth for canonical ingredients and aliases.

Required Artifact + Ownership:
- Dataset path: `pantrypal/data/canonical_ingredients.json`
- Validator/report path (planning target): `pantrypal/tests` validator outputs
- Ownership: backend data contract (normalization + matching consumers)

Contract Additions:
- `id` required, unique, regex-enforced: `^ing_[0-9]{4,}$`
- `canonical_name` required, unique, pre-normalized (lowercase, trimmed, single-space)
- `aliases` required array:
	- may be empty only with explicit justification in review note
	- all alias entries must be pre-normalized (lowercase, trimmed, single-space)
	- no duplicate aliases within a record
	- aliases globally unique across all aliases and all canonical names

Validator Acceptance (hard-fail):
- invalid `id` format
- duplicate `id`
- duplicate `canonical_name`
- alias collision (alias used by multiple records)
- alias equals a different record's canonical name
- invalid casing/spacing normalization

Versioning Rule:
- Dataset carries `version` and `last_updated` metadata (or companion changelog entry).
- Every dataset edit requires:
	1. validator pass
	2. edge-case coverage matrix re-check
	3. version bump note

Exit Criteria (revised):
- All contract rules pass validator with zero blocking failures.
- Version/change-control evidence is recorded.
- Dataset approved as sole mapping source.

---

#### Phase 1: Deterministic Normalization Contract
Objective:
- Freeze a strict, fully deterministic normalization specification with no implementation-time interpretation.

Unified Internal Output Schema (single definition):
```
{
	raw: string,
	normalized: string,
	canonical_name: string | null,
	canonical_id: string | null
}
```

API-level rule remains:
- `normalized_ingredients: string[]` where each entry is:
	- `canonical_name` if present
	- otherwise `normalized`

Frozen v1 Pipeline (strict order):
1. Trim + lowercase
2. Protect known multi-word phrases (dataset-driven phrase lookup set)
3. Punctuation transform using fixed policy table
4. Descriptor removal using frozen descriptor lexicon
5. Whitespace normalization (collapse multi-space to single)
6. Singularization using fixed strategy (irregular map first, then suffix rules)
7. Full-phrase matching precedence:
	 - exact canonical_name match
	 - exact alias match
	 - else unmapped (`canonical_id = null`, `canonical_name = null`)
8. Deduplicate after normalization/mapping

No partial-token guessing rule:
- Token-level inference is disallowed for mapping decisions.
- If full-phrase lookup fails, return unmapped fallback.

Punctuation Transformation Table (v1):
- Replace with single space: `-`, `/`, `,`, `.`, `(`, `)`, `:`, `;`, `&`
- Remove apostrophes only: `'`
- Preserve alphanumeric characters and spaces

Frozen Descriptor Lexicon (v1):
- `fresh`, `chopped`, `diced`, `sliced`, `organic`, `large`, `small`, `extra`, `virgin`
- No `etc.` expansion allowed without Phase 1 spec update review

Singularization Strategy (v1):
- Step A: irregular map exact replacements (e.g., `tomatoes -> tomato`, `potatoes -> potato`, `leaves -> leaf`, `knives -> knife`, `loaves -> loaf`)
- Step B: deterministic suffix rules in order:
	- `ies -> y`
	- `oes -> o`
	- trailing `s` removal except protected endings (`ss`, `us`)
- Step C: if rule would produce empty/invalid token, keep prior value

Tie/Collision Behavior:
- Tie should be impossible after Phase 0 global uniqueness rules.
- If encountered, mapping hard-fails validation path (not runtime guessing).

Exit Criteria (revised):
- Pipeline spec contains zero ambiguous language.
- Edge-case set explicitly mapped to expected outcomes.
- Contract aligned across planning docs with one internal schema definition.

---

#### Phases 2-7 (unchanged architecture, tightened gates)
- Phase 2 Matching: continue canonical-only matching; block progression if raw-string fallback appears in core logic.
- Phase 3 Retrieval: require at least one canonical overlap; maintain meal-quality constraints.
- Phase 4 Scoring: preserve overlap ratio and missing-ingredient penalties; add stable tie-break rule.
- Phase 5 API: enforce schema checks against unified normalization contract.
- Phase 6 Frontend: map sections strictly to on-hand vs related partitions.
- Phase 7 Testing: include explicit contract tests for Phase 0 validator and Phase 1 deterministic pipeline.

### B) Re-Submission Readiness Checklist
- Canonical artifact path and ownership are now explicit.
- Schema strictness and fail-fast validation rules are now explicit.
- Dataset versioning/re-validation gate is now explicit.
- Phase 1 descriptor, punctuation, singularization, precedence, and no-guessing rules are now explicit.
- Output schema conflict is resolved to one internal definition.

## Non-Implementation Confirmation (Revision v2)
- No code written
- No dataset artifacts created or changed
- No tests executed
- Plan revised only, per request

---

## Phase 0 Implementation Review (2026-03-17)

Decision: **REJECT**

Review basis:
- Ingredient Normalization checklist in `ai-workflow/review_checklist.md`
- Implemented dataset: `pantrypal/data/canonical_ingredients.json`

### 1) Dataset Structure Correctness

Status: **PASS**

Validated:
- JSON structure present with top-level metadata + `ingredients[]`.
- 120 ingredient records present.
- Required per-record fields present (`id`, `canonical_name`, `aliases`).
- `id` format conforms to `^ing_[0-9]{4,}$` for all records.
- No duplicate `id` values.
- No duplicate `canonical_name` values.
- Lowercase/trimmed formatting appears consistent with spec.

### 2) Duplicate/Conflicting Mapping Audit

Status: **PASS (hard collision checks)**

Validated:
- No alias duplicates within a single record.
- No global alias collisions (same alias mapped to multiple canonicals).
- No alias that equals a different record's canonical name.

### 3) Multi-word Ingredient Handling

Status: **PARTIAL (blocker present)**

Validated present:
- Multi-word canonicals/aliases are represented (e.g., `olive oil`, `soy sauce`, `extra virgin olive oil`, `garlic cloves`).

Blocking gap:
- Required edge-case ingredient `ice cream` is not present as canonical or alias.
- Checklist requires this case to pass; missing coverage makes dataset incomplete for Phase 1 normalization guarantees.

### 4) Alias Quality and Coverage

Status: **PARTIAL (quality risk present)**

Findings:
- Coverage is broad across proteins, produce, grains, oils, and condiments.
- At least one alias is overly ambiguous against naming policy intent:
	- `pepper` -> `black pepper` while `bell pepper` exists as a separate canonical family.
	- This can cause deterministic but semantically wrong mappings for user inputs like "pepper".

### Checklist Outcome

- Deterministic/canonical mapping readiness: **mostly satisfied**
- No-guessing/collision safety: **satisfied**
- Required edge-case coverage: **NOT satisfied** (`ice cream` missing)
- Ambiguity control: **not fully satisfied** (`pepper` alias is too broad)

Final gate result:
- **REJECT** until the dataset is updated to include `ice cream` support and ambiguous aliases (starting with `pepper`) are corrected or explicitly disambiguated.

---

## Phase 0 Implementation Review Pass 3 (2026-03-17)

Decision: **REJECT**

Evidence reviewed:
- `pantrypal/data/canonical_ingredients.json`
- Ingredient Normalization checklist in `ai-workflow/review_checklist.md`

### Dataset Structure Correctness
- PASS: 120 records parsed successfully.
- PASS: all `id` values match `^ing_[0-9]{4,}$`.
- PASS: no duplicate `id` values.
- PASS: no duplicate `canonical_name` values.
- PASS: each record follows `id` + `canonical_name` + `aliases` structure.

### No Duplicate or Conflicting Mappings
- PASS: no alias collisions across canonical records.
- PASS: no duplicate alias repeated inside a record.
- PASS: no alias that equals a different canonical name.

### Multi-word Ingredient Handling
- PASS: key multi-word terms exist (`olive oil`, `soy sauce`, `extra virgin olive oil`, `garlic cloves`).
- FAIL (blocking): required checklist case `ice cream` is still missing (not present as canonical or alias).

### Alias Quality and Coverage
- PARTIAL: broad category coverage is present.
- FLAG: `pepper` is aliased to `black pepper` while `bell pepper` exists as a distinct canonical. This is deterministic but semantically ambiguous for user input `pepper`.

### Ingredient Normalization Checklist Gate
- Required edge-case coverage includes `ice cream -> ice cream`.
- Current dataset coverage result: `ice cream = false`.

Final gate result:
- **REJECT** due to incomplete required edge-case coverage and unresolved alias ambiguity risk.

---

## Phase 0 Implementation Update (2026-03-17)

Status:
- Phase 0 implemented.
- Scope limited to canonical ingredient dataset only.
- No normalization work started.

### Implemented Artifact
- Created dataset file: `pantrypal/data/canonical_ingredients.json`

### Schema Definition (Implemented)
Each canonical ingredient record uses:
- `id`: string identifier (`ing_0001` style)
- `canonical_name`: canonical ingredient phrase
- `aliases`: list of alternate phrases mapped to the same canonical ingredient

Dataset-level schema metadata included in the file:
- `id`: `string (regex: ^ing_[0-9]{4,}$)`
- `canonical_name`: `string (lowercase, trimmed, single-space)`
- `aliases`: `array of strings (lowercase, trimmed, single-space)`

### Initial Dataset Coverage
- Total canonical ingredients added: 120
- Categories covered:
	- proteins and seafood
	- vegetables and herbs
	- grains and staples
	- oils and fats
	- condiments, sauces, and spices

### Multi-word Ingredient Coverage (Examples)
- `olive oil`
- `soy sauce`
- `sweet potato`
- `bell pepper`
- `bok choy`
- `fish sauce`
- `coconut milk`
- `tomato paste`
- `apple cider vinegar`
- `maple syrup`

### Constraint Compliance
- Phase 0 only: completed
- Normalization pipeline: not started
- Matching/scoring/API/frontend/test phases: untouched

---

## Review Pass 2 (2026-03-17)

Decision: **APPROVE**

Scope reviewed:
- Phase 0 canonical dataset detail sufficiency
- Phase 1 normalization enforceability/determinism
- Remaining ambiguity/guessing gaps

### Phase 0 Verdict: Sufficiently detailed

Why it now passes:
- Canonical artifact path is explicit (`pantrypal/data/canonical_ingredients.json`).
- Contract constraints are concrete and testable (`id` regex, uniqueness, normalized casing/spacing rules).
- Alias policy is globally enforceable (global uniqueness across aliases and canonical names).
- Hard-fail validator criteria are explicit.
- Versioning and re-validation gates are explicit.

Residual non-blocking note:
- If metadata (`version`, `last_updated`) is stored outside the dataset file (companion changelog), keep one documented canonical location to avoid split-brain updates.

### Phase 1 Verdict: Enforceable and deterministic

Why it now passes:
- Pipeline order is frozen and explicit.
- Multi-word protection is now a formal pipeline step.
- Punctuation policy is explicit (replace/remove behavior defined).
- Descriptor lexicon is frozen (no open-ended "etc.").
- Singularization strategy is explicit (irregular map first, then ordered suffix rules).
- Matching precedence is explicit and deterministic.
- No-guessing rule is explicit (no token inference fallback for mapping).
- Internal output schema has been unified (`canonical_name: string | null`).

Residual non-blocking note:
- Ensure descriptor lexicon and irregular map are versioned artifacts (not inline constants scattered across modules) to preserve determinism across future edits.

### Ambiguity/Guessing Gap Check

Result:
- No blocking ambiguity remains in the planning contract for Phases 0 and 1.
- Remaining risks are implementation hygiene risks, not specification gaps.

Approval condition:
- Proceed to implementation only if validator + contract tests are created before or alongside Phase 1 code.

---

## Phase 0 Execution Record (2026-03-17, User Request)

Status:
- Implemented Phase 0 only.
- Did not proceed to normalization.

### Deliverable 1: Schema Defined
Implemented schema in dataset artifact with required fields:
- `id`
- `canonical_name`
- `aliases`

Location:
- `pantrypal/data/canonical_ingredients.json`

### Deliverable 2: Initial Dataset Created
- Canonical ingredient records present: **120**
- Meets requirement of at least 50-100 ingredients (and includes more for broader canonical coverage).

### Deliverable 3: Category Diversity Included
Dataset includes diverse categories, including:
- proteins/seafood (e.g., chicken, beef, salmon, tofu)
- vegetables/herbs (e.g., onion, tomato, broccoli, cilantro)
- oils/fats (e.g., olive oil, vegetable oil, sesame oil)
- condiments/sauces/spices (e.g., soy sauce, fish sauce, mustard, cumin)

### Deliverable 4: Multi-word Ingredients Included
Representative multi-word entries included:
- `soy sauce`
- `olive oil`
- `sweet potato`
- `bell pepper`
- `apple cider vinegar`
- `worcestershire sauce`

### Constraint Confirmation
- Normalization phase was not started.
- No Phase 1+ implementation was performed in this step.

---

## Phase 1 Implementation Review (2026-03-17)

Decision: **REJECT**

Scope reviewed:
- Pipeline order correctness
- No guessing / no semantic shortcuts
- Proper canonical dataset usage
- Required edge-case handling

Evidence:
- Implementation: `pantrypal/app/utils/normalization.py`
- Tests: `pantrypal/tests/test_normalization.py`
- Command: `"/Users/maccalledmonds/ML Projects/GroceryGuru/.venv/bin/python" -m pytest -q pantrypal/tests/test_normalization.py`

### 1) Pipeline Order Correctness

Status: **PASS (with one spec-alignment note)**

Observed order in code:
1. trim + lowercase
2. punctuation removal
3. descriptor removal
4. whitespace normalization
5. singularization
6. canonical/alias lookup

This is deterministic and consistent with the earlier strict-order implementation intent.

### 2) No Guessing / No Semantic Shortcuts

Status: **PASS**

Validated:
- No LLM, embeddings, or fuzzy similarity used in normalization path.
- Mapping is exact phrase lookup against canonical dataset index.
- Unknown ingredients correctly fallback to cleaned normalized text with `canonical_id = null`.

### 3) Proper Dataset Usage

Status: **PASS**

Validated:
- Canonical mappings are loaded from `canonical_ingredients.json`.
- Alias/canonical collisions are detected and fail fast during index construction.

### 4) Required Edge Case Handling

Status: **FAIL (blocking)**

Required cases tested:
- `Fresh Tomatoes -> tomato` : pass
- `garlic cloves -> garlic` : **fail**
- `extra virgin olive oil -> olive oil` : pass
- `soy sauce -> soy sauce` : pass
- `ice cream -> ice cream` : pass

Blocking failure detail:
- `normalize_ingredient("garlic cloves")` returns normalized `garlic clove` with `canonical_name = None`.
- Result does not map to canonical `garlic`, violating required normalization case.
- Unit tests confirm this failure (`2 failed, 6 passed`), including:
	- `test_normalize_required_edge_cases`
	- `test_normalize_ingredient_internal_contract_when_mapped`

Final gate result:
- **REJECT** until required edge-case mapping is fixed and normalization tests pass fully.

---

## Phase 1 Implementation Update (2026-03-17)

Status:
- Implemented Phase 1: Ingredient Normalization System.
- Deterministic, dataset-driven normalization only.

### Implemented Components

1. Normalization function:
- Added `normalize_ingredient(raw_ingredient: str) -> NormalizedIngredient`
- Added deterministic output contract fields:
	- `raw`
	- `normalized`
	- `canonical_name`
	- `canonical_id`

2. Alias lookup logic:
- Implemented canonical index loader from `pantrypal/data/canonical_ingredients.json`
- Built full-phrase lookup map across:
	- `canonical_name`
	- `aliases[]`
- Enforced collision-safe behavior during index load:
	- raises hard error on alias/canonical collisions

3. Multi-word ingredient handling:
- Full phrase lookup is primary behavior (no token-level guessing)
- Multi-word ingredients map deterministically from canonical dataset
	(examples supported by dataset: `soy sauce`, `olive oil`, `ice cream`)

### Pipeline Implemented (Exact Order)
For each ingredient:
1. trim + lowercase
2. remove punctuation
3. remove descriptors (`fresh`, `chopped`, `diced`, `sliced`, `organic`, `large`, `small`, `extra`, `virgin`)
4. normalize whitespace
5. singularize tokens (irregular map + deterministic suffix rules)
6. alias/canonical full-phrase match against canonical dataset
7. canonical mapping if found, otherwise deterministic fallback (`canonical_id = null`)

### Determinism and Constraints
- No LLM usage in normalization.
- No embeddings/semantic matching.
- No FAISS usage.
- No fuzzy matching.
- Deduplication occurs after normalization in `normalize_ingredients`.

### Files Updated
- `pantrypal/app/config.py`
	- added `CANONICAL_INGREDIENTS_PATH`
- `pantrypal/app/utils/normalization.py`
	- replaced fuzzy/spaCy pipeline with deterministic canonical mapping pipeline
- `pantrypal/tests/test_normalization.py`
	- updated tests for required edge cases and deterministic contract behavior

### Validation Note
- Static diagnostics report no code errors.
- Runtime test execution command `pytest` is unavailable in current environment (`command not found`).

---

## Phase 0 Implementation Review Pass 4 (2026-03-17)

Decision: **APPROVE**

Review scope (Ingredient Normalization checklist):
- Dataset structure correctness
- Alias quality and coverage
- Duplicate/conflicting mapping checks
- Multi-word ingredient handling

### Dataset Structure Correctness
- PASS: dataset file is valid JSON with schema metadata and `ingredients[]`.
- PASS: 121 canonical records present.
- PASS: all `id` values match `^ing_[0-9]{4,}$`.
- PASS: no duplicate `id` values.
- PASS: no duplicate `canonical_name` values.

### Duplicate or Conflicting Mappings
- PASS: no duplicate aliases within any single record.
- PASS: no cross-record alias collisions.
- PASS: no alias that equals a different record's canonical name.

### Multi-word Ingredient Handling
- PASS: required multi-word ingredients are represented.
- Verified edge-case coverage required by checklist:
	- `tomatoes` present
	- `garlic cloves` present
	- `extra virgin olive oil` present
	- `soy sauce` present
	- `ice cream` present

### Alias Quality and Coverage
- PASS: previously ambiguous alias risk was reduced (`pepper` alias is no longer present under `black pepper`).
- PASS: broad category coverage remains intact while preserving canonical uniqueness constraints.

Final gate result:
- **APPROVE** Phase 0 dataset for progression to Phase 1 normalization implementation.

---

## Phase 1 Implementation Update (Final, 2026-03-17)

Status:
- Phase 1 implemented and validated.
- Deterministic normalization pipeline in place using canonical dataset from Phase 0.

### Implemented (Phase 1 Only)

1. Normalization function
- Implemented in `pantrypal/app/utils/normalization.py`:
	- `normalize_ingredient(raw_ingredient: str) -> NormalizedIngredient`
	- `normalize_ingredients(ingredients: list[str]) -> list[str]`

2. Alias lookup logic
- Canonical data source: `pantrypal/data/canonical_ingredients.json`
- Built deterministic canonical index from:
	- `canonical_name`
	- `aliases[]`
- Added fail-fast collision checks at index-build time.

3. Multi-word ingredient handling
- Phrase-level lookup is primary and deterministic.
- Supported examples include:
	- `soy sauce`
	- `olive oil`
	- `ice cream`

### Pipeline Compliance (Exact Order)
Implemented order for each ingredient:
1. trim + lowercase
2. remove punctuation
3. descriptor removal
4. whitespace normalization
5. singularization
6. alias/canonical matching
7. canonical mapping or deterministic fallback (`canonical_id = null`)

### Determinism and Prohibited Methods
- No LLM usage in normalization path.
- No embeddings.
- No FAISS.
- No fuzzy matching.

### Blocking Bug Fixed During Validation
- Issue: `garlic cloves` was singularized to `garlic clove` and failed alias lookup.
- Fix: canonical index now stores dataset phrases in the same deterministic lookup-normalized form used for input, preserving strict pipeline semantics while ensuring alias matches after singularization.

### Validation Result
- Command executed:
	- `"/Users/maccalledmonds/ML Projects/GroceryGuru/.venv/bin/python" -m pytest -q pantrypal/tests/test_normalization.py`
- Result: `8 passed`

### Scope Confirmation
- Only Phase 1 normalization system was implemented/adjusted.
- No progression to retrieval/scoring/API/frontend phases in this step.

---

## Phase 1 Implementation Review Pass 2 (2026-03-17)

Decision: **APPROVE**

Review focus:
- Pipeline order correctness
- No guessing / semantic shortcuts
- Proper dataset usage
- Required normalization edge cases

Evidence checked:
- Implementation: `pantrypal/app/utils/normalization.py`
- Tests: `pantrypal/tests/test_normalization.py`
- Test command: `"/Users/maccalledmonds/ML Projects/GroceryGuru/.venv/bin/python" -m pytest -q pantrypal/tests/test_normalization.py`

### 1) Pipeline Order Correctness
- PASS: code executes deterministic order:
	1. trim + lowercase
	2. punctuation removal
	3. descriptor removal
	4. whitespace normalization
	5. singularization
	6. alias/canonical lookup
	7. canonical mapping or fallback

### 2) No Guessing / Semantic Shortcuts
- PASS: no LLM, embeddings, FAISS, or fuzzy matching in normalization flow.
- PASS: unknown ingredients fallback to cleaned normalized string with `canonical_id = null`.

### 3) Proper Dataset Usage
- PASS: canonical and alias mappings are loaded from `pantrypal/data/canonical_ingredients.json`.
- PASS: canonical index build performs fail-fast collision checks.

### 4) Required Edge Cases
- PASS: required cases produce expected outputs:
	- `Fresh Tomatoes -> tomato`
	- `garlic cloves -> garlic`
	- `extra virgin olive oil -> olive oil`
	- `soy sauce -> soy sauce`
	- `ice cream -> ice cream`

Test result:
- `8 passed` in `pantrypal/tests/test_normalization.py`

Final gate result:
- **APPROVE** (no rule violations observed in this review pass).

---

## Strict Review Pass (2026-03-17, run_review)

Latest developer phase identified:
- **Phase 1 Implementation Update (Final, 2026-03-17)**

Review scope (strict):
- ingredient matching correctness
- edge cases (empty pantry, partial matches)
- data assumptions
- API structure
- code quality
- reject if canonical dataset or normalization incomplete

Canonical/normalization gate:
- Canonical dataset: complete for required edge cases.
- Normalization implementation: deterministic and currently passing required normalization tests.
- Normalization incompleteness trigger: **NOT triggered**.

## Issues

### Critical

1) API accepts dietary filters but does not apply them in hybrid recommendations
- In `backend/main.py`, request `filters` are validated but not propagated to hybrid ranking path.
- `HybridRecommendationEngine.recommend_recipes(...)` currently has no `filters` parameter, so API filter input is effectively ignored.
- Impact: response contract appears to support filters, but runtime behavior violates expectation and can return non-compliant recipes.

2) Downstream matching is not strictly canonical-only in all paths
- In `pantrypal/app/utils/scoring.py` and `pantrypal/app/utils/database_engine.py`, matching uses `recipe.ingredients_normalized or recipe.ingredients`.
- This introduces fallback to raw ingredient strings when normalized fields are absent.
- Impact: violates strict canonical-only matching rule from review checklist (raw fallback path remains possible).

### Medium

1) Generated recipe scoring path is not canonicalized before overlap scoring
- In `pantrypal/app/utils/ranking.py`, generated ingredient overlap is computed from lowercased raw strings.
- No canonical remap is enforced before scoring.
- Impact: partial overlap quality can drift when generated terms are valid but non-canonical variants.

2) Missing tests for critical API filter behavior
- Existing backend tests validate response shape/latency but do not assert that `filters` alter result set.
- Impact: contract drift can persist without failing CI.

### Minor

1) Data-quality assumption is implicit
- Matching quality assumes `ingredients_normalized` in recipe data is canonical and consistently maintained.
- No explicit runtime/assertion check guards this assumption.

## Required Fixes

1) Propagate dietary filters through hybrid path
- Add `filters` parameter to `HybridRecommendationEngine.recommend_recipes(...)`.
- Apply filters to database retrieval/ranking path before final partitioning.
- Add integration test proving `filters=["vegan"]` returns only vegan-tagged recipes.

2) Enforce canonical-only matching in downstream logic
- Remove raw fallback (`or recipe.ingredients`) from matching/scoring paths used for recommendation ranking.
- Ensure recipes are pre-normalized/canonicalized (or canonicalize at load/index time with a strict validation gate).

3) Canonicalize generated recipe ingredients before overlap scoring
- Normalize+canonical-map generated ingredient lists before computing on-hand overlap score.
- Add test with alias variant inputs to prove deterministic canonical overlap.

4) Add guardrail tests for strict rules
- Empty pantry behavior (already present) should remain.
- Partial-match behavior should assert canonical overlap semantics, not only presence of any overlap.
- Add regression test asserting no raw-string fallback in ranking/matching decisions.

## Final Decision

**REJECTED**

Reason:
- Blocking violations exist in API filter behavior and canonical-only matching integrity, which fail strict review criteria despite Phase 1 normalization itself passing.

---

## Strict Review Pass 2 (2026-03-17, run_review)

Latest developer phase identified:
- **Phase 2 Feedback Remediation (Current-Phase Strict Review Fixes)**

Review scope:
- ingredient matching correctness
- edge cases (empty pantry, partial matches)
- data assumptions
- API structure
- code quality
- reject if canonical dataset or normalization incomplete

Validation evidence:
- Canonical dataset + normalization required cases present and passing.
- Test suite executed:
	- `pantrypal/tests/test_normalization.py`
	- `pantrypal/tests/test_hybrid_engine.py`
	- `pantrypal/tests/test_scoring.py`
	- `pantrypal/tests/test_ranking.py`
	- `backend/tests/test_recommend_ai_integration.py`
	- `backend/tests/test_recommend_latency.py`
- Result: **20 passed**

## Issues

### Critical
- None.

### Medium
1) Dietary filter enforcement is complete for database retrieval path, but generated recipe filter compliance remains a known assumption/risk.
- API now propagates filters into hybrid/database flow.
- Generated items are not explicitly post-filtered by dietary tags in this phase.

### Minor
1) Canonicalization-at-runtime dependency
- Matching correctness depends on runtime canonicalization when recipe normalized fields are absent.
- This is acceptable, but data-quality drift would be easier to detect with an explicit data validation check during load.

## Required Fixes

1) Add generated-result dietary compliance gate (or post-filter)
- Ensure `filters` are enforced consistently across both database and generated outputs.

2) Add a recipe-data canonical integrity check
- During recipe load/index warm-up, verify normalized ingredients are canonical or auto-canonicalize with explicit warning metrics.

## Final Decision

**APPROVED**

Reason:
- No critical rule violations remain.
- Canonical dataset and normalization are complete and validated.
- Ingredient matching, edge-case handling, API structure, and code quality meet current-phase strict acceptance criteria.

---

## Phase
Phase 2 Feedback Remediation (Current-Phase Strict Review Fixes)

## Summary
- Reviewer feedback existed for the current phase, so all listed blocking items were addressed before moving forward.
- Implemented filter propagation from API request to hybrid recommendation engine and into database retrieval.
- Removed raw-string fallback from matching/scoring paths by canonicalizing recipe ingredients when pre-normalized fields are absent.
- Canonicalized generated recipe ingredients before overlap scoring in ranking.
- Added regression tests for filter propagation and canonical overlap behavior.
- Validation run passed: `20 passed`.

## Files changed
- `backend/main.py`
- `backend/tests/test_recommend_ai_integration.py`
- `backend/tests/test_recommend_latency.py`
- `pantrypal/app/utils/database_engine.py`
- `pantrypal/app/utils/hybrid_engine.py`
- `pantrypal/app/utils/ranking.py`
- `pantrypal/app/utils/scoring.py`
- `pantrypal/tests/test_ranking.py`

## Assumptions
- If `recipe.ingredients_normalized` is missing, canonicalizing raw recipe ingredients at load/score time is acceptable and preferred over raw-string matching.
- Applying dietary filters to database retrieval is sufficient for API filter correctness in this phase.
- Existing LLM output remains untrusted for exact overlap scoring until canonicalized in ranking.

## Any uncertainties
- Database filtering currently relies on `diet_tags` quality in recipe data; incorrect tags could still produce noisy filtered results.
- Generated-recipe dietary compliance is not fully enforced in this phase when filters are applied (LLM output may still require stricter post-filtering in a future phase).

---

## Phase
Phase 2 Feedback Remediation Pass 2 (Current-Phase Reviewer Follow-Ups)

## Summary
- Reviewer feedback existed for the current phase (Strict Review Pass 2 medium items), and both items were addressed in this pass.
- Added a generated-result dietary compliance gate so generated recipes are filtered by requested dietary tags before partitioning.
- Added canonical integrity validation/auto-canonicalization for recipe normalized ingredient fields during database index preparation.
- Kept scope to one phase only (current-phase feedback remediation).
- Validation suite passed: `22 passed`.

## Files changed
- `pantrypal/app/utils/database_engine.py`
- `pantrypal/app/utils/hybrid_engine.py`
- `pantrypal/app/utils/ranking.py`
- `pantrypal/tests/test_hybrid_engine.py`
- `pantrypal/tests/test_database_engine.py`

## Assumptions
- Generated recipes without explicit `diet_tags` should not pass non-empty filter requests.
- Auto-canonicalization of recipe normalized ingredient values at index/score time is acceptable to preserve strict canonical matching guarantees.

## Any uncertainties
- Generated recipe dietary tag quality depends on upstream generation behavior; strict post-generation tag assignment rules may still be needed for stronger guarantees.
- Canonical integrity logging currently reports normalization/canonicalization activity but does not yet export structured metrics.

---

## Phase
Phase 2 Feedback Remediation Pass 3 (Current-Phase Reviewer Feedback)

## Summary
- Reviewer feedback existed for the current phase (Strict Review Pass 3 required fixes), and both remaining items were addressed.
- Added structured canonical integrity metrics during recipe index warm-up, including indexed recipe count, repaired-recipe count, canonicalized values, and unknown values.
- Added stronger generated dietary-filter guarantees by deterministic ingredient-based diet-tag inference when explicit `diet_tags` are sparse/missing.
- Kept scope to one phase only (current-phase feedback remediation).
- Validation suite passed: `26 passed`.

## Files changed
- `pantrypal/app/utils/database_engine.py`
- `pantrypal/app/utils/ranking.py`
- `pantrypal/tests/test_database_engine.py`
- `pantrypal/tests/test_ranking.py`

## Assumptions
- Deterministic ingredient-hint inference is an acceptable post-generation validation policy for dietary filtering when explicit tags are absent.
- Structured log-exported metrics satisfy current observability needs for canonical integrity during warm-up.

## Any uncertainties
- Heuristic dietary inference can still misclassify edge cases for complex ingredient phrases not covered by hint sets.
- Metrics are exported as structured log/state data; if external telemetry is required later, an explicit metrics sink may still be needed.

---

## Phase
Phase 3: Similar Recipe Retrieval

## Summary
- No unresolved reviewer feedback existed for the latest phase, so the next phase was implemented.
- Implemented similar-recipe quality gates in database retrieval to better satisfy Phase 3 requirements:
	- kept canonical-overlap requirement (minimum 1 overlap already enforced by scoring gate)
	- excluded obvious non-meal/trivial candidates (e.g., sauce/drink-like titles, very low-ingredient recipes)
- Preserved deterministic ranking by overlap and missing ingredients.
- Added deterministic tests for non-meal exclusion and ranking behavior.
- Validation suite passed: `28 passed`.

## Files changed
- `pantrypal/app/utils/database_engine.py`
- `pantrypal/tests/test_database_engine.py`

## Assumptions
- Title-keyword and minimum-ingredient heuristics are an acceptable first-pass implementation for avoiding condiments/drinks/trivial similar recommendations.
- Existing overlap + missing-ingredient scoring remains the correct ranking foundation for this phase.

## Any uncertainties
- Some valid recipes could be filtered out by non-meal title heuristics if naming is unusual.
- Meal-quality gating is currently heuristic-based; a future data-driven classifier/rule table may improve precision and recall.

---

## Phase
Phase 4: Scoring System

## Summary
- No unresolved reviewer feedback existed for the latest phase, so the next phase was implemented.
- Implemented Phase 4 scoring formula alignment in core scoring paths:
	- base score uses overlap ratio: `matched / total required ingredients`
	- score is reduced by a missing-ingredient penalty
- Updated both recipe scoring and generated ranking scoring to follow this model deterministically.
- Added explicit tests for formula correctness and missing-penalty behavior.
- Validation suite passed: `30 passed`.

## Files changed
- `pantrypal/app/utils/scoring.py`
- `pantrypal/app/utils/ranking.py`
- `pantrypal/tests/test_scoring.py`
- `pantrypal/tests/test_ranking.py`

## Assumptions
- The existing penalty caps are acceptable for Phase 4 as long as the base formula remains `matched / total required`.
- Keeping `coverage` as the unpenalized overlap ratio is useful for transparency while `score` is the penalized ranking value.

## Any uncertainties
- Penalty constants may need calibration against user feedback to avoid over-penalizing otherwise good partial matches.
- Generated recipe ingredient lists may vary in granularity, which can influence denominator size and therefore relative score.

---

## Phase
Phase 5: API Layer

## Summary
- No unresolved reviewer feedback existed for the latest phase, so the next phase was implemented.
- Hardened API request handling for recommendation endpoints:
	- normalized dietary filters to lowercase
	- removed duplicate filters before downstream execution
	- kept strict rejection for unsupported filters
	- preserved empty/whitespace ingredient rejection
- Ensured downstream hybrid path receives normalized filter values.
- Added API validation and response-contract tests for fallback metadata and request validation behavior.
- Validation suite passed: `34 passed`.

## Files changed
- `backend/main.py`
- `backend/tests/test_recommend_validation.py`

## Assumptions
- Filter normalization to lowercase is the intended API contract behavior for user-provided filter values.
- Deduplicating repeated filters before execution is safe and does not change semantic intent.

## Any uncertainties
- If clients rely on strict case-sensitive filter rejection, lowercase normalization may be broader than previously expected behavior.
- API response contract remains aligned to `on_hand_recipes`/`related_recipes`; if a legacy `exact`/`similar` schema is required externally, a compatibility layer may still be needed.

---

## Phase
Phase 6: Frontend Integration

## Summary
- No unresolved reviewer feedback existed for the latest phase, so the next phase was implemented.
- Updated frontend results presentation to match required two-section UX:
	- `Cook Now` for on-hand/exact-style results
	- `Almost There` for similar/related results with missing ingredients
- Kept existing API mapping unchanged (`on_hand_recipes` -> Cook Now, `related_recipes` -> Almost There).
- Preserved existing loading, fallback, and empty-state behaviors.

## Files changed
- `frontend/src/App.tsx`

## Assumptions
- Renaming and clarifying section headings/subtitles is sufficient for Phase 6 integration in this pass, given backend partitions are already wired and tested.
- Existing card-level rendering of missing ingredients and scores already satisfies the core “why suggested” UX requirement.

## Any uncertainties
- There are no frontend automated tests in this workspace validating heading text/content mapping, so this phase was verified by code-path consistency rather than UI test assertions.
- If product copy requirements are stricter, wording for the section subtitles may need final stakeholder review.

---

## Phase
Phase 7: Testing & Edge-Case Hardening

## Summary
- No unresolved reviewer feedback existed for the latest phase, so the next phase was implemented.
- Added dedicated Phase 7 edge-case tests for required reliability scenarios:
	- empty pantry rejection
	- large ingredient list handling
	- unknown ingredient fallback behavior
	- ambiguous ingredient non-forced mapping (`pepper`)
	- no-overlap retrieval guard (requires at least one overlap)
- Executed edge-case tests plus existing regression suite.
- Validation suite passed: `39 passed`.

## Files changed
- `pantrypal/tests/test_phase7_edge_cases.py`

## Assumptions
- Treating ambiguous input like `pepper` as unmapped (rather than forcing a canonical) is the correct deterministic behavior under current alias policy.
- Current test-level coverage is sufficient to close the listed Phase 7 requirements for this implementation cycle.

## Any uncertainties
- Large-list testing currently validates correctness and stability but does not enforce explicit latency thresholds under load.
- Additional ambiguity families beyond `pepper` may still need expanded test fixtures if future dataset aliases become broader.

---

## Strict Review Pass 3 (2026-03-17, run_review)

Latest developer phase identified:
- **Phase 2 Feedback Remediation Pass 2 (Current-Phase Reviewer Follow-Ups)**

Review strict scope:
- Ingredient matching correctness
- Edge cases (empty pantry, partial matches)
- Data assumptions
- API structure
- Code quality
- Reject if canonical dataset or normalization incomplete

Validation evidence:
- Canonical dataset and normalization are complete and validated.
- Full review suite executed and passing:
	- `pantrypal/tests/test_normalization.py`
	- `pantrypal/tests/test_hybrid_engine.py`
	- `pantrypal/tests/test_scoring.py`
	- `pantrypal/tests/test_ranking.py`
	- `pantrypal/tests/test_database_engine.py`
	- `backend/tests/test_recommend_ai_integration.py`
	- `backend/tests/test_recommend_latency.py`
- Result: **all passing** (`22 passed` in latest expanded run; `20 passed` in prior strict run)

## Issues

### Critical
- None.

### Medium
1) Generated recipe filtering depends on presence/quality of `diet_tags` in generated outputs.
- Behavior is now safe by default (untagged generated items are excluded when filters are requested), but recommendation recall may drop when tags are absent/low quality.

### Minor
1) Canonical integrity observability is log-only.
- Canonical repair/validation happens, but structured counters/metrics are not exported for monitoring.

## Required fixes

1) Add structured canonical integrity metrics
- Export counts for canonicalized/unknown recipe ingredient values during index warm-up.

2) Strengthen generated diet-tag guarantees
- Add generation-time constraints or post-generation validation policy so filtered requests retain quality/recall without relying on sparse tags.

## Final Decision

**APPROVED**

Reason:
- No checklist-blocking violations remain.
- Ingredient matching is deterministic/canonicalized across normalization, scoring, database retrieval, and generated overlap ranking.
- Edge-case coverage and API contract behavior are validated by passing tests.

---

## Strict Review Pass 4 (2026-03-17, run_review)

Latest developer phase identified:
- **Phase 2 Feedback Remediation Pass 3 (Current-Phase Reviewer Feedback)**

Strict review scope:
- Ingredient matching correctness
- Edge cases (empty pantry, partial matches)
- Data assumptions
- API structure
- Code quality
- Reject if canonical dataset or normalization incomplete

Validation evidence:
- Canonical dataset and deterministic normalization remain complete.
- Full strict suite run:
	- `pantrypal/tests/test_normalization.py`
	- `pantrypal/tests/test_hybrid_engine.py`
	- `pantrypal/tests/test_scoring.py`
	- `pantrypal/tests/test_ranking.py`
	- `pantrypal/tests/test_database_engine.py`
	- `backend/tests/test_recommend_ai_integration.py`
	- `backend/tests/test_recommend_latency.py`
- Result: **26 passed**

## Issues

### Critical
- None.

### Medium
1) Dietary-filter inference for generated recipes is heuristic.
- Current implementation uses deterministic ingredient-hint rules when explicit tags are missing.
- This is safe and test-covered, but complex ingredient phrases can still be misclassified.

### Minor
1) Canonical integrity metrics are structured and accessible in-process, but external sink/export is not yet defined.

## Required fixes

1) Add targeted edge-case tests for heuristic dietary inference
- Include difficult/generated ingredient phrases to reduce false positives/negatives in filtered mode.

2) Define optional metrics export integration
- If operational observability is required, route canonical integrity metrics to the project's telemetry path.

## Final Decision

**APPROVED**

Reason:
- No checklist-blocking violations found.
- Matching, edge-case handling, data assumptions, API structure, and code quality satisfy strict acceptance criteria for the latest developer phase.

---

## Strict Review Pass 5 (2026-03-17, run_review)

Latest developer phase identified:
- **Phase 3: Similar Recipe Retrieval**

Review strict scope:
- Ingredient matching correctness
- Edge cases (empty pantry, partial matches)
- Data assumptions
- API structure
- Code quality
- If canonical dataset or normalization incomplete -> reject

Validation evidence:
- Canonical dataset and deterministic normalization remain complete and in use.
- Full strict suite executed on current code:
	- `pantrypal/tests/test_normalization.py`
	- `pantrypal/tests/test_hybrid_engine.py`
	- `pantrypal/tests/test_scoring.py`
	- `pantrypal/tests/test_ranking.py`
	- `pantrypal/tests/test_database_engine.py`
	- `backend/tests/test_recommend_ai_integration.py`
	- `backend/tests/test_recommend_latency.py`
- Result: **28 passed**

## Issues

### Critical
- None.

### Medium
1) Similar-recipe quality gates are heuristic-driven.
- Non-meal exclusion relies on title keyword hints and minimum ingredient-count threshold.
- This is deterministic and test-covered, but may over-filter uncommon valid meals or under-filter edge naming patterns.

### Minor
1) Dietary inference and meal-quality heuristics should continue to expand with observed production examples.
- Current behavior is stable and deterministic but rule coverage may need periodic refinement.

## Required fixes

1) Add targeted false-positive/false-negative fixtures for non-meal filtering
- Include unusual meal titles and edge condiment-like names to tune heuristics safely.

2) Extend heuristic regression set
- Add additional retrieval tests for borderline partial-overlap cases to preserve ranking quality as rules evolve.

## Final Decision

**APPROVED**

Reason:
- No checklist-blocking violations were found.
- Matching correctness, edge-case handling, data assumptions, API structure, and code quality meet strict acceptance criteria for the latest implemented phase.

---

## Strict Review Pass 6 (2026-03-17, run_review)

Latest developer phase identified:
- **Phase 4: Scoring System**

Strict review scope:
- Ingredient matching correctness
- Edge cases (empty pantry, partial matches)
- Data assumptions
- API structure
- Code quality
- If canonical dataset or normalization is incomplete -> reject

Validation evidence:
- Canonical dataset and normalization remain complete and deterministic.
- Full strict suite executed on latest code:
	- `pantrypal/tests/test_normalization.py`
	- `pantrypal/tests/test_hybrid_engine.py`
	- `pantrypal/tests/test_scoring.py`
	- `pantrypal/tests/test_ranking.py`
	- `pantrypal/tests/test_database_engine.py`
	- `backend/tests/test_recommend_ai_integration.py`
	- `backend/tests/test_recommend_latency.py`
- Result: **30 passed**

## Issues

### Critical
- None.

### Medium
1) Scoring parameter calibration remains heuristic.
- Missing-ingredient penalties and caps are deterministic and tested, but may still require empirical tuning for best ranking quality in production.

### Minor
1) Score field semantics can be clarified further across response consumers.
- `coverage` is unpenalized overlap ratio while `score` is penalized ranking value; ensure frontend/docs consistently reflect that distinction.

## Required fixes

1) Add calibration benchmark fixtures
- Introduce a small locked benchmark set to detect quality regressions when tuning penalty constants.

2) Document score semantics in API contract notes
- Explicitly define `coverage` vs `score` interpretation for downstream consumers.

## Final Decision

**APPROVED**

Reason:
- No checklist-blocking violations found.
- Ingredient matching, edge-case handling, data assumptions, API structure, and code quality satisfy strict acceptance criteria for the latest developer phase.

---

## Strict Review Pass 7 (2026-03-17, run_review)

Latest developer phase identified:
- **Phase 5: API Layer**

Strict review scope:
- Ingredient matching correctness
- Edge cases (empty pantry, partial matches)
- Data assumptions
- API structure
- Code quality
- If canonical dataset or normalization is incomplete -> reject

Validation evidence:
- Canonical dataset and normalization remain complete and deterministic.
- Strict suite executed including API validation tests:
	- `backend/tests/test_recommend_ai_integration.py`
	- `backend/tests/test_recommend_latency.py`
	- `backend/tests/test_recommend_validation.py`
	- `pantrypal/tests/test_normalization.py`
	- `pantrypal/tests/test_hybrid_engine.py`
	- `pantrypal/tests/test_scoring.py`
	- `pantrypal/tests/test_ranking.py`
	- `pantrypal/tests/test_database_engine.py`
- Result: **34 passed**

## Issues

### Critical
- None.

### Medium
1) API filter normalization broadens accepted client input shape.
- Lowercasing + deduplication is deterministic and tested, but may differ from strict legacy case-sensitive client expectations.

### Minor
1) Legacy schema compatibility is still an integration consideration.
- Current contract uses `on_hand_recipes`/`related_recipes`; if any external client still expects `exact`/`similar`, a compatibility shim may be required.

## Required fixes

1) Publish explicit API contract note for filter normalization
- Document lowercase normalization and dedup semantics for `filters` in API docs/changelog.

2) Add compatibility check item for external consumers
- Verify all active clients are aligned to `on_hand_recipes`/`related_recipes` response keys.

## Final Decision

**APPROVED**

Reason:
- No checklist-blocking violations were found.
- Ingredient matching correctness, edge-case handling, data assumptions, API structure, and code quality satisfy strict acceptance criteria for the latest developer phase.

---

## Strict Review Pass 8 (2026-03-17, run_review)

Latest developer phase identified:
- **Phase 5: API Layer**

Review strict scope:
- Ingredient matching correctness
- Edge cases (empty pantry, partial matches)
- Data assumptions
- API structure
- Code quality
- If canonical dataset or normalization is incomplete -> reject

Validation evidence:
- Canonical dataset + normalization are complete and deterministic.
- Strict suite re-run on current state:
	- `backend/tests/test_recommend_ai_integration.py`
	- `backend/tests/test_recommend_latency.py`
	- `backend/tests/test_recommend_validation.py`
	- `pantrypal/tests/test_normalization.py`
	- `pantrypal/tests/test_hybrid_engine.py`
	- `pantrypal/tests/test_scoring.py`
	- `pantrypal/tests/test_ranking.py`
	- `pantrypal/tests/test_database_engine.py`
- Result: **34 passed**

## Issues

### Critical
- None.

### Medium
1) Filter normalization behavior should remain explicitly documented for client teams.
- API lowercases and deduplicates `filters`; this is deterministic and tested but can differ from assumptions in legacy clients.

### Minor
1) Response-key compatibility remains a migration check item.
- Contract is stable as `on_hand_recipes` + `related_recipes`; external clients expecting older naming need explicit verification.

## Required fixes

1) Keep API behavior notes updated
- Maintain changelog/docs entries for filter normalization and dedup semantics.

2) Keep compatibility checklist active
- Verify all consumers are aligned with current response keys and fallback metadata fields.

## Final Decision

**APPROVED**

Reason:
- No strict-review blocking violations detected.
- Ingredient matching, edge-case handling, data assumptions, API structure, and code quality remain compliant for the latest developer phase.

---

## Strict Review Pass 9 (2026-03-17, run_review)

Latest developer phase identified:
- **Phase 7: Testing & Edge-Case Hardening**

Strict review scope:
- Ingredient matching correctness
- Edge cases (empty pantry, partial matches)
- Data assumptions
- API structure
- Code quality
- If canonical dataset or normalization is incomplete -> reject

Validation evidence:
- Canonical dataset and deterministic normalization are complete.
- Phase 7 edge-case suite plus full strict regression executed:
	- `pantrypal/tests/test_phase7_edge_cases.py`
	- `backend/tests/test_recommend_ai_integration.py`
	- `backend/tests/test_recommend_latency.py`
	- `backend/tests/test_recommend_validation.py`
	- `pantrypal/tests/test_normalization.py`
	- `pantrypal/tests/test_hybrid_engine.py`
	- `pantrypal/tests/test_scoring.py`
	- `pantrypal/tests/test_ranking.py`
	- `pantrypal/tests/test_database_engine.py`
- Result: **39 passed**

## Issues

### Critical
- None.

### Medium
1) Ambiguity coverage is currently exemplified by `pepper`; broader ambiguous-term families should be expanded over time.
- Behavior is deterministic and safe (no forced mapping), but dataset growth can introduce new ambiguous aliases.

### Minor
1) Large-list edge-case test validates correctness/stability but not explicit performance SLO thresholds.

## Required fixes

1) Expand ambiguity regression corpus
- Add additional ambiguous inputs beyond `pepper` to protect no-guessing guarantees as alias catalog grows.

2) Add optional performance threshold assertions for large inputs
- If required by product SLOs, define and test upper bounds for normalization/recommend latency on large ingredient lists.

## Final Decision

**APPROVED**

Reason:
- No checklist-blocking violations were found.
- Ingredient matching correctness, edge-case handling, data assumptions, API structure, and code quality satisfy strict acceptance criteria for the latest developer phase.