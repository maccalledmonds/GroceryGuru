#!/usr/bin/env python3
"""Gate git commit tool usage by running required test suites first."""

import json
import re
import subprocess
import sys
from pathlib import Path

COMMIT_PATTERN = re.compile(r"(^|\s)git\s+commit(\s|$)")


def emit(decision: str, reason: str, system_message: str = "") -> None:
    payload = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason": reason,
        }
    }
    if system_message:
        payload["systemMessage"] = system_message
    print(json.dumps(payload))


def extract_tool_info(event: dict) -> tuple[str, str]:
    tool_name = (
        event.get("toolName")
        or event.get("tool_name")
        or event.get("name")
        or ""
    )

    tool_input = event.get("toolInput") or event.get("tool_input") or {}
    command = ""
    if isinstance(tool_input, dict):
        command = tool_input.get("command", "")
    return str(tool_name), str(command)


def run_check(command: str, repo_root: Path) -> tuple[bool, str]:
    proc = subprocess.run(
        command,
        cwd=repo_root,
        shell=True,
        text=True,
        capture_output=True,
    )
    output = (proc.stdout + proc.stderr).strip()
    return proc.returncode == 0, output


def main() -> int:
    raw = sys.stdin.read().strip()
    if not raw:
        emit("allow", "No hook payload provided")
        return 0

    try:
        event = json.loads(raw)
    except json.JSONDecodeError:
        emit("allow", "Hook payload was not valid JSON")
        return 0

    tool_name, command = extract_tool_info(event)
    if tool_name != "run_in_terminal":
        emit("allow", "Only terminal commands are checked")
        return 0

    if not COMMIT_PATTERN.search(command):
        emit("allow", "Not a git commit command")
        return 0

    repo_root = Path(__file__).resolve().parents[3]
    python_exec = sys.executable
    checks = [
        ("pantrypal", f'PYTHONPATH=. "{python_exec}" -m pytest -q pantrypal/tests'),
        ("backend", f'PYTHONPATH=. "{python_exec}" -m pytest -q backend/tests'),
    ]

    for suite_name, suite_command in checks:
        ok, output = run_check(suite_command, repo_root)
        if not ok:
            details = output[-4000:] if output else "No output captured."
            emit(
                "deny",
                f"{suite_name} pre-commit checks failed",
                f"Blocked git commit. Failing command: {suite_command}\n\n{details}",
            )
            return 0

    emit("allow", "All pre-commit checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
