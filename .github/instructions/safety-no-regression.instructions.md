---
description: "Use when implementing features, bug fixes, refactors, or dependency changes in GroceryGuru. Enforce hard no-regression engineering behavior: preserve existing behavior, update tests with code changes, and validate backend and pantrypal test suites before finalizing."
name: "GroceryGuru No-Regression Rules"
applyTo: "**"
---
# GroceryGuru No-Regression Rules

- Treat backward compatibility as a hard requirement unless the user explicitly asks for a breaking change.
- Keep edits minimal and scoped; do not rewrite unrelated code or change public contracts without approval.
- When changing logic, add or update tests in the same change.
- Before finalizing code changes, run both test suites from repo root with `PYTHONPATH=.`:
  - `PYTHONPATH=. pytest -q pantrypal/tests`
  - `PYTHONPATH=. pytest -q backend/tests`
- Treat test failures as a hard stop: do not mark the task complete until failures are fixed or the user explicitly approves proceeding.
- If tests cannot be run, report exactly what was not run and why.
- Never use destructive git commands (`reset --hard`, checkout reverts) unless explicitly requested.
- If unexpected unrelated file changes appear, stop and ask the user how to proceed.
