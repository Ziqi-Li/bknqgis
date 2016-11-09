# -*- coding: utf-8 -*-
"""
/***************************************************************************
 bknqgis
                                 A QGIS plugin
 Link Bokeh to QGIS
                              -------------------
        begin                : 2016-10-31
        git sha              : $Format:%H$
        copyright            : (C) 2016 by Ziqi Li
        email                : liziqi1992@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QUrl
from PyQt4.QtGui import QAction, QIcon, QFileDialog
# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from bknqgis_dialog import bknqgisDialog
import os.path
import pysal

from bokeh.io import output_file, show
from bokeh.models import GeoJSONDataSource
from bokeh.plotting import figure
from bokeh.sampledata.sample_geojson import geojson
from bokeh.plotting import figure
from bokeh.resources import CDN
from bokeh.embed import file_html
import qgis



class bknqgis:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'bknqgis_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = bknqgisDialog()
        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&bknqgis')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'bknqgis')
        self.toolbar.setObjectName(u'bknqgis')
        self.dlg.lineEdit.clear()
        self.dlg.pushButton.clicked.connect(self.select_output_file)
    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        return QCoreApplication.translate('bknqgis', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """



        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToWebMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/bknqgis/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'bknqgis'),
            callback=self.run,
            parent=self.iface.mainWindow())


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginWebMenu(
                self.tr(u'&bknqgis'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar


    def select_output_file(self):
        filename = QFileDialog.getSaveFileName(self.dlg, "Select output file ","", '*.txt')
        self.dlg.lineEdit.setText(filename)

    def run(self):
        """Run method that performs all the real work"""
        layers = self.iface.legendInterface().layers()
        layer_list = []
        for layer in layers:
            layer_list.append(layer.name())
        self.dlg.comboBox.addItems(layer_list)

        file_path = "/Users/Ziqi/Desktop/map.html"
        self.dlg.preview.load(QUrl.fromLocalFile(file_path))


        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            selectedLayerIndex = self.dlg.comboBox.currentIndex()
            selectedLayer = layers[selectedLayerIndex]
            settings = {}
            selectedField = "CRIME"
            settings["layer"] = selectedLayer
            settings["field"] = selectedField
            qgis.bkExport(settings)
            #show(p)
            self.dlg.preview.setUrl(QUrl('/Users/Ziqi/Desktop/map.html'))
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
