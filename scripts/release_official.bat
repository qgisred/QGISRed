@echo off
:: Release official version (minor +1): 0.17.3 → 0.18.0
cd /d "%~dp0.."
python scripts\release.py --official
pause
