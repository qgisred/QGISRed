#!/usr/bin/env python3
"""PostToolUse hook (Write|Edit), local-only: after Claude edits NativeAOT.cs (C#) or
one of the Python dependency mixins, compare exported method signatures against the
Python ctypes bindings that call them. A mismatch here does not fail the build on
either side -- it crashes QGIS natively at runtime the next time that method is
called, which is exactly why it deserves its own check instead of trusting compile +
test on each side separately.

Only flags what will actually break at runtime: a Python call with no matching C#
EntryPoint, or one whose argument count disagrees. A C# export with no Python caller
yet is not reported -- that's not a bug, just an export nobody has wired up.

Identical copy lives in ../git_repo_c/.claude/hooks/ -- this is a local, personal
check (see .claude/settings.local.json), not shared via git, so duplication across
the two repos is simpler than trying to share one file between them.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
THIS_REPO = os.path.dirname(os.path.dirname(HERE))
QGISRED_ROOT = os.path.dirname(THIS_REPO)
PY_REPO = os.path.join(QGISRED_ROOT, "git_repo")
CS_REPO = os.path.join(QGISRED_ROOT, "git_repo_c")

NATIVEAOT = os.path.join(CS_REPO, "GISRed.QGISRed", "NativeAOT.cs")
DEPS_DIR = os.path.join(PY_REPO, "tools", "dependencies")

CS_EXPORT_RE = re.compile(
    r'EntryPoint\s*=\s*"(\w+)".*?\]\s*\n\s*public static (?:unsafe )?IntPtr \w+\(([^)]*)\)',
    re.DOTALL,
)
PY_ARGTYPES_RE = re.compile(r"mydll\.(\w+)\.argtypes\s*=\s*\(([^)]*)\)")


def _argCount(paramsText):
    paramsText = paramsText.strip()
    if not paramsText:
        return 0
    return len([p for p in paramsText.split(",") if p.strip()])


def parseCsharpExports(path):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    return {name: _argCount(params) for name, params in CS_EXPORT_RE.findall(text)}


def parsePythonArgtypes(depsDir):
    calls = {}
    for fname in os.listdir(depsDir):
        if not fname.endswith(".py"):
            continue
        with open(os.path.join(depsDir, fname), encoding="utf-8") as f:
            text = f.read()
        for name, params in PY_ARGTYPES_RE.findall(text):
            calls[name] = _argCount(params)
    return calls


def relevantEdit(filePath):
    normalized = filePath.replace("\\", "/")
    return normalized.endswith("NativeAOT.cs") or "tools/dependencies/" in normalized


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return
    filePath = (payload.get("tool_input") or {}).get("file_path") or (payload.get("tool_response") or {}).get("filePath") or ""
    if not relevantEdit(filePath):
        return
    if not (os.path.exists(NATIVEAOT) and os.path.isdir(DEPS_DIR)):
        return

    csExports = parseCsharpExports(NATIVEAOT)
    pyCalls = parsePythonArgtypes(DEPS_DIR)

    problems = []
    for name, pyCount in pyCalls.items():
        if name not in csExports:
            problems.append('Python calls mydll.%s (%d args) but no C# EntryPoint "%s" exists in NativeAOT.cs' % (name, pyCount, name))
        elif csExports[name] != pyCount:
            problems.append("Arg count mismatch for %s: C# exports %d args, Python declares %d" % (name, csExports[name], pyCount))

    if not problems:
        return

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": "Possible Python<->C# ABI drift (NativeAOT.cs vs tools/dependencies/):\n" + "\n".join("  - %s" % p for p in problems),
        }
    }))


if __name__ == "__main__":
    main()
