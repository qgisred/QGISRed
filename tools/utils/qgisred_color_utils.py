# -*- coding: utf-8 -*-
import math

from qgis.PyQt.QtGui import QColor

ACHROMATIC_SATURATION = 0.1
_D65_WHITE = (95.047, 100.0, 108.883)


def _linearChannel(value):
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def _labCurve(ratio):
    return ratio ** (1.0 / 3.0) if ratio > 216.0 / 24389.0 else (24389.0 / 27.0 * ratio + 16.0) / 116.0


def toLab(color):
    red, green, blue = (_linearChannel(channel) for channel in (color.redF(), color.greenF(), color.blueF()))
    x = (0.4124564 * red + 0.3575761 * green + 0.1804375 * blue) * 100.0
    y = (0.2126729 * red + 0.7151522 * green + 0.0721750 * blue) * 100.0
    z = (0.0193339 * red + 0.1191920 * green + 0.9503041 * blue) * 100.0
    fx, fy, fz = (_labCurve(value / white) for value, white in zip((x, y, z), _D65_WHITE))
    return 116.0 * fy - 16.0, 500.0 * (fx - fy), 200.0 * (fy - fz)


def deltaE(first, second):
    """CIE76 distance between two colors: below ~2 the eye cannot tell them apart."""
    return math.dist(toLab(first), toLab(second))


def complementaryColor(color):
    """Hue rotated half a turn in HSV; an achromatic color has no hue, so it flips to black or white."""
    hue, saturation, value, _ = color.getHsvF()
    if saturation < ACHROMATIC_SATURATION or hue < 0:
        return QColor(0, 0, 0) if toLab(color)[0] >= 50.0 else QColor(255, 255, 255)
    return QColor.fromHsvF((hue + 0.5) % 1.0, saturation, value)
