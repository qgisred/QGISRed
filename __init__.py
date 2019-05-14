# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QGISRed
                                 A QGIS plugin
 Some util tools for GISRed
                             -------------------
        begin                : 2019-03-26
        copyright            : (C) 2019 by REDHISP (UPV)
        email                : fmartine@hma.upv.es
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load GISRed class from file GISRed.

    :param iface: A QGIS interface instance.
    :type iface: QgisInterface
    """
    #
    from .qgisred_plugins import QGISRed
    return QGISRed(iface)
