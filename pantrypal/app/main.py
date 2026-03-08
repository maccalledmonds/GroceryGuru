"""Streamlit UI for PantryPal recipe recommendations."""

from __future__ import annotations

from io import BytesIO
from typing import Any

import streamlit as st

try:
    from .config import DEFAULT_TOP_K, SUPPORTED_FILTERS
    from .models import load_recipes
    from .utils.image_classifier import predict_ingredients_from_image
    from .utils.normalization import normalize_ingredients
    from .utils.scoring import recommend_recipes
except ImportError:
    try:
        from app.config import DEFAULT_TOP_K, SUPPORTED_FILTERS
        from app.models import load_recipes
        from app.utils.image_classifier import predict_ingredients_from_image
        from app.utils.normalization import normalize_ingredients
        from app.utils.scoring import recommend_recipes
    except ImportError:
        from pantrypal.app.config import DEFAULT_TOP_K, SUPPORTED_FILTERS
        from pantrypal.app.models import load_recipes
        from pantrypal.app.utils.image_classifier import predict_ingredients_from_image
        from pantrypal.app.utils.normalization import normalize_ingredients
        from pantrypal.app.utils.scoring import recommend_recipes


def _parse_text_ingredients(raw_text: str) -> list[str]:
    return [piece.strip() for piece in raw_text.split(",") if piece.strip()]


def _build_query_ingredients(text_ingredients: list[str], image_ingredients: list[str]) -> list[str]:
    return list(dict.fromkeys(text_ingredients + image_ingredients))


def _render_recipe_card(recipe: dict[str, Any]) -> None:
    st.subheader(recipe["title"])
    st.write(f"Match score: {recipe['score']:.3f}")
    st.write(f"Match percentage: {recipe['match_percentage']}%")

    nutrition = recipe.get("nutrition", {})
    st.write(
        "Nutrition: "
        f"Calories {nutrition.get('calories', 0.0)} | "
        f"Protein {nutrition.get('protein', 0.0)}g | "
        f"Fat {nutrition.get('fat', 0.0)}g | "
        f"Carbs {nutrition.get('carbs', 0.0)}g"
    )

    tags = recipe.get("diet_tags", [])
    st.caption("Diet tags: " + (", ".join(tags) if tags else "none"))

    with st.expander("Instructions"):
        st.write(recipe.get("instructions", "No instructions available."))


def main() -> None:
    """Run Streamlit app."""

    st.set_page_config(page_title="PantryPal", page_icon="🥕", layout="wide")
    st.title("PantryPal")

    with st.sidebar:
        st.header("Filters")
        selected_filters = st.multiselect(
            "Dietary filters",
            options=sorted(SUPPORTED_FILTERS),
            default=[],
        )
        top_k = st.slider("Top K", min_value=1, max_value=20, value=DEFAULT_TOP_K)

    ingredient_text = st.text_input(
        "Enter ingredients (comma-separated)",
        placeholder="eggs, spinach, feta cheese",
    )

    uploaded_image = st.file_uploader(
        "Optional pantry image",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=False,
    )

    if st.button("Recommend Recipes"):
        raw_ingredients = _parse_text_ingredients(ingredient_text)

        predicted_from_image: list[str] = []
        if uploaded_image is not None:
            predicted_from_image = predict_ingredients_from_image(BytesIO(uploaded_image.read()))
            if predicted_from_image:
                st.info("Image-derived ingredients: " + ", ".join(predicted_from_image))

        all_inputs = _build_query_ingredients(raw_ingredients, predicted_from_image)
        if not all_inputs:
            st.warning("Please provide ingredients via text input or image upload.")
            return

        normalized = normalize_ingredients(all_inputs)
        if not normalized:
            st.warning("No valid ingredients were recognized. Try different ingredient names.")
            return

        recipes = load_recipes()
        results = recommend_recipes(
            user_ingredients=normalized,
            recipes=recipes,
            top_k=top_k,
            filters=selected_filters,
        )

        if not results:
            st.info("No recipes matched your ingredients and selected filters.")
            return

        st.success(f"Found {len(results)} matching recipes.")
        for recipe in results:
            _render_recipe_card(recipe)
            st.divider()


if __name__ == "__main__":
    main()
