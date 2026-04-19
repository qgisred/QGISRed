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
::   Excluded top-level names  : .git  .vscode  .claude  images  scripts
::                               .gitignore  README.md  qgisred.pro  resources.qrc
::   Excluded dir names (any depth): __pycache__
::   Excluded extensions       : .pyc  .pyo  .ts
::
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$d   = $env:PS_PLUGIN_DIR;" ^
    "$out = $env:PS_OUTPUT_ZIP;" ^
    "$nm  = $env:PS_PLUGIN_NAME;" ^
    "$exTop = @('.git','.vscode','.claude','images','scripts','.githooks','tests','.gitignore','.gitattributes','README.md','INTERNALS.md','pytest.ini','qgisred.pro','resources.qrc');" ^
    "$exDir = @('__pycache__','.pytest_cache');" ^
    "$exExt = @('.pyc','.pyo','.ts');" ^
    "Add-Type -Assembly System.IO.Compression.FileSystem;" ^
    "$zip = [System.IO.Compression.ZipFile]::Open($out, 'Create');" ^
    "Get-ChildItem -Path $d -Recurse -File | ForEach-Object {" ^
    "    $rel   = $_.FullName.Substring($d.Length + 1);" ^
    "    $parts = $rel -split '\\';" ^
    "    $skip  = $exTop -contains $parts[0];" ^
    "    for ($i = 0; $i -lt $parts.Length - 1; $i++) {" ^
    "        if ($exDir -contains $parts[$i]) { $skip = $true }" ^
    "    };" ^
    "    if ($exExt -contains $_.Extension) { $skip = $true };" ^
    "    if (-not $skip) {" ^
    "        $arc = ($nm + '/' + $rel) -replace '\\\\','/';" ^
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
