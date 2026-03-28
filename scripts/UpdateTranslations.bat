@echo off
:: Change to the directory where this script is located (QGISRed plugin folder)
cd /d "%~dp0.."

:: Use %LOCALAPPDATA% to dynamically get the user's folder (C:\Users\<user>\AppData\Local)
set "OSGEO4W_BAT=%LOCALAPPDATA%\Programs\OSGeo4W\OSGeo4W.bat"

:: Check if the OSGeo4W.bat file exists in the default path
if not exist "%OSGEO4W_BAT%" (
    echo Error: OSGeo4W.bat shell not found.
    echo Searched path: %OSGEO4W_BAT%
    echo.
    echo If you have QGIS installed in another location ^(e.g., C:\OSGeo4W^),
    echo you need to edit this .bat file with your correct path in the OSGEO4W_BAT variable.
    echo.
    pause
    exit /b 1
)

echo Starting OSGeo4W shell from:
echo "%OSGEO4W_BAT%"
echo.
echo Preparing execution of: pylupdate5 qgisred.pro
echo.

:: Call OSGeo4W.bat setting the working directory via cmd /c to ensure it runs inside the plugin folder
call "%OSGEO4W_BAT%" cmd /c "cd /d ""%~dp0.."" && pylupdate5 qgisred.pro"

echo.
echo Operation completed (or OSGeo4W window closed).
pause
