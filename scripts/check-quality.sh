#!/bin/sh
# QGISRed code quality check (flake8)
# Usage: scripts/check-quality.sh [--stats]
#
# Install flake8 once with: python -m pip install flake8

cd "$(dirname "$0")/.."

echo ""
echo "============================================="
echo " QGISRed - Code Quality Check (flake8)"
echo "============================================="
echo ""

if ! python -m flake8 --version >/dev/null 2>&1; then
    echo "flake8 not installed. Run: python -m pip install flake8"
    exit 1
fi

if [ "$1" = "--stats" ]; then
    python -m flake8 . --statistics --count
else
    python -m flake8 .
fi

FLAKE8_EXIT=$?

echo ""
if [ "$FLAKE8_EXIT" -eq 0 ]; then
    echo " [OK] No issues found."
else
    echo " [FAIL] Issues found above. Fix them before committing."
fi

exit $FLAKE8_EXIT
