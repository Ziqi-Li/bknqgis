# -*- coding: utf-8 -*-
"""
/***************************************************************************
 bknqgis
                                 A QGIS plugin
 Link Bokeh to QGIS
                             -------------------
        begin                : 2016-10-31
        copyright            : (C) 2016 by Ziqi Li
        email                : liziqi1992@gmail.com
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
    """Load bknqgis class from file bknqgis.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .bknqgis import bknqgis
    return bknqgis(iface)
