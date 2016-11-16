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
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import QgsMessageLog
import resources
from bknqgis_dialog import bknqgisDialog
import os.path
#import pysal as ps
import numpy as np
import geopandas as gpd
import pandas as pd
import shapely as shp
from shapely.geometry import shape
import json
from bokeh.io import output_file, show
from bokeh.models import ColumnDataSource,GeoJSONDataSource,CategoricalColorMapper,HoverTool
from bokeh.plotting import figure
from bokeh.sampledata.sample_geojson import geojson
from bokeh.resources import CDN, INLINE
from bokeh.embed import file_html
from bokeh.charts.attributes import cat, color


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
        self.dlg.outputBTN.clicked.connect(self.select_output_file)
        self.dlg.previewBTN.clicked.connect(self.preview)
        self.dlg.comboBoxLayer.activated.connect(self.onLayerChange)
        self.dlg.lineEditWidth.textEdited.connect(self.onWidthChange)
        self.dlg.lineEditHeight.textEdited.connect(self.onHeightChange)
        self.dlg.lineEditWidth.setValidator(QIntValidator())
        self.dlg.lineEditHeight.setValidator(QIntValidator())
        self.dlg.lineEditWidth.setMaxLength(4)
        self.dlg.lineEditHeight.setMaxLength(4)
        self.dlg.progressBar.setValue(0)
        self.dlg.progressBar.setMinimum(0)
        self.dlg.progressBar.setMaximum(100)
        self.dlg.ratioCheckBox.setChecked(True)
        self.dlg.ratioCheckBox.stateChanged.connect(self.onWidthChange)
        self.dlg.lineEdit.setText('/Users/Ziqi/Desktop/bokeh-map.html')

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

    def run(self):
        """Run method that performs all the real work"""
        #
        self.dlg.comboBoxLayer.clear()
        #self.dlg.progressBar.setValue(0)
        layers = self.iface.legendInterface().layers()
        #layer_list = []
        for layer in layers:
            self.dlg.comboBoxLayer.addItem(layer.name(), layer)
        #self.dlg.comboBoxLayer.addItems(layer_list)
        selectedLayerIndex = self.dlg.comboBoxLayer.currentIndex()
        selectedLayer = self.dlg.comboBoxLayer.itemData(selectedLayerIndex)
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            pass

    def select_output_file(self):
        filename = QFileDialog.getSaveFileName(self.dlg, "Select output file ","", '*.html')
        self.dlg.lineEdit.setText(filename)

    def preview(self):
        file_path = "/Users/Ziqi/Desktop/map.html"
        selectedLayerIndex = self.dlg.comboBoxLayer.currentIndex()
        selectedLayer = self.dlg.comboBoxLayer.itemData(selectedLayerIndex)
        selectedFieldIndex = self.dlg.comboBoxField.currentIndex()
        selectedField = self.dlg.comboBoxField.itemData(selectedFieldIndex)

        settings = {}
        settings["layer"] = selectedLayer
        settings["field"] = self.dlg.valueFieldText.text()
        settings["outputFile"] = self.dlg.lineEdit.text()
        settings["width"] = int(self.dlg.lineEditWidth.text())
        settings["height"] = int(self.dlg.lineEditHeight.text())
        settings["title"] = "Bokeh Test Map"
        print selectedLayer.name()
        print selectedField.name()
        self.bkExport(settings)
        messageBox = QMessageBox()
        messageBox.setWindowTitle( "Success" )
        messageBox.setText( "HTML Exported Successful")
        messageBox.exec_()
        #QgsMessageLog.logMessage("HTML Page Exported")
        print settings["outputFile"]

    def onLayerChange(self, index):
        self.dlg.comboBoxField.clear() # clears the combobox
        layer = self.dlg.comboBoxLayer.itemData( index ) # gets selected layer
        for field in layer.pendingFields():
            self.dlg.comboBoxField.addItem( field.name(), field ) # lists layer fields
        renderer = layer.rendererV2()
        self.dlg.valueFieldText.setText(renderer.usedAttributes()[0])
        ratio = layer.extent().width()/layer.extent().height()
        print (ratio)
        self.dlg.lineEditHeight.setText("1000")
        self.dlg.lineEditWidth.setText(str(int(int(self.dlg.lineEditHeight.text())*ratio)))

    def onWidthChange(self):
        if self.dlg.ratioCheckBox.isChecked():
            print ("checked")
            selectedLayerIndex = self.dlg.comboBoxLayer.currentIndex()
            selectedLayer = self.dlg.comboBoxLayer.itemData(selectedLayerIndex)
            ratio = selectedLayer.extent().width()/selectedLayer.extent().height()
            if self.dlg.lineEditWidth.text():
                self.dlg.lineEditHeight.setText(str(int(int(self.dlg.lineEditWidth.text())/ratio)))
            else:
                self.dlg.lineEditHeight.setText("")
            print (self.dlg.lineEditHeight.text(),self.dlg.lineEditWidth.text())

    def onHeightChange(self):
        if self.dlg.ratioCheckBox.isChecked():
            print ("checked")
            selectedLayerIndex = self.dlg.comboBoxLayer.currentIndex()
            selectedLayer = self.dlg.comboBoxLayer.itemData(selectedLayerIndex)
            ratio = selectedLayer.extent().width()/selectedLayer.extent().height()
            if self.dlg.lineEditHeight.text():
                self.dlg.lineEditWidth.setText(str(int(int(self.dlg.lineEditHeight.text())*ratio)))
            else:
                self.dlg.lineEditWidth.setText("")
            print (self.dlg.lineEditHeight.text(),self.dlg.lineEditWidth.text())

    def gpd_bokeh(self,df):
        """Convert geometries from geopandas to bokeh format"""
        nan = float('nan')
        lons = []
        lats = []
        for i,shape in enumerate(df.geometry.values):
            if shape.geom_type == 'MultiPolygon':
                gx = []
                gy = []
                ng = len(shape.geoms) - 1
                for j,member in enumerate(shape.geoms):
                    xy = np.array(list(member.exterior.coords))
                    xs = xy[:,0].tolist()
                    ys = xy[:,1].tolist()
                    gx.extend(xs)
                    gy.extend(ys)
                    if j < ng:
                        gx.append(nan)
                        gy.append(nan)
                lons.append(gx)
                lats.append(gy)

            else:
                xy = np.array(list(shape.exterior.coords))
                xs = xy[:,0].tolist()
                ys = xy[:,1].tolist()
                lons.append(xs)
                lats.append(ys)

        return lons,lats

    def bkExport(self,settings):
    #layer = iface.legendInterface().layers()[0]
        layer = settings["layer"]
        field = settings["field"]
        gdfList = []
        total = float(layer.featureCount())
        counter = 0
        for feature in layer.getFeatures():
            #print feature.geometry().exportToGeoJSON(17)
            counter = counter+1
            print counter
            self.dlg.progressBar.setValue(counter/total*100)
            featJsonString = feature.geometry().geometry().asJSON(17)
            featJson = json.loads(featJsonString)
            df = {}
            df["geometry"] = shape(featJson)
            df["data"] = feature[field]
            df["class"] = -1
            gdf = gpd.GeoDataFrame([df])
            gdfList.append(gdf)

        gdf2 = gpd.GeoDataFrame(pd.concat(gdfList,ignore_index=True))

        lons, lats = self.gpd_bokeh(gdf2)
        data = list(gdf2["data"])

        #map settings
        #ratio = layer.extent().width()/layer.extent().height()
        #height = int(layer.extent().height()*20)
        height = settings["height"]
        width = settings["width"]
        renderer = layer.rendererV2()
        if renderer.type() == 'singleSymbol':
            print "singleSymbol"
            color = renderer.symbol().color().name()
            color_mapper = CategoricalColorMapper(factors=[-1], palette=[color])
        elif renderer.type() == 'categorizedSymbol':
            print "categorizedSymbol"

        elif renderer.type() == 'graduatedSymbol':
            print "graduatedSymbol"
            ranges = renderer.ranges()

            for i in xrange(len(ranges)):
                print ranges[i].lowerValue()
                print ranges[i].upperValue()
                gdf2["class"][(gdf2["data"] >= ranges[i].lowerValue()) & (gdf2["data"] <= ranges[i].upperValue())] = i

            colorPalette = [symbol.color().name() for symbol in renderer.symbols()]
            color_mapper = CategoricalColorMapper(factors=sorted(list(gdf2["class"].unique())), palette=colorPalette)
        else:
            print "otherSymbols"
        TOOLS = "pan,wheel_zoom,box_zoom,reset,hover,save"

        colorClass  = list(gdf2["class"])
        source = ColumnDataSource(data=dict(
            x=lons,
            y=lats,
            data = data,
            category = colorClass
        ))
        #plot_width=width, plot_height=height,
        p = figure(
            title=settings["title"], tools=TOOLS,plot_width=width, plot_height=height,
            x_axis_location=None, y_axis_location=None
        )
        p.grid.grid_line_color = None
        p.patches('x', 'y', source=source, fill_alpha=1, line_color="black", line_width=0.5,fill_color = {'field': 'category', 'transform': color_mapper},)


        hover = p.select_one(HoverTool)
        hover.point_policy = "follow_mouse"
        hover.tooltips = [
            (field, "@data")
            #("(Long, Lat)", "($x, $y)"),
        ]


        html = file_html(p, CDN, "my plot")
        with open(settings["outputFile"], "w") as my_file:
            my_file.write(html)
        print ("exported")
