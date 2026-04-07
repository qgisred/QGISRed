@echo off
:: Change to the directory where this script is located (QGISRed plugin folder)
cd /d "%~dp0.."

echo --------------------------------------------------------------------------------
echo   Removing obsolete entries (type="obsolete") from .ts files in the i18n folder
echo   This script analyzes all .ts files and completely removes any message entries
echo   that are marked as obsolete.
echo --------------------------------------------------------------------------------
echo.

:: Execute the cleaning script using python
python scripts\clean_ts.py

echo.
echo Operation completed.
pause
