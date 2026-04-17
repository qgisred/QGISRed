@echo on
:: Change to the parent directory (QGISRed plugin folder)
cd /d "%~dp0.."

:: If something fails, we need to ensure the python executed is the one from QGIS
:: setting the environmental variable of the python folder in QGis installation folder
python -m PyQt5.pyrcc_main -o resources3x.py resources.qrc
:: Patch the generated file to use qgis.PyQt for Qt5/Qt6 compatibility
python -c "import sys; fh=open('resources3x.py', 'r'); c=fh.read(); fh.close(); fh=open('resources3x.py', 'w'); fh.write(c.replace('from PyQt5 import QtCore', 'from qgis.PyQt import QtCore')); fh.close()"

pause