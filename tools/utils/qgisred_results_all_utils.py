# -*- coding: utf-8 -*-
import os

from qgis.core import QgsFeatureRequest, QgsVectorLayer


ALL_FIELD_NAME_OVERRIDES = {"UnitHdLoss": "UnitHeadLo"}


class QGISRedResultsAllUtils:
    """Read the <Network>_<Scenario>_{Node|Link}_All.shp files holding results for every time step."""

    @staticmethod
    def getAllShapefilePathForLayer(resultsLayer):
        source = (resultsLayer.source() or "").split("|")[0]
        if not source.lower().endswith(".shp"):
            return None
        allPath = source[:-4] + "_All.shp"
        return allPath if os.path.exists(allPath) else None

    @staticmethod
    def loadAllLayer(path):
        layer = QgsVectorLayer(path, "temp_results_all", "ogr")
        return layer if layer.isValid() else None

    @staticmethod
    def getAllFieldName(propertyName, allLayer):
        fieldName = ALL_FIELD_NAME_OVERRIDES.get(propertyName, propertyName)
        return fieldName if allLayer.fields().indexFromName(fieldName) >= 0 else None

    @staticmethod
    def getIdFieldName(allLayer):
        for candidate in ("Id", "NodeID", "LinkID", "ID"):
            if allLayer.fields().indexFromName(candidate) >= 0:
                return candidate
        return "Id"

    @staticmethod
    def collectAllNumericValues(allLayer, fieldName, idSet=None, absolute=False, filterExpression=""):
        values = []
        idFieldName = QGISRedResultsAllUtils.getIdFieldName(allLayer)
        request = QgsFeatureRequest().setFilterExpression(filterExpression) if filterExpression else None
        featureIterator = allLayer.getFeatures(request) if request is not None else allLayer.getFeatures()
        for feature in featureIterator:
            if idSet is not None and str(feature[idFieldName]) not in idSet:
                continue
            raw = feature[fieldName]
            if raw is None:
                continue
            try:
                value = float(raw)
            except (TypeError, ValueError):
                continue
            values.append(abs(value) if absolute else value)
        values.sort()
        return values

    @staticmethod
    def collectAllUniqueValues(allLayer, fieldName, idSet=None, limit=10000, filterExpression=""):
        values = set()
        idFieldName = QGISRedResultsAllUtils.getIdFieldName(allLayer)
        request = QgsFeatureRequest().setFilterExpression(filterExpression) if filterExpression else None
        featureIterator = allLayer.getFeatures(request) if request is not None else allLayer.getFeatures()
        for feature in featureIterator:
            if idSet is not None and str(feature[idFieldName]) not in idSet:
                continue
            value = feature[fieldName]
            if value is None:
                continue
            values.add(value)
            if len(values) >= limit:
                break
        try:
            return sorted(values)
        except TypeError:
            return sorted(values, key=lambda item: str(item))
