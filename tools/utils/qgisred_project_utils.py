# -*- coding: utf-8 -*-
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import QgsProject

_AMERICAN_UNITS = frozenset(["CFS", "GPM", "MGD", "IMGD", "AFD"])


class QGISRedProjectUtils:
    """Read-only access to QGISRed project settings stored in QgsProject."""

    @staticmethod
    def getQualityModel() -> str:
        """Return the quality model type: 'Chemical', 'Age', 'Trace', or 'None'."""
        model, _ = QgsProject.instance().readEntry("QGISRed", "project_qualitymodel", "Chemical")
        return model

    @staticmethod
    def getChemicalLabel() -> str:
        """Return the chemical substance label defined in Analysis Options, or ''."""
        label, _ = QgsProject.instance().readEntry("QGISRed", "project_chemicallabel", "")
        return label.strip()

    @staticmethod
    def getTraceNode() -> str:
        """Return the Trace source node ID defined in Analysis Options, or ''."""
        node, _ = QgsProject.instance().readEntry("QGISRed", "project_tracenode", "")
        return node.strip()

    @staticmethod
    def getQualityDisplayName() -> str:
        """Return the display name for the Quality result field based on the quality model."""
        model = QGISRedProjectUtils.getQualityModel().upper()
        if model == "AGE":
            return QCoreApplication.translate("QGISRedProjectUtils", "Age")
        if model == "TRACE":
            node = QGISRedProjectUtils.getTraceNode()
            label = QCoreApplication.translate("QGISRedProjectUtils", "Trace %1").replace("%1", str(node)).strip()
            return label if node else QCoreApplication.translate("QGISRedProjectUtils", "Trace")
        label = QGISRedProjectUtils.getChemicalLabel()
        return label if label else QCoreApplication.translate("QGISRedProjectUtils", "Chemical")

    @staticmethod
    def showReactRate() -> bool:
        """Return True if ReactRate should be shown (Chemical quality simulation only)."""
        return QGISRedProjectUtils.getQualityModel().upper() not in ("NONE", "AGE", "TRACE")

    @staticmethod
    def getUnits() -> str:
        """Return 'SI' or 'US' based on the project flow unit setting."""
        units, _ = QgsProject.instance().readEntry("QGISRed", "project_units", "LPS")
        return "US" if units in _AMERICAN_UNITS else "SI"

    @staticmethod
    def getFlowUnit() -> str:
        """Return the raw flow unit code stored in the project (e.g. 'LPS', 'GPM')."""
        units, _ = QgsProject.instance().readEntry("QGISRed", "project_units", "LPS")
        return units

    @staticmethod
    def getConcentrationUnits() -> str:
        """Return concentration units string, e.g. 'mg/L' or 'µg/L'."""
        units, _ = QgsProject.instance().readEntry("QGISRed", "project_concentrationunits", "mg/L")
        return units

    @staticmethod
    def getHeadlossFormula() -> str:
        """Return the headloss formula code stored in the project (e.g. 'D-W', 'H-W')."""
        formula, _ = QgsProject.instance().readEntry("QGISRed", "project_headloss", "D-W")
        return formula
