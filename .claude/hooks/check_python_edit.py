#!/usr/bin/env python3
"""PostToolUse hook (Write|Edit): after Claude edits a .py file in this repo, run
flake8 on it and the full pytest suite, and hand any failure back to Claude via
additionalContext. Silent on a clean run — nothing to surface."""
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def main():
    payload = json.load(sys.stdin)
    file_path = (
        (payload.get("tool_input") or {}).get("file_path")
        or (payload.get("tool_response") or {}).get("filePath")
        or ""
    )
    if not file_path.endswith(".py"):
        return

    flake8 = subprocess.run(
        ["py", "-3", "-m", "flake8", file_path],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    pytest = subprocess.run(
        ["py", "-3", "-m", "pytest", "tests/", "-q"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )

    if flake8.returncode == 0 and pytest.returncode == 0:
        return

    parts = []
    if flake8.returncode != 0:
        parts.append("flake8 (%s):\n%s%s" % (file_path, flake8.stdout, flake8.stderr))
    if pytest.returncode != 0:
        parts.append("pytest (tests/):\n%s%s" % (pytest.stdout[-3000:], pytest.stderr[-1000:]))

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": "\n\n".join(parts),
        }
    }))


if __name__ == "__main__":
    main()
