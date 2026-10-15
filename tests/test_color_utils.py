import pytest

from QGISRed.tools.utils.qgisred_color_utils import deltaE, complementaryColor, toLab
from qgis.PyQt.QtGui import QColor

pytestmark = pytest.mark.skipif(not isinstance(QColor, type), reason="needs a real QColor")


def test_identical_colors_have_no_distance():
    assert deltaE(QColor(255, 255, 255), QColor(255, 255, 255)) == 0


def test_white_lab():
    lightness, a, b = toLab(QColor(255, 255, 255))
    assert round(lightness) == 100 and abs(a) < 0.1 and abs(b) < 0.1


def test_near_white_is_below_threshold_and_blue_is_not():
    assert deltaE(QColor(255, 255, 255), QColor(254, 254, 254)) < 2
    assert deltaE(QColor(255, 255, 255), QColor(0, 78, 255)) > 2


def test_complement_of_white_is_black():
    assert complementaryColor(QColor(255, 255, 255)).name() == "#000000"


def test_complement_of_blue_is_yellowish():
    assert complementaryColor(QColor(0, 0, 255)).name() == "#ffff00"
