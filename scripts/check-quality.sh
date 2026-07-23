#!/bin/sh
# QGISRed code quality and security check (flake8 + bandit)
# Usage: scripts/check-quality.sh [--stats]
#
# Install once with: python -m pip install flake8 bandit

cd "$(dirname "$0")/.."

echo ""
echo "============================================="
echo " QGISRed - Code Quality & Security Check"
echo "============================================="
echo ""

OVERALL_EXIT=0

# ── Flake8 ──────────────────────────────────────────────────────────────────
echo "[1/2] Flake8 code quality"
if ! python -m flake8 --version >/dev/null 2>&1; then
    echo "  flake8 not installed. Run: python -m pip install flake8"
else
    if [ "$1" = "--stats" ]; then
        python -m flake8 . --statistics --count
    else
        python -m flake8 .
    fi
    [ $? -ne 0 ] && OVERALL_EXIT=1
fi

echo ""

# ── Bandit ──────────────────────────────────────────────────────────────────
echo "[2/2] Bandit security scan"
if ! python -m bandit --version >/dev/null 2>&1; then
    echo "  bandit not installed. Run: python -m pip install bandit"
else
    python -m bandit -r . -c pyproject.toml -f txt
    [ $? -ne 0 ] && OVERALL_EXIT=1
fi

echo ""
if [ "$OVERALL_EXIT" -eq 0 ]; then
    echo " [OK] All checks passed."
else
    echo " [FAIL] Issues found above. Fix them before committing."
fi

exit $OVERALL_EXIT
