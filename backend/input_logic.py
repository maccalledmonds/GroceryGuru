from typing import List, Dict, Tuple, Optional
import csv
import re

# try to use RapidFuzz for speed; fall back to thefuzz if not installed
try:
    from rapidfuzz import fuzz as rfuzz
    from rapidfuzz import process as rprocess
    def _FUZZ_SCORE(a: str, b: str, score_cutoff=None):
        return rfuzz.token_set_ratio(a, b)
    _EXTRACT = rprocess.extract
except Exception:
    from thefuzz import fuzz as tfuzz
    from thefuzz import process as tprocess
    def _FUZZ_SCORE(a: str, b: str, score_cutoff=None):
        return tfuzz.token_set_ratio(a, b)
    _EXTRACT = tprocess.extract


class IngredientNormalizer:
    def __init__(self, csv_path: str = "standard_ingredients_list.csv"):
        # load ingredients and categories
        self.csv_path = csv_path
        self.standard_ingredients: List[str] = []
        self.ingredient_to_category: Dict[str, str] = {}
        with open(self.csv_path, newline="", encoding="utf-8") as file:
            reader = csv.reader(file)
            for row in reader:
                if not row:
                    continue
                name = row[0].strip().lower()
                category = row[1].strip().lower() if len(row) > 1 else ""
                if name:
                    self.standard_ingredients.append(name)
                    self.ingredient_to_category[name] = category

        # category priority to prefer base ingredients vs modifiers like sauces/condiments
        self.category_priority = {
            "protein": 10,
            "produce": 9,
            "fruit": 9,
            "vegetable": 9,
            "dairy": 8,
            "grain": 7,
            "baking": 6,
            "oil": 5,
            "condiment": 3,
            "seasoning": 4,
            "spread": 4,
            "sweetener": 4,
            "liquid": 4,
            "": 1,
        }

        # tokens that often indicate modifiers (use to de-prioritize matches containing only modifier)
        self.modifier_tokens = {"sauce", "paste", "salt", "sugar", "oil", "dressing", "powder", "extract", "mix"}

    def _normalize_text(self, text: str) -> str:
        text = text.lower().strip()
        text = re.sub(r"[^\w\s'-]", " ", text)  # remove punctuation
        text = re.sub(r"\s+", " ", text)
        return text

    def _tokens(self, text: str) -> List[str]:
        return [t for t in re.split(r"[\s\-]+", text) if t]

    def _category_score(self, ingredient: str) -> int:
        return self.category_priority.get(self.ingredient_to_category.get(ingredient, ""), 1)

    def _head_token_candidates(self, token: str) -> List[str]:
        # return standard ingredients where any token equals the given token
        tok = token.lower()
        matches = []
        for ing in self.standard_ingredients:
            ing_tokens = self._tokens(ing)
            if tok in ing_tokens:
                matches.append(ing)
        return matches

    def _rank_candidates(self, candidates: List[Tuple[str, int]]) -> List[Tuple[str, float]]:
        # candidates are (ingredient, fuzzy_score)
        ranked = []
        for ing, fuzz_score in candidates:
            category_score = self._category_score(ing)
            # combine fuzz score and category priority; adjust weights as needed
            combined = fuzz_score * 0.8 + category_score * 2.0
            # penalize if candidate is mostly a modifier (e.g., contains only modifier token)
            tokens = set(self._tokens(ing))
            if tokens & self.modifier_tokens and not (tokens - self.modifier_tokens):
                combined *= 0.6
            ranked.append((ing, combined))
        ranked.sort(key=lambda x: x[1], reverse=True)
        return ranked

    def normalize_ingredient(self, input_text: str, top_k: int = 3, score_cutoff: int = 60) -> List[Tuple[str, float]]:
        """
        Normalize user input and return ranked suggestions.
        Returns a list of (ingredient, score) sorted desc. If empty, return [].
        """
        raw = input_text
        text = self._normalize_text(raw)

        # 1) exact match
        if text in self.standard_ingredients:
            return [(text, 100.0)]

        # 2) token/head matches (e.g., "fish" -> candidates with token "fish")
        tokens = self._tokens(text)
        if tokens:
            # prefer longest/most specific token if multiword input
            primary = tokens[0] if len(tokens) == 1 else max(tokens, key=len)
            head_candidates = self._head_token_candidates(primary)
            if head_candidates:
                # score these candidates with fuzzy ratio to get best form + category boost
                cand_scores = []
                for cand in head_candidates:
                    fuzz_s = _FUZZ_SCORE(text, cand)
                    cand_scores.append((cand, fuzz_s))
                ranked = self._rank_candidates(cand_scores)
                # return top_k filtered by cutoff
                results = [(i, s) for i, s in ranked[:top_k] if (s - (self._category_score(i)*2.0)) >= score_cutoff*0.6]
                if results:
                    return results

        # 3) fuzzy fallback across all standard ingredients
        # use the library extract to get top fuzzy candidates
        raw_candidates = _EXTRACT(text, self.standard_ingredients, scorer=_FUZZ_SCORE, limit=top_k)
        # raw_candidates items differ between libraries; normalize to (ingredient, score)
        norm_candidates = []
        for item in raw_candidates:
            if isinstance(item, tuple) and len(item) >= 2:
                cand_name = item[0]
                cand_score = float(item[1])
                norm_candidates.append((cand_name, cand_score))
        # combine with category priority and re-rank
        ranked = self._rank_candidates(norm_candidates)
        # filter by cutoff
        filtered = [(i, s) for i, s in ranked if (s - self._category_score(i)*2.0) >= score_cutoff]
        if not filtered and ranked:
            # still return top few even if below cutoff (for UX)
            filtered = ranked[:min(len(ranked), top_k)]
        return filtered

    def best_match(self, input_text: str) -> Optional[str]:
        suggestions = self.normalize_ingredient(input_text, top_k=5)
        if not suggestions:
            return None
        # return the top suggestion's ingredient name
        return suggestions[0][0]


# test usage
if __name__ == "__main__":
    normalizer = IngredientNormalizer()
    while True:
        user = input("Ingredient (or 'done'): ").strip()
        if not user or user.lower() == "done":
            break
        suggestions = normalizer.normalize_ingredient(user, top_k=5)
        if not suggestions:
            print("No suggestions found.")
        else:
            print("Suggestions (ranked):")
            for ingredient, score in suggestions:
                category = normalizer.ingredient_to_category.get(ingredient, "")
                print(f"  {ingredient}  (category={category}, score={score:.1f})")
                print("\n")
