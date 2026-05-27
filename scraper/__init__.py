"""Epicurious recipe scraper for GroceryGuru.

This package is intentionally separate from `pantrypal`. It does scrape-time
data cleaning (including spaCy-based ingredient extraction) and writes a
clean recipe corpus to ``pantrypal/data``. Runtime normalization inside
``pantrypal`` stays deterministic and rule-based as required by the project.
"""

__all__ = []
