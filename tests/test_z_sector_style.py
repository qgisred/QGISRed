# -*- coding: utf-8 -*-
"""Demand sectors without demand (Z) are drawn in their own orange-red, dashed, and no other sector takes it."""
import pytest

from .conftest import REAL_QGIS

from QGISRed.tools.utils.qgisred_styling_utils import (
    QGISRedStylingUtils, DEMAND_BUILDER_FALLBACK_COLORS, Z_SECTOR_COLOR, Z_SECTOR_MIN_DELTA_E)


@pytest.mark.parametrize("value, expected", [
    ("Z1", True), ("Z12", True), ("S1", False), ("U1", False), ("Z", False), ("Z1a", False), ("z1", False),
    ("1", False), (1, False), (None, False),
])
def test_onlyNumberedZClassesAreZSectors(value, expected):
    assert QGISRedStylingUtils.isZSectorClass(value) is expected


@pytest.mark.skipif(not REAL_QGIS, reason="needs real QGIS colours")
def test_thePaletteLosesTheColoursCloseToTheZColour():
    from qgis.PyQt.QtGui import QColor
    from QGISRed.tools.utils.qgisred_color_utils import deltaE

    palette = [QColor(name) for name in DEMAND_BUILDER_FALLBACK_COLORS]
    zColor = QColor(Z_SECTOR_COLOR)

    result = QGISRedStylingUtils.sectorPalette(palette)

    assert len(result) >= 6
    assert all(deltaE(color, zColor) >= Z_SECTOR_MIN_DELTA_E for color in result)


@pytest.mark.skipif(not REAL_QGIS, reason="needs real QGIS renderers")
def test_aZSectorTakesTheZColourAndTheOthersDoNot(tmp_path):
    from qgis.core import QgsVectorLayer, QgsFeature, QgsGeometry, QgsPointXY
    from qgis.PyQt.QtGui import QColor

    layer = QgsVectorLayer("LineString?crs=EPSG:25830&field=Class:string", "sectors", "memory")
    provider = layer.dataProvider()
    for index, sector in enumerate(["S1", "S2", "Z1", "S3"]):
        feature = QgsFeature(layer.fields())
        feature.setGeometry(QgsGeometry.fromPolylineXY([QgsPointXY(index, 0), QgsPointXY(index, 1)]))
        feature.setAttributes([sector])
        provider.addFeature(feature)
    layer.updateExtents()

    QGISRedStylingUtils(str(tmp_path / "project"), "Net").setSectorsStyle(layer)

    colors = {category.value(): category.symbol().color().name() for category in layer.renderer().categories()}
    assert colors["Z1"] == QColor(Z_SECTOR_COLOR).name()
    assert Z_SECTOR_COLOR not in [colors[name] for name in ("S1", "S2", "S3")]
    assert len({colors[name] for name in ("S1", "S2", "S3")}) == 3
