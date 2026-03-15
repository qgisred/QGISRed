@echo on
:: Change to the parent directory (QGISRed plugin folder)
cd /d "%~dp0.."

:: If something fails, we need to ensure the python executed is the one from QGIS
:: setting the environmental variable of the python folder in QGis installation folder
python -m PyQt5.pyrcc_main -o resources3x.py resources.qrc