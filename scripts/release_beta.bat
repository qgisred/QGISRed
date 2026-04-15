@echo off
:: Release beta version (patch +1): 0.17.3 → 0.17.4
cd /d "%~dp0.."
python scripts\release.py --beta
pause
