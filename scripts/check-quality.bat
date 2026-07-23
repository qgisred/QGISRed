@echo off
:: QGISRed code quality check (flake8)
:: Usage: scripts\check-quality.bat [--stats]
::
:: Runs from any directory — always operates on the repo root.
:: Install flake8 once with: python -m pip install flake8

setlocal
cd /d "%~dp0.."

echo.
echo =============================================
echo  QGISRed - Code Quality Check (flake8 %1)
echo =============================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: python not found on PATH.
    exit /b 1
)

python -m flake8 --version >nul 2>&1
if errorlevel 1 (
    echo flake8 not installed. Installing...
    python -m pip install flake8
)

if "%1"=="--stats" (
    python -m flake8 . --statistics --count
) else (
    python -m flake8 .
)

set FLAKE8_EXIT=%ERRORLEVEL%

echo.
if %FLAKE8_EXIT% equ 0 (
    echo  [OK] No issues found.
) else (
    echo  [FAIL] Issues found above. Fix them before committing.
)

exit /b %FLAKE8_EXIT%
