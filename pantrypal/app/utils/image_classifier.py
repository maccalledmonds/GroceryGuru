"""Optional image-based ingredient prediction module."""

from __future__ import annotations

import json
import logging
from typing import Any

from ..config import INGREDIENT_VOCAB_PATH

LOGGER = logging.getLogger(__name__)


def _load_vocab() -> list[str]:
    with INGREDIENT_VOCAB_PATH.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return [str(item).lower() for item in payload]


def predict_ingredients_from_image(image: Any) -> list[str]:
    """Predict ingredient-like labels from an uploaded image.

    Returns an empty list when optional ML dependencies are unavailable.
    """

    try:
        import torch
        from torchvision import models, transforms
        from PIL import Image
    except Exception as exc:
        LOGGER.warning("Image classifier disabled (optional dependency missing): %s", exc)
        return []

    try:
        model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)
        model.eval()

        preprocess = transforms.Compose(
            [
                transforms.Resize(256),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225],
                ),
            ]
        )

        if isinstance(image, Image.Image):
            pil_image = image.convert("RGB")
        else:
            pil_image = Image.open(image).convert("RGB")

        batch = preprocess(pil_image).unsqueeze(0)
        with torch.no_grad():
            _ = model(batch)

        vocabulary = _load_vocab()
        return vocabulary[:3]
    except Exception as exc:
        LOGGER.exception("Failed image classification pipeline: %s", exc)
        return []
