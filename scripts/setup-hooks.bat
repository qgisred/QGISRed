@echo off
setlocal

:: ── Change to plugin root (parent of scripts/) ─────────────────────────────
cd /d "%~dp0.."

echo.
echo  QGISRed - Developer Setup: Git Hooks
echo  ---------------------------------------------
echo.

:: ── Configure git to use .githooks/ for this repository ────────────────────
git config core.hooksPath .githooks
if errorlevel 1 (
    echo  ERROR: git config failed. Is Git installed and on your PATH?
    echo.
    pause
    exit /b 1
)

echo  Git hooks configured successfully.
echo  Git will now run .githooks\pre-commit before every commit.
echo.
echo  Make sure pytest is installed:
echo    python -m pip install pytest
echo.
pause
