# -*- coding: utf-8 -*-
"""Extent and temporary boxes used to show elements on the map."""
from unittest.mock import MagicMock

from QGISRed.tools.utils import qgisred_flash_boxes as flash
from QGISRed.tools.utils.qgisred_flash_boxes import QGISRedFlashBoxes, boundingExtent


def test_boundingExtent_containsAllPointsWithAMargin():
    xmin, ymin, xmax, ymax = boundingExtent([(0, 0), (100, 50)], (1000, 1000))

    assert (xmin, ymin) == (-15, -7.5)
    assert (xmax, ymax) == (115, 57.5)


def test_boundingExtent_ofASinglePointUsesTheCanvasSize():
    xmin, ymin, xmax, ymax = boundingExtent([(10, 20)], (1000, 400))

    assert (xmin, xmax) == (-90, 110)
    assert (ymin, ymax) == (-80, 120)


def test_boundingExtent_ofPointsOnALineOnlyOpensTheFlatAxis():
    xmin, ymin, xmax, ymax = boundingExtent([(0, 5), (100, 5)], (1000, 1000))

    assert (xmin, xmax) == (-15, 115)
    assert (ymin, ymax) == (-95, 105)


def _point(x, y):
    point = MagicMock()
    point.x.return_value = x
    point.y.return_value = y
    return point


def test_show_drawsOneBandPerPointAndClearRemovesThem():
    canvas = MagicMock()
    canvas.mapUnitsPerPixel.return_value = 2.0
    boxes = QGISRedFlashBoxes(canvas)

    boxes.show([_point(0, 0), _point(5, 5)])

    assert len(boxes._bands) == 2
    boxes.clear()
    assert boxes._bands == []
    assert canvas.scene.return_value.removeItem.call_count == 2


def test_show_withoutPointsDrawsNothing():
    boxes = QGISRedFlashBoxes(MagicMock())

    boxes.show([])

    assert boxes._bands == []


def test_boxesAreThinAndRed():
    assert flash.BOX_COLOR == (255, 0, 0)
    assert flash.BOX_WIDTH == 1
