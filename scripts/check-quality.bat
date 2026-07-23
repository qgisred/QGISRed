@echo off
:: QGISRed code quality and security check (flake8 + bandit)
:: Usage: scripts\check-quality.bat [--stats]
::
:: Runs from any directory — always operates on the repo root.
:: Install once with: python -m pip install flake8 bandit

setlocal
cd /d "%~dp0.."

echo.
echo =============================================
echo  QGISRed - Code Quality ^& Security Check
echo =============================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: python not found on PATH.
    exit /b 1
)

set OVERALL_EXIT=0

:: ── Flake8 ──────────────────────────────────────────────────────────────────
echo [1/2] Flake8 code quality
python -m flake8 --version >nul 2>&1
if errorlevel 1 (
    echo   flake8 not installed. Run: python -m pip install flake8
) else (
    if "%1"=="--stats" (
        python -m flake8 . --statistics --count
    ) else (
        python -m flake8 .
    )
    if errorlevel 1 set OVERALL_EXIT=1
)

echo.

:: ── Bandit ──────────────────────────────────────────────────────────────────
echo [2/2] Bandit security scan
python -m bandit --version >nul 2>&1
if errorlevel 1 (
    echo   bandit not installed. Run: python -m pip install bandit
) else (
    python -m bandit -r . -c pyproject.toml -f txt
    if errorlevel 1 set OVERALL_EXIT=1
)

echo.
if %OVERALL_EXIT% equ 0 (
    echo  [OK] All checks passed.
) else (
    echo  [FAIL] Issues found above. Fix them before committing.
)

exit /b %OVERALL_EXIT%
