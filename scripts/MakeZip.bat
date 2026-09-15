@echo off
setlocal

:: ── Change to plugin root (parent of scripts/) ────────────────────────────────
cd /d "%~dp0.."

:: ── Read version from metadata.txt ────────────────────────────────────────────
for /f "tokens=2 delims==" %%v in ('findstr "^version=" metadata.txt') do (
    set "VERSION=%%v"
)
set "VERSION=%VERSION: =%"

:: ── Resolve output path (parent folder of plugin root) ────────────────────────
for %%i in ("%CD%\..") do set "PARENT_DIR=%%~fi"

:: ── Environment variables read by PowerShell ──────────────────────────────────
set "PS_PLUGIN_DIR=%CD%"
set "PS_PLUGIN_NAME=QGISRed"
set "PS_OUTPUT_ZIP=%PARENT_DIR%\QGISRed_v%VERSION%.zip"

echo Plugin dir : %PS_PLUGIN_DIR%
echo Version    : %VERSION%
echo Output ZIP : %PS_OUTPUT_ZIP%
echo.

if exist "%PS_OUTPUT_ZIP%" del "%PS_OUTPUT_ZIP%"

:: ── Build ZIP via PowerShell (.NET ZipFile, exclusion-aware) ──────────────────
::
::   Excluded top-level names  : .git  .vscode  .claude  CLAUDE.md  news  scripts  .github
::                               .flake8  pyproject.toml (dev/CI tooling, unused at runtime)
::   images/                    : only qgisred.svg is kept; all other files excluded
::                               .gitignore  README.md  qgisred.pro  resources.qrc
::   defaults/layerStyles/icons/ : only pumps/reservoirs/tanks/valves.svg are kept — the
::                               ones qgisred_profile_plot.py reads from disk at runtime.
::                               The other icons here are already embedded as base64 inside
::                               the shipped .qml.bak styles; the loose files are dev source
::                               material only, kept for re-editing a style later.
::   Excluded dir names (any depth): __pycache__
::   Excluded extensions       : .pyc  .pyo  .ts
::   Excluded file names       : the style database, shipped by the dependencies installer
::                               instead. By name, never by the .bak extension: the ~30
::                               default styles in defaults/layerStyles are .qml.bak.
::                               Also i18n/QGISRed_PT_BR_glossary.md — a translator reference,
::                               not read by the plugin.
::
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$d   = $env:PS_PLUGIN_DIR;" ^
    "$out = $env:PS_OUTPUT_ZIP;" ^
    "$nm  = $env:PS_PLUGIN_NAME;" ^
    "$exTop = @('.git','.vscode','.claude','news','scripts','.githooks','.github','tests','.gitignore','.gitattributes','.flake8','CLAUDE.md','README.md','INTERNALS.md','pytest.ini','pyproject.toml','qgisred.pro','resources.qrc');" ^
    "$exDir = @('__pycache__','.pytest_cache');" ^
    "$exExt = @('.pyc','.pyo','.ts');" ^
    "$exFile = @('qgisred_symbology_style.db','qgisred_symbology_style.db.bak','QGISRed_PT_BR_glossary.md');" ^
    "$keepStyleIcons = @('pumps.svg','reservoirs.svg','tanks.svg','valves.svg');" ^
    "Add-Type -Assembly System.IO.Compression.FileSystem;" ^
    "$zip = [System.IO.Compression.ZipFile]::Open($out, 'Create');" ^
    "Get-ChildItem -Path $d -Recurse -File | ForEach-Object {" ^
    "    $rel   = $_.FullName.Substring($d.Length + 1);" ^
    "    $parts = $rel -split '\\';" ^
    "    $skip  = $exTop -contains $parts[0];" ^
    "    if ($parts[0] -eq 'images' -and $_.Name -ne 'qgisred.svg') { $skip = $true };" ^
    "    if ($parts.Length -ge 4 -and $parts[0] -eq 'defaults' -and $parts[1] -eq 'layerStyles' -and $parts[2] -eq 'icons' -and $keepStyleIcons -notcontains $_.Name) { $skip = $true };" ^
    "    for ($i = 0; $i -lt $parts.Length - 1; $i++) {" ^
    "        if ($exDir -contains $parts[$i]) { $skip = $true }" ^
    "    };" ^
    "    if ($exExt -contains $_.Extension) { $skip = $true };" ^
    "    if ($exFile -contains $_.Name) { $skip = $true };" ^
    "    if (-not $skip) {" ^
    "        $arc = ($nm + '/' + $rel) -replace '\\','/';" ^
    "        [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(" ^
    "            $zip, $_.FullName, $arc, 'Optimal') | Out-Null;" ^
    "        Write-Host ('  + ' + $arc)" ^
    "    }" ^
    "};" ^
    "$zip.Dispose();" ^
    "$kb = [math]::Round((Get-Item $out).Length / 1KB, 1);" ^
    "Write-Host '';" ^
    "Write-Host ('Done  ' + (Get-Item $out).Name + '  (' + $kb + ' KB)')"

echo.
pause
