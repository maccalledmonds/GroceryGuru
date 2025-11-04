from thefuzz import fuzz, process
from typing import List, Dict
import csv



class IngredientNormalizer:
    def __init__(self):
        # Example ingredient dictionary - you can expand this or load from a database
        with open("standard_ingredients_list.csv", "r") as file:
            self.standard_ingredients = [row[0] for row in csv.reader(file) if row]
        
    def normalize_ingredient(self, input_text: str, limit: str = 3) -> str:
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
        match = process.extract(
            input_text,
            self.standard_ingredients,
            scorer=fuzz.ratio,
            limit = limit
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
    

    inputs_list = []
    while True:
        test_inputs = input("What ingredients do you have? ")
        if test_inputs.lower() == "done":
            break
        else:
            inputs_list.append(test_inputs)
            print(inputs_list)
    
    
    
    for ingredient in inputs_list:
        normalized = normalizer.normalize_ingredient(ingredient)
        print(f"Input: {ingredient} -> Normalized: {normalized}")