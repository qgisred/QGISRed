@echo on
:: If something fails, we need to ensure the python executed is the one from QGIS
:: setting the environmental variable of the python folder in QGis installation folder
python -m PyQt5.pyrcc_main -o resources3x.py resources.qrc