from thefuzz import fuzz, process
from typing import List, Dict

from thefuzz import fuzz
from thefuzz import process
from typing import List, Dict

class IngredientNormalizer:
    def __init__(self):
        # Example ingredient dictionary - you can expand this or load from a database
        self.standard_ingredients = [
            "tomato", "onion", "garlic", "chicken", "beef",
            "carrot", "potato", "rice", "pasta", "olive oil"
        ]
        
    def normalize_ingredient(self, input_text: str, score_cutoff: int = 80) -> str:
        """
        Normalize user input to standard ingredient names using fuzzy matching
        
        Args:
            input_text: Raw user input text
            score_cutoff: Minimum similarity score (0-100) to accept a match
            
        Returns:
            Normalized ingredient name or original input if no match found
        """
        input_text = input_text.lower().strip()
        
        # Find the best match from standard ingredients
        match = process.extractOne(
            input_text,
            self.standard_ingredients,
            scorer=fuzz.ratio,
            score_cutoff=score_cutoff
        )
        
        return match[0] if match else input_text
    
    def normalize_ingredient_list(self, ingredients: List[str]) -> List[str]:
        """
        Normalize a list of ingredients
        """
        return [self.normalize_ingredient(ing) for ing in ingredients]


# Example usage
if __name__ == "__main__":
    normalizer = IngredientNormalizer()
    
    # Test cases
    test_inputs = [
        "tomaeto",  # misspelling
        "onions",   # plural
        "garlick",  # misspelling
        "chicken breast",  # compound term
    ]
    
    for ingredient in test_inputs:
        normalized = normalizer.normalize_ingredient(ingredient)
        print(f"Input: {ingredient} -> Normalized: {normalized}")